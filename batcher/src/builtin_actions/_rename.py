"""Built-in "Rename" action."""

from src import builtin_commands_common
from src import invoker as invoker_
from src import renamer as renamer_
from src.procedure_groups import *


__all__ = [
  'RenameImageForConvertAction',
  'RenameImageForExportImagesAction',
  'RenameImageForEditAndSaveImagesAction',
  'RenameLayerAction',
]


class RenameImageForConvertAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(
        self,
        image_batcher,
        pattern,
        rename_images=True,
        rename_folders=False,
  ):
    self._renamer = renamer_.ItemRenamer(pattern, rename_images, rename_folders)
    self._renamed_parents = set()

  def _process(
        self,
        image_batcher,
        pattern,
        rename_images=True,
        rename_folders=False,
  ):
    if rename_folders:
      for parent in image_batcher.current_item.parents:
        if parent not in self._renamed_parents:
          parent.name = self._renamer.rename(image_batcher, item=parent)
          self._renamed_parents.add(parent)

    if rename_images:
      image_batcher.current_item.name = self._renamer.rename(image_batcher)


class RenameImageForExportImagesAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, image_batcher, pattern):
    self._renamer = renamer_.ItemRenamer(pattern, rename_items=True, rename_folders=False)

  def _process(self, image_batcher, pattern):
    image_batcher.current_item.name = self._renamer.rename(image_batcher)


class RenameImageForEditAndSaveImagesAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, image_batcher, pattern, rename_only_new_images=True):
    self._renamer = renamer_.ItemRenamer(pattern, rename_items=True, rename_folders=False)

  def _process(self, image_batcher, pattern, rename_only_new_images=True):
    image = image_batcher.current_item.raw
    is_new_image = image.get_file() is None

    if not rename_only_new_images or is_new_image:
      image_batcher.current_item.name = self._renamer.rename(image_batcher)


class RenameLayerAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, layer_batcher, pattern, rename_layers=True, rename_folders=False):
    self._renamer = renamer_.ItemRenamer(pattern, rename_layers, rename_folders)
    self._renamed_parents = set()

  def _process(self, layer_batcher, pattern, rename_layers=True, rename_folders=False):
    if rename_folders:
      for parent in layer_batcher.current_item.parents:
        if parent not in self._renamed_parents:
          parent.name = self._renamer.rename(layer_batcher, item=parent)
          self._renamed_parents.add(parent)

          if (layer_batcher.edit_mode
              and layer_batcher.process_names
              and not layer_batcher.is_preview):
            parent.raw.set_name(parent.name)

    if rename_layers:
      layer_batcher.current_item.name = self._renamer.rename(layer_batcher)

      if layer_batcher.process_names and not layer_batcher.is_preview:
        layer_batcher.current_layer.set_name(layer_batcher.current_item.name)


RENAME_FOR_CONVERT_DICT = {
  'name': 'rename_for_convert',
  'function': RenameImageForConvertAction,
  'display_name': _('Rename'),
  'menu_path': _('File and Naming'),
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
  'function': RenameImageForExportImagesAction,
  'display_name': _('Rename'),
  'menu_path': _('File and Naming'),
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
  'function': RenameImageForEditAndSaveImagesAction,
  'display_name': _('Rename'),
  'menu_path': _('File and Naming'),
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
  'function': RenameLayerAction,
  'display_name': _('Rename'),
  'menu_path': _('File and Naming'),
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
  'function': RenameLayerAction,
  'display_name': _('Rename'),
  'menu_path': _('File and Naming'),
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
