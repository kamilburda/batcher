"""Renaming image/layer names according to the specified pattern.

The pattern can contain one or more fields provided in this module.
"""

import collections
import datetime
import os
import pathlib
import re
import string
from typing import Any, Callable, Dict, Generator, List, Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from config import CONFIG
from src import itemtree
from src import utils
from src.path import fileext
from src.path import pattern as pattern_
from src.procedure_groups import *


class ItemRenamer:
  
  def __init__(
        self,
        pattern: str,
        rename_items: bool = True,
        rename_folders: bool = False,
        fields_raw: Optional[Dict[str, Any]] = None,
  ):
    if fields_raw is not None:
      self._fields_raw = fields_raw
    else:
      self._fields_raw = get_fields()

    self._rename_items = rename_items
    self._rename_folders = rename_folders

    self._name_pattern = pattern_.StringPattern(
      pattern=pattern,
      fields=_get_fields_and_substitute_funcs(_init_fields(self._fields_raw)))

  @property
  def fields_raw(self):
    return self._fields_raw

  @property
  def rename_items(self):
    return self._rename_items

  @property
  def rename_folders(self):
    return self._rename_folders

  def rename(self, batcher: 'src.core.Batcher', item: Optional[itemtree.Item] = None):
    if item is None:
      item = batcher.current_item
    
    return self._name_pattern.substitute(self, batcher, item)


def _get_fields_and_substitute_funcs(fields):
  return {
    field.regex: field.substitute_func
    for field in fields if field.substitute_func is not None}


def _init_fields(fields_raw):
  fields = []
  
  for field_raw in fields_raw.values():
    # Use a copy to avoid modifying the original that could be reused.
    field_raw_copy = field_raw.copy()
    
    field_type = field_raw_copy.pop('type')
    fields.append(field_type(**field_raw_copy))
  
  return fields


def get_field_descriptions(fields=None):
  if fields is None:
    fields = get_fields()

  descriptions = []
  
  for field in fields.values():
    if isinstance(field, Field):
      descriptions.append((field.display_name, field.str_to_insert, field.regex, str(field)))
    else:
      descriptions.append(
        (field['display_name'], field['str_to_insert'], field['regex'],
         _get_formatted_examples(field['examples_lines'])))
  
  return descriptions


def _get_formatted_examples(examples_lines):
  if not examples_lines:
    return ''
  
  formatted_examples_lines = []
  
  for example_line in examples_lines:
    if len(example_line) > 1:
      formatted_examples_lines.append(' \u2192 '.join(example_line))
    else:
      formatted_examples_lines.append(*example_line)
  
  return '\n'.join(['<b>{}</b>'.format(_('Examples'))] + formatted_examples_lines)


class Field:
  
  def __init__(
        self,
        regex: str,
        substitute_func: Callable,
        display_name: str,
        str_to_insert: str,
        examples_lines: List[List[str]],
        procedure_groups: List[str],
  ):
    self._regex = regex
    self._substitute_func = substitute_func
    self._display_name = display_name
    self._str_to_insert = str_to_insert
    self._examples_lines = examples_lines
    self._procedure_groups = procedure_groups
  
  def __str__(self) -> str:
    return self.examples
  
  @property
  def regex(self) -> str:
    return self._regex
  
  @property
  def substitute_func(self) -> Callable:
    return self._substitute_func
  
  @property
  def display_name(self) -> str:
    return self._display_name
  
  @property
  def str_to_insert(self) -> str:
    return self._str_to_insert
  
  @property
  def examples_lines(self) -> List[List[str]]:
    return self._examples_lines
  
  @property
  def examples(self) -> str:
    return _get_formatted_examples(self._examples_lines)

  @property
  def procedure_groups(self) -> List[str]:
    return self._procedure_groups


