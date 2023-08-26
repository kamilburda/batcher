from typing import Callable, Dict, List, Optional, Tuple, Union

import collections.abc
import sys

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject


_PROCEDURE_FUNCTIONS = []
_PROCEDURE_NAMES_AND_DATA = {}
_PLUGIN_PROPERTIES = {}
_USE_LOCALE = False


def register_procedure(
      procedure: Callable,
      arguments: Optional[List[Union[Dict, str]]] = None,
      return_values: Optional[List[Union[Dict, str]]] = None,
      menu_label: Optional[str] = None,
      menu_path: Optional[Union[str, List[str]]] = None,
      image_types: Optional[str] = None,
      documentation: Optional[Union[Tuple[str, str], Tuple[str, str, str]]] = None,
      attribution: Optional[Tuple[str, str, str]] = None,
      auxiliary_arguments: Optional[List[Union[Dict, str]]] = None,
      argument_sync: Optional[Gimp.ArgumentSync] = None,
      run_data: Optional[List] = None,
      additional_init: Optional[Callable] = None,
):
  _PROCEDURE_FUNCTIONS.append(procedure)

  proc_name = procedure.__name__.replace('_', '-')
  _PROCEDURE_NAMES_AND_DATA[proc_name] = {}

  proc_dict = _PROCEDURE_NAMES_AND_DATA[proc_name]
  proc_dict['arguments'] = _parse_and_check_parameters(arguments)
  proc_dict['return_values'] = _parse_and_check_parameters(return_values)
  proc_dict['menu_label'] = menu_label
  proc_dict['menu_path'] = menu_path
  proc_dict['image_types'] = image_types
  proc_dict['documentation'] = documentation
  proc_dict['attribution'] = attribution
  proc_dict['auxiliary_arguments'] = _parse_and_check_parameters(auxiliary_arguments)
  proc_dict['argument_sync'] = argument_sync
  proc_dict['run_data'] = run_data
  proc_dict['additional_init'] = additional_init


def _parse_and_check_parameters(parameters):
  if parameters is None:
    return None

  if not isinstance(parameters, collections.abc.Iterable) or isinstance(parameters, str):
    raise TypeError('Arguments, return values and auxiliary arguments must be a list-like iterable')

  processed_parameters = {}

  for param in parameters:
    if isinstance(param, dict):
      if 'name' not in param:
        raise ValueError(
          ('Dictionary describing a parameter (argument, return value or auxiliary argument)'
           ' must also contain the "name" key representing the parameter name as registered'
           ' in GIMP'))

      name = param.pop('name').replace('_', '-')
      if name not in _PLUGIN_PROPERTIES:
        _PLUGIN_PROPERTIES[name] = GObject.Property(**param)

      processed_parameters[name] = _PLUGIN_PROPERTIES[name]
    elif isinstance(param, str):
      name = param.replace('_', '-')

      if name not in _PLUGIN_PROPERTIES:
        raise ValueError(
          ('You can only specify parameter name if a dictionary containing the name'
           ' was already specified before'))

      processed_parameters[name] = _PLUGIN_PROPERTIES[name]
    else:
      raise TypeError('Parameters must only contain dictionaries or strings')

  return processed_parameters


def set_use_locale(enabled):
  """If `True`, enables plug-in localization, `False` otherwise.

  You do not need to call this function explicitly as pygimplib will call it
  automatically. If the `locale` directory under the main plug-in directory
  exists, localization will be enabled.

  You can call this function explicitly to enable localization if you use a
  custom localization approach that does not rely on the presence of the
  `locale` subdirectory.
  """
  global _USE_LOCALE
  _USE_LOCALE = bool(enabled)


def main():
  # `GObject.property` objects must be specified when defining a `Gimp.PlugIn`
  # subclass, they cannot be added later as this will result in errors
  # (probably because the parent class of `Gimp.PlugIn`, `GObject.GObject`, has
  # a metaclass that performs property initialization upon class definition, not
  # object instantiation).
  # Therefore, the custom `Gimp.PlugIn` subclass must be created dynamically
  # where it is possible to pass a dictionary of class attributes, including
  # `GObject.property` objects.

  # noinspection PyPep8Naming
  PyPlugIn = _create_plugin_class()

  # noinspection PyUnresolvedReferences
  Gimp.main(PyPlugIn.__gtype__, sys.argv)


def _create_plugin_class(class_name='PyPlugIn', bases=(Gimp.PlugIn,)):
  class_dict = {}

  for name, gobject_property in _PLUGIN_PROPERTIES.items():
    class_dict[name.replace('-', '_')] = gobject_property

  class_dict['do_query_procedures'] = _do_query_procedures
  class_dict['do_create_procedure'] = _do_create_procedure

  if not _USE_LOCALE:
    class_dict['do_set_i18n'] = _disable_locale

  return type(
    class_name,
    bases,
    class_dict,
  )


def _do_query_procedures(plugin_instance):
  return list(_PROCEDURE_NAMES_AND_DATA)


def _do_create_procedure(plugin_instance, proc_name):
  if proc_name in _PROCEDURE_NAMES_AND_DATA:
    proc_dict = _PROCEDURE_NAMES_AND_DATA[proc_name]
  else:
    return None

  procedure = Gimp.Procedure.new(
    plugin_instance,
    proc_name,
    Gimp.PDBProcType.PLUGIN,
    _run,
    proc_dict['run_data'])

  if proc_dict['arguments'] is not None:
    for name in proc_dict['arguments']:
      procedure.add_argument_from_property(plugin_instance, name)

  if proc_dict['return_values'] is not None:
    for name in proc_dict['return_values']:
      procedure.add_return_value_from_property(plugin_instance, name)

  if proc_dict['auxiliary_arguments'] is not None:
    for name in proc_dict['auxiliary_arguments']:
      procedure.add_aux_argument_from_property(plugin_instance, name)

  if proc_dict['menu_label'] is not None:
    procedure.set_menu_label(proc_dict['menu_label'])

  menu_path = proc_dict['menu_path']
  if menu_path is not None:
    if isinstance(menu_path, str):
      procedure.add_menu_path(menu_path)
    elif isinstance(menu_path, collections.abc.Iterable):
      for path in menu_path:
        procedure.add_menu_path(path)
    else:
      raise TypeError(f'menu path "{menu_path}" must be a string or an iterable')

  if proc_dict['image_types'] is not None:
    procedure.set_image_types(proc_dict['image_types'])

  if proc_dict['documentation'] is not None:
    if len(proc_dict['documentation']) == 2:
      procedure.set_documentation(*proc_dict['documentation'], proc_name)
    elif len(proc_dict['documentation']) == 3:
      procedure.set_documentation(*proc_dict['documentation'])
    else:
      raise ValueError('documentation must be a tuple of 2 or 3 elements')

  if proc_dict['attribution'] is not None:
    procedure.set_attribution(*proc_dict['attribution'])

  if proc_dict['argument_sync'] is not None:
    procedure.set_argument_sync(proc_dict['argument_sync'])

  if proc_dict['additional_init'] is not None:
    proc_dict['additional_init'](procedure)

  return procedure


def _disable_locale(plugin_instance, name):
  return False


def _run(*args):
  raise NotImplementedError
