"""Built-in conditions."""

import re

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import file_formats as file_formats_
from src import itemtree
from src.path import fileext
from src.procedure_groups import *


def is_layer(item, _layer_batcher):
  return item.type == itemtree.TYPE_ITEM


def is_nonempty_group(item, _layer_batcher):
  return item.type == itemtree.TYPE_GROUP and item.raw.get_children()


def is_imported(item, _image_batcher):
  return item.raw.get_imported_file() is not None


def is_not_imported(item, _image_batcher):
  return not is_imported(item, _image_batcher)


def has_matching_file_extension(item, batcher):
  return fileext.get_file_extension(item.orig_name).lower() == batcher.file_extension.lower()


def is_matching_text(item, _batcher, match_mode, text, ignore_case_sensitivity):
  if not text:
    return True

  if ignore_case_sensitivity:
    processed_item_name = item.orig_name.lower()
    processed_text = text.lower()
  else:
    processed_item_name = item.orig_name
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
  file_extension = fileext.get_file_extension(item.orig_name).lower()
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


def has_xcf_file(item, _image_batcher):
  return item.raw.get_xcf_file() is not None


def has_no_xcf_file(item, image_batcher):
  return not has_xcf_file(item, image_batcher)


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


_BUILTIN_CONDITIONS_LIST = [
  {
    'name': 'layers',
    'type': 'condition',
    'function': is_layer,
    'display_name': _('Layers'),
    'menu_path': _('Layer'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'group_layers',
    'type': 'condition',
    'function': is_nonempty_group,
    'display_name': _('Group Layers'),
    'menu_path': _('Layer'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'visible',
    'type': 'condition',
    'function': is_visible,
    # FOR TRANSLATORS: Think of "Only visible items" when translating this
    'display_name': _('Visible'),
    'menu_path': _('Layer'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'selected_in_gimp',
    'type': 'condition',
    'function': is_item_in_items_selected_in_gimp,
    # FOR TRANSLATORS: Think of "Only items selected in GIMP" when translating this
    'display_name': _('Selected in GIMP'),
    'menu_path': _('Layer'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'with_color_tags',
    'type': 'condition',
    'function': has_color_tags,
    # FOR TRANSLATORS: Think of "Only items with color tags" when translating this
    'display_name': _('With Color Tags'),
    'menu_path': _('Layer'),
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
    'type': 'condition',
    'function': has_no_color_tags,
    # FOR TRANSLATORS: Think of "Only items without color tags" when translating this
    'display_name': _('Without Color Tags'),
    'menu_path': _('Layer'),
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
    'name': 'not_background',
    'type': 'condition',
    'function': has_no_color_tag,
    # FOR TRANSLATORS: Think of "Only items that are not background" when translating this
    'display_name': _('Not Background'),
    'menu_path': _('Layer'),
    # This condition is added/removed automatically alongside `insert_background_for_layers`.
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
    'type': 'condition',
    'function': has_no_color_tag,
    # FOR TRANSLATORS: Think of "Only items that are not foreground" when translating this
    'display_name': _('Not Foreground'),
    'menu_path': _('Layer'),
    # This condition is added/removed automatically alongside `insert_foreground_for_layers`.
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
    'name': 'matching_text',
    'type': 'condition',
    'function': is_matching_text,
    # FOR TRANSLATORS: Think of "Only items matching text" when translating this
    'display_name': _('Matching Text...'),
    'menu_path': _('Naming'),
    'additional_tags': ALL_PROCEDURE_GROUPS,
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
    'name': 'matching_file_extension',
    'type': 'condition',
    'function': has_matching_file_extension,
    # FOR TRANSLATORS: Think of "Only items matching file extension" when translating this
    'display_name': _('Matching File Extension'),
    'menu_path': _('Naming'),
    'additional_tags': ALL_PROCEDURE_GROUPS,
  },
  {
    'name': 'recognized_file_format',
    'type': 'condition',
    'function': has_recognized_file_format,
    # FOR TRANSLATORS: Think of "Only items with a recognized file format" when translating this
    'display_name': _('Recognized File Format'),
    'menu_path': _('Naming'),
    'additional_tags': [CONVERT_GROUP],
  },
  {
    'name': 'imported',
    'type': 'condition',
    'function': is_imported,
    'display_name': _('Imported'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_imported',
    'type': 'condition',
    'function': is_not_imported,
    'display_name': _('Not Imported'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'saved_or_exported',
    'type': 'condition',
    'function': is_saved_or_exported,
    'display_name': _('Saved or Exported'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_saved_or_exported',
    'type': 'condition',
    'function': is_not_saved_or_exported,
    'display_name': _('Not Saved or Exported'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'with_unsaved_changes',
    'type': 'condition',
    'function': has_unsaved_changes,
    # FOR TRANSLATORS: Think of "Only items with unsaved changes" when translating this
    'display_name': _('With Unsaved Changes'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'with_no_unsaved_changes',
    'type': 'condition',
    'function': has_no_unsaved_changes,
    # FOR TRANSLATORS: Think of "Only items with no unsaved changes" when translating this
    'display_name': _('With No Unsaved Changes'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'xcf_file',
    'type': 'condition',
    'function': has_xcf_file,
    # FOR TRANSLATORS: Think of "Only items being an XCF (native GIMP) file" when translating this
    'display_name': _('XCF (Native GIMP) File'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'not_xcf_file',
    'type': 'condition',
    'function': has_no_xcf_file,
    # FOR TRANSLATORS: Think of "Only items not being an XCF file" when translating this
    'display_name': _('Not XCF (Native GIMP) File'),
    'menu_path': _('File'),
    'additional_tags': [EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  },
  {
    'name': 'top_level',
    'type': 'condition',
    'function': is_top_level,
    # FOR TRANSLATORS: Think of "Only top-level items" when translating this
    'display_name': _('Top-Level'),
    'additional_tags': [CONVERT_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
]

# Create a separate dictionary for functions since objects cannot be saved to
# a persistent source. Saving them as strings would not be reliable as
# function names and paths may change when refactoring or adding/modifying
# features. The 'function' setting is set to an empty value as the function
# can be inferred via the command's 'orig_name' setting.
BUILTIN_CONDITIONS = {}
BUILTIN_CONDITIONS_FUNCTIONS = {}

# A filter is a function indicating when a command should not be available.
# This can be useful to hide built-in commands that depend on the presence of
# a third-party plug-in or to make the command (un)available for particular
# versions of GIMP.
BUILTIN_CONDITIONS_AVAILABILITY_FUNCTIONS = {}

for command_dict in _BUILTIN_CONDITIONS_LIST:
  function = command_dict['function']
  command_dict['function'] = ''

  BUILTIN_CONDITIONS[command_dict['name']] = command_dict
  BUILTIN_CONDITIONS_FUNCTIONS[command_dict['name']] = function

  if 'available' in command_dict:
    BUILTIN_CONDITIONS_AVAILABILITY_FUNCTIONS[command_dict['name']] = command_dict.pop('available')
