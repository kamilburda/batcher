"""Built-in "Rename" procedure."""

from src import builtin_actions_common
from src import renamer as renamer_
from src.procedure_groups import *


__all__ = [
  'rename_image',
  'rename_layer',
]


def rename_image(image_batcher, pattern, rename_images=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern, rename_images, rename_folders)
  renamed_parents = set()

  while True:
    if rename_folders:
      for parent in image_batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(image_batcher, item=parent)
          renamed_parents.add(parent)

    if rename_images:
      image_batcher.current_item.name = renamer.rename(image_batcher)

    yield


def rename_layer(layer_batcher, pattern, rename_layers=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern, rename_layers, rename_folders)
  renamed_parents = set()

  while True:
    if rename_folders:
      for parent in layer_batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(layer_batcher, item=parent)
          renamed_parents.add(parent)

          if (layer_batcher.edit_mode
              and layer_batcher.process_names
              and not layer_batcher.is_preview):
            parent.raw.set_name(parent.name)

    if rename_layers:
      layer_batcher.current_item.name = renamer.rename(layer_batcher)

      if layer_batcher.process_names and not layer_batcher.is_preview:
        layer_batcher.current_layer.set_name(layer_batcher.current_item.name)

    yield


RENAME_FOR_CONVERT_DICT = {
  'name': 'rename_for_convert',
  'function': rename_image,
  'display_name': _('Rename'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, CONVERT_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'rename_images',
      'default_value': True,
      'display_name': _('Rename images'),
    },
    {
      'type': 'bool',
      'name': 'rename_folders',
      'default_value': False,
      'display_name': _('Rename folders'),
    },
  ],
}

RENAME_FOR_EXPORT_IMAGES_DICT = {
  'name': 'rename_for_export_images',
  'function': rename_image,
  'display_name': _('Rename'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_IMAGES_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'rename_images',
      'default_value': True,
      'display_name': _('Rename images'),
    },
  ],
}

RENAME_FOR_EXPORT_LAYERS_DICT = {
  'name': 'rename_for_export_layers',
  'function': rename_layer,
  'display_name': _('Rename'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_LAYERS_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': '[layer name]',
      'display_name': _('Layer filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'rename_layers',
      'default_value': True,
      'display_name': _('Rename layers'),
    },
    {
      'type': 'bool',
      'name': 'rename_folders',
      'default_value': False,
      'display_name': _('Rename folders'),
    },
  ],
}

RENAME_FOR_EDIT_LAYERS_DICT = {
  'name': 'rename_for_edit_layers',
  'function': rename_layer,
  'display_name': _('Rename'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': '[layer name]',
      'display_name': _('Layer name pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'rename_layers',
      'default_value': True,
      'display_name': _('Rename layers'),
    },
    {
      'type': 'bool',
      'name': 'rename_folders',
      'default_value': False,
      'display_name': _('Rename group layers'),
    },
  ],
}
