"""Extracting GUI attributes for GEGL operations (layer effects) provided by
GIMP.

Since there is no way currently to obtain GUI-specific numerical properties
for `GimpUi.SpinScale` for GEGL operations such as soft boundaries or step
sizes, these must be hard-coded in the plug-in. The official GEGL
documentation is scraped for contents.
"""

import os
import html.parser
import json
import re
import urllib.request
import urllib.parse

from src import utils


GEGL_DOCS_BASE_URL = 'https://www.gegl.org/operations/'

DEV_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))
PLUGIN_DIRPATH = os.path.dirname(DEV_DIRPATH)
SRC_DIRPATH = os.path.join(PLUGIN_DIRPATH, 'src')

OUTPUT_FILEPATH = os.path.join(SRC_DIRPATH, '_gegl_operations_custom_attributes.py')


class OperationsIndexParser(html.parser.HTMLParser):
  def __init__(self):
    super().__init__()

    self.links = set()

  def handle_starttag(self, tag, attributes):
    if tag != 'a':
      return

    href = dict(attributes).get('href', '')

    # Example: gegl-waves.html
    # While the hierarchy of the GEGL index page is more complex, it is
    # sufficient to check for prefixes in this case.
    if any(href.startswith(prefix) for prefix in ['gegl-', 'svg-']) and href.endswith('.html'):
      self.links.add(href)

  def get_links(self, base_url):
    return [urllib.parse.urljoin(base_url, link) for link in self.links]


def fetch(url):
  request = urllib.request.Request(
    url,
    headers={
      'User-Agent': 'Mozilla/5.0',
    },
  )

  with urllib.request.urlopen(request) as response:
    return response.read().decode('utf-8', errors='ignore')


def extract_operation_name_from_title(operation_html):
  match = re.search(
    r'<title>\s*(.*?)\s*</title>',
    operation_html,
    flags=re.IGNORECASE | re.DOTALL,
  )

  if not match:
    return None

  return match.group(1).strip()


def extract_ui_attributes(html_text):
  attributes_to_keep = [
    'ui-minimum',
    'ui-maximum',
    'ui-gamma',
    'ui-step-small',
    'ui-step-big',
    'ui-digits',
  ]

  matches = re.findall(f'name:.*?</div>', html_text, flags=re.DOTALL | re.IGNORECASE)

  arguments = {}

  for match in matches:
    processed_match = match.replace('&nbsp;', '').replace('<b>', '').replace('</b>', '')

    raw_attributes = [line.strip() for line in processed_match.splitlines()]
    attributes_for_argument = {}
    for raw_attribute in raw_attributes:
      components = raw_attribute.split(':')
      if (len(components) == 2
          and (components[0] in attributes_to_keep or components[0] in ['type', 'name'])):
        attributes_for_argument[components[0]] = components[1]

    if ('name' in attributes_for_argument
        and attributes_for_argument.get('type') in ['int', 'double']):
      arguments[attributes_for_argument['name']] = attributes_for_argument

  return arguments


def format_attributes_for_commands(operations_and_attributes):
  attribute_name_map = {
    'ui-minimum': 'soft_minimum',
    'ui-maximum': 'soft_maximum',
    'ui-gamma': 'gamma',
    'ui-step-small': 'step_increment',
    'ui-step-big': 'page_increment',
    'ui-digits': 'digits',
  }

  output = {}

  for operation_name, arguments in operations_and_attributes.items():
    output[operation_name] = {}

    for argument_name, attributes in arguments.items():
      output[operation_name][argument_name] = {'gui_type_kwargs': {}}

      attribute_dict = output[operation_name][argument_name]['gui_type_kwargs']
      for attribute_name, value in attributes.items():
        value_type = attributes['type']

        if attribute_name not in attribute_name_map:
          continue

        if 'inf' in value:
          continue

        if value_type == 'int':
          value_class = int
        elif value_type == 'double':
          value_class = float
        else:
          continue

        try:
          processed_value = value_class(value)
        except Exception:
          continue

        attribute_dict[attribute_name_map[attribute_name]] = processed_value

      # The docs show only two digits. However, three are required in this case.
      # Taken from:
      # https://gitlab.gnome.org/GNOME/gegl/-/blob/master/gegl/gegl-op.h#L758
      if ('step_increment' in attribute_dict
          and attribute_dict['step_increment'] == 0.0
          and 'page_increment' in attribute_dict
          and attribute_dict['page_increment'] == 0.1
          and 'soft_maximum' in attribute_dict
          and attribute_dict['soft_maximum'] <= 5.0):
        attribute_dict['step_increment'] = 0.001

  return output


def main():
  index_html = fetch(GEGL_DOCS_BASE_URL)

  parser = OperationsIndexParser()
  parser.feed(index_html)

  operations_and_arguments = {}

  for op_url in sorted(parser.get_links(GEGL_DOCS_BASE_URL)):
    try:
      print(f'Processing: {op_url}')

      operation_html_text = fetch(op_url)

      operation_name = extract_operation_name_from_title(operation_html_text)

      if not operation_name:
        print(f'Missing <title> in {op_url}')
        continue

      arguments = extract_ui_attributes(operation_html_text)

      if arguments:
        operations_and_arguments[operation_name] = arguments

    except Exception as e:
      print(f'Failed: {op_url}')
      print(f'Error: {e}')

  output = format_attributes_for_commands(operations_and_arguments)

  # We avoid constructing and unparsing an AST by exploiting the fact that
  # JSON objects are parsed as Python dictionaries.
  raw_output = json.dumps(output, indent=2, ensure_ascii=False)
  # Single quotes are used in the plug-in source code everywhere.
  raw_output = raw_output.replace('"', "'")

  raw_output = f'''"""Custom attributes for GEGL operations (layer effects) installed in GIMP."""

GEGL_OPERATIONS_AND_CUSTOM_ATTRIBUTES = {raw_output}
'''

  with open(OUTPUT_FILEPATH, 'w', encoding='utf-8') as f:
    f.write(raw_output)

  print(f'Output successfully written to {OUTPUT_FILEPATH}')


if __name__ == '__main__':
  main()
