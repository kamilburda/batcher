"""Creating settings from PDB procedures."""

import inspect
from typing import List, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib.pypdb import pdb

from src import placeholders
from src.path import uniquify


def get_setting_data_from_pdb_procedure(
      pdb_procedure_or_name: Union[pg.pypdb.PDBProcedure, str],
) -> Tuple[pg.pypdb.PDBProcedure, str, List]:
  """Given the input, returns a PDB procedure, its name and arguments.

  The returned arguments are a list of dictionaries. From each dictionary,
  `pygimplib.setting.Setting` instances can be created.

  If the procedure contains arguments with the same name, each subsequent
  identical name is made unique (since arguments are internally represented as
  `pygimplib.setting.Setting` instances, whose names must be unique within a
  `pygimplib.setting.Group` instance).
  """

  if isinstance(pdb_procedure_or_name, str):
    pdb_procedure = pdb[pdb_procedure_or_name]
    pdb_procedure_name = pdb_procedure_or_name
  else:
    pdb_procedure = pdb_procedure_or_name
    pdb_procedure_name = pdb_procedure.name

  pdb_procedure_argument_names = []
  arguments = []

  for proc_arg in pdb_procedure.arguments:
    retval = pg.setting.get_setting_type_and_kwargs(proc_arg.value_type, proc_arg, pdb_procedure)

    if retval is not None:
      setting_type, setting_type_init_kwargs = retval

      placeholder_type_name = placeholders.get_placeholder_type_name_from_pdb_type(
        proc_arg.value_type, proc_arg)

      if placeholder_type_name is not None:
        setting_type_init_kwargs = _remove_invalid_init_arguments_for_placeholder_settings(
          setting_type, placeholder_type_name, setting_type_init_kwargs)
        setting_type = pg.setting.SETTING_TYPES[placeholder_type_name]
    else:
      setting_type = placeholders.PlaceholderUnsupportedParameterSetting
      setting_type_init_kwargs = {}
      placeholder_type_name = pg.setting.SETTING_TYPES[setting_type]

    unique_pdb_param_name = uniquify.uniquify_string(
      proc_arg.name,
      pdb_procedure_argument_names,
      generator=_generate_unique_pdb_procedure_argument_name())

    pdb_procedure_argument_names.append(unique_pdb_param_name)

    argument_dict = {
      'type': setting_type,
      'name': unique_pdb_param_name,
      'display_name': proc_arg.blurb,
      **setting_type_init_kwargs,
    }

    if hasattr(proc_arg, 'default_value') and proc_arg.default_value is not None:
      if placeholder_type_name is None:
        argument_dict['default_value'] = _get_arg_default_value(pdb_procedure_name, proc_arg)
      elif setting_type == placeholders.PlaceholderUnsupportedParameterSetting:
        argument_dict['default_param_value'] = proc_arg.default_value

    if setting_type == pg.setting.BoolSetting:
      argument_dict['gui_type'] = 'check_button'

    if inspect.isclass(setting_type) and issubclass(setting_type, pg.setting.NumericSetting):
      if hasattr(proc_arg, 'minimum'):
        argument_dict['min_value'] = proc_arg.minimum
      if hasattr(proc_arg, 'maximum'):
        argument_dict['max_value'] = proc_arg.maximum

    if proc_arg.value_type == Gimp.RunMode.__gtype__:
      argument_dict['default_value'] = Gimp.RunMode.NONINTERACTIVE

    arguments.append(argument_dict)

  return pdb_procedure, pdb_procedure_name, arguments


def _remove_invalid_init_arguments_for_placeholder_settings(
      setting_type, placeholder_type_name, setting_type_init_kwargs):
  if isinstance(setting_type, str):
    setting_type = pg.SETTING_TYPES[setting_type]

  placeholder_type = pg.SETTING_TYPES[placeholder_type_name]

  setting_init_params = inspect.signature(setting_type.__init__).parameters
  placeholder_setting_init_params = inspect.signature(placeholder_type.__init__).parameters

  return {
    key: value for key, value in setting_type_init_kwargs.items()
    if key in setting_init_params or key in placeholder_setting_init_params
  }


def _generate_unique_pdb_procedure_argument_name():
  i = 2
  while True:
    yield f'-{i}'
    i += 1


def _get_arg_default_value(pdb_procedure_name, proc_arg):
  if pdb_procedure_name in _PDB_PROCEDURES_AND_CUSTOM_DEFAULT_ARGUMENT_VALUES:
    proc_args_with_custom_defaults = (
      _PDB_PROCEDURES_AND_CUSTOM_DEFAULT_ARGUMENT_VALUES[pdb_procedure_name])
    if proc_arg.name in proc_args_with_custom_defaults:
      return proc_args_with_custom_defaults[proc_arg.name]

  return proc_arg.default_value


_PDB_PROCEDURES_AND_CUSTOM_DEFAULT_ARGUMENT_VALUES = {
  'file-pdf-export': {'ignore-hidden': False, 'layers-as-pages': True, 'reverse-order': True},
  'plug-in-lighting': {'new-image': False},
  'plug-in-map-object': {'new-image': False, 'new-layer': False},
  'plug-in-smooth-palette': {'show-image': False},
  'script-fu-add-bevel': {'toggle': False},
  'script-fu-circuit': {'toggle-3': False},
  'script-fu-fuzzy-border': {'toggle-3': False, 'toggle-4': False},
  'script-fu-old-photo': {'toggle-4': False},
  'script-fu-round-corners': {'toggle-3': False},
  'script-fu-slide': {'toggle': False},
  'script-fu-spinning-globe': {'toggle-3': False},
}
