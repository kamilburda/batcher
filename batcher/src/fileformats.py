"""List of built-in and several third-party file formats supported by GIMP.

Each file format contains at least a name and a list of file extensions.

The list can be used for:
* listing all known and supported file formats in GUI
* checking that the corresponding file format plug-in is installed
"""

from pygimplib import pdb


def _create_file_formats(file_formats_params):
  return [_FileFormat(**params) for params in file_formats_params]


def _create_file_formats_dict(file_formats):
  file_formats_dict = {}
  
  for file_format in file_formats:
    for file_extension in file_format.file_extensions:
      if file_extension not in file_formats_dict and file_format.version_check_func():
        file_formats_dict[file_extension] = file_format
  
  return file_formats_dict


def _create_file_format_aliases(file_formats):
  file_format_aliases = {}

  for file_format in file_formats:
    for file_extension in file_format.file_extensions:
      if file_extension not in file_format_aliases:
        file_format_aliases[file_extension] = file_format.file_extensions[0]

  return file_format_aliases


class _FileFormat:
  
  def __init__(
        self,
        description,
        file_extensions,
        import_procedure_name=None,
        export_procedure_name=None,
        version_check_func=None,
        **kwargs):
    self.description = description
    self.file_extensions = file_extensions
    
    self.import_procedure_name = import_procedure_name
    self.export_procedure_name = export_procedure_name
    
    self.version_check_func = version_check_func if version_check_func is not None else lambda: True
    
    for name, value in kwargs.items():
      setattr(self, name, value)

  def is_import_installed(self):
    return self._is_import_proc_builtin() or self.import_procedure_name in pdb

  def _is_import_proc_builtin(self):
    return self.import_procedure_name is None

  def is_export_installed(self):
    return self._is_export_proc_builtin() or self.export_procedure_name in pdb

  def _is_export_proc_builtin(self):
    return self.export_procedure_name is None


FILE_FORMATS = _create_file_formats([
  {'description': 'Alias Pix image',
   'file_extensions': ['pix', 'matte', 'mask', 'alpha', 'als'],
   'export_procedure_name': 'file-pix-save'},
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
   'file_extensions': ['jpg', 'jpeg', 'jpe'],
   'export_procedure_name': 'file-jpeg-save'},
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
   'file_extensions': ['png'],
   'export_procedure_name': 'file-png-save'},
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
"""List of `_FileFormat` instances representing file import and export
procedures.
"""

FILE_FORMATS_DICT = _create_file_formats_dict(FILE_FORMATS)
"""Dictionary of (file extension, `_FileFormat` instance) pairs representing
file import and export procedures.

Only `_FileFormat` instances compatible with the version of the currently 
running GIMP instance are included.
"""

FILE_FORMAT_ALIASES = _create_file_format_aliases(FILE_FORMATS)
