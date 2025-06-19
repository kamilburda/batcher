"""Built-in "Save" action."""

import os

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import builtin_commands_common
from src import utils
from src.path import validators as validators_
from src.procedure_groups import *
from src.pypdb import pdb

from . import _utils as builtin_actions_utils


__all__ = [
  'save',
]


_XCF_FILE_EXTENSION = '.xcf'


def save(
      batcher,
      output_directory,
      save_existing_image_to_its_original_location,
):
  images_to_reset_dirty_state_for = []

  batcher.invoker.add(
    _reset_dirty_state_of_images_after_cleanup,
    ['after_cleanup_contents'],
    [images_to_reset_dirty_state_for],
  )

  while True:
    if not batcher.process_export:
      yield
      continue

    image = batcher.current_image
    item = batcher.current_item

    image_xcf_file = image.get_xcf_file()

    save_to_original_folder = (
      image_xcf_file is not None and save_existing_image_to_its_original_location)
    should_set_new_image_file = not save_to_original_folder

    if not item.name.endswith(_XCF_FILE_EXTENSION):
      image_filename = f'{item.name}{_XCF_FILE_EXTENSION}'
    else:
      image_filename = item.name

    item.save_state(builtin_actions_utils.EXPORT_NAME_ITEM_STATE)
    builtin_actions_utils.set_item_export_name(item, image_filename)
    _validate_name(item)

    if save_to_original_folder:
      image_file = image_xcf_file

      new_image_file = Gio.file_new_for_path(
        builtin_actions_utils.get_item_filepath(
          item,
          Gio.file_new_for_path(os.path.dirname(image_file.get_path())),
        ))

      if not image_file.equal(new_image_file):
        image_file = new_image_file
        should_set_new_image_file = True
    else:
      image_file = Gio.file_new_for_path(
        builtin_actions_utils.get_item_filepath(item, output_directory))

    if image_file.get_path() is not None:
      os.makedirs(os.path.dirname(image_file.get_path()), exist_ok=True)
    pdb.gimp_xcf_save(run_mode=Gimp.RunMode.NONINTERACTIVE, image=image, file=image_file)

    if should_set_new_image_file:
      image.set_file(image_file)

    images_to_reset_dirty_state_for.append(image)

    yield


def _validate_name(item):
  builtin_actions_utils.set_item_export_name(
    item,
    validators_.FilenameValidator.validate(builtin_actions_utils.get_item_export_name(item)))


def _reset_dirty_state_of_images_after_cleanup(_batcher, images_to_reset_dirty_state_for):
  for image in images_to_reset_dirty_state_for:
    if image.is_valid():
      image.clean_all()

  images_to_reset_dirty_state_for.clear()


SAVE_DICT = {
  'name': 'save',
  'function': save,
  'display_name': _('Save'),
  'description': _(
    'Saves the image in the native GIMP format (XCF). If the image already exists, it is'
    ' overwritten. To export the image in another file format, use the "Export Images" menu.'),
  'display_options_on_create': True,
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
      'none_ok': False,
      'set_default_if_not_exists': True,
      'gui_type_kwargs': {
        'show_clear_button': False,
      },
    },
    {
      'type': 'bool',
      'name': 'save_existing_image_to_its_original_location',
      'default_value': True,
      'display_name': _(
        'Save existing XCF image to its original location (ignore "Output folder")'),
    },
  ],
}