class NumberField(Field):
  
  def __init__(
        self,
        regex: str,
        display_name: str,
        str_to_insert: str,
        examples_lines: List[List[str]],
        procedure_groups: List[str],
  ):
    super().__init__(
      regex,
      self._get_number,
      display_name,
      str_to_insert,
      examples_lines,
      procedure_groups,
    )
    
    # key: field value
    # value: dict of (parent or None, number generator) pairs
    self._global_number_generators = collections.defaultdict(dict)
  
  @staticmethod
  def generate_number(
        initial_number: int,
        padding: int,
        ascending: bool = True,
  ) -> Generator[str, None, None]:
    i = initial_number
    if ascending:
      increment = 1
    else:
      increment = -1
    
    while True:
      str_i = str(i)
      
      if len(str_i) < padding:
        str_i = '0' * (padding - len(str_i)) + str_i
      
      yield str_i
      i += increment
  
  def _get_number(self, renamer, batcher, item, field_value, *args):
    reset_numbering_on_parent = True
    ascending = True
    padding = None
    
    for arg in args:
      if arg == '%n':
        reset_numbering_on_parent = False
      elif arg.startswith('%d'):
        ascending = False
        try:
          padding = int(arg[len('%d'):])
        except ValueError:
          pass
    
    if reset_numbering_on_parent:
      parent_item = item.parent if item.parent is not None else None
      parent = parent_item.key if parent_item is not None else None
    else:
      parent_item = None
      parent = None
    
    if parent not in self._global_number_generators[field_value]:
      padding = padding if padding is not None else len(field_value)
      initial_number = int(field_value)

      if batcher.matching_items is not None:
        if renamer.rename_items and not renamer.rename_folders:
          tree_items = batcher.matching_items
        elif renamer.rename_items and renamer.rename_folders:
          tree_items = batcher.matching_items_and_parents
        elif not renamer.rename_items and renamer.rename_folders:
          tree_items = [
            item for item in batcher.matching_items_and_parents
            if item.type == itemtree.TYPE_FOLDER]
        else:
          tree_items = batcher.matching_items
      else:
        tree_items = batcher.item_tree

      if initial_number == 0 and not ascending:
        if reset_numbering_on_parent:
          if parent_item is not None:
            initial_number = len([
              item_ for item_ in tree_items
              if item_.depth == parent_item.depth + 1 and item_.parent == parent_item])
          else:
            initial_number = len([item_ for item_ in tree_items if item_.depth == 0])
        else:
          initial_number = len(tree_items)
      
      self._global_number_generators[field_value][parent] = self.generate_number(
        initial_number, padding, ascending)
    
    return next(self._global_number_generators[field_value][parent])


class _PercentTemplate(string.Template):
  
  delimiter = '%'


def _get_image_name_for_image_batcher(
      _renamer, image_batcher, item, _field_value, file_extension_strip_mode=''):
  if file_extension_strip_mode == '%e':
    return item.name
  elif file_extension_strip_mode == '%i':
    if fileext.get_file_extension(item.name) == image_batcher.file_extension:
      return item.name
  elif file_extension_strip_mode == '%n':
    if fileext.get_file_extension(item.name) != image_batcher.file_extension:
      return item.name

  return fileext.get_filename_root(item.name)


def _get_image_name_for_layer_batcher(
      _renamer, batcher, _item, _field_value, file_extension_strip_mode=''):
  image = batcher.current_image
  if image is not None and image.get_name() is not None:
    image_name = image.get_name()
  else:
    image_name = _('Untitled')

  if file_extension_strip_mode == '%e':
    return image_name
  else:
    return fileext.get_filename_with_new_file_extension(image_name, '')


def _get_layer_name(
      _renamer,
      layer_batcher,
      item,
      _field_value,
      file_extension_strip_mode='',
):
  if file_extension_strip_mode == '%e':
    return item.name
  elif file_extension_strip_mode == '%i':
    if fileext.get_file_extension(item.name) == layer_batcher.file_extension:
      return item.name
  elif file_extension_strip_mode == '%n':
    if fileext.get_file_extension(item.name) != layer_batcher.file_extension:
      return item.name

  return fileext.get_filename_root(item.name)


def _get_item_path(
      item_substitute_func,
      renamer,
      batcher,
      item,
      field_value,
      separator='-',
      wrapper=None,
      file_extension_strip_mode='',
):
  path_component_token = '%c'
  
  if wrapper is None:
    wrapper = '{}'
  else:
    if path_component_token in wrapper:
      wrapper = wrapper.replace(path_component_token, '{}')
    else:
      wrapper = '{}'
  
  path_components = [parent.name for parent in item.parents]
  path_components += [
    item_substitute_func(renamer, batcher, item, field_value, file_extension_strip_mode)]
  
  return separator.join(wrapper.format(path_component) for path_component in path_components)


