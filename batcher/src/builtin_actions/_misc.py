"""An assorted collection of simple built-in actions."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import builtin_commands_common
from src.path import fileext
from src.procedure_groups import *


__all__ = [
  'apply_opacity_from_group_layers',
  'merge_filters',
  'merge_visible_layers',
]


def apply_opacity_from_group_layers(layer_batcher):
  new_layer_opacity = layer_batcher.current_layer.get_opacity() / 100.0

  raw_parent = layer_batcher.current_item.raw.get_parent()
  while raw_parent is not None:
    new_layer_opacity = new_layer_opacity * (raw_parent.get_opacity() / 100.0)
    raw_parent = raw_parent.get_parent()

  layer_batcher.current_layer.set_opacity(new_layer_opacity * 100.0)


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


APPLY_OPACITY_FROM_GROUP_LAYERS_DICT = {
  'name': 'apply_opacity_from_group_layers',
  'function': apply_opacity_from_group_layers,
  'display_name': _('Apply opacity from group layers'),
  'description': _(
    'Combines opacity from all parent group layers and the current layer.'),
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
}

MERGE_FILTERS_DICT = {
  'name': 'merge_filters',
  'function': merge_filters,
  'display_name': _('Merge filters'),
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
  'display_name': _('Merge visible layers'),
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
  'display_name': _('Remove file extension from imported images'),
  'description': _('Imported images represent non-native GIMP files (i.e. not XCF).'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
}
