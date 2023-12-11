"""List of built-in and several third-party file formats supported by GIMP.

Each file format contains at least a name and a list of file extensions.

The list can be used for:
* listing all known and supported file formats in GUI
* checking that the corresponding file format plug-in is installed
"""

from collections.abc import Iterable
from typing import Callable, List, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

from .pypdb import pdb


def get_default_save_procedure() -> Callable:
  """Returns the `Gimp.file_save()` procedure with a more convenient interface.

  The differences from `Gimp.file_save()` include:
  * A single layer (drawable) can also be passed instead of always a list.
  * The file path is specified as a string instead of a `Gio.File` instance.
  """
  return _save_image_default


def _save_image_default(
      run_mode: Gimp.RunMode,
      image: Gimp.Image,
      layer_or_layers: Union[Gimp.Layer, List[Gimp.Layer]],
      filepath: Union[str, Gio.File],
):
  if not isinstance(layer_or_layers, Iterable):
    layers = [layer_or_layers]
  else:
    layers = layer_or_layers

  if not isinstance(filepath, Gio.File):
    image_file = Gio.file_new_for_path(filepath)
  else:
    image_file = filepath

  layer_array = GObject.Value(Gimp.ObjectArray)
  Gimp.value_set_object_array(layer_array, Gimp.Layer, layers)

  pdb.gimp_file_save(image, len(layers), layer_array.get_boxed(), image_file, run_mode=run_mode)

  return pdb.last_status


def get_save_procedure(file_extension: str) -> Callable:
  """Returns the file save procedure for the given file extension.

  If the file extension is not valid or does not have a specific save
  procedure defined, the default save procedure is returned (as returned by
  `get_default_save_procedure()`).
  """
  if file_extension in FILE_FORMATS_DICT:
    file_format = FILE_FORMATS_DICT[file_extension]
    if file_format.save_procedure_func and file_format.is_installed():
      return file_format.save_procedure_func
  
  return get_default_save_procedure()


def _create_file_formats(file_formats_params):
  return [_FileFormat(**params) for params in file_formats_params]


def _create_file_formats_dict(file_formats_):
  file_formats_dict_ = {}
  
  for file_format in file_formats_:
    for file_extension in file_format.file_extensions:
      if file_extension not in file_formats_dict_ and file_format.version_check_func():
        file_formats_dict_[file_extension] = file_format
  
  return file_formats_dict_


class _FileFormat:
  
  def __init__(
        self,
        description,
        file_extensions,
        save_procedure_name=None,
        save_procedure_func=None,
        save_procedure_func_args=None,
        versions=None,
        **kwargs):
    self.description = description
    self.file_extensions = file_extensions
    
    self.save_procedure_name = save_procedure_name
    
    if save_procedure_func is not None:
      self.save_procedure_func = save_procedure_func
    else:
      self.save_procedure_func = get_default_save_procedure()
    
    if save_procedure_func_args is not None:
      self.save_procedure_func_args = save_procedure_func_args
    else:
      self.save_procedure_func_args = []
    
    self.version_check_func = versions if versions is not None else lambda: True
    
    for name, value in kwargs.items():
      setattr(self, name, value)
  
  def is_builtin(self):
    return not self.save_procedure_name
  
  def is_third_party(self):
    return bool(self.save_procedure_name)
  
  def is_installed(self):
    return self.is_builtin() or (self.is_third_party() and self.save_procedure_name in pdb)


