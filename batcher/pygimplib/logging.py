"""Logging-related classes."""

from collections.abc import Iterable
import datetime
import os
import sys
from typing import IO, Optional

from . import constants
from . import pdbutils as pgpdbutils

_LOG_MODES = ('none', 'error', 'output_and_error')

_TEE_STDOUT = None
_TEE_STDERR = None


def log_output(
      log_mode: str,
      log_dirpaths: Iterable[str],
      log_output_filename: Optional[str] = None,
      log_error_filename: Optional[str] = None,
      log_header_title: str = '',
      flush_output: bool = False):
  """Duplicates output from `sys.stdout` and `sys.stderr` to files.

  Logging is reset on each call to this function. For example,
  if ``log_mode`` was ``'output_and_error'`` and ``log_mode`` in the current
  call is ``'none'``, any log files created by this function are closed,
  and `sys.stdout` and `sys.stderr` are restored.

  Args:
    log_mode:
      The log mode. Possible values:
      * ``'none'`` - No action is performed, i.e. the output is not duplicated
        anywhere.
      * ``'error'`` - Duplicates error output (`sys.stderr`) to a file.
      * ``'output_and_error'`` - Both the standard (`sys.stdout`) and the error
        output (`sys.stderr`) are duplicated to log files.
    log_dirpaths:
      List of directory paths for log files. If the first path is not valid or
      the permission to write is denied, subsequent directories are used.
    log_output_filename:
      File name of the log file to write standard output to. This parameter
      must not be ``None`` if ``log_mode`` is ``'output_and_error'``. Applies
      to the ``'output_and_error'`` mode only.
    log_error_filename:
      File name of the log file to write error output to. This parameter must
      not be ``None`` if ``log_mode`` is ``'output_and_error'`` or
      ``'error'``.
    log_header_title:
      Optional title in the log header, written before the first output to the
      log files.
    flush_output:
      If ``True``, the output is flushed after each instance of writing.
  """
  global _TEE_STDOUT
  global _TEE_STDERR

  _close_log_files_and_reset_streams(_TEE_STDOUT, _TEE_STDERR)

  if log_mode == 'none':
    return

  if log_mode in ['error', 'output_and_error']:
    log_error_file = create_log_file(log_dirpaths, log_error_filename)
    if log_error_file is not None:
      _TEE_STDERR = Tee(sys.stderr, log_header_title=log_header_title, flush_output=flush_output)
      _TEE_STDERR.start(log_error_file)

    if log_mode == 'output_and_error':
      log_output_file = create_log_file(log_dirpaths, log_output_filename)
      if log_output_file is not None:
        _TEE_STDOUT = Tee(sys.stdout, log_header_title=log_header_title, flush_output=flush_output)
        _TEE_STDOUT.start(log_output_file)
  else:
    raise ValueError(f'invalid log mode "{log_mode}"; allowed values: {", ".join(_LOG_MODES)}')


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
        os.path.join(log_dirpath, log_filename), mode, encoding=constants.TEXT_FILE_ENCODING)
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

  sys.stdout = sys.__stdout__
  sys.stderr = sys.__stderr__


# Original version: https://stackoverflow.com/a/616686
class Tee(object):
  """File-like object that duplicates a stream -- either ``stdout`` or
  ``stderr`` -- to the specified file, much like the Unix `tee` command.
  """

  def __init__(
        self,
        stream: IO,
        log_header_title: Optional[str] = None,
        flush_output: bool = False,
  ):
    """Initializes a `Tee` instance.

    Args:
      stream:
        Either `sys.stdout` or `sys.stderr`. Other objects are invalid and raise
        `ValueError`.
      log_header_title:
        Header text to write when writing into the file for the first time.
      flush_output:
        If ``True``, the output is flushed after each write.
    """
    self._streams = {sys.stdout: 'stdout', sys.stderr: 'stderr'}

    self.log_header_title = log_header_title if log_header_title is not None else ''
    self.flush_output = flush_output

    self._file = None
    self._is_running = False

    self._orig_stream = None
    self._stream_name = ''
    self._stream = None

    self.stream = stream

  def __del__(self):
    if self.is_running():
      self.stop()

  @property
  def stream(self):
    """The stream whose output is being duplicated"""
    return self._stream

  @stream.setter
  def stream(self, value: IO):
    """Modifies the stream to duplicate output from.

    Args:
      value:
        Stream object -- either `sys.stdout` or `sys.stderr`.
    """
    self._stream = value
    if value in self._streams:
      self._stream_name = self._streams[value]
    else:
      raise ValueError('invalid stream; must be sys.stdout or sys.stderr')

  def start(self, file_: IO):
    """Starts duplicating output to the specified file.

    Args:
      file_:
        File or file-like object to write output to.
    """
    self._orig_stream = self.stream
    setattr(sys, self._stream_name, self)

    self._file = file_
    self._is_running = True

  def stop(self):
    """Stops duplicating output to the file."""
    setattr(sys, self._stream_name, self._orig_stream)
    self._file.close()

    self._file = None
    self._is_running = False

  def is_running(self):
    """Return ``True`` if duplication to file is enabled, ``False`` otherwise.
    """
    return self._is_running

  def write(self, data):
    """Writes output to both the stream and the specified file.

    If `log_header_title` is not empty, the log header is written before the
    first output.
    """
    if self.log_header_title:
      self._file.write(get_log_header(self.log_header_title))

    self._write_with_flush(data)

    if not self.flush_output:
      self.write = self._write
    else:
      self.write = self._write_with_flush

  def _write(self, data):
    self._file.write(data)
    self._stream.write(data)

  def _write_with_flush(self, data):
    self._file.write(data)
    self._file.flush()
    self._stream.write(data)
    self._stream.flush()

  def flush(self):
    self._file.flush()
    self._stream.flush()
