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
      or not file_format_procedure_exists(processed_file_format, import_or_export)):
    return

  if import_or_export == 'import':
    pdb_proc_name = FILE_FORMATS_DICT[processed_file_format].import_procedure_name
    common_arguments = _COMMON_PDB_ARGUMENTS_FOR_FILE_LOAD
  elif import_or_export == 'export':
    pdb_proc_name = FILE_FORMATS_DICT[processed_file_format].export_procedure_name
    common_arguments = _COMMON_PDB_ARGUMENTS_FOR_FILE_EXPORT
  else:
    raise ValueError('invalid value for import_or_export; must be either "import" or "export"')

  _pdb_proc, _pdb_proc_name, file_format_options_list = (
    settings_from_pdb_.get_setting_data_from_pdb_procedure(pdb_proc_name))

  processed_file_format_options_list = _remove_common_file_format_options(
    file_format_options_list, common_arguments)

  options_settings = create_file_format_options_settings(
    processed_file_format_options_list)

  file_format_options[processed_file_format] = options_settings


def _remove_common_file_format_options(file_format_options_list, common_arguments):
  return [
    option_dict for index, option_dict in enumerate(file_format_options_list)
    if not (
      index in common_arguments
      and common_arguments[index] == option_dict.get('name', None))
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


def fill_and_get_file_format_options_as_kwargs(
      file_format_options, file_format, import_or_export):
  fill_file_format_options(file_format_options, file_format, import_or_export)

  if file_format in file_format_options:
    return {
      setting.name.replace('-', '_'): setting.value_for_pdb
      for setting in file_format_options[file_format]
    }
  else:
    return None


def file_format_procedure_exists(file_format, import_or_export):
  if file_format not in FILE_FORMATS_DICT:
    return False

  if import_or_export == 'import':
    return FILE_FORMATS_DICT[file_format].has_import_proc()
  elif import_or_export == 'export':
    return FILE_FORMATS_DICT[file_format].has_export_proc()
  else:
    raise ValueError('invalid value for import_or_export; must be either "import" or "export"')


class _FileFormat:
  
  def __init__(
        self,
        file_extensions,
        import_procedure_name=None,
        import_func=None,
        export_procedure_name=None,
        export_func=None,
        version_check_func=None,
        description=None,
        **kwargs):
    self.file_extensions = file_extensions
    
    self.import_procedure_name = import_procedure_name
    self._import_func = import_func

    self.export_procedure_name = export_procedure_name
    self._export_func = export_func
    
    self.version_check_func = version_check_func if version_check_func is not None else lambda: True

    self._description = description
    
    for name, value in kwargs.items():
      setattr(self, name, value)

  def get_description(self, import_or_export, max_char_length_for_inferred_description=35):
    """Returns the description of the file format.

    If passing ``description=None`` to `__init__()` and ``import_or_export``
    is equal to ``'import'`` or ``'export'``, the description is inferred
    from the procedure whose name is `import_procedure_name` or
    `export_procedure_name`, respectively. If the load/export procedure does
    not exist, the string ``'<first file extension in uppercase> image'`` is
    returned. The string is also returned if the procedure exists and the label
    has more than ``max_char_length_for_inferred_description`` characters.

    If passing a string to the ``description`` parameter in `__init__()`,
    then that description is returned.
    """
    if self._description is not None:
      return self._description
    else:
      if import_or_export not in ['import', 'export']:
        raise ValueError('invalid value for import_or_export; must be either "import" or "export"')

      menu_label = None

      if import_or_export == 'import' and self.import_procedure_name in pdb:
        menu_label = pdb[self.import_procedure_name].menu_label

      if import_or_export == 'export' and self.export_procedure_name in pdb:
        menu_label = pdb[self.export_procedure_name].menu_label

      if menu_label and len(menu_label) <= max_char_length_for_inferred_description:
        return menu_label
      else:
        return _('{} image').format(self.file_extensions[0].upper())

  def has_import_proc(self):
    return self.import_procedure_name in pdb

  def get_import_func(self):
    if self._import_func is None:
      return pdb[self.import_procedure_name]
    else:
      return self._import_func

  def has_export_proc(self):
    return self.export_procedure_name in pdb

  def get_export_func(self):
    if self._export_func is None:
      return pdb[self.export_procedure_name]
    else:
      return self._export_func


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


def _gimp_xcf_save_wrapper(options=None, **kwargs):
  pdb.gimp_xcf_save(**kwargs)


FILE_FORMATS = _create_file_formats([
  {'file_extensions': ['txt', 'ansi', 'text'],
   'export_procedure_name': 'file-aa-export'},
  {'file_extensions': ['ani'],
   'import_procedure_name': 'file-ani-load',
   'export_procedure_name': 'file-ani-export',},
  {'file_extensions': ['bmp'],
   'import_procedure_name': 'file-bmp-load',
   'export_procedure_name': 'file-bmp-export'},
  {'file_extensions': ['xcf.bz2', 'xcfbz2'],
   'import_procedure_name': 'file-bz2-load',
   'export_procedure_name': 'file-bz2-export'},
  {'file_extensions': ['cel'],
   'import_procedure_name': 'file-cel-load',
   'export_procedure_name': 'file-cel-export'},
  {'file_extensions': ['xhtml'],
   'export_procedure_name': 'file-colorxhtml-export'},
  {'file_extensions': ['c'],
   'export_procedure_name': 'file-csource-export'},
  {'file_extensions': ['cur'],
   'import_procedure_name': 'file-cur-load',
   'export_procedure_name': 'file-cur-export'},
  {'file_extensions': ['dcx'],
   'import_procedure_name': 'file-dcx-load'},
  {'file_extensions': ['dds'],
   'import_procedure_name': 'file-dds-load',
   'export_procedure_name': 'file-dds-export'},
  {'file_extensions': ['desktop'],
   'import_procedure_name': 'file-desktop-link-load'},
  {'file_extensions': ['dicom', 'dcm'],
   'import_procedure_name': 'file-dicom-load',
   'export_procedure_name': 'file-dicom-export'},
  {'file_extensions': ['eps'],
   'import_procedure_name': 'file-eps-load',
   'export_procedure_name': 'file-eps-export'},
  {'file_extensions': ['exr'],
   'import_procedure_name': 'file-exr-load',
   'export_procedure_name': 'file-exr-export'},
  {'file_extensions': ['ff'],
   'import_procedure_name': 'file-farbfeld-load',
   'export_procedure_name': 'file-farbfeld-export'},
  {'file_extensions': ['g3'],
   'import_procedure_name': 'file-faxg3-load'},
  {'file_extensions': ['fit', 'fits'],
   'import_procedure_name': 'file-fits-load',
   'export_procedure_name': 'file-fits-export'},
  {'file_extensions': ['fli', 'flc'],
   'import_procedure_name': 'file-fli-load',
   'export_procedure_name': 'file-fli-export'},
  {'file_extensions': ['gbr'],
   'import_procedure_name': 'file-gbr-load',
   'export_procedure_name': 'file-gbr-export'},
  {'file_extensions': ['gbp'],
   'import_procedure_name': 'file-gbr-load'},
  {'file_extensions': ['gif'],
   'import_procedure_name': 'file-gif-load',
   'export_procedure_name': 'file-gif-export'},
  {'file_extensions': ['gih'],
   'import_procedure_name': 'file-gih-load',
   'export_procedure_name': 'file-gih-export'},
  {'file_extensions': ['xcf.gz', 'xcfgz'],
   'import_procedure_name': 'file-gz-load',
   'export_procedure_name': 'file-gz-export'},
  {'file_extensions': ['h'],
   'export_procedure_name': 'file-header-export'},
  {'file_extensions': ['avif'],
   'import_procedure_name': 'file-heif-av1-load',
   'export_procedure_name': 'file-heif-av1-export'},
  {'file_extensions': ['hej2'],
   'import_procedure_name': 'file-heif-hej2-load'},
  {'file_extensions': ['heif', 'heic'],
   'import_procedure_name': 'file-heif-load',
   'export_procedure_name': 'file-heif-export'},
  {'file_extensions': ['hgt'],
   'import_procedure_name': 'file-hgt-load'},
  {'file_extensions': ['html', 'htm'],
   'export_procedure_name': 'file-html-table-export'},
  {'file_extensions': ['icns'],
   'import_procedure_name': 'file-icns-load',
   'export_procedure_name': 'file-icns-export'},
  {'file_extensions': ['ico'],
   'import_procedure_name': 'file-ico-load',
   'export_procedure_name': 'file-ico-export'},
  {'file_extensions': ['iff', 'ilbm', 'lbm', 'acbm', 'ham', 'ham6', 'ham8'],
   'import_procedure_name': 'file-iff-load'},
  {'file_extensions': ['j2k', 'j2c', 'jpc'],
   'import_procedure_name': 'file-j2k-load'},
  {'file_extensions': ['jp2'],
   'import_procedure_name': 'file-jp2-load'},
  {'file_extensions': ['jpg', 'jpeg', 'jpe'],
   'import_procedure_name': 'file-jpeg-load',
   'export_procedure_name': 'file-jpeg-export'},
  {'file_extensions': ['jxl'],
   'import_procedure_name': 'file-jpegxl-load',
   'export_procedure_name': 'file-jpegxl-export'},
  {'file_extensions': ['lnk'],
   'import_procedure_name': 'file-lnk-load'},
  {'file_extensions': ['mng'],
   'export_procedure_name': 'file-mng-export'},
  {'file_extensions': ['ora'],
   'import_procedure_name': 'file-openraster-load',
   'export_procedure_name': 'file-openraster-export'},
  {'file_extensions': ['pam'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-pam-export'},
  {'file_extensions': ['pat'],
   'import_procedure_name': 'file-pat-load',
   'export_procedure_name': 'file-pat-export'},
  {'file_extensions': ['pbm'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-pbm-export'},
  {'file_extensions': ['pcx', 'pcc'],
   'import_procedure_name': 'file-pcx-load',
   'export_procedure_name': 'file-pcx-export'},
  {'file_extensions': ['pdf'],
   'import_procedure_name': 'file-pdf-load',
   'export_procedure_name': 'file-pdf-export'},
  {'file_extensions': ['pfm'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-pfm-export'},
  {'file_extensions': ['pgm'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-pgm-export'},
  {'file_extensions': ['pix', 'matte', 'mask', 'alpha', 'als'],
   'import_procedure_name': 'file-pix-load',
   'export_procedure_name': 'file-pix-export'},
  {'file_extensions': ['png'],
   'import_procedure_name': 'file-png-load',
   'export_procedure_name': 'file-png-export'},
  {'file_extensions': ['pnm'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-pnm-export'},
  {'file_extensions': ['ppm'],
   'import_procedure_name': 'file-pnm-load',
   'export_procedure_name': 'file-ppm-export'},
  {'file_extensions': ['ps'],
   'import_procedure_name': 'file-ps-load',
   'export_procedure_name': 'file-ps-export'},
  {'file_extensions': ['psb'],
   'import_procedure_name': 'file-psd-load'},
  {'file_extensions': ['psd'],
   'import_procedure_name': 'file-psd-load',
   'export_procedure_name': 'file-psd-export'},
  {'file_extensions': ['psp', 'tub', 'pspimage', 'psptube'],
   'import_procedure_name': 'file-psp-load'},
  {'file_extensions': ['qoi'],
   'import_procedure_name': 'file-qoi-load',
   'export_procedure_name': 'file-qoi-export'},
  {'file_extensions': ['raw', 'data'],
   'import_procedure_name': 'file-raw-load',
   'export_procedure_name': 'file-raw-export'},
  {'file_extensions': ['hdr'],
   'import_procedure_name': 'file-rgbe-load',
   'export_procedure_name': 'file-rgbe-export'},
  {'file_extensions': ['sgi', 'rgb', 'rgba', 'bw', 'icon'],
   'import_procedure_name': 'file-sgi-load',
   'export_procedure_name': 'file-sgi-export'},
  {'file_extensions': ['im1', 'im8', 'im24', 'im32', 'rs', 'ras', 'sun'],
   'import_procedure_name': 'file-sunras-load',
   'export_procedure_name': 'file-sunras-export'},
  {'file_extensions': ['svg'],
   'import_procedure_name': 'file-svg-load'},
  {'file_extensions': ['tga'],
   'import_procedure_name': 'file-tga-load',
   'export_procedure_name': 'file-tga-export'},
  {'file_extensions': ['vda', 'icb', 'vst'],
   'import_procedure_name': 'file-tga-load'},
  {'file_extensions': ['tif', 'tiff'],
   'import_procedure_name': 'file-tiff-load',
   'export_procedure_name': 'file-tiff-export'},
  {'file_extensions': ['wbmp'],
   'import_procedure_name': 'file-wbmp-load'},
  {'file_extensions': ['webp'],
   'import_procedure_name': 'file-webp-load',
   'export_procedure_name': 'file-webp-export'},
  {'file_extensions': ['wmf', 'apm'],
   'import_procedure_name': 'file-wmf-load'},
  {'file_extensions': ['xbm', 'icon', 'bitmap'],
   'import_procedure_name': 'file-xbm-load',
   'export_procedure_name': 'file-xbm-export'},
  {'file_extensions': ['xmc'],
   'import_procedure_name': 'file-xmc-load',
   'export_procedure_name': 'file-xmc-export'},
  {'file_extensions': ['xpm'],
   'import_procedure_name': 'file-xpm-load',
   'export_procedure_name': 'file-xpm-export'},
  {'file_extensions': ['xwd'],
   'import_procedure_name': 'file-xwd-load',
   'export_procedure_name': 'file-xwd-export'},
  {'file_extensions': ['xcf.xz', 'xcfxz'],
   'import_procedure_name': 'file-xz-load',
   'export_procedure_name': 'file-xz-export'},
  {'file_extensions': ['xcf'],
   'import_procedure_name': 'gimp-xcf-load',
   'export_procedure_name': 'gimp-xcf-save',
   'export_func': _gimp_xcf_save_wrapper},
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

# HACK: Is there a better way to detect common arguments for load/export procedures?
_COMMON_PDB_ARGUMENTS_FOR_FILE_LOAD = {
  0: 'run-mode',
  1: 'file',
}

_COMMON_PDB_ARGUMENTS_FOR_FILE_EXPORT = {
  0: 'run-mode',
  1: 'image',
  2: 'file',
  3: 'options',
}
