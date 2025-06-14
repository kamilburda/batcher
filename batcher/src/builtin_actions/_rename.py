"""Built-in "Rename" action."""

from src import builtin_commands_common
from src import renamer as renamer_
from src.procedure_groups import *


__all__ = [
  'rename_image_for_convert',
  'rename_image_for_export_images',
  'rename_image_for_edit_and_save_images',
  'rename_layer',
]


def rename_image_for_convert(
      image_batcher,
      pattern,
      rename_images=True,
      rename_folders=False,
):
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


def rename_image_for_export_images(image_batcher, pattern):
  renamer = renamer_.ItemRenamer(pattern, rename_items=True, rename_folders=False)

  while True:
    image_batcher.current_item.name = renamer.rename(image_batcher)

    yield


def rename_image_for_edit_and_save_images(image_batcher, pattern, rename_only_new_images=True):
  renamer = renamer_.ItemRenamer(pattern, rename_items=True, rename_folders=False)

  while True:
    image = image_batcher.current_item.raw
    is_new_image = image.get_file() is None

    if not rename_only_new_images or is_new_image:
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
  'function': rename_image_for_convert,
  'display_name': _('Rename'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, CONVERT_GROUP],
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
  'function': rename_image_for_export_images,
  'display_name': _('Rename'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EXPORT_IMAGES_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
  ],
}

RENAME_FOR_EDIT_AND_SAVE_IMAGES_DICT = {
  'name': 'rename_for_edit_and_save_images',
  'function': rename_image_for_edit_and_save_images,
  'display_name': _('Rename'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'name_pattern',
      'name': 'pattern',
      'default_value': 'image[001]',
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'rename_only_new_images',
      'default_value': True,
      'display_name': _('Rename only new images'),
    },
  ],
}

RENAME_FOR_EXPORT_LAYERS_DICT = {
  'name': 'rename_for_export_layers',
  'function': rename_layer,
  'display_name': _('Rename'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EXPORT_LAYERS_GROUP],
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
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
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
