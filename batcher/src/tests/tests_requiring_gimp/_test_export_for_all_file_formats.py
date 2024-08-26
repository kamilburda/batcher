import os

from src import exceptions
from src import file_formats as file_formats_
from src import utils as utils_


def test_export_for_all_file_formats(batcher, settings, output_dirpath):
  for file_format in file_formats_.FILE_FORMATS:
    for file_extension in file_format.file_extensions:
      try:
        batcher.run(
          output_directory=os.path.join(output_dirpath, file_extension),
          file_extension=file_extension,
          **utils_.get_settings_for_batcher(settings['main']))
      except exceptions.ExportError:
        # Do not stop if one file format causes an error.
        continue
