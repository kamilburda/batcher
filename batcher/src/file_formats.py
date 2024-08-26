"""Managing file formats supported by GIMP and some third-party plug-ins.

A list of file format wrappers is provided that contains at least a name and a
list of file extensions. The list can be used for:
* checking that a file format is supported,
* obtaining file format options (arguments).
"""

import pygimplib as pg
from pygimplib import pdb

from src import settings_from_pdb as settings_from_pdb_


def fill_file_format_options(file_format_options, file_format, import_or_export):
  processed_file_format = FILE_FORMAT_ALIASES.get(file_format, file_format)

  if (processed_file_format is None
      or processed_file_format in file_format_options
      or processed_file_format not in FILE_FORMATS_DICT):
    return

  if import_or_export == 'import':
    pdb_proc_name = FILE_FORMATS_DICT[processed_file_format].import_procedure_name
  elif import_or_export == 'export':
    pdb_proc_name = FILE_FORMATS_DICT[processed_file_format].export_procedure_name
  else:
    raise ValueError(
      'invalid value for import_or_export; must be either "import" or "export"')

  if pdb_proc_name is None:
    return

  _pdb_proc, _pdb_proc_name, file_format_options_list = (
    settings_from_pdb_.get_setting_data_from_pdb_procedure(pdb_proc_name))

  processed_file_format_options_list = _remove_common_file_format_options(
    file_format_options_list, import_or_export)

  options_settings = create_file_format_options_settings(
    processed_file_format_options_list)

  file_format_options[processed_file_format] = options_settings


def fill_and_get_file_format_options_as_kwargs(
      file_format_options, file_format, import_or_export):
  fill_file_format_options(file_format_options, file_format, import_or_export)

  if file_format in file_format_options:
    kwargs = {}

    for setting in file_format_options[file_format]:
      if (import_or_export == 'import'
          and setting.name in _PDB_ARGUMENTS_TO_FILTER_FOR_FILE_LOAD.values()):
        continue

      if (import_or_export == 'export'
          and setting.name in _PDB_ARGUMENTS_TO_FILTER_FOR_FILE_EXPORT.values()):
        continue

      if isinstance(setting, pg.setting.ArraySetting):
        length_name = setting.get_length_name(use_default=False)
        if length_name is not None:
          kwargs[length_name.replace('-', '_')] = len(setting.value)

      kwargs[setting.name.replace('-', '_')] = setting.value

    return kwargs
  else:
    return None


def _remove_common_file_format_options(file_format_options_list, import_or_export):
  if import_or_export == 'import':
    options_to_filter = _PDB_ARGUMENTS_TO_FILTER_FOR_FILE_LOAD
  elif import_or_export == 'export':
    options_to_filter = _PDB_ARGUMENTS_TO_FILTER_FOR_FILE_EXPORT
  else:
    raise ValueError('invalid value for import_or_export; must be either "import" or "export"')

  return [
    option_dict for index, option_dict in enumerate(file_format_options_list)
    if not (index in options_to_filter and option_dict['name'] == options_to_filter[index])
  ]


def create_file_format_options_settings(file_format_options_list):
  group = pg.setting.Group('file_format_options')

  processed_file_format_options_list = []
  file_format_options_values = {}

  for file_format_options in file_format_options_list:
    if 'value' in file_format_options:
      # The 'value' key must not be present when creating settings in a group
      # from a dictionary.
      file_format_options_values[file_format_options['name']] = file_format_options.pop('value')

    processed_file_format_options_list.append(file_format_options)

  group.add(processed_file_format_options_list)

  for setting_name, value in file_format_options_values.items():
    group[setting_name].set_value(value)

  return group


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

# HACK: Is there a better way to detect common arguments for load/export
# procedures?
_PDB_ARGUMENTS_TO_FILTER_FOR_FILE_LOAD = {
  0: 'run-mode',
  1: 'file',
}

_PDB_ARGUMENTS_TO_FILTER_FOR_FILE_EXPORT = {
  0: 'run-mode',
  1: 'image',
  2: 'drawables',
  3: 'file',
}
