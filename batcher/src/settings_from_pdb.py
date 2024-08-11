"""Creating settings from PDB procedures."""

import inspect
from typing import List, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import pygimplib as pg
from pygimplib.pypdb import pdb

from src import placeholders
from src.path import uniquify


def get_setting_dict_from_pdb_procedure(
      pdb_procedure_or_name: Union[Gimp.Procedure, str]) -> Tuple[Gimp.Procedure, str, List]:
  """Given the input, returns a GIMP PDB procedure, its name and arguments.

  The returned arguments are a list of dictionaries. From each dictionary,
  `pygimplib.setting.Setting` instances can be created.

  If the procedure contains arguments with the same name, each subsequent
  identical name is made unique (since arguments are internally represented as
  `pygimplib.setting.Setting` instances, whose names must be unique within a
  `pygimplib.setting.Group` instance).
  """

  if isinstance(pdb_procedure_or_name, str):
    pdb_procedure = pdb[pdb_procedure_or_name].proc
    pdb_procedure_name = pdb_procedure_or_name
  else:
    pdb_procedure = pdb_procedure_or_name
    pdb_procedure_name = pdb_procedure.get_name()

  pdb_procedure_argument_names = []
  arguments = []

  for proc_arg in pdb_procedure.get_arguments():
    retval = pg.setting.get_setting_type_from_gtype(proc_arg.value_type, proc_arg)

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
      'display_name': proc_arg.name,
      **setting_type_init_kwargs,
    }

    if hasattr(proc_arg, 'default_value') and proc_arg.default_value is not None:
      if placeholder_type_name is None:
        argument_dict['default_value'] = _get_arg_default_value(pdb_procedure_name, proc_arg)
      elif setting_type == placeholders.PlaceholderUnsupportedParameterSetting:
        argument_dict['default_param_value'] = proc_arg.default_value

    if setting_type == pg.setting.BoolSetting:
      argument_dict['gui_type'] = 'check_button_no_text'

    if inspect.isclass(setting_type) and issubclass(setting_type, pg.setting.NumericSetting):
      if hasattr(proc_arg, 'minimum'):
        argument_dict['min_value'] = proc_arg.minimum
      if hasattr(proc_arg, 'maximum'):
        argument_dict['max_value'] = proc_arg.maximum

    if proc_arg.value_type == Gimp.RunMode.__gtype__:
      argument_dict['default_value'] = Gimp.RunMode.NONINTERACTIVE

    arguments.append(argument_dict)

  _set_up_array_arguments(arguments)

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

  if proc_arg.value_type not in [GObject.TYPE_CHAR, GObject.TYPE_UCHAR]:
    return proc_arg.default_value
  else:
    # For gchar and guchar types, the default value may be a string, while the
    # value type is expected to be an int. We convert the value to int if
    # possible to avoid errors (e.g. in `pygimplib.setting.NumericSetting`
    # validation).
    if isinstance(proc_arg.default_value, str):
      try:
        return ord(proc_arg.default_value)
      except Exception:
        return proc_arg.default_value
    else:
      return proc_arg.default_value


def _set_up_array_arguments(arguments_list):
  array_length_argument_indexes = []

  for i, argument_dict in enumerate(arguments_list):
    setting_type = pg.setting.process_setting_type(argument_dict['type'])

    if issubclass(setting_type, (pg.setting.ArraySetting, placeholders.PlaceholderArraySetting)):
      array_element_type = pg.setting.process_setting_type(argument_dict['element_type'])
    else:
      array_element_type = None

    if (issubclass(setting_type, pg.setting.ArraySetting)
        and i > 0
        and array_element_type != pg.setting.StringSetting):
      _set_array_setting_attributes_based_on_length_attribute(
        argument_dict, arguments_list[i - 1], array_element_type)

    if (issubclass(setting_type, (pg.setting.ArraySetting, placeholders.PlaceholderArraySetting))
        and i > 0
        and array_element_type != pg.setting.StringSetting):
      array_length_argument_indexes.append(i - 1)

  _remove_array_length_parameters(arguments_list, array_length_argument_indexes)


def _set_array_setting_attributes_based_on_length_attribute(
      array_dict, array_length_dict, element_type):
  min_array_size = array_length_dict.get('min_value', 0)

  array_dict['min_size'] = min_array_size
  array_dict['max_size'] = array_length_dict.get('max_value')
  array_dict['default_value'] = tuple([element_type.get_default_default_value()] * min_array_size)


def _remove_array_length_parameters(arguments_list, array_length_argument_indexes):
  for index in reversed(array_length_argument_indexes):
    del arguments_list[index]


_PDB_PROCEDURES_AND_CUSTOM_DEFAULT_ARGUMENT_VALUES = {
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
