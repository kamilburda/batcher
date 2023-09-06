"""Functions to modify strings or file paths to make them unique."""

from collections.abc import Iterable
import os
from typing import Callable, Generator, Optional

__all__ = [
  'uniquify_string',
  'uniquify_filepath',
  'uniquify_string_generic',
]


def uniquify_string(
      str_: str,
      existing_strings: Iterable[str],
      position: Optional[int] = None,
      generator: Optional[Generator[str, None, None]] = None,
) -> str:
  """Modifies `str_` if needed to be unique among all ``existing_strings``.

  For more information on the ``position`` and ``generator`` parameters, see
  ``uniquify_string_generic()``.
  """
  return uniquify_string_generic(
    str_,
    lambda str_param: str_param not in existing_strings,
    position,
    generator)
  

def uniquify_filepath(
      filepath: str,
      position: Optional[int] = None,
      generator: Optional[Generator[str, None, None]] = None,
) -> str:
  """Modifies the specified file path to be unique if a file with the same path
  already exists.

  For more information on the ``position`` and ``generator`` parameters, see
  ``uniquify_string_generic()``.
  """
  return uniquify_string_generic(
    filepath,
    lambda filepath_param: not os.path.exists(filepath_param),
    position,
    generator)


def uniquify_string_generic(
      str_: str,
      is_unique_func: Callable[[str], bool],
      position: Optional[int] = None,
      generator: Optional[Generator[str, None, None]] = None,
) -> str:
  """Modifies ``str_`` to be unique if ``is_unique_func`` for the given string
  returns ``False``.

  If the string must be made unique, a substring is inserted according to
  ``generator`` at the given ``position``. Otherwise, ``str_`` is returned
  unmodified.
  
  Args:
    str_:
      The string to make unique.
    is_unique_func:
      A function that returns ``True`` if ``str_`` is unique, ``False``
      otherwise. ``is_unique_func`` must accept a string as its only parameter
      and return a boolean.
    position:
      Position (index) where the substring is inserted.
      If ``position`` is ``None``, the substring is inserted at the end of
      ``str_``.
    generator:
      A generator object that generates a unique substring in each iteration.
      If ``None``, the generator yields default strings - ``' (1)'``,
      ``' (2)'``, and so on.
    
    An example of a custom generator:

      def _generate_unique_copy_string():
        substr = ' - copy'
        yield substr
        
        substr = ' - another copy'
        yield substr
         
        i = 2
        while True:
          yield f'{substr} {i}'
          i += 1
    
    This custom generator yields ``' - copy'``, ``' - another copy'``,
    ``' - another copy 2'``, and so on.
  """
  
  def _get_uniquified_string(gen):
    return f'{str_[0:position]}{next(gen)}{str_[position:]}'

  def _generate_unique_number():
    i = 1
    while True:
      yield f' ({i})'
      i += 1
  
  if is_unique_func(str_):
    return str_
  
  if position is None:
    position = len(str_)
  
  if generator is None:
    generator = _generate_unique_number()
  
  uniq_str = _get_uniquified_string(generator)
  while not is_unique_func(uniq_str):
    uniq_str = _get_uniquified_string(generator)
  
  return uniq_str