def _get_image_path(
      renamer,
      image_batcher,
      item,
      field_value,
      separator='-',
      wrapper=None,
      file_extension_strip_mode='',
):
  return _get_item_path(
    _get_image_name_for_image_batcher,
    renamer,
    image_batcher,
    item,
    field_value,
    separator=separator,
    wrapper=wrapper,
    file_extension_strip_mode=file_extension_strip_mode,
  )


def _get_layer_path(
      renamer,
      layer_batcher,
      item,
      field_value,
      separator='-',
      wrapper=None,
      file_extension_strip_mode='',
):
  return _get_item_path(
    _get_layer_name,
    renamer,
    layer_batcher,
    item,
    field_value,
    separator=separator,
    wrapper=wrapper,
    file_extension_strip_mode=file_extension_strip_mode,
  )


def _get_output_directory(
      _renamer,
      batcher,
      _item,
      _field_value,
      path_component_strip_mode='%b',
      separator='-',
      wrapper=None,
):
  path_component_token = '%c'

  if wrapper is None:
    wrapper = '{}'
  else:
    if path_component_token in wrapper:
      wrapper = wrapper.replace(path_component_token, '{}')
    else:
      wrapper = '{}'

  if batcher.output_directory is not None and batcher.output_directory.get_path() is not None:
    output_dirpath = batcher.output_directory.get_path()
  else:
    output_dirpath = ''

  path_components = pathlib.Path(output_dirpath).parts

  if path_component_strip_mode.startswith('%b'):
    num_path_components_from_end = 1
    try:
      num_path_components_from_end = int(path_component_strip_mode[len('%b'):])
    except ValueError:
      pass

    path_components = path_components[-num_path_components_from_end:]
  elif path_component_strip_mode.startswith('%f'):
    num_path_components_from_start = 1
    try:
      num_path_components_from_start = int(path_component_strip_mode[len('%f'):])
    except ValueError:
      pass

    path_components = path_components[:num_path_components_from_start]

  return separator.join(wrapper.format(path_component) for path_component in path_components)


def _get_tags(_renamer, _layer_batcher, item, _field_value, *args):
  color_tag = item.raw.get_color_tag()
  color_tag_default_names = {
    value: value.value_nick
    for value in utils.get_enum_values(Gimp.ColorTag)}

  # Make sure items without tags produce an empty string.
  del color_tag_default_names[Gimp.ColorTag.NONE]

  color_tag_name = color_tag_default_names.get(color_tag, '')

  if not args:
    return color_tag_name

  color_to_alternate_name_mapping = collections.defaultdict(lambda: color_tag_name)
  tag_token = '%t'

  if not args:
    tag_wrapper = '{}'
  else:
    tag_wrapper = args[0].replace(tag_token, '{}')

  processed_args = args[1:]

  for i in range(0, len(processed_args), 2):
    arg_color_name = processed_args[i].lower()

    if i + 1 < len(processed_args):
      color_to_alternate_name_mapping[arg_color_name] = processed_args[i + 1]
    else:
      color_to_alternate_name_mapping[arg_color_name] = processed_args[i]
      break

  num_token_occurrences = tag_wrapper.count('{}')

  mapped_color_tag_name = color_to_alternate_name_mapping[color_tag_name]

  if mapped_color_tag_name:
    return tag_wrapper.format(*([mapped_color_tag_name] * num_token_occurrences))
  else:
    return ''


def _get_current_date(_renamer, _batcher, _item, _field_value, date_format='%Y-%m-%d'):
  return datetime.datetime.now().strftime(date_format)


