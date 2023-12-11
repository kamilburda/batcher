"""Validation of file paths, directory paths and file extensions."""

import abc
import os
import pathlib
import re
from typing import List, Tuple

__all__ = [
  'FileValidatorErrorStatuses',
  'StringValidator',
  'FilenameValidator',
  'FilepathValidator',
  'DirpathValidator',
  'FileExtensionValidator',
]


def N_(str_):
  return str_


class FileValidatorErrorStatuses:
  
  ERROR_STATUSES = (
    IS_EMPTY,
    HAS_INVALID_CHARS,
    DRIVE_HAS_INVALID_CHARS,
    HAS_TRAILING_SPACES,
    HAS_TRAILING_PERIOD,
    HAS_INVALID_NAMES,
    EXISTS_BUT_IS_NOT_DIR
  ) = list(range(7))


class StringValidator(metaclass=abc.ABCMeta):
  """Interface to validate strings.
  
  This class does not specify which strings are valid (i.e. whether they contain
  invalid characters, substrings, etc.). This should be handled by subclasses.
  """
  
  ERROR_STATUSES_MESSAGES = {}
  
  @classmethod
  def is_valid(cls, string_to_check: str) -> Tuple[bool, List[Tuple[int, str]]]:
    """Checks if the specified string is valid.
    
    Returns:
      A tuple of two elements:
        * ``True`` if the string is valid, ``False`` otherwise.
        * ``status_messages`` - If the string is invalid, ``status_messages`` is
          a list of (status code, status message) tuples describing why the string
          is invalid. Otherwise, it is an empty list.
    """
    pass
  
  @classmethod
  def validate(cls, string_to_validate: str) -> str:
    """Modifies the specified string to make it valid."""
    pass
  
  @classmethod
  def _get_status(cls, status):
    return status, _(cls.ERROR_STATUSES_MESSAGES[status])


class FilenameValidator(StringValidator):
  r"""Class for validating file names (basenames).
  
  In this class, filenames are considered valid if they:
    * do not contain control characters with ordinal numbers 0-31 and 127-159
    * do not contain the following special characters:

        <>:"/\|?*

    * do not start or end with spaces
    * do not end with one or more periods
    * do not have invalid names according to the naming conventions for the
      Windows platform:
      http://msdn.microsoft.com/en-us/library/aa365247%28VS.85%29
    * are not empty or ``None``
  """
  
  _INVALID_CHARS_PATTERN = r'[\x00-\x1f\x7f-\x9f<>:"\\/|?*]'
  
  # Invalid names for the Windows platform. Taken from:
  # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247%28v=vs.85%29.aspx
  _INVALID_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6',
    'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
    'LPT7', 'LPT8', 'LPT9'}
  
  ERROR_STATUSES_MESSAGES = {
    FileValidatorErrorStatuses.IS_EMPTY: N_('Filename is not specified.'),
    FileValidatorErrorStatuses.HAS_INVALID_CHARS: N_(
      'Filename contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_TRAILING_SPACES: N_(
      'Filename cannot end with spaces.'),
    FileValidatorErrorStatuses.HAS_TRAILING_PERIOD: N_(
      'Filename cannot end with a period.'),
    FileValidatorErrorStatuses.HAS_INVALID_NAMES: N_(
      '"{}" is a reserved name that cannot be used in filenames.\n')}
  
  @classmethod
  def is_valid(cls, filename: str) -> Tuple[bool, List[Tuple[int, str]]]:
    if not filename or filename is None:
      return False, [cls._get_status(FileValidatorErrorStatuses.IS_EMPTY)]
    
    status_messages = []
    
    if re.search(cls._INVALID_CHARS_PATTERN, filename):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_INVALID_CHARS))
    
    if filename.endswith(' '):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_SPACES))
    
    if filename.endswith('.'):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_PERIOD))
    
    root, _unused = os.path.splitext(filename)
    if root.upper() in cls._INVALID_NAMES:
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_INVALID_NAMES))
    
    is_valid = not status_messages
    return is_valid, status_messages
  
  @classmethod
  def validate(cls, filename: str) -> str:
    """Validates the specified filename by removing invalid characters.
    
    If the filename is one of the reserved names for the Windows platform,
    ``' (1)'`` is appended to the filename (before the file extension if it
    has one).
    
    If the filename is truncated to an empty string, ``'Untitled'`` is returned.
    """
    filename = re.sub(cls._INVALID_CHARS_PATTERN, '', filename).strip(' ').rstrip('.')
    
    root, ext = os.path.splitext(filename)
    # For reserved names, the comparison must be case-insensitive (because
    # Windows has case-insensitive filenames).
    if root.upper() in cls._INVALID_NAMES:
      filename = f'{root} (1){ext}'
    
    if not filename:
      filename = _('Untitled')
    
    return filename


