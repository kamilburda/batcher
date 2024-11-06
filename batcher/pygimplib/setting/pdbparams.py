"""Class to generate GIMP PDB parameters out of settings and parse GIMP
procedure arguments to assign them as values to settings.
"""

from collections.abc import Iterable
from typing import Any, Dict, List, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from . import group as group_
from . import settings as settings_

__all__ = [
  'create_params',
  'list_param_values',
]


def create_params(
      *settings_or_groups: Union[settings_.Setting, group_.Group],
      recursive=False,
) -> List[Dict[str, Any]]:
  """Returns a list of GIMP PDB parameters from the specified `setting.Setting`
  and `setting.Group` instances.

  A PDB parameter is represented as a dictionary of ``(parameter name, value)``
  pairs.

  If ``recursive`` is ``True``, groups are traversed recursively. Otherwise,
  only top-level settings within each group from ``settings_or_groups`` are
  considered.
  """
  settings = _list_settings(settings_or_groups, recursive=recursive)
  
  params = []
  
  for setting in settings:
    if setting.can_be_registered_to_pdb():
      params.extend(setting.get_pdb_param())

  return params


def list_param_values(
      settings_or_groups: Iterable[Union[settings_.Setting, group_.Group]],
      ignore_run_mode: bool = True,
      recursive=False,
) -> List:
  """Returns a list of setting values (`setting.Setting.value` properties)
  registrable to PDB.

  A setting can be registered if `setting.Setting.can_be_registered_to_pdb()`
  returns ``True``.
  
  If ``ignore_run_mode`` is ``True``, setting(s) named ``'run_mode'`` are
  ignored. This makes it possible to call PDB functions with the setting
  values without manually omitting the ``'run_mode'`` setting.

  If ``recursive`` is ``True``, groups are traversed recursively. Otherwise,
  only top-level settings within each group from ``settings_or_groups`` are
  considered.
  """
  settings = _list_settings(settings_or_groups, recursive=recursive)

  if ignore_run_mode:
    for i, setting in enumerate(settings):
      if isinstance(setting, settings_.EnumSetting) and setting.enum_type == Gimp.RunMode:
        del settings[i]
        break
  
  return [setting.value_for_pdb for setting in settings if setting.can_be_registered_to_pdb()]


def _list_settings(settings_or_groups, recursive=False):
  settings = []
  for setting_or_group in settings_or_groups:
    if isinstance(setting_or_group, settings_.Setting):
      settings.append(setting_or_group)
    elif isinstance(setting_or_group, group_.Group):
      if recursive:
        settings.extend(setting_or_group.walk())
      else:
        settings.extend(
          iter(setting for setting in setting_or_group if isinstance(setting, settings_.Setting)))
    else:
      raise TypeError(
        f'{setting_or_group} is not an instance of type {settings_.Setting} or {group_.Group}')
  
  return settings
