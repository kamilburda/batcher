"""Built-in constraints."""

import re

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import file_formats as file_formats_
from src.path import fileext
from src.procedure_groups import *


def is_layer(item, _layer_batcher):
  return item.type == pg.itemtree.TYPE_ITEM


def is_nonempty_group(item, _layer_batcher):
  return item.type == pg.itemtree.TYPE_GROUP and item.raw.get_children()


def is_imported(item, _image_batcher):
  return item.raw.get_imported_file() is not None


def is_not_imported(item, _image_batcher):
  return not is_imported(item, _image_batcher)


def has_matching_file_extension(item, batcher):
  return fileext.get_file_extension(item.name).lower() == batcher.file_extension.lower()


def is_matching_text(item, _batcher, match_mode, text, ignore_case_sensitivity):
  if not text:
    return True

  if ignore_case_sensitivity:
    processed_item_name = item.name.lower()
    processed_text = text.lower()
  else:
    processed_item_name = item.name
    processed_text = text

  if match_mode == MatchModes.STARTS_WITH:
    return processed_item_name.startswith(processed_text)
  elif match_mode == MatchModes.DOES_NOT_START_WITH:
    return not processed_item_name.startswith(processed_text)
  elif match_mode == MatchModes.CONTAINS:
    return processed_text in processed_item_name
  elif match_mode == MatchModes.DOES_NOT_CONTAIN:
    return processed_text not in processed_item_name
  elif match_mode == MatchModes.ENDS_WITH:
    return processed_item_name.endswith(processed_text)
  elif match_mode == MatchModes.DOES_NOT_END_WITH:
    return not processed_item_name.endswith(processed_text)
  elif match_mode == MatchModes.REGEX:
    try:
      match = re.search(processed_text, processed_item_name)
    except re.error:
      return False
    else:
      return match is not None
  else:
    raise ValueError(
      f'unrecognized match mode; must be one of: {", ".join(MatchModes.MATCH_MODES)}')


def has_recognized_file_format(item, _image_batcher):
  file_extension = fileext.get_file_extension(item.name).lower()
  return (
    file_extension
    and file_extension in file_formats_.FILE_FORMATS_DICT
    and file_formats_.FILE_FORMATS_DICT[file_extension].has_import_proc()
  )


def is_saved_or_exported(item, _image_batcher):
  return item.raw.get_file() is not None


def is_not_saved_or_exported(item, _image_batcher):
  return not is_saved_or_exported(item, _image_batcher)


def is_item_in_items_selected_in_gimp(item, _layer_batcher):
  image = item.raw.get_image()
  return image.is_valid() and item.raw in image.get_selected_layers()


def is_top_level(item, _batcher):
  return item.depth == 0


def is_visible(item, _layer_batcher):
  return item.raw.get_visible()


def has_color_tag(item, _layer_batcher, color_tag, *_args, **_kwargs):
  return item.raw.get_color_tag() == color_tag


def has_color_tags(item, _layer_batcher, color_tags=None):
  item_color_tag = item.raw.get_color_tag()

  if item_color_tag == Gimp.ColorTag.NONE:
    return False
  else:
    if color_tags:
      return any(item_color_tag == tag for tag in color_tags)
    else:
      return item_color_tag != Gimp.ColorTag.NONE


def has_no_color_tag(item, _layer_batcher, color_tag, *_args, **_kwargs):
  return not has_color_tag(item, _layer_batcher, color_tag)


def has_no_color_tags(item, _layer_batcher, color_tags=None):
  return not has_color_tags(item, _layer_batcher, color_tags)


def has_unsaved_changes(item, _image_batcher):
  return item.raw.is_dirty()


def has_no_unsaved_changes(item, _image_batcher):
  return not has_unsaved_changes(item, _image_batcher)


class MatchModes:
  MATCH_MODES = (
    STARTS_WITH,
    DOES_NOT_START_WITH,
    CONTAINS,
    DOES_NOT_CONTAIN,
    ENDS_WITH,
    DOES_NOT_END_WITH,
    REGEX,
  ) = (
    'starts_with',
    'does_not_start_with',
    'contains',
    'does_not_contain',
    'ends_with',
    'does_not_end_with',
    'regex',
  )