def _get_attributes(_renamer, layer_batcher, _item, _field_value, pattern, measure='%px'):
  image = layer_batcher.current_image
  layer = layer_batcher.current_layer

  fields = {}

  if image is not None:
    fields.update({
      'iw': image.get_width(),
      'ih': image.get_height(),
    })

  if layer is not None:
    layer_fields = {}

    if measure == '%px':
      layer_fields = {
        'lw': layer.get_width(),
        'lh': layer.get_height(),
        'lx': layer.get_offsets().offset_x,
        'ly': layer.get_offsets().offset_y,
      }
    elif measure.startswith('%pc'):
      match = re.match(r'^' + re.escape('%pc') + r'([0-9]*)$', measure)

      if match is not None:
        if match.group(1):
          round_digits = int(match.group(1))
        else:
          round_digits = 2

        layer_fields = {
          'lw': round(layer.get_width() / image.get_width(), round_digits),
          'lh': round(layer.get_height() / image.get_height(), round_digits),
          'lx': round(layer.get_offsets().offset_x / image.get_width(), round_digits),
          'ly': round(layer.get_offsets().offset_y / image.get_height(), round_digits),
        }

    fields.update(layer_fields)

  return _PercentTemplate(pattern).safe_substitute(fields)


def _replace(
      renamer,
      batcher,
      item,
      _field_value,
      field_to_replace_str,
      pattern,
      replacement,
      *count_and_flags):
  field_name, field_args = pattern_.StringPattern.parse_field(field_to_replace_str)

  try:
    field_func = renamer.fields_raw[field_name]['substitute_func']
  except KeyError:
    return ''
  
  str_to_process = field_func(renamer, batcher, item, field_name, *field_args)
  
  count = 0
  flags = 0
  
  if len(count_and_flags) >= 1:
    try:
      count = int(count_and_flags[0])
    except ValueError:
      pass

  for flag_name in count_and_flags[1:]:
    processed_flag_name = flag_name.upper()
    if processed_flag_name in re.RegexFlag.__members__:
      flags |= getattr(re, flag_name.upper())
  
  return re.sub(pattern, replacement, str_to_process, count=count, flags=flags)


_examples_lines_for_output_folder_field_for_windows = [
  [_(r'Suppose that the output folder is "C:\Users\username\Pictures".')],
  ['[output folder]', 'Pictures'],
  ['[output folder, %]', 'C-Users-username-Pictures'],
  ['[output folder, %b2]', 'username-Pictures'],
  ['[output folder, %b2, _]', 'username_Pictures'],
  ['[output folder, %b2, _, (%c)]', '(username)_(Pictures)'],
  ['[output folder, %f2]', 'C-Users'],
]


_examples_lines_for_output_folder_field_for_unix = [
  [_('Suppose that the output folder is "/home/username/Pictures".')],
  ['[output folder]', 'Pictures'],
  ['[output folder, %]', 'home-username-Pictures'],
  ['[output folder, %b2]', 'username-Pictures'],
  ['[output folder, %b2, _]', 'username_Pictures'],
  ['[output folder, %b2, _, (%c)]', '(username)_(Pictures)'],
  ['[output folder, %f2]', 'home-username'],
]

if os.name == 'nt':
  _examples_lines_for_output_folder_field = _examples_lines_for_output_folder_field_for_windows
else:
  _examples_lines_for_output_folder_field = _examples_lines_for_output_folder_field_for_unix


