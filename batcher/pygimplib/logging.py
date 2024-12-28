"""Logging-related classes."""

from collections.abc import Iterable
import datetime
import os
import sys
from typing import IO, List, Optional


try:
  import gi
  gi.require_version('Gimp', '3.0')
  from gi.repository import Gimp

  from . import invocation as pginvocation
except (ImportError, ValueError):
  _gobject_dependent_modules_imported = False
else:
  _gobject_dependent_modules_imported = True


from . import constants as pgconstants

_HANDLES = ('file', 'gimp_message')

_TEE_STDOUT = None
_TEE_STDERR = None


_ORIG_STDOUT = sys.stdout
_ORIG_STDERR = sys.stderr


def log_output(
      stdout_handles: Optional[List[str]] = None,
      stderr_handles: Optional[List[str]] = None,
      log_dirpaths: Optional[List[str]] = None,
      log_output_filename: Optional[str] = None,
      log_error_filename: Optional[str] = None,
      log_header_title: str = '',
      flush_output: bool = False):
  """Duplicates output from `sys.stdout` and `sys.stderr` to files.

  You may duplicate output to sources specified via `stdout_handles` and error
  output via `stderr_handles`, respectively. Use one or more of the following
  handles:
  * ``'file'`` - duplicates output to a file.
  * ``'gimp_message'`` - duplicates output to the GIMP message console.

  Logging is reset on each call to this function and `sys.stdout` and
  `sys.stderr` are restored at the beginning of this function.

  Args:
    stdout_handles: List of handles to duplicate standard output to.
    stderr_handles: List of handles to duplicate standard error output to.
    log_dirpaths:
      List of directory paths for log files if the ``'file'`` handle is
      specified. If the first path is not valid or the permission to write is
      denied there, subsequent directories are probed until a valid directory is
      identified.
    log_output_filename:
      File name of the log file to write standard output to if the ``'file'``
      handle is specified in ``stdout_handles``.
    log_error_filename:
      File name of the log file to write standard output to if the ``'file'``
      handle is specified in ``stderr_handles``.
    log_header_title:
      Optional title in the log header, written before the first output to the
      log files.
    flush_output:
      If ``True``, the output is flushed after each instance of writing. Only
      has effect for ``'file'`` handles.
  """
  global _TEE_STDOUT
  global _TEE_STDERR

  _close_log_files_and_reset_streams(_TEE_STDOUT, _TEE_STDERR)

  output_files = _prepare_log_files(stdout_handles, log_dirpaths, log_output_filename)

  if output_files:
    _TEE_STDOUT = Tee('stdout', log_header_title=log_header_title, flush_output=flush_output)
    _TEE_STDOUT.start(output_files)

  error_files = _prepare_log_files(stderr_handles, log_dirpaths, log_error_filename)

  if error_files:
    _TEE_STDERR = Tee('stderr', log_header_title=log_header_title, flush_output=flush_output)
    _TEE_STDERR.start(error_files)


def _prepare_log_files(handles, log_dirpaths, log_filename):
  log_files = []

  if handles is not None:
    for handle in handles:
      if handle == 'file':
        if log_dirpaths is None or log_filename is None:
          raise ValueError(
            'log directory paths and filename must be specified if logging to a file')

        log_files.append(create_log_file(log_dirpaths, log_filename))
      elif handle == 'gimp_message':
        if _gobject_dependent_modules_imported:
          log_files.append(GimpMessageFile())
      else:
        raise ValueError(f'handle not valid; valid handles: {", ".join(_HANDLES)}')

  return log_files


def get_log_header(log_header_title: str) -> str:
  """Returns the header written to a file before writing output for the first
  time.
  """
  return '\n'.join(('', '=' * 80, log_header_title, str(datetime.datetime.now()), '\n'))