_BUILTIN_CONSTRAINTS_LIST = [
  {
    'name': 'layers',
    'type': 'constraint',
    'function': is_layer,
    'display_name': _('Layers'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'group_layers',
    'type': 'constraint',
    'function': is_nonempty_group,
    'display_name': _('Group layers'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'imported',
    'type': 'constraint',
    'function': is_imported,
    'display_name': _('Imported'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_imported',
    'type': 'constraint',
    'function': is_not_imported,
    'display_name': _('Not imported'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_background',
    'type': 'constraint',
    'function': has_no_color_tag,
    # FOR TRANSLATORS: Think of "Only items that are not background" when translating this
    'display_name': _('Not background'),
    # This constraint is added/removed automatically alongside `insert_background_for_layers`.
    'additional_tags': [],
    'arguments': [
      {
        'type': 'enum',
        'name': 'color_tag',
        'enum_type': Gimp.ColorTag,
        'excluded_values': [Gimp.ColorTag.NONE],
        'default_value': Gimp.ColorTag.BLUE,
        'gui_type': None,
      },
      {
        'type': 'bool',
        'name': 'last_enabled_value',
        'default_value': True,
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'not_foreground',
    'type': 'constraint',
    'function': has_no_color_tag,
    # FOR TRANSLATORS: Think of "Only items that are not foreground" when translating this
    'display_name': _('Not foreground'),
    # This constraint is added/removed automatically alongside `insert_foreground_for_layers`.
    'additional_tags': [],
    'arguments': [
      {
        'type': 'enum',
        'name': 'color_tag',
        'enum_type': Gimp.ColorTag,
        'excluded_values': [Gimp.ColorTag.NONE],
        'default_value': Gimp.ColorTag.GREEN,
        'gui_type': None,
      },
      {
        'type': 'bool',
        'name': 'last_enabled_value',
        'default_value': True,
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'matching_file_extension',
    'type': 'constraint',
    'function': has_matching_file_extension,
    # FOR TRANSLATORS: Think of "Only items matching file extension" when translating this
    'display_name': _('Matching file extension'),
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'matching_text',
    'type': 'constraint',
    'function': is_matching_text,
    # FOR TRANSLATORS: Think of "Only items matching text" when translating this
    'display_name': _('Matching text...'),
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'choice',
        'name': 'match_mode',
        'default_value': MatchModes.CONTAINS,
        'items': [
          (MatchModes.STARTS_WITH, _('Starts with text')),
          (MatchModes.DOES_NOT_START_WITH, _('Does not start with text')),
          (MatchModes.CONTAINS, _('Contains text')),
          (MatchModes.DOES_NOT_CONTAIN, _('Does not contain text')),
          (MatchModes.ENDS_WITH, _('Ends with text')),
          (MatchModes.DOES_NOT_END_WITH, _('Does not end with text')),
          (MatchModes.REGEX, _('Matches regular expression')),
        ],
        'display_name': _('How to perform matching'),
      },
      {
        'type': 'string',
        'name': 'text',
        'default_value': 'image',
        'display_name': _('Text to match'),
      },
      {
        'type': 'bool',
        'name': 'ignore_case_sensitivity',
        'default_value': False,
        'display_name': _('Ignore case sensitivity'),
      },
    ],
  },
  {
    'name': 'recognized_file_format',
    'type': 'constraint',
    'function': has_recognized_file_format,
    # FOR TRANSLATORS: Think of "Only items with a recognized file format" when translating this
    'display_name': _('Recognized file format'),
    'additional_tags': [CONVERT_GROUP],
  },
  {
    'name': 'saved_or_exported',
    'type': 'constraint',
    'function': is_saved_or_exported,
    'display_name': _('Saved or exported'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_saved_or_exported',
    'type': 'constraint',
    'function': is_not_saved_or_exported,
    'display_name': _('Not saved or exported'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'selected_in_gimp',
    'type': 'constraint',
    'function': is_item_in_items_selected_in_gimp,
    # FOR TRANSLATORS: Think of "Only items selected in GIMP" when translating this
    'display_name': _('Selected in GIMP'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'top_level',
    'type': 'constraint',
    'function': is_top_level,
    # FOR TRANSLATORS: Think of "Only top-level items" when translating this
    'display_name': _('Top-level'),
    'additional_tags': [CONVERT_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'visible',
    'type': 'constraint',
    'function': is_visible,
    # FOR TRANSLATORS: Think of "Only visible items" when translating this
    'display_name': _('Visible'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'with_color_tags',
    'type': 'constraint',
    'function': has_color_tags,
    # FOR TRANSLATORS: Think of "Only items with color tags" when translating this
    'display_name': _('With color tags'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
    'arguments': [
      {
        'type': 'array',
        'name': 'color_tags',
        'display_name': _('Color tags'),
        'element_type': 'enum',
        'element_enum_type': Gimp.ColorTag,
        'element_excluded_values': [Gimp.ColorTag.NONE],
        'element_default_value': Gimp.ColorTag.BLUE,
        'default_value': (),
      },
    ],
  },
  {
    'name': 'without_color_tags',
    'type': 'constraint',
    'function': has_no_color_tags,
    # FOR TRANSLATORS: Think of "Only items without color tags" when translating this
    'display_name': _('Without color tags'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
    'arguments': [
      {
        'type': 'array',
        'name': 'color_tags',
        'display_name': _('Color tags'),
        'element_type': 'enum',
        'element_enum_type': Gimp.ColorTag,
        'element_excluded_values': [Gimp.ColorTag.NONE],
        'element_default_value': Gimp.ColorTag.BLUE,
        'default_value': (),
      },
    ],
  },
  {
    'name': 'with_unsaved_changes',
    'type': 'constraint',
    'function': has_unsaved_changes,
    # FOR TRANSLATORS: Think of "Only items with unsaved changes" when translating this
    'display_name': _('With unsaved changes'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'with_no_unsaved_changes',
    'type': 'constraint',
    'function': has_no_unsaved_changes,
    # FOR TRANSLATORS: Think of "Only items with no unsaved changes" when translating this
    'display_name': _('With no unsaved changes'),
    'additional_tags': [EXPORT_IMAGES_GROUP],
  },
]

# Translated display names could be displayed out of alphabetical order,
# hence the sorting.
_BUILTIN_CONSTRAINTS_LIST.sort(
  key=lambda item: item.get('menu_path', item.get('display_name', item['name'])))

# Create a separate dictionary for functions since objects cannot be saved
# to a persistent source. Saving them as strings would not be reliable as
# function names and paths may change when refactoring or adding/modifying features.
# The 'function' setting is set to an empty value as the function can be inferred
# via the action's 'orig_name' setting.
BUILTIN_CONSTRAINTS = {}
BUILTIN_CONSTRAINTS_FUNCTIONS = {}

for action_dict in _BUILTIN_CONSTRAINTS_LIST:
  function = action_dict['function']
  action_dict['function'] = ''
  
  BUILTIN_CONSTRAINTS[action_dict['name']] = action_dict
  BUILTIN_CONSTRAINTS_FUNCTIONS[action_dict['name']] = function
