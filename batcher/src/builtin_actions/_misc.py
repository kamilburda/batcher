"""Miscellaneous built-in actions."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import builtin_commands_common
from src import exceptions
from src import utils_pdb
from src.path import fileext
from src.procedure_groups import *

from . import _utils as builtin_actions_utils


__all__ = [
  'duplicate_layer',
  'merge_layer',
  'merge_filters',
  'merge_visible_layers',
  'remove_file_extension_from_imported_images',
]


def duplicate_layer(batcher, layer, position):
  layer_position = batcher.current_image.get_item_position(layer)

  if position == builtin_actions_utils.InsertionPositions.BACKGROUND:
    index = layer_position + 1
  elif position == builtin_actions_utils.InsertionPositions.FOREGROUND:
    index = layer_position
  elif position == builtin_actions_utils.InsertionPositions.TOP:
    index = 0
  elif position == builtin_actions_utils.InsertionPositions.BOTTOM:
    index = len(batcher.current_image.get_layers())
  else:
    raise ValueError(f'position {position} is not valid')

  return utils_pdb.copy_and_paste_layer(
    layer,
    batcher.current_image,
    parent=None,
    position=index,
  )


def merge_layer(batcher, layer, merge_type):
  layer_position = batcher.current_image.get_item_position(layer)
  current_layer_position = batcher.current_image.get_item_position(batcher.current_layer)

  if layer_position == current_layer_position - 1:
    _merge_layer(batcher, merge_type, layer, batcher.current_layer, batcher.current_layer)
  elif layer_position == current_layer_position + 1:
    _merge_layer(batcher, merge_type, batcher.current_layer, layer, batcher.current_layer)
  else:
    layers = batcher.current_image.get_layers()

    if layer_position + 1 >= len(layers):
      raise exceptions.SkipCommand(_('No layer below position {}.').format(layer_position))

    _merge_layer(batcher, merge_type, layer, layers[layer_position + 1], layer)


def _merge_layer(
      batcher,
      merge_type,
      layer_to_merge_down,
      layer_below,
      reference_layer,
):
  name = reference_layer.get_name()
  visible = reference_layer.get_visible()
  color_tag = reference_layer.get_color_tag()

  layer_to_merge_down.set_visible(True)
  layer_below.set_visible(True)

  merged_layer = batcher.current_image.merge_down(layer_to_merge_down, merge_type)

  # Avoid errors if merging failed for some reason.
  if merged_layer is not None:
    merged_layer.set_name(name)
    merged_layer.set_visible(visible)
    merged_layer.set_color_tag(color_tag)

    if reference_layer == batcher.current_layer:
      batcher.current_layer = merged_layer


def merge_filters(_batcher, layer):
  layer.merge_filters()


def merge_visible_layers(image_batcher, merge_type):
  image = image_batcher.current_image

  image.merge_visible_layers(merge_type)

  for layer in image.get_layers():
    if not layer.get_visible():
      image.remove_layer(layer)


def remove_file_extension_from_imported_images(image_batcher):
  image = image_batcher.current_item.raw

  if image.get_imported_file() is not None and image.get_xcf_file() is None:
    image_batcher.current_item.name = fileext.get_filename_root(image_batcher.current_item.name)


def _on_after_add_duplicate_layer_action(_actions, action, _orig_action_dict, _settings):
  builtin_commands_common.set_up_display_name_change_for_command(
    _set_display_name_for_duplicate_layer,
    action['arguments/layer'],
    action,
  )


def _set_display_name_for_duplicate_layer(layer_setting, action):
  if layer_setting.value == 'background_layer':
    action['display_name'].set_value(_('Duplicate Layer Below'))
  elif layer_setting.value == 'foreground_layer':
    action['display_name'].set_value(_('Duplicate Layer Above'))
  elif isinstance(layer_setting.value, dict) and layer_setting.value['name'] == 'layer_at_position':
    action['display_name'].set_value(
      _('Duplicate Layer at Position {}').format(layer_setting.value['position']))
  else:
    action['display_name'].set_value(_('Duplicate Layer'))


def _on_after_add_merge_layer_action(_actions, action, _orig_action_dict, _settings):
  builtin_commands_common.set_up_display_name_change_for_command(
    _set_display_name_for_merge_layer,
    action['arguments/layer'],
    action,
  )


def _set_display_name_for_merge_layer(layer_setting, action):
  if layer_setting.value == 'background_layer':
    action['display_name'].set_value(_('Merge with Layer Below'))
  elif layer_setting.value == 'foreground_layer':
    action['display_name'].set_value(_('Merge with Layer Above'))
  elif isinstance(layer_setting.value, dict) and layer_setting.value['name'] == 'layer_at_position':
    action['display_name'].set_value(
      _('Merge Layer {} with Layer Below').format(layer_setting.value['position']))
  else:
    action['display_name'].set_value(_('Merge Layer'))


DUPLICATE_LAYER_DICT = {
  'name': 'duplicate_layer',
  'function': duplicate_layer,
  'display_name': _('Duplicate Layer'),
  'menu_path': _('Layers and Composition'),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
    {
      'type': 'choice',
      'name': 'position',
      'default_value': builtin_actions_utils.InsertionPositions.FOREGROUND,
      'display_name': _('Position'),
      'items': [
        (builtin_actions_utils.InsertionPositions.FOREGROUND, _('Above layer')),
        (builtin_actions_utils.InsertionPositions.BACKGROUND, _('Below layer')),
        (builtin_actions_utils.InsertionPositions.TOP, _('Top')),
        (builtin_actions_utils.InsertionPositions.BOTTOM, _('Bottom')),
      ],
    },
  ],
  'after_add_handler': _on_after_add_duplicate_layer_action,
}


MERGE_LAYER_DICT = {
  'name': 'merge_layer',
  'function': merge_layer,
  'display_name': _('Merge Layer'),
  'menu_path': _('Layers and Composition'),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer_without_current_layer',
      'name': 'layer',
      'display_name': _('Target Layer'),
    },
    {
      'type': 'enum',
      'name': 'merge_type',
      'enum_type': Gimp.MergeType,
      'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
      'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
      'display_name': _('Merge type'),
    },
  ],
  'after_add_handler': _on_after_add_merge_layer_action,
}


MERGE_FILTERS_DICT = {
  'name': 'merge_filters',
  'function': merge_filters,
  'display_name': _('Merge Filters'),
  'menu_path': _('Layers and Composition'),
  'description': _('Merges all visible filters (layer effects) in the specified layer.'),
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
  ],
}

MERGE_VISIBLE_LAYERS_DICT = {
  'name': 'merge_visible_layers',
  'function': merge_visible_layers,
  'display_name': _('Merge Visible Layers'),
  'menu_path': _('Layers and Composition'),
  'description': _(
    'Merges all visible layers within the image into a single layer. Invisible layers are'
    ' removed.\n\nThis is useful if the image contains multiple layers and you want to apply'
    ' filters (layer effects) or other actions on the entire image.'),
  'additional_tags': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'enum',
      'name': 'merge_type',
      'enum_type': Gimp.MergeType,
      'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
      'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
      'display_name': _('Merge type'),
    },
  ],
}

REMOVE_FILE_EXTENSION_FROM_IMPORTED_IMAGES_DICT = {
  'name': 'remove_file_extension_from_imported_images',
  'function': remove_file_extension_from_imported_images,
  'display_name': _('Remove File Extension from Imported Images'),
  'description': _('Imported images represent non-native GIMP files (i.e. not XCF).'),
  'menu_path': _('File and Naming'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
}