def create_log_file(log_dirpaths: Iterable[str], log_filename: str, mode: str = 'a') -> IO:
  """Creates a log file in the first file path that can be written to.

  Args:
    log_dirpaths:
      A list-like of directory paths. The first path along with
      ``log_filename`` is used to create a log file. If that fails,
      the second directory path is used, and so on, until a file is
      successfully created.
    log_filename:
      File name of the log file.
    mode:
      Mode for opening a file. Can be any mode accepted by the built-in
      `open()`.

  Returns:
    The created log file upon successful creation, ``None`` otherwise.
  """
  log_file = None

  for log_dirpath in log_dirpaths:
    try:
      os.makedirs(log_dirpath, exist_ok=True)
    except OSError:
      continue

    try:
      log_file = open(
        os.path.join(log_dirpath, log_filename), mode, encoding=pgconstants.TEXT_FILE_ENCODING)
    except IOError:
      continue
    else:
      break

  return log_file


def _close_log_files_and_reset_streams(tee_stdout, tee_stderr):
  if tee_stdout is not None:
    tee_stdout.stop()

  if tee_stderr is not None:
    tee_stderr.stop()

  sys.stdout = _ORIG_STDOUT
  sys.stderr = _ORIG_STDERR


if _gobject_dependent_modules_imported:
  class GimpMessageFile:

    def __init__(self, handler_type=Gimp.MessageHandlerType.ERROR_CONSOLE, delay_milliseconds=50):
      self._orig_handler = Gimp.message_get_handler()
      self._delay_milliseconds = delay_milliseconds

      Gimp.message_set_handler(handler_type)

      self._buffer = ''

    def write(self, data):
      self._buffer += str(data)

      pginvocation.timeout_add_strict(self._delay_milliseconds, self._display_data_and_flush)

    def flush(self):
      pass

    def close(self):
      Gimp.message_set_handler(self._orig_handler)

    def _display_data_and_flush(self):
      Gimp.message(self._buffer)
      self._buffer = ''


# Original version: https://stackoverflow.com/a/616686
class Tee:
  """File-like object that duplicates a stream -- either ``stdout`` or
  ``stderr`` -- to the specified files, much like the Unix `tee` command.
  """

  def __init__(
        self,
        stream_name: str,
        log_header_title: Optional[str] = None,
        flush_output: bool = False,
  ):
    """Initializes a `Tee` instance.

    Args:
      stream_name:
        Either ``'stdout'`` or ``'stderr'`` representing `sys.stdout` or
        `sys.stderr`, respectively. Other objects are invalid and raise
        `ValueError`.
      log_header_title:
        Header text to write when writing into the file for the first time.
      flush_output:
        If ``True``, the output is flushed after each write.
    """
    self._valid_stream_names = {'stdout', 'stderr'}

    if stream_name not in self._valid_stream_names:
      raise ValueError(f'invalid stream "{stream_name}"; must be "stdout" or "stderr"')

    self._stream_name = stream_name

    self.log_header_title = log_header_title if log_header_title is not None else ''
    self.flush_output = flush_output

    self._orig_stream = getattr(sys, stream_name)

    self._files = []
    self._is_running = False

  def start(self, files: List):
    """Starts duplicating output to the specified files or file-like objects."""
    setattr(sys, self._stream_name, self)

    self._files = files
    self._is_running = True

  def stop(self):
    """Stops duplicating output to the files specified in `start()`."""
    if not self._is_running:
      return

    setattr(sys, self._stream_name, self._orig_stream)

    for file_ in self._files:
      file_.close()

    self._files = []
    self._is_running = False

  def is_running(self):
    """Return ``True`` if the duplication of output is enabled, ``False``
    otherwise.
    """
    return self._is_running

  def write(self, data):
    """Writes output to both the stream and the files specified in `start()`.

    If `log_header_title` is not empty, the log header is written before the
    first output.
    """
    if self.log_header_title:
      for file_ in self._files:
        file_.write(get_log_header(self.log_header_title))

    self._write_with_flush(data)

    if not self.flush_output:
      self.write = self._write
    else:
      self.write = self._write_with_flush

  def _write(self, data):
    for file_ in self._files:
      file_.write(data)

    if self._orig_stream is not None:
      self._orig_stream.write(data)

  def _write_with_flush(self, data):
    for file_ in self._files:
      file_.write(data)
      file_.flush()

    if self._orig_stream is not None:
      self._orig_stream.write(data)
      self._orig_stream.flush()

  def flush(self):
    for file_ in self._files:
      file_.flush()

    if self._orig_stream is not None:
      self._orig_stream.flush()
