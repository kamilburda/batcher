"""Built-in action for loading image files."""

from typing import Callable, Dict, Optional, Tuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import exceptions
from src import file_formats as file_formats_
from src import invoker as invoker_
from src import pypdb
from src.path import fileext
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

    if file_format_import_options is None:
      file_format_import_options = {}

    return _load_image(
      image_file,
      fileext.get_file_extension(batcher.current_item.orig_name.lower()),
      file_format_import_options,
    )


def _load_image(
      image_file,
      file_extension,
      file_format_import_options,
):
  try:
    image = _import_image(
      image_file,
      file_extension,
      file_format_import_options,
    )
  except pypdb.PDBProcedureError as e:
    if e.status == Gimp.PDBStatusType.CANCEL:
      raise exceptions.BatcherCancelError('canceled')
    else:
      raise
  else:
    return image


def _import_image(
      image_file,
      file_extension,
      file_format_import_options,
):
  import_func, kwargs = get_import_function(file_extension, file_format_import_options)

  return import_func(
    run_mode=Gimp.RunMode.NONINTERACTIVE,
    file=image_file,
    **kwargs,
  )


def get_import_function(
      file_extension: str,
      file_format_import_options: Dict,
) -> Tuple[Callable, Dict]:
  """Returns the file import procedure and file format settings given the
  file extension.

  If the file extension is not recognized, the default GIMP import procedure is
  returned (``gimp-file-load``).
  """
  if file_extension in file_formats_.FILE_FORMATS_DICT:
    file_format = file_formats_.FILE_FORMATS_DICT[file_extension]
    if file_format.has_import_proc():
      file_format_option_kwargs = file_formats_.fill_and_get_file_format_options_as_kwargs(
        file_format_import_options, file_extension, 'import')

      if file_format_option_kwargs is not None:
        return file_format.get_import_func(), file_format_option_kwargs

  return pdb.gimp_file_load, {}


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
