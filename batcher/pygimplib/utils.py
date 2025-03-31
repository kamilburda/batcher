"""Utility functions and classes."""

import ast
import contextlib
import inspect
import os
import struct
import sys
import traceback as traceback_
from typing import Callable, Optional, Tuple, Type
import warnings

from gi.repository import GLib


def empty_context(*args, **kwargs) -> contextlib.AbstractContextManager:
  """Returns a context manager that does nothing.

  This is a wrapper of `contextlib.nullcontext` that allows passing arbitrary
  arguments that will be ignored.
  """
  return contextlib.nullcontext()


def empty_func(*args, **kwargs):
  """A function that does nothing and returns ``None``.

  Use this function when an empty function is desired to be passed as a
  parameter.
  
  For example, if you need to serialize a `collections.defaultdict`
  instance (e.g. via `pickle`) returning ``None`` for missing keys,
  you need to use a named function instead of ``lambda: None``. To emphasize
  this particular intent, you may want to use the alias `return_none_func()`
  instead.
  """
  return None


return_none_func = empty_func
"""Alias for `empty_func()` emphasizing that the function should be used
whenever ``None`` is meant to be returned."""


def create_empty_func(return_value=None) -> Callable:
  """Returns an empty function returning the specified return value."""
  def _empty_func_with_return_value(*args, **kwargs):
    return return_value
  
  return _empty_func_with_return_value


def stringify_object(object_, name: Optional[str] = None) -> str:
  """Returns a string representation of the specified object.

  ``name`` is an object identifier that can be used in the ``__str__()``
  method of a class to return a more readable string representation than the
  default.
  """
  return f'<{type(object_).__qualname__} "{name}">'


def reprify_object(object_, name: Optional[str] = None) -> str:
  """Returns a string representation of the object useful for ``repr()`` calls.
  
  The first part of the string, the class path, starts from the
  ``'pygimplib'`` package. If the full class path is not available, only the
  class name is given.

  A custom ``name``, if not ``None``, replaces the default ``'object'``
  substring inserted in the string.
  """
  object_type = type(object_)
  
  if hasattr(object_type, '__module__'):
    object_type_path = f'{object_type.__module__}.{object_type.__qualname__}'
  else:
    object_type_path = object_type.__qualname__

  object_id = id(object_)

  return '<{} {} at {}>'.format(
    object_type_path,
    f'"{name}"' if name is not None else 'object',
    f'{object_id:#0{32 - len(hex(object_id))}x}',
  )


def get_module_root(full_module_name: str, name_component_to_trim_after: str) -> str:
  """Returns the root of the specified module path.

  The root is the part of the module path (separated by ``'.'`` characters)
  from the beginning up to the matching module name component including that
  component (``name_component_to_trim_after``).
  
  If ``name_component_to_trim_after`` does not match any name component from
  ``full_module_name``, ``full_module_name`` is returned.
  """
  module_name_components = full_module_name.split('.')
  
  if name_component_to_trim_after in module_name_components:
    name_component_index = module_name_components.index(name_component_to_trim_after)
    return '.'.join(module_name_components[:name_component_index + 1])
  else:
    return full_module_name


def get_pygimplib_module_path() -> str:
  """Returns the top-level module path of the pygimplib library."""
  return get_module_root(__name__, 'pygimplib')


def get_current_module_filepath() -> str:
  """Returns the full path name of the module this function is called from."""
  return inspect.stack()[1][1]


def create_read_only_property(obj, name: str, value):
  """Dynamically adds a read-only property to the ``obj`` object.

  A property and its accompanying private attribute are created. The property
  will have name ``name`` and the private attribute will have the property name
  prepended with ``_``, i.e. ``_[name]``

  The private attribute holds the ``value`` and the property returns this value.
  """
  setattr(obj, f'_{name}', value)
  setattr(
    type(obj),
    name,
    property(fget=lambda obj_, name_=name: getattr(obj_, f'_{name_}')))


def bytes_to_signed_bytes(data: bytes) -> Tuple[int, ...]:
  """Coverts a ``bytes`` object to a sequence of signed byte values (values from
  -128 to 127).

  This function is useful when pickling data to be stored as data for
  `Gimp.Parasite` instances as GIMP parasites do not accept data with byte
  values from 128 to 255.
  """
  return struct.unpack(f'>{len(data)}b', data)


def signed_bytes_to_bytes(data: Tuple[int, ...]) -> bytes:
  """Coverts a sequence of signed byte values (values from -128 to 127) to
  ``bytes``.

  This function is useful when unpickling data from `Gimp.Parasite`
  instances as GIMP parasites do not accept data with byte values from 128 to
  255.
  """
  return struct.pack(f'>{len(data)}b', *data)


