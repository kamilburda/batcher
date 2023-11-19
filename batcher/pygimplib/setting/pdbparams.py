"""Class to generate GIMP PDB parameters out of settings and parse GIMP
procedure arguments to assign them as values to settings.
"""

from collections.abc import Iterable
from typing import Any, Dict, Generator, List, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from . import group as group_
from . import settings as settings_

__all__ = [
  'create_params',
  'iter_args',
  'list_param_values',
]


def create_params(
      *settings_or_groups: Union[settings_.Setting, group_.Group],
) -> List[Dict[str, Any]]:
  """Returns a list of GIMP PDB parameters from the specified `setting.Setting`
  and `setting.Group` instances.

  A PDB parameter is represented as a dictionary of ``(parameter name, value)``
  pairs.
  """
  settings = _list_settings(settings_or_groups)
  
  params = []
  
  for setting in settings:
    if setting.can_be_registered_to_pdb():
      params.extend(setting.get_pdb_param())
  
  return params


def iter_args(
      args: Union[List, Tuple], settings: Union[List, Tuple]
) -> Generator[Any, None, None]:
  """Iterates over arguments passed to a GIMP PDB procedure, skipping redundant
  arguments.

  ``settings`` is a list of `setting.Setting` instances that may modify the
  iteration. For example, if an argument is matched by a setting of type
  `setting.ArraySetting`, the array argument causes the preceding argument to
  be skipped. The preceding argument is the array length and does not need to
  exist as a separate setting because the length can be obtained from the
  array itself in Python.

  If there are more settings than non-skipped arguments, the remaining settings
  will be ignored.
  """
  indexes_of_array_length_settings = set()
  index = 0
  
  for setting in settings:
    if isinstance(setting, settings_.ArraySetting):
      index += 1
      indexes_of_array_length_settings.add(index - 1)
    
    index += 1
  
  for arg_index in range(min(len(args), index)):
    if arg_index not in indexes_of_array_length_settings:
      yield args[arg_index]


def list_param_values(
      settings_or_groups: Iterable[settings_.Setting, group_.Group], ignore_run_mode: bool = True,
) -> List:
  """Returns a list of setting values (`setting.Setting.value` properties)
  registrable to PDB.

  A setting can be registered if `setting.Setting.can_be_registered_to_pdb()`
  returns ``True``.
  
  If ``ignore_run_mode`` is ``True``, setting(s) named ``'run_mode'`` are
  ignored. This makes it possible to call PDB functions with the setting
  values without manually omitting the ``'run_mode'`` setting.
  """
  settings = _list_settings(settings_or_groups)
  
  if ignore_run_mode:
    for i, setting in enumerate(settings):
      if isinstance(setting, settings_.EnumSetting) and setting.enum_type == Gimp.RunMode:
        del settings[i]
        break
  
  return [setting.value_for_pdb for setting in settings if setting.can_be_registered_to_pdb()]


def _list_settings(settings_or_groups):
  settings = []
  for setting_or_group in settings_or_groups:
    if isinstance(setting_or_group, settings_.Setting):
      settings.append(setting_or_group)
    elif isinstance(setting_or_group, group_.Group):
      settings.extend(setting_or_group.walk())
    else:
      raise TypeError(
        f'{setting_or_group} is not an instance of type {settings_.Setting} or {group_.Group}')
  
  return settings
