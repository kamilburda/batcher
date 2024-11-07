"""Class to generate GIMP PDB parameters out of settings and parse GIMP
procedure arguments to assign them as values to settings.
"""
from typing import List, Union

from . import group as group_
from . import settings as settings_

__all__ = [
  'create_params',
]


def create_params(
      *settings_or_groups: Union[settings_.Setting, group_.Group],
      recursive=False,
) -> List[List]:
  """Returns a list of GIMP PDB parameters from the specified `setting.Setting`
  and `setting.Group` instances.

  A PDB parameter is represented as a list of values. See the ``arguments``
  parameter in `pygimplib.procedure.register_procedure()` for more information.

  If ``recursive`` is ``True``, groups are traversed recursively. Otherwise,
  only top-level settings within each group from ``settings_or_groups`` are
  considered.
  """
  params = []
  
  for setting in _list_settings(settings_or_groups, recursive=recursive):
    param = setting.get_pdb_param()
    if param is not None:
      params.append(param)

  return params


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