class FilepathValidator(StringValidator):
  r"""Class for validating file paths (relative or absolute).
  
  The same validation rules that apply to file names in the
  ``FilenameValidator`` class apply to file paths in this class, with the
  following exceptions:
    * ``'/'`` and ``'\'`` characters are allowed
    * ``':'`` character is allowed to appear at the root level only as part of a
      drive letter, e.g. ``'C:\'``
  """

  _INVALID_CHARS = r'\x00-\x1f\x7f-\x9f<>"|?*'
  _VALID_DRIVE_CHARS = r':'
  
  _INVALID_CHARS_PATTERN_WITHOUT_DRIVE = f'[{_INVALID_CHARS}]'
  _INVALID_CHARS_PATTERN = f'[{_INVALID_CHARS}{_VALID_DRIVE_CHARS}]'
  
  _INVALID_NAMES = FilenameValidator._INVALID_NAMES
  
  ERROR_STATUSES_MESSAGES = {
    FileValidatorErrorStatuses.IS_EMPTY: N_('File path is not specified.'),
    FileValidatorErrorStatuses.DRIVE_HAS_INVALID_CHARS: N_(
      'Drive letter contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_INVALID_CHARS: N_(
      'File path contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_TRAILING_SPACES: N_(
      'Path components in the file path cannot end with spaces.'),
    FileValidatorErrorStatuses.HAS_TRAILING_PERIOD: N_(
      'Path components in the file path cannot end with a period.'),
    FileValidatorErrorStatuses.HAS_INVALID_NAMES: N_(
      '"{}" is a reserved name that cannot be used in file paths.\n')}
  
  @classmethod
  def is_valid(cls, filepath):
    if not filepath or filepath is None:
      return False, [cls._get_status(FileValidatorErrorStatuses.IS_EMPTY)]
    
    status_messages = []
    statuses = set()
    invalid_names_status_message = ''
    
    filepath = os.path.normpath(filepath)
    
    drive, path = os.path.splitdrive(filepath)
    
    if drive:
      if re.search(cls._INVALID_CHARS_PATTERN_WITHOUT_DRIVE, drive):
        status_messages.append(
          cls._get_status(FileValidatorErrorStatuses.DRIVE_HAS_INVALID_CHARS))
    
    path_components = pathlib.Path(path).parts
    for path_component in path_components:
      if re.search(cls._INVALID_CHARS_PATTERN, path_component):
        statuses.add(FileValidatorErrorStatuses.HAS_INVALID_CHARS)
      if path_component.endswith(' '):
        statuses.add(FileValidatorErrorStatuses.HAS_TRAILING_SPACES)
      if path_component.endswith('.'):
        statuses.add(FileValidatorErrorStatuses.HAS_TRAILING_PERIOD)
      
      root, _unused = os.path.splitext(path_component)
      if root.upper() in cls._INVALID_NAMES:
        statuses.add(FileValidatorErrorStatuses.HAS_INVALID_NAMES)
        invalid_names_status_message += (
          cls.ERROR_STATUSES_MESSAGES[
            FileValidatorErrorStatuses.HAS_INVALID_NAMES].format(root))
    
    if FileValidatorErrorStatuses.HAS_INVALID_CHARS in statuses:
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_INVALID_CHARS))
    if FileValidatorErrorStatuses.HAS_TRAILING_SPACES in statuses:
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_SPACES))
    if FileValidatorErrorStatuses.HAS_TRAILING_PERIOD in statuses:
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_PERIOD))
    if FileValidatorErrorStatuses.HAS_INVALID_NAMES in statuses:
      invalid_names_status_message = invalid_names_status_message.rstrip('\n')
      status_messages.append(
        (FileValidatorErrorStatuses.HAS_INVALID_NAMES, invalid_names_status_message))
    
    is_valid = not status_messages
    return is_valid, status_messages
  
  @classmethod
  def validate(cls, filepath):
    filepath = os.path.normpath(filepath)
    drive, path = os.path.splitdrive(filepath)
    
    if drive:
      drive = re.sub(cls._INVALID_CHARS_PATTERN_WITHOUT_DRIVE, '', drive)
    
    path_components = list(pathlib.Path(path).parts)
    for i in range(len(path_components)):
      path_component = re.sub(cls._INVALID_CHARS_PATTERN, '', path_components[i])
      path_component = path_component.strip(' ').rstrip('.')
      
      root, ext = os.path.splitext(path_component)
      if root.upper() in cls._INVALID_NAMES:
        path_component = f'{root} (1){ext}'
      
      path_components[i] = path_component
    
    # Normalize again, since the last path component might be truncated to an
    # empty string, resulting in a trailing slash.
    filepath = os.path.normpath(os.path.join(drive, *path_components))
    
    return filepath


