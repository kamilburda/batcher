"""Handling of existing files by the user - overwrite, skip, etc."""

import abc
import os
from typing import Dict, Optional, Tuple

from . import path as pgpath


class OverwriteChooser(metaclass=abc.ABCMeta):
  """Interface to indicate how to handle existing files.

  For example, if the user attempts to save a file to a path that already
  exists, subclasses of this class can be used to provide options to the user on
  how to handle the existing file (e.g. skip, overwrite or rename the existing
  file).
  """

  def __init__(self, overwrite_mode: int):
    """Initializes the instance with a default overwrite mode."""
    super().__init__()

    self._overwrite_mode = overwrite_mode
  
  @property
  def overwrite_mode(self) -> int:
    """The overwrite mode chosen by the user.

    By default, this is set to the value provided during object instantiation.
    """
    return self._overwrite_mode
  
  @abc.abstractmethod
  def choose(self, filepath: Optional[str] = None) -> int:
    """Returns a value indicating how to handle the conflicting file.

    The user is assumed to choose one of the possible overwrite modes. The
    overwrite modes and the implementation of handling conflicting files are
    left to the developer using the return value provided by this method.
    
    ``filepath`` is a file path that points to an existing file. This class uses
    the file path to simply display it to the user.
    """
    pass


class NoninteractiveOverwriteChooser(OverwriteChooser):
  """Class that simply stores an overwrite mode specified upon instantiation.

  The overwrite mode cannot be modified after instantiation.

  This class is suitable to be used in a non-interactive environment, i.e. with
  no user interaction.
  """
  
  def choose(self, filepath: Optional[str] = None) -> int:
    return self._overwrite_mode


class InteractiveOverwriteChooser(OverwriteChooser, metaclass=abc.ABCMeta):
  """Abstract class for choosing an overwrite mode interactively.
  """
  
  def __init__(
        self,
        values_and_display_names: Dict[int, str],
        default_value: int,
        default_response: int,
  ):
    super().__init__(default_value)
    
    self.values_and_display_names = values_and_display_names
    """Dictionary of (value, display name) pairs which define overwrite modes
    and their human-readable names.
    """

    self._values = list(self.values_and_display_names)
    
    if default_value not in self._values:
      raise ValueError(
        f'invalid default mode "{default_value}"; must be one of the following: {self._values}')

    self.default_response = default_response
    """Default overwrite mode to return if the user made a choice that
    returns a value not in ``values_and_display_names``. ``default_response``
    does not have to be any of the values in ``values_and_display_names``.
    """

    self._apply_to_all = False

  @property
  def apply_to_all(self) -> bool:
    """If ``True``, the user's choice applies to the current and all subsequent
    files. If ``False``, the user's choice applies to current file only.
    """
    return self._apply_to_all
  
  def choose(self, filepath: Optional[str] = None) -> int:
    if self._overwrite_mode is None or not self._apply_to_all:
      return self._choose(filepath)
    else:
      return self._overwrite_mode
  
  @abc.abstractmethod
  def _choose(self, filepath: str):
    """Allows the user to choose the overwrite mode and return it.
    
    If the choice results in a value that is not in
    ``values_and_display_names``, ``default_response``, must be returned.
    """
    pass


def handle_overwrite(
      filepath: str, overwrite_chooser: OverwriteChooser, position: Optional[int] = None
) -> Tuple[int, str]:
  """Resolves how to handle an existing file path.

  ``overwrite_chooser`` is presented to the user to let them choose the
  overwrite mode. The ``overwrite_chooser`` instance must support overwrite
  modes specified in `OverwriteModes`. See `OverwriteModes` for information
  about the possible values and their meanings.

  If ``filepath`` does not exist, there is no need to perform any action, hence
  `OverwriteModes.DO_NOTHING` is returned.

  If the chosen overwrite mode is `OverwriteModes.RENAME_NEW` or
  `OverwriteModes.RENAME_EXISTING`, the new or existing file path is made
  unique, respectively. A unique substring is appended to the end of the file
  name. The position of the substring can be customized via ``position`` (for
  example, to place the substring before the file extension).

  Returns:
    A tuple of (chosen overwrite mode, file path).

    The overwrite mode is returned by ``overwrite_chooser``, which the caller
    of this function can further use (especially `OverwriteModes.SKIP` or
    `OverwriteModes.CANCEL`).

    The returned file path is identical to the one passed as the argument,
    unless the `OverwriteModes.RENAME_NEW` mode is chosen, in which case a
    modified file path is returned.
  """
  if os.path.exists(filepath):
    overwrite_chooser.choose(filepath=os.path.abspath(filepath))

    if overwrite_chooser.overwrite_mode in (
         OverwriteModes.RENAME_NEW, OverwriteModes.RENAME_EXISTING):
      processed_filepath = pgpath.uniquify_filepath(filepath, position)
      if overwrite_chooser.overwrite_mode == OverwriteModes.RENAME_NEW:
        filepath = processed_filepath
      else:
        os.rename(filepath, processed_filepath)

    return overwrite_chooser.overwrite_mode, filepath
  else:
    return OverwriteModes.DO_NOTHING, filepath


class OverwriteModes:
  """Overwrite modes used by ``handle_overwrite`` and recommended to be handled
  by custom ``OverwriteChooser`` subclasses.
  """
  REPLACE = 0
  """Indicates to overwrite an existing file with new contents."""

  SKIP = 1
  """Indicates to avoid overwriting an existing file."""

  RENAME_NEW = 2
  """Indicates to rename the file path whose contents are about to be written
  to the file system.
  """

  RENAME_EXISTING = 3
  """Indicates to rename the existing file path in the file system."""

  CANCEL = 4
  """This value should be used if the user terminated the overwrite chooser,
  for example by closing a dialog if an interactive overwrite chooser is used.
  """

  DO_NOTHING = 5
  """This value should if there is no need to display an overwrite chooser, i.e.
  if a file path does not exist and no action should be taken.
  """

  OVERWRITE_MODES = REPLACE, SKIP, RENAME_NEW, RENAME_EXISTING, CANCEL, DO_NOTHING