FILE_FORMATS = _create_file_formats([
  {'description': 'Alias Pix image',
   'file_extensions': ['pix', 'matte', 'mask', 'alpha', 'als']},
  {'description': 'Apple Icon Image',
   'file_extensions': ['icns']},
  {'description': 'ASCII art',
   'file_extensions': ['txt', 'ansi', 'text']},
  {'description': 'AutoDesk FLIC animation',
   'file_extensions': ['fli', 'flc']},
  {'description': 'bzip archive',
   'file_extensions': ['xcf.bz2', 'xcfbz2']},
  {'description': 'C source code',
   'file_extensions': ['c']},
  {'description': 'C source code header',
   'file_extensions': ['h']},
  {'description': 'Colored XHTML text',
   'file_extensions': ['xhtml']},
  {'description': 'DDS image',
   'file_extensions': ['dds']},
  {'description': 'DICOM image',
   'file_extensions': ['dcm', 'dicom']},
  {'description': 'Encapsulated PostScript',
   'file_extensions': ['eps']},
  {'description': 'Flexible Image Transport System',
   'file_extensions': ['fit', 'fits']},
  {'description': 'GIF image',
   'file_extensions': ['gif']},
  {'description': 'GIMP brush',
   'file_extensions': ['gbr']},
  {'description': 'GIMP brush (animated)',
   'file_extensions': ['gih']},
  {'description': 'GIMP pattern',
   'file_extensions': ['pat']},
  {'description': 'GIMP XCF image',
   'file_extensions': ['xcf']},
  {'description': 'gzip archive',
   'file_extensions': ['xcf.gz', 'xcfgz']},
  {'description': 'HEIF/AVIF',
   'file_extensions': ['avif']},
  {'description': 'HEIF/HEIC',
   'file_extensions': ['heif', 'heic']},
  {'description': 'HTML table',
   'file_extensions': ['html', 'htm']},
  {'description': 'JPEG image',
   'file_extensions': ['jpg', 'jpeg', 'jpe']},
  {'description': 'JPEG XL image',
   'file_extensions': ['jxl']},
  {'description': 'KISS CEL',
   'file_extensions': ['cel']},
  {'description': 'Microsoft Windows animated cursor',
   'file_extensions': ['ani']},
  {'description': 'Microsoft Windows cursor',
   'file_extensions': ['cur']},
  {'description': 'Microsoft Windows icon',
   'file_extensions': ['ico']},
  {'description': 'MNG animation',
   'file_extensions': ['mng']},
  {'description': 'OpenEXR image',
   'file_extensions': ['exr']},
  {'description': 'OpenRaster',
   'file_extensions': ['ora']},
  {'description': 'PAM image',
   'file_extensions': ['pam']},
  {'description': 'PBM image',
   'file_extensions': ['pbm']},
  {'description': 'PFM image',
   'file_extensions': ['pfm']},
  {'description': 'PGM image',
   'file_extensions': ['pgm']},
  {'description': 'Photoshop image',
   'file_extensions': ['psd']},
  {'description': 'PNG image',
   'file_extensions': ['png']},
  {'description': 'PNM image',
   'file_extensions': ['pnm']},
  {'description': 'Portable Document Format',
   'file_extensions': ['pdf']},
  {'description': 'PostScript document',
   'file_extensions': ['ps']},
  {'description': 'PPM image',
   'file_extensions': ['ppm']},
  {'description': 'Quite OK Image',
   'file_extensions': ['qoi']},
  {'description': 'Radiance RGBE',
   'file_extensions': ['hdr']},
  {'description': 'Raw image data',
   'file_extensions': ['data', 'raw']},
  {'description': 'Silicon Graphics IRIS image',
   'file_extensions': ['sgi', 'rgb', 'rgba', 'bw', 'icon']},
  {'description': 'SUN Rasterfile image',
   'file_extensions': ['im1', 'im8', 'im24', 'im32', 'rs', 'ras', 'sun']},
  {'description': 'TarGA image',
   'file_extensions': ['tga']},
  {'description': 'TIFF image or BigTIFF image',
   'file_extensions': ['tif', 'tiff']},
  {'description': 'WebP image',
   'file_extensions': ['webp']},
  {'description': 'Windows BMP image',
   'file_extensions': ['bmp']},
  {'description': 'X11 Mouse Cursor',
   'file_extensions': ['xmc']},
  {'description': 'X BitMap image',
   'file_extensions': ['xbm', 'bitmap']},
  {'description': 'X PixMap image',
   'file_extensions': ['xpm']},
  {'description': 'X window dump',
   'file_extensions': ['xwd']},
  {'description': 'xz archive',
   'file_extensions': ['xcf.xz', 'xcfxz']},
  {'description': 'ZSoft PCX image',
   'file_extensions': ['pcx', 'pcc']},
])
"""List of `_FileFormat` instances."""

FILE_FORMATS_DICT = _create_file_formats_dict(FILE_FORMATS)
"""Dictionary of (file extension, `_FileFormat` instance) pairs.

Only `_FileFormat` instances compatible with the version of the currently 
running GIMP instance are included.
"""
