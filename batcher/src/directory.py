"""Data structures representing a directory.

The directory defined allows storing special values that can be used in the
client code to dynamically resolve a directory.
"""

from typing import Callable, List, Union
import dataclasses
import os

from gi.repository import Gio

from src import utils
from src.procedure_groups import *


class DirectoryTypes:

  DIRECTORY_TYPES = (
    DIRECTORY,
    SPECIAL,
  ) = 'directory', 'special'


class Directory:
  """A simple data structure holding a directory.

  The value can refer to a directory path or a special value that is resolved
  dynamically.
  """

  def __init__(
        self,
        value: Union[str, Gio.File, None] = None,
        type_: str = DirectoryTypes.DIRECTORY,
  ):
    self.type_ = type_
    """Directory type. See `DirectoryTypes` for possible values."""
    self.value: str
    """Directory path if `type_` is `DirectoryTypes.DIRECTORY`, or a special
    value if `type_` is `DirectoryTypes.SPECIAL`.
    """

    if self.type_ == DirectoryTypes.DIRECTORY:
      if value is None:
        self.value = utils.get_default_dirpath()
      elif isinstance(value, Gio.File):
        self.value = (
          value.get_path() if value.get_path() is not None else utils.get_default_dirpath())
      else:
        self.value = value
    elif self.type_ == DirectoryTypes.SPECIAL:
      if value is not None:
        self.value = value
      else:
        raise ValueError('if directory type is DirectoryTypes.SPECIAL, value must not be None')
    else:
      raise ValueError(f'unrecognized/unsupported directory type: {self.type_}')

  def resolve(self, batcher: 'src.core.Batcher') -> str:
    """Resolves the current value to a directory path.

    If `type_` is `DirectoryTypes.DIRECTORY`, `value` is returned unchanged.

    If `type_` is `DirectoryTypes.SPECIAL`, a directory path is based on
    `value` and the ``batcher`` parameter. ``batcher`` is a
    `src.core.Batcher` instance used to perform batch processing. For
    resolving the directory, information about the current state of
    processing, such as `current_image` or `current_item` can be of use. If
    `value` has no associated resolution function, `value` is returned
    unchanged.
    """
    if self.type_ == DirectoryTypes.DIRECTORY:
      return self.value
    elif self.type_ == DirectoryTypes.SPECIAL:
      special_values = get_special_values()
      if self.value in special_values:
        return special_values[self.value].resolve_func(batcher)
      else:
        return self.value
    else:
      raise ValueError(f'unrecognized/unsupported directory type: {self.type_}')


def get_special_values():
  """Returns a list of allowed special values given the currently running
  plug-in procedure.
  """
  # We import `CONFIG` here to avoid circular imports.
  from config import CONFIG

  return {
    name: special_value for name, special_value in _SPECIAL_VALUES.items()
    if CONFIG.PROCEDURE_GROUP in special_value.procedure_groups
  }


def _get_top_level_directory(batcher):
  if batcher.current_item.parents:
    return os.path.dirname(batcher.current_item.parents[0].id)
  else:
    return os.path.dirname(batcher.current_item.id)


@dataclasses.dataclass(frozen=True)
class SpecialValue:
  name: str
  display_name: str
  resolve_func: Callable
  procedure_groups: List[str]


_SPECIAL_VALUES = {
  'match_input_folders': SpecialValue(
    'match_input_folders',
    _('Match input folders'),
    _get_top_level_directory,
    [CONVERT_GROUP],
  ),
}
