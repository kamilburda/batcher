"""Data structures representing a directory.

The directory defined allows storing special values that can be used in the
client code to dynamically resolve a directory.
"""

from typing import Callable, Union
import dataclasses
import os

from gi.repository import Gio

from src import utils


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
      if self.value in SPECIAL_VALUES:
        return SPECIAL_VALUES[self.value].resolve_func(batcher)
      else:
        return self.value
    else:
      raise ValueError(f'unrecognized/unsupported directory type: {self.type_}')


def _get_top_level_directory(batcher):
  # TODO: Make this work for Export Images
  # TODO: Make this work for Edit and Save Images
  if batcher.current_item.parents:
    return os.path.dirname(batcher.current_item.parents[0].id)
  else:
    return os.path.dirname(batcher.current_item.id)


@dataclasses.dataclass(frozen=True)
class SpecialValue:
  name: str
  display_name: str
  resolve_func: Callable


SPECIAL_VALUES = {
  'match_input_folders': SpecialValue(
    'match_input_folders', _('Match input folders'), _get_top_level_directory),
}
