#!/usr/bin/env python3

"""Processing of HTML files from a Jekyll-generated page so that they can be
used without running the Jekyll server (e.g. included in release packages as
user documentation).
"""

import os
import pathlib
import re
import shutil
import sys

import html.parser
import xml.etree.ElementTree as ElementTree

import yaml


FILE_ENCODING = 'utf-8'

FILENAMES_AND_DIRNAMES_TO_REMOVE = [
  'dev',
  'feed.xml',
  'Gemfile',
  'Gemfile.lock',
  'robots.txt',
  'sitemap.xml',
  'staticman.yml',
]

DOCS_DIRNAME = 'documentation'

HTML_DOCTYPE_DECLARATION = '<!DOCTYPE html>'
INDEX_HTML = 'index.html'

HTML_VOID_ELEMENTS = {
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'keygen', 'link',
  'menuitem', 'meta', 'param', 'source', 'track', 'wbr',
}

HTML_ELEMENTS_WITH_URLS = {
  'a': ['href'],
  'applet': ['codebase'],
  'area': ['href'],
  'base': ['href'],
  'blockquote': ['cite'],
  'body': ['background'],
  'del': ['cite'],
  'form': ['action'],
  'frame': ['longdesc', 'src'],
  'head': ['profile'],
  'iframe': ['longdesc', 'src'],
  'img': ['longdesc', 'src', 'usemap'],
  'input': ['src', 'usemap', 'formaction'],
  'ins': ['cite'],
  'link': ['href'],
  'object': ['classid', 'codebase', 'data', 'usemap'],
  'q': ['cite'],
  'script': ['src'],
  'audio': ['src'],
  'button': ['formaction'],
  'command': ['icon'],
  'embed': ['src'],
  'html': ['manifest'],
  'source': ['src'],
  'track': ['src'],
  'video': ['poster', 'src'],
}

PAGE_CONFIG_FILENAME = '_config.yml'
PAGE_CONFIG = None


def main(site_dirpath, page_config_filepath):
  init_page_config(page_config_filepath)

  remove_redundant_files(site_dirpath)

  for html_filepath in get_html_filepaths(site_dirpath):
    parser = get_html_parser(html_filepath)
    html_relative_filepath = os.path.relpath(html_filepath, site_dirpath)

    adjust_boolean_attributes_to_be_valid_xml(parser.tree)

    remove_baseurl_in_url_attributes(html_relative_filepath, parser.tree)

    with open(html_filepath, 'wb') as f:
      write_to_html_file(parser.tree, f)

  reorganize_files(site_dirpath)


def adjust_boolean_attributes_to_be_valid_xml(root):
  for elem in root.iter():
    for attribute_name in elem.attrib:
      if elem.attrib[attribute_name] is None:
        elem.attrib[attribute_name] = ''


class LocalJekyllHTMLParser(html.parser.HTMLParser):
  
  def __init__(self):
    super().__init__()

    self.tree_builder = ElementTree.TreeBuilder()
    self.tree = None
  
  def handle_starttag(self, tag, attributes):
    self.tree_builder.start(tag, dict(attributes))
    if tag in HTML_VOID_ELEMENTS:
      self.tree_builder.end(tag)
  
  def handle_endtag(self, tag):
    self.tree_builder.end(tag)
  
  def handle_startendtag(self, tag, attributes):
    self.tree_builder.start(tag, dict(attributes))
    self.tree_builder.end(tag)

  def handle_data(self, data):
    self.tree_builder.data(data)

  def close(self):
    super().close()

    self.tree = ElementTree.ElementTree(self.tree_builder.close())


def find_all_html_elements_recursive(html_tree, match):
  elements_to_traverse = [html_tree.getroot()]
  matches = []
  
  while elements_to_traverse:
    element = elements_to_traverse.pop(0)
    
    matches.extend(element.findall(match))
    
    elements_to_traverse.extend(list(element))
  
  return matches
  

def get_html_filepaths(site_dirpath):
  html_filepaths = []
  
  for root, _dirnames, filenames in os.walk(site_dirpath):
    for filename in filenames:
      if filename.endswith('.html'):
        html_filepaths.append(os.path.join(root, filename))
  
  return html_filepaths


