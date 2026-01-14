"""Built-in "Save" action."""

import os

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import builtin_commands_common
from src import directory as directory_
from src import invoker as invoker_
from src.path import validators as validators_
from src.procedure_groups import *
from src.pypdb import pdb

from . import _utils as builtin_actions_utils


__all__ = [
  'SaveAction',
  'on_after_add_save_action',
]


_XCF_FILE_EXTENSION = '.xcf'


class SaveAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(
        self,
        batcher,
        output_directory,
        output_directory_for_new_images,
  ):
    self._images_to_reset_dirty_state_for = []

    batcher.invoker.add(
      _reset_dirty_state_of_images_after_cleanup,
      ['after_cleanup_contents'],
      [self._images_to_reset_dirty_state_for],
    )

  def _process(
        self,
        batcher,
        output_directory,
        output_directory_for_new_images,
  ):
    if not batcher.process_export:
      return

    image = batcher.current_image
    item = batcher.current_item

    orig_image_file = image.get_xcf_file()

    if not item.name.endswith(_XCF_FILE_EXTENSION):
      image_filename = f'{item.name}{_XCF_FILE_EXTENSION}'
    else:
      image_filename = item.name

    item.save_state(builtin_actions_utils.EXPORT_NAME_ITEM_STATE)
    builtin_actions_utils.set_item_export_name(item, image_filename)
    _validate_name(item)

    output_dirpath = output_directory.resolve(batcher)

    if output_dirpath is None:
      # This should always resolve to a fixed directory as this parameter has no
      # special value allowed.
      output_dirpath = output_directory_for_new_images.resolve(batcher)

    new_image_file = Gio.file_new_for_path(
      builtin_actions_utils.get_item_filepath(item, output_dirpath))

    if new_image_file.get_path() is not None:
      os.makedirs(os.path.dirname(new_image_file.get_path()), exist_ok=True)

    pdb.gimp_xcf_save(run_mode=Gimp.RunMode.NONINTERACTIVE, image=image, file=new_image_file)

    if orig_image_file is not None and not orig_image_file.equal(new_image_file):
      image.set_file(new_image_file)

    self._images_to_reset_dirty_state_for.append(image)


def _validate_name(item):
  builtin_actions_utils.set_item_export_name(
    item,
    validators_.FilenameValidator.validate(builtin_actions_utils.get_item_export_name(item)))


def _reset_dirty_state_of_images_after_cleanup(_batcher, images_to_reset_dirty_state_for):
  for image in images_to_reset_dirty_state_for:
    if image.is_valid():
      image.clean_all()

  images_to_reset_dirty_state_for.clear()


def on_after_add_save_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value == 'save':
    action['arguments/output_directory'].connect_event(
      'value-changed',
      _set_visible_for_output_directory_for_new_images_setting,
      action['arguments/output_directory_for_new_images'],
    )

    _set_visible_for_output_directory_for_new_images_setting(
      action['arguments/output_directory'],
      action['arguments/output_directory_for_new_images'],
    )


def _set_visible_for_output_directory_for_new_images_setting(
      output_directory_setting,
      output_directory_for_new_images_setting,
):
  is_visible = (
    output_directory_setting.value.type_ == directory_.DirectoryTypes.SPECIAL
    and output_directory_setting.value.value == 'use_original_location')

  output_directory_for_new_images_setting.gui.set_visible(is_visible)


SAVE_DICT = {
  'name': 'save',
  'function': SaveAction,
  'display_name': _('Save'),
  'description': _(
    'Saves the image in the native GIMP format (XCF). '
    'To export the image in another file format, use the "Export Images" menu.'),
  'display_options_on_create': True,
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'directory',
      'name': 'output_directory',
      'default_value': 'special:///use_original_location',
      'display_name': _('Output folder'),
      'gui_type_kwargs': {
        'max_width_chars': 60,
      },
    },
    {
      'type': 'directory',
      'name': 'output_directory_for_new_images',
      'default_value': None,
      'display_name': _('Output folder for new and imported images'),
      'procedure_groups': [],
      'gui_type_kwargs': {
        'max_width_chars': 60,
      },
    },
  ],
}