_FIELDS_LIST = [
  {
    'type': NumberField,
    'regex': '^[0-9]+$',
    # FOR TRANSLATORS: Translate only the "image" part
    'display_name': _('image001'),
    'str_to_insert': 'image[001]',
    'examples_lines': [
      ['[001]', '001, 002, ...'],
      ['[1]', '1, 2, ...'],
      ['[005]', '005, 006, ...'],
      [_('To continue numbering across folders, use %n.')],
      ['[001, %n]', '001, 002, ...'],
      [_('To use descending numbers, use %d.')],
      [_('Suppose that the number of images is 5:')],
      ['[000, %d]', '005, 004, ...'],
      ['[10, %d2]', '10, 09, ...'],
    ],
    'procedure_groups': ALL_PROCEDURE_GROUPS,
  },
  {
    'type': Field,
    'regex': 'image name',
    'substitute_func': _get_image_name_for_image_batcher,
    'display_name': _('Image name'),
    'str_to_insert': '[image name]',
    'examples_lines': [
      [_('Suppose that an image is named "Image.png" and the file extension is "png".')],
      ['[image name]', 'Image'],
      ['[image name, %e]', 'Image.png'],
      ['[image name, %i]', 'Image.png'],
      ['[image name, %n]', 'Image'],
      [_('Suppose that an image is named "Image.jpg" and the file extension is "png".')],
      ['[image name, %e]', 'Image.jpg'],
      ['[image name, %i]', 'Image'],
      ['[image name, %n]', 'Image.jpg'],
    ],
    'procedure_groups': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'type': Field,
    'regex': 'image path',
    'substitute_func': _get_image_path,
    'display_name': _('Image path'),
    'str_to_insert': '[image path]',
    'examples_lines': [
      [_('Suppose that an image named "Left" has parent folders named "Hands" and "Body".')],
      ['[image path]', 'Body-Hands-Left'],
      ['[image path, _]', 'Body_Hands_Left'],
      ['[image path, _, (%c)]', '(Body)_(Hands)_(Left)'],
      [_('Suppose that an image is named "Left.jpg" and the file extension is "png".')],
      ['[image path, -, %c, %e]', 'Body-Hands-Left.jpg'],
      ['[image path, -, %c, %i]', 'Body-Hands-Left'],
      ['[image path, -, %c, %n]', 'Body-Hands-Left.jpg'],
    ],
    'procedure_groups': [CONVERT_GROUP],
  },
  {
    'type': Field,
    'regex': 'layer name',
    'substitute_func': _get_layer_name,
    'display_name': _('Layer name'),
    'str_to_insert': '[layer name]',
    'examples_lines': [
      [_('Suppose that a layer is named "Frame.png" and the file extension is "png".')],
      ['[layer name]', 'Frame'],
      ['[layer name, %e]', 'Frame.png'],
      ['[layer name, %i]', 'Frame.png'],
      ['[layer name, %n]', 'Frame'],
      [_('Suppose that a layer is named "Frame.jpg" and the file extension is "png".')],
      ['[layer name, %e]', 'Frame.jpg'],
      ['[layer name, %i]', 'Frame'],
      ['[layer name, %n]', 'Frame.jpg'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'full layer name',
    'substitute_func': _get_layer_name,
    'display_name': _('Full layer name'),
    'str_to_insert': '[layer name, %e]',
    'examples_lines': [],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'image name',
    'substitute_func': _get_image_name_for_layer_batcher,
    'display_name': _('Image name'),
    'str_to_insert': '[image name]',
    'examples_lines': [
      [_('Suppose that the image is named "Image.xcf".')],
      ['[image name]', 'Image'],
      ['[image name, %e]', 'Image.xcf'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'layer path',
    'substitute_func': _get_layer_path,
    'display_name': _('Layer path'),
    'str_to_insert': '[layer path]',
    'examples_lines': [
      [_('Suppose that a layer named "Left" has parent groups named "Hands" and "Body".')],
      ['[layer path]', 'Body-Hands-Left'],
      ['[layer path, _]', 'Body_Hands_Left'],
      ['[layer path, _, (%c)]', '(Body)_(Hands)_(Left)'],
      [_('Suppose that the layer is named "Left.jpg" and the file extension is "png".')],
      ['[layer path, -, %c, %e]', 'Body-Hands-Left.jpg'],
      ['[layer path, -, %c, %i]', 'Body-Hands-Left'],
      ['[layer path, -, %c, %n]', 'Body-Hands-Left.jpg'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'output folder',
    'substitute_func': _get_output_directory,
    'display_name': _('Output folder'),
    'str_to_insert': '[output folder]',
    'examples_lines': _examples_lines_for_output_folder_field,
    'procedure_groups': ALL_PROCEDURE_GROUPS,
  },
  {
    'type': Field,
    'regex': 'tags',
    'substitute_func': _get_tags,
    'display_name': _('Tags'),
    'str_to_insert': '[tags]',
    'examples_lines': [
      [_('Suppose that a layer has a green color tag.')],
      ['[tags]', 'green'],
      [_('You can map a color to another name.')],
      ['[tags, %t, green, background]', 'background'],
      ['[tags, (%t), green, background]', '(background)'],
      [_('Missing tags are ignored.')],
      ['[tags, %t, blue, foreground]', ''],
      ['[tags, %t, green, background, blue, foreground]', 'background'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'current date',
    'substitute_func': _get_current_date,
    'display_name': _('Current date'),
    'str_to_insert': '[current date]',
    'examples_lines': [
      ['[current date]', '2019-01-28'],
      [_('Custom date format uses formatting as per the "strftime" function in Python.')],
      ['[current date, %m.%d.%Y_%H-%M]', '28.01.2019_19-04'],
    ],
    'procedure_groups': ALL_PROCEDURE_GROUPS,
  },
  {
    'type': Field,
    'regex': 'attributes',
    'substitute_func': _get_attributes,
    'display_name': _('Attributes'),
    'str_to_insert': '[attributes]',
    'examples_lines': [
      [_('Suppose that an image has width and height of 1000 and 500 pixels, respectively,'
         'and the current layer has width, height, <i>x</i>-offset and <i>y</i>-offset\n'
         'of 1000, 270, 0 and 40 pixels, respectively.')],
      ['[attributes, %iw-%ih]', '1000-500'],
      ['[attributes, %lw-%lh-%lx-%ly]', '1000-270-0-40'],
      ['[attributes, %lw-%lh-%lx-%ly, %pc]', '1.0-0.54-0.0-0.08'],
      ['[attributes, %lw-%lh-%lx-%ly, %pc1]', '1.0-0.5-0.0-0.1'],
    ],
    'procedure_groups': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'type': Field,
    'regex': 'attributes',
    'substitute_func': _get_attributes,
    'display_name': _('Attributes'),
    'str_to_insert': '[attributes]',
    'examples_lines': [
      [_('Suppose that a layer has width, height, <i>x</i>-offset and <i>y</i>-offset\n'
         'of 1000, 270, 0 and 40 pixels, respectively,\n'
         'and the image has width and height of 1000 and 500 pixels, respectively.')],
      ['[attributes, %lw-%lh-%lx-%ly]', '1000-270-0-40'],
      ['[attributes, %lw-%lh-%lx-%ly, %pc]', '1.0-0.54-0.0-0.08'],
      ['[attributes, %lw-%lh-%lx-%ly, %pc1]', '1.0-0.5-0.0-0.1'],
      ['[attributes, %iw-%ih]', '1000-500'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
  {
    'type': Field,
    'regex': 'replace',
    'substitute_func': _replace,
    'display_name': _('Replace'),
    'str_to_insert': '[replace]',
    'examples_lines': [
      [_('Suppose that an image is named "Animal copy #1".')],
      ['[replace, [image name], [a], [b] ]', 'Animbl copy #1'],
      [_('You can use the regular expression syntax as defined in the "re" module for Python.')],
      ['[replace, [image name], [ copy(?: #[[0-9]]+)*$], [] ]', 'Animal'],
      [_('You can specify the number of replacements and flags as defined'
         ' in the "re" module for Python.')],
      ['[replace, [image name], [a], [b], 1, ignorecase]', 'bnimal copy #1'],
    ],
    'procedure_groups': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'type': Field,
    'regex': 'replace',
    'substitute_func': _replace,
    'display_name': _('Replace'),
    'str_to_insert': '[replace]',
    'examples_lines': [
      [_('Suppose that a layer is named "Animal copy #1".')],
      ['[replace, [layer name], [a], [b] ]', 'Animbl copy #1'],
      [_('You can use the regular expression syntax as defined in the "re" module for Python.')],
      ['[replace, [layer name], [ copy(?: #[[0-9]]+)*$], [] ]', 'Animal'],
      [_('You can specify the number of replacements and flags as defined'
         ' in the "re" module for Python.')],
      ['[replace, [layer name], [a], [b], 1, ignorecase]', 'bnimal copy #1'],
    ],
    'procedure_groups': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
  },
]


def get_fields(tags=None):
  if tags is None:
    tags = [CONFIG.PROCEDURE_GROUP]

  return {
    field['regex']: field
    for field in _FIELDS_LIST
    if any(tag in field['procedure_groups'] for tag in tags)
  }
