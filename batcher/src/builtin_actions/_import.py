"""Built-in action for loading image files."""

from typing import Dict, Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import exceptions
from src import invoker as invoker_
from src import pypdb
from src.pypdb import pdb

__all__ = [
  'ImportAction',
]


class ImportAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(
        self,
        batcher: 'src.core.Batcher',
        image_file: Gio.File,
        file_format_import_options: Optional[Dict] = None,
  ):
    pass

  def _process(
        self,
        batcher: 'src.core.Batcher',
        image_file: Gio.File,
        file_format_import_options: Optional[Dict] = None,
  ):
    if not image_file.query_exists():
      if not batcher.continue_on_error or batcher.is_preview:
        raise exceptions.BatcherFileLoadError(_('File not found'), image_file.get_path())
      else:
        return

    return _load_image(image_file)


def _load_image(image_file):
  # TODO: Replace with functions from `fileformats`
  try:
    image = pdb.gimp_file_load(
      run_mode=Gimp.RunMode.NONINTERACTIVE,
      file=image_file,
    )
  except pypdb.PDBProcedureError as e:
    if e.status == Gimp.PDBStatusType.CANCEL:
      raise exceptions.BatcherCancelError('canceled')
    else:
      raise
  else:
    return image


IMPORT_DICT = {
  'name': 'import',
  'function': ImportAction,
  'display_name': _('Import image'),
  'description': _('Loads an image from a file.'),
  # This action is only used internally in `core.ImageBatcher` to load images
  # to be processed.
  'additional_tags': [],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'file',
      'name': 'image_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Image'),
      'none_ok': True,
    },
    {
      'type': 'file_format_options',
      'name': 'file_format_import_options',
      'import_or_export': 'import',
      'gui_type': 'file_format_options',
      'display_name': _('File format options'),
      'gui_type_kwargs': {
        'placeholder_label': _('No recognized image formats in added files'),
      },
    },
  ],
}