def escaped_string_to_bytes(str_: str, remove_overflow: bool = False) -> bytes:
  """Converts the input string with escaped characters to a byte sequence.

  Any characters after "unescaping" in the input string with an ordinal number
  higher than 255 will cause an overflow error to be raised. You can pass
  ``remove_overflow=True`` to remove such characters.

  The input string is meant to contain escape sequences such as ``'\\x7f'`` for
  special characters rather than the corresponding unescaped characters.
  If the input string contains certain unescaped characters (such as the NUL
  character), they are internally escaped to make sure that the whole string is
  unescaped without errors.
  """
  processed_str = (
    str_.replace('\x00', '\\x00')  # NUL character
    .replace('\x0a', '\\x0a')  # LF character
    .replace('\x0d', '\\x0d')  # CR character
    .replace('"', '\\x22')  # `"` is used to enclose strings in `ast.literal_eval()`
  )

  try:
    processed_str = ast.literal_eval(f'"{processed_str}"')
  except Exception:
    return b''
  else:
    return string_to_bytes(processed_str, remove_overflow=remove_overflow)


def string_to_bytes(str_: str, remove_overflow: bool = False) -> bytes:
  """Converts the input string to a byte sequence.

  Any characters in the input string with an ordinal number higher than 255 will
  cause an overflow error to be raised. You can pass ``remove_overflow=True`` to
  remove such characters.
  """
  if remove_overflow:
    str_processed = ''.join(i for i in str_ if ord(i) <= 255)
  else:
    str_processed = str_

  return bytes(ord(c) for c in str_processed)


def bytes_to_escaped_string(bytes_: bytes) -> str:
  """Converts the input byte sequence to a string with escaped special character
  sequences.

  For example, a byte sequence ``b'Test\x00\x7f\xffdata'`` will be converted to
  ``'Test\\x00\\x7f\\xffdata'``.
  """
  # Removes the `b'` prefix and the `'` suffix
  return repr(bytes_)[2:-1]


def bytes_to_string(bytes_: bytes) -> str:
  """Converts the input byte sequence to a string.

  For example, a byte sequence ``b'Test\x00\x7f\xffdata'`` will be converted to
  ``'Test\x00\x7f\xffdata'``.
  """
  return bytes_.decode('ansi')


def warn_with_traceback(message: str, *args, traceback=None, **kwargs):
  """Prints a warning that includes the traceback up to the warning function
  call.

  You can pass additional arguments defined in `warnings.warn`.

  You can also pass a custom traceback if already created.
  """
  orig_showwarning = warnings.showwarning
  warnings.showwarning = _showwarning_with_traceback(traceback=traceback)

  warnings.warn(message, *args, **kwargs)

  warnings.showwarning = orig_showwarning


def format_message_with_traceback(
      message: str,
      category: Type[Warning],
      filename: str,
      lineno: int,
      stack_levels_to_keep: Optional[int] = -1,
) -> str:
  """Formats a message to include traceback.

  ``message``, ``category``, ``filename`` and ``lineno`` have the same meaning
  as in `warnings.showwarning()`.

  For the description of ``stack_levels_to_keep``, see `get_traceback()`.
  """
  return (
    f'{"=" * 80}\n'
    f'{filename}:{lineno}: {category.__qualname__}: {message}\n'
    '\nTraceback:\n'
    f'{get_traceback(stack_levels_to_keep)}'
  )


def get_traceback(stack_levels_to_keep: Optional[int] = -1):
  """Returns traceback of the most recent call.

  ``stack_levels_to_keep`` is the number of stack levels to keep when printing
  the traceback. The value can be negative to remove the last ``n`` levels, or
  ``None`` to keep all levels.
  """
  extracted_stack = traceback_.extract_stack()
  # This ensures that the call to `traceback.extract_stack()` will not be
  # included.
  extracted_stack = extracted_stack[:stack_levels_to_keep]

  return "".join(traceback_.format_list(extracted_stack))


def _showwarning_with_traceback(traceback=None):

  def _showwarning(message, category, filepath, lineno, file=None, line=None):
    """Wrapper to print warnings with traceback.

    Taken from: https://stackoverflow.com/a/22376126
    """
    log_file = file if hasattr(file, 'write') else sys.stderr

    if traceback is None:
      # `stack_levels_to_keep` is set to a value such that all function calls
      # leading to obtaining this message and printing the warning are ignored.
      formatted_traceback = format_message_with_traceback(
        message, category, filepath, lineno, stack_levels_to_keep=-5)
    else:
      formatted_traceback = traceback

    log_file.write(formatted_traceback)

  return _showwarning


def get_default_dirpath():
  """Returns a directory path that can be used as a default value for directory
  settings.

  The ``Pictures`` user folder is returned by default. If that is not available,
  the current working directory is returned instead.
  """
  try:
    dirpath = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
  except Exception:
    dirpath = None

  if dirpath is not None:
    return dirpath
  else:
    return os.getcwd()


def get_enum_values(enum_type):
  """Returns an iterable of values for the specified enumerated type.

  This is a wrapper function providing compatibility across multiple PyGObject
  versions as enums were reworked in PyGObject 3.51.0.
  """
  if hasattr(enum_type, '__members__'):
    return enum_type.__members__.values()
  elif hasattr(enum_type, '__enum_values__'):
    return enum_type.__enum_values__.values()