def remove_redundant_files(site_dirpath):
  for filename in FILENAMES_AND_DIRNAMES_TO_REMOVE:
    filepath_to_remove = os.path.join(site_dirpath, filename)
    if os.path.isfile(filepath_to_remove):
      os.remove(filepath_to_remove)
    elif os.path.isdir(filepath_to_remove):
      shutil.rmtree(filepath_to_remove)


def remove_baseurl_in_url_attributes(html_relative_filepath, html_tree):
  html_relative_filepath_components = pathlib.Path(html_relative_filepath).parts
  
  if len(html_relative_filepath_components) == 0:
    return
  
  if len(html_relative_filepath_components) == 1:
    new_baseurl = '.'
  else:
    new_baseurl = '../' * (len(html_relative_filepath_components) - 1)
    new_baseurl = new_baseurl.rstrip('/')
  
  def _get_relative_url_without_baseurl(url_attribute_value):
    new_url_attribute_value = url_attribute_value
    new_url_attribute_value = re.sub(
      r'^' + re.escape(PAGE_CONFIG['baseurl']), new_baseurl, new_url_attribute_value)
    if re.match(r'.*/[^/]+#[^/]*$', new_url_attribute_value):
      new_url_attribute_value = re.sub(
        r'(.*)/([^/]+)#([^/]*)$', rf'\1/\2/{INDEX_HTML}#\3', new_url_attribute_value)
    elif re.match(r'.*/#[^/]*$', new_url_attribute_value):
      new_url_attribute_value = re.sub(
        r'(.*)/#([^/]*)$', rf'\1/{INDEX_HTML}#\2', new_url_attribute_value)
    else:
      new_url_attribute_value = re.sub(r'/$', rf'/{INDEX_HTML}', new_url_attribute_value)

    return new_url_attribute_value
  
  modify_url_attributes(html_tree, _get_relative_url_without_baseurl)


def modify_url_attributes(html_tree, get_new_url_attribute_value_func):
  for tag, attributes in HTML_ELEMENTS_WITH_URLS.items():
    elements_to_fix = find_all_html_elements_recursive(html_tree, tag)
    
    for element in elements_to_fix:
      for attribute in attributes:
        attribute_value = element.get(attribute)
        if attribute_value is not None:
          element.set(attribute, get_new_url_attribute_value_func(attribute_value))

  elements_with_style_attribute_to_fix = html_tree.findall(".//*[@style]")
  for element in elements_with_style_attribute_to_fix:
    if 'style' in element.attrib:
      style_attribute = element.attrib['style']
      match = re.match(r'(.*url\([\'"])(.*?)([\'"]\).*?)$', style_attribute)
      if match:
        new_url = get_new_url_attribute_value_func(match.group(2))
        element.set('style', f'{match.group(1)}{new_url}{match.group(3)}')


def reorganize_files(site_dirpath):
  """Places all files except the top HTML file in one directory. Files are
  renamed for improved readability.
  """
  docs_dirpath = os.path.normpath(os.path.join(site_dirpath, DOCS_DIRNAME))

  names_to_move = os.listdir(site_dirpath)

  os.makedirs(docs_dirpath, exist_ok=True)

  for name in names_to_move:
    shutil.move(os.path.join(site_dirpath, name), os.path.join(docs_dirpath, name))


def write_to_html_file(html_tree, html_file):
  html_file.write(HTML_DOCTYPE_DECLARATION.encode() + b'\n')
  html_tree.write(html_file, encoding=FILE_ENCODING, xml_declaration=False, method='html')


def get_html_parser(html_filepath):
  parser = LocalJekyllHTMLParser()
  
  with open(html_filepath, 'r', encoding=FILE_ENCODING) as f:
    parser.feed(f.read())
  
  parser.close()
  
  return parser


def init_page_config(page_config_filepath):
  global PAGE_CONFIG
  
  if PAGE_CONFIG is None:
    with open(page_config_filepath, 'r', encoding=FILE_ENCODING) as f:
      PAGE_CONFIG = yaml.load(f.read(), Loader=yaml.SafeLoader)


def modify_url_attributes_in_file(
      html_filepath,
      get_new_url_attribute_value_func,
      output_html_filepath,
      page_config_filepath):
  init_page_config(page_config_filepath)
  
  parser = get_html_parser(html_filepath)
  
  modify_url_attributes(parser.tree, get_new_url_attribute_value_func)
  
  with open(output_html_filepath, 'wb') as f:
    write_to_html_file(parser.tree, f)


if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2])
