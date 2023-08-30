"""Logging-related classes."""

# NOTE: In order to allow logging errors as early as possible (before plug-in
# initialization), we are breaking the 'all imports at the beginning of module' convention.

import datetime
import os
import sys
import traceback


_LOG_MODES = ('none', 'exceptions', 'files', 'gimp_console')

_exception_logger = None


def log_output(
      log_mode,
      log_dirpaths,
      log_stdout_filename,
      log_stderr_filename,
      log_header_title='',
      gimp_console_message_delay_milliseconds=0):
  """
  Enable logging of output.
  
  Parameters:
  
  * `log_mode` - The log mode. Possible values:
    
    * 'none' - Do not log anything.
    
    * 'exceptions' - Only log exceptions to the error log file.
    
    * 'files' - Redirect `stdout` and `stderr` to log files.
    
    * 'gimp_console' - Redirect `stdout` and `stderr` to the GIMP error console.
  
  * `log_dirpaths` - List of directory paths for log files. If the first path is
    invalid or permission to write is denied, subsequent directories are used.
    For the `'gimp_console'` mode, this parameter has no effect.
  
  * `log_stdout_filename` - Filename of the log file to write standard output
    to. Applies to the `'files'` mode only.
  
  * `log_stderr_filename` - Filename of the log file to write error output to.
    Applies to the `'exceptions'` and `'files'` modes only.
  
  * `log_header_title` - Optional title in the log header, written before the
    first output to the log files. Applies to the `'exceptions'` and `'files'`
    modes only.
  
  * `gimp_console_message_delay_milliseconds` - The delay to display messages to
    the GIMP console in milliseconds. Only applies to the `'gimp_console'` mode.
  """
  _restore_orig_state(log_mode)
  
  if log_mode == 'none':
    return
  
  if log_mode == 'exceptions':
    _redirect_exception_output_to_file(
      log_dirpaths, log_stderr_filename, log_header_title)
  elif log_mode == 'files':
    stdout_file = create_log_file(log_dirpaths, log_stdout_filename)
    
    if stdout_file is not None:
      sys.stdout = SimpleLogger(stdout_file, log_header_title)
    
    stderr_file = create_log_file(log_dirpaths, log_stderr_filename)
    
    if stderr_file is not None:
      sys.stderr = SimpleLogger(stderr_file, log_header_title)
  elif log_mode == 'gimp_console':
    from . import pdbutils as pgpdbutils
    
    sys.stdout = pgpdbutils.GimpMessageFile(
      message_delay_milliseconds=gimp_console_message_delay_milliseconds)
    sys.stderr = pgpdbutils.GimpMessageFile(
      message_prefix='Error: ',
      message_delay_milliseconds=gimp_console_message_delay_milliseconds)
  else:
    raise ValueError('invalid log mode "{}"; allowed values: {}'.format(
      log_mode, ', '.join(_LOG_MODES)))


def get_log_header(log_header_title):
  return '\n'.join(('', '=' * 80, log_header_title, str(datetime.datetime.now()), '\n'))


def create_log_file(log_dirpaths, log_filename, mode='a'):
  """
  Create a log file in the first file path that can be written to.
  
  Return the log file upon successful creation, `None` otherwise.
  """
  log_file = None
  
  for log_dirpath in log_dirpaths:
    try:
      os.makedirs(log_dirpath, exist_ok=True)
    except OSError:
      continue
    
    try:
      log_file = open(os.path.join(log_dirpath, log_filename), mode, encoding='utf-8')
    except IOError:
      continue
    else:
      break
  
  return log_file


def _restore_orig_state(log_mode):
  global _exception_logger
  
  for file_ in [_exception_logger, sys.stdout, sys.stderr]:
    if (file_ is not None
        and hasattr(file_, 'close')
        and file_ not in [sys.__stdout__, sys.__stderr__]):
      try:
        file_.close()
      except IOError:
        # An exception could occur for an invalid file descriptor.
        pass
  
  _exception_logger = None
  sys.excepthook = sys.__excepthook__
   
  sys.stdout = sys.__stdout__
  sys.stderr = sys.__stderr__


def _redirect_exception_output_to_file(log_dirpaths, log_filename, log_header_title):
  global _exception_logger
  
  def create_file_upon_exception_and_log_exception(exc_type, exc_value, exc_traceback):
    global _exception_logger
    
    _exception_log_file = create_log_file(log_dirpaths, log_filename)
    
    if _exception_log_file is not None:
      _exception_logger = SimpleLogger(_exception_log_file, log_header_title)
      log_exception(exc_type, exc_value, exc_traceback)
      
      sys.excepthook = log_exception
    else:
      sys.excepthook = sys.__excepthook__
  
  def log_exception(exc_type, exc_value, exc_traceback):
    global _exception_logger
    
    _exception_logger.write(
      ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
  
  sys.excepthook = create_file_upon_exception_and_log_exception


class SimpleLogger(object):
  """
  This class wraps a file object to write a header before the first output.
  """
  
  def __init__(self, file_, log_header_title):
    self._log_file = file_
    self._log_header_title = log_header_title
  
  def write(self, data):
    if self._log_header_title:
      self._write(get_log_header(self._log_header_title))
    
    self._write(data)
    
    self.write = self._write
  
  def _write(self, data):
    self._log_file.write(str(data))
    self.flush()
  
  def flush(self):
    self._log_file.flush()
  
  def close(self):
    self._log_file.close()