class DirpathValidator(FilepathValidator):
  """Class used for validating directory paths (relative or absolute).
  
  The same validation rules that apply to file paths in the
  `FilepathValidator` class apply to directory paths in this class,
  with the following additions:
    * the specified path must be a directory path
  """
  
  ERROR_STATUSES_MESSAGES = {
    FileValidatorErrorStatuses.IS_EMPTY: N_('Directory path is not specified.'),
    FileValidatorErrorStatuses.DRIVE_HAS_INVALID_CHARS: N_(
      'Drive letter contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_INVALID_CHARS: N_(
      'Directory path contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_TRAILING_SPACES: N_(
      'Path components in the directory path cannot end with spaces.'),
    FileValidatorErrorStatuses.HAS_TRAILING_PERIOD: N_(
      'Path components in the directory path cannot end with a period.'),
    FileValidatorErrorStatuses.HAS_INVALID_NAMES: N_(
      '"{}" is a reserved name that cannot be used in directory paths.\n'),
    FileValidatorErrorStatuses.EXISTS_BUT_IS_NOT_DIR: N_(
      'Specified path is not a directory path.')}
  
  @classmethod
  def is_valid(cls, dirpath):
    is_valid, status_messages = super().is_valid(dirpath)

    if not is_valid:
      return is_valid, status_messages
    
    if os.path.exists(dirpath) and not os.path.isdir(dirpath):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.EXISTS_BUT_IS_NOT_DIR))
    
    is_valid = not status_messages
    return is_valid, status_messages
  

class FileExtensionValidator(StringValidator):
  r"""Class use for validating file extensions.
  
  In this class, file extensions are considered valid if they:
    * do not contain control characters with ordinal numbers 0-31 and 127-159
    * do not contain the following special characters:

        <>:"/\|?*

    * do not end with spaces or periods
  """
  
  _INVALID_CHARS_PATTERN = FilenameValidator._INVALID_CHARS_PATTERN
  
  ERROR_STATUSES_MESSAGES = {
    FileValidatorErrorStatuses.IS_EMPTY: N_('File extension is not specified.'),
    FileValidatorErrorStatuses.HAS_INVALID_CHARS: N_(
      'File extension contains invalid characters.'),
    FileValidatorErrorStatuses.HAS_TRAILING_SPACES: N_(
      'File extension cannot end with spaces.'),
    FileValidatorErrorStatuses.HAS_TRAILING_PERIOD: N_(
      'File extension cannot end with a period.')}
  
  @classmethod
  def is_valid(cls, file_extension):
    if not file_extension or file_extension is None:
      return False, [cls._get_status(FileValidatorErrorStatuses.IS_EMPTY)]
    
    status_messages = []
    
    if re.search(cls._INVALID_CHARS_PATTERN, file_extension):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_INVALID_CHARS))
    
    if file_extension.endswith(' '):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_SPACES))
      
    if file_extension.endswith('.'):
      status_messages.append(
        cls._get_status(FileValidatorErrorStatuses.HAS_TRAILING_PERIOD))
    
    is_valid = not status_messages
    return is_valid, status_messages
  
  @classmethod
  def validate(cls, file_extension):
    return re.sub(cls._INVALID_CHARS_PATTERN, '', file_extension).rstrip(' ').rstrip('.')
