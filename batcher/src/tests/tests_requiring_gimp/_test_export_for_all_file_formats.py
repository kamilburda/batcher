import os

from src import directory as directory_
from src import exceptions
from src import file_formats as file_formats_
from src import utils_setting as utils_setting_


def test_export_for_all_file_formats(batcher, settings, output_dirpath: str):
  for file_format in file_formats_.FILE_FORMATS:
    if not file_format.has_export_proc():
      continue

    for file_extension in file_format.file_extensions:
      try:
        batcher.run(
          output_directory=directory_.Directory(os.path.join(output_dirpath, file_extension)),
          file_extension=file_extension,
          **utils_setting_.get_settings_for_batcher(settings['main']))
      except exceptions.ImageExportError:
        # Do not stop if one file format causes an error.
        continue
