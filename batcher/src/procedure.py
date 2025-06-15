"""Wrappers to simplify registering and running functions as GIMP procedures.
"""

from collections.abc import Iterable
import functools
import inspect
import sys
from typing import Callable, List, Optional, Tuple, Type, Union

import gi

gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib

from src import initnotifier


_PROCEDURE_NAMES_AND_DATA = {}
_USE_LOCALE = False
_INIT_PROCEDURES_FUNC = None
_QUIT_FUNC = None


def register_procedure(
      procedure: Callable,
      procedure_type: Type[Gimp.Procedure] = Gimp.ImageProcedure,
      arguments: Optional[Union[Iterable[List], Callable[[], Iterable[List]]]] = None,
      return_values: Optional[Union[Iterable[List], Callable[[], Iterable[List]]]] = None,
      menu_label: Optional[str] = None,
      menu_path: Optional[Union[str, Iterable[str]]] = None,
      image_types: Optional[str] = None,
      sensitivity_mask: Optional[Gimp.ProcedureSensitivityMask] = None,
      documentation: Optional[Union[Tuple[str, str], Tuple[str, str, str]]] = None,
      attribution: Optional[Tuple[str, str, str]] = None,
      auxiliary_arguments: Optional[Union[Iterable[List], Callable[[], Iterable[List]]]] = None,
      run_data: Optional[Iterable] = None,
      init_ui: bool = True,
      init_gegl: bool = True,
      pdb_procedure_type: Gimp.PDBProcType = Gimp.PDBProcType.PLUGIN,
      additional_init: Optional[Callable] = None,
      export_metadata: bool = False,
      interpreter_name: Optional[str] = None,
      extract_func: Optional[Callable] = None,
      extract_data: Optional[Iterable] = None,
):
  # noinspection PyUnresolvedReferences
  """Registers a function as a GIMP procedure.

  The installed procedure can then be accessed via the GIMP procedural
  database (PDB) and, optionally, from the GIMP user interface.

  The function name is used as the procedure name as found in the GIMP PDB,
  with ``_`` characters replaced with ``-``.

  This is a wrapper for the `Gimp.PlugIn` class to simplify the registration of
  plug-ins and their procedures.

  The description of parameters is provided below. For more detailed information
  about the parameters, consult the `Gimp.Procedure` class (namely functions
  starting with ``add_`` or ``set_``).

  Args:
    procedure: The function to register.
    procedure_type:
      Type of procedure to create. Can be `Gimp.Procedure` or any of its
      subclasses, depending on the intended usage of the GIMP procedure to be
      registered. If ``procedure_type`` is `Gimp.ImageProcedure`, several PDB
      arguments will be pre-filled (see the documentation for
      `Gimp.ImageProcedure` for more information).
    arguments: List of arguments (procedure parameters), or a function returning
      a list of arguments.
      Each argument must be a list containing the following elements in this
      order:
      * argument type. The type corresponds to one of the
        ``Gimp.Procedure.add_*_argument`` functions (e.g. the ``'boolean'``
        type corresponds to the `Gimp.Procedure.add_boolean_argument` function).
      * positional arguments according to the signature of the
        ``Gimp.Procedure.add_*_argument`` function corresponding to the
        argument type.

      Underscores in argument names (``_``) are automatically replaced with
      hyphens (``-``).

      If your argument list contains arguments of type e.g. `Gegl.Color`, you
      will have to pass a function taking no parameters, for example:
      >>> def get_arguments():
      >>>   _default_foreground_color = Gegl.Color.new('black')
      >>>   _default_foreground_color.set_rgba(0.65, 0.6, 0.3, 1.0)
      >>>
      >>>   _default_background_color = Gegl.Color.new('black')
      >>>   _default_background_color.set_rgba(0.1, 0.4, 0.15, 1.0)
      >>>
      >>>   return [
      >>>     [
      >>>       'color',
      >>>       'foreground-color',
      >>>       'Foreground color',
      >>>       'Foreground color',
      >>>       True,
      >>>       _default_foreground_color,
      >>>       GObject.ParamFlags.READWRITE,
      >>>     ],
      >>>     [
      >>>       'color',
      >>>       'background-color',
      >>>       'Background color',
      >>>       'Background color',
      >>>       True,
      >>>       _default_background_color,
      >>>       GObject.ParamFlags.READWRITE,
      >>>     ],
      >>>   ]

      For documentation on the ``Gimp.Procedure.add_*_argument`` functions, see:
      https://lazka.github.io/pgi-docs/#Gimp-3.0/classes/Procedure.html
    return_values: List of return values, or a function returning a list of
      return values.
      See ``arguments`` for more information about the contents and format of
      the list.

      The argument type (first list element of a return value) corresponds to
      one of the ``Gimp.Procedure.add_*_return_value`` functions (e.g. the
      ``'boolean'`` type corresponds to the
      `Gimp.Procedure.add_boolean_return_value` function).

      For documentation on the ``Gimp.Procedure.add_*_return_value`` functions,
      see: https://lazka.github.io/pgi-docs/#Gimp-3.0/classes/Procedure.html
    menu_label: Name of the menu entry in the GIMP user interface.
    menu_path: Path of the menu entry in the GIMP user interface.
      This can be a single string or a list of strings if you want your
      procedure to be accessible from mutliple menu paths in GIMP.
    image_types: Image types to which the procedure applies.
    sensitivity_mask:
      `Gimp.ProcedureSensitivityMask` determining when the menu entry will be
      accessible (sensitive).
    documentation: Procedure documentation.
      This is either a tuple of (short description, help) strings or
      (short description, help, help ID) strings.
      The help is a detailed description of the procedure.
      The help ID is set automatically if omitted, it is not required to
      specify it explicitly.
    attribution: Plug-in authors, copyright notice and date.
      This is a tuple of (authors, copyright notice, date) strings.
    auxiliary_arguments: List of auxiliary arguments, or a function returning
      a list of auxiliary arguments.
      See ``arguments`` for more information about the contentsn and format of
      the list.

      The argument type (first list element of an auxiliary argument)
      corresponds to one of the ``Gimp.Procedure.add_*_aux_argument``
      functions (e.g. the ``'boolean'`` type corresponds to the
      `Gimp.Procedure.add_boolean_aux_argument` function).

      For documentation on the ``Gimp.Procedure.add_*_aux_argument`` functions,
      see: https://lazka.github.io/pgi-docs/#Gimp-3.0/classes/Procedure.html
    run_data: Custom parameters passed to ``procedure`` as its last argument.
      ``procedure`` should only contain the run data as its last argument if
      ``run_data`` is not ``None``.
    init_ui: If ``True``, user interface is initialized via `GimpUi.init`.
      See `GimpUi.init` for more information.
    init_gegl:
      If ``True``, GEGL (library providing layer effects) is initialized via
      `Gegl.init`. See `Gegl.init` for more information.
    pdb_procedure_type: One of the values of the `Gimp.PDBProcType` enum.
    additional_init: Function allowing customization of procedure registration.
      The function accepts a single argument - a ``Gimp.Procedure`` instance
      corresponding to the registered procedure.
      You can use this function to call registration-related functions not
      available via this function, e.g. `Gimp.Procedure.set_argument_sync`
      on individual procedure arguments.
    export_metadata: Indicates whether GIMP should handle metadata exporting.
      Applicable only if ``procedure_type`` is `Gimp.ExportProcedure` and
      otherwise ignored.
      See the documentation for `Gimp.ExportProcedure` for more information.
    interpreter_name: Name of the batch interpreter to be registered.
      Applicable only if ``procedure_type`` is `Gimp.BatchProcedure` and
      otherwise ignored.
      See the documentation for `Gimp.BatchProcedure` for more information.
    extract_func: See `Gimp.VectorLoadProcedure.new()` for more information.
      Applicable only if ``procedure_type`` is `Gimp.VectorLoadProcedure` and
      otherwise ignored.
    extract_data: See `Gimp.VectorLoadProcedure.new()` for more information.
      Applicable only if ``procedure_type`` is `Gimp.VectorLoadProcedure` and
      otherwise ignored.

  Example:

    >>> register_procedure(
    ...   plug_in_awesome_filter,
    ...   arguments=[
    ...     [
    ...        'enum',
    ...        'run-mode',
    ...        'Run mode',
    ...        'The run mode',
    ...        Gimp.RunMode,
    ...        Gimp.RunMode.NONINTERACTIVE,
    ...        GObject.ParamFlags.READWRITE,
    ...     ],
    ...     [
    ...        'string',
    ...        'output-directory',
    ...        'Output directory',
    ...        'Output _directory',
    ...        'some_dir',
    ...        GObject.ParamFlags.READWRITE,
    ...     ],
    ...   ],
    ...   return_values=[
    ...     [
    ...        'int',
    ...        'num-layers',
    ...        'Number of processed layers',
    ...        'Number of processed layers',
    ...        0,
    ...        GObject.ParamFlags.READWRITE,
    ...     ],
    ...   ],
    ...   menu_label='Awesome Filter',
    ...   menu_path='<Image>/Filters',
    ...   image_types='*',
    ...   documentation=('An awesome filter.',
    ...                  'Applies a mind-blowing filter to each layer.'),
    ...   attribution=('Jane Doe, John Doe', 'Jane Doe, John Doe', '2024'),
    ... )
  """
  global _INIT_PROCEDURES_FUNC
  global _QUIT_FUNC

  proc_name = procedure.__name__.replace('_', '-')

  if proc_name in _PROCEDURE_NAMES_AND_DATA:
    raise ValueError(f'procedure "{proc_name}" is already registered')

  _PROCEDURE_NAMES_AND_DATA[proc_name] = {}

  proc_dict = _PROCEDURE_NAMES_AND_DATA[proc_name]
  proc_dict['procedure'] = procedure
  proc_dict['procedure_type'] = procedure_type
  proc_dict['arguments'] = arguments
  proc_dict['return_values'] = return_values
  proc_dict['menu_label'] = menu_label
  proc_dict['menu_path'] = menu_path
  proc_dict['image_types'] = image_types
  proc_dict['sensitivity_mask'] = sensitivity_mask
  proc_dict['documentation'] = documentation
  proc_dict['attribution'] = attribution
  proc_dict['auxiliary_arguments'] = auxiliary_arguments
  proc_dict['run_data'] = run_data
  proc_dict['init_ui'] = init_ui
  proc_dict['init_gegl'] = init_gegl
  proc_dict['pdb_procedure_type'] = pdb_procedure_type
  proc_dict['additional_init'] = additional_init
  proc_dict['export_metadata'] = export_metadata
  proc_dict['interpreter_name'] = interpreter_name
  proc_dict['extract_func'] = extract_func
  proc_dict['extract_data'] = extract_data


def _parse_and_check_parameters(parameters):
  if parameters is None:
    return None

  if callable(parameters):
    processed_parameters = parameters()
  else:
    processed_parameters = parameters

  if not isinstance(processed_parameters, Iterable):
    raise TypeError('Arguments and return values must be specified as a list-like iterable')

  parsed_parameters = {}

  for param in processed_parameters:
    processed_param = list(param)

    if isinstance(processed_param, list):
      if len(processed_param) < 2:
        raise ValueError(
          ('The list describing an argument or a return value must contain'
           ' at least two elements - type and name'))

      if not isinstance(processed_param[0], str):
        raise TypeError('The type of the argument or return value must be a string')

      if not isinstance(processed_param[1], str):
        raise TypeError('The name of the argument or return value must be a string')

      name = processed_param.pop(1).replace('_', '-')

      if name in parsed_parameters:
        raise ValueError(f'Argument or return value named "{name}" was already specified')

      parsed_parameters[name] = processed_param
    else:
      raise TypeError('Only lists are allowed when specifying an argument or return value')

  return parsed_parameters


def set_use_locale(enabled):
  """If ``True``, enables plug-in localization, ``False`` otherwise.

  You can call this function explicitly to enable localization if you use a
  custom localization approach that does not rely on the presence of the
  ``locale`` subdirectory.
  """
  global _USE_LOCALE
  _USE_LOCALE = bool(enabled)


def set_init_procedures_func(func: Optional[Callable] = None):
  """Sets a function returning a list of procedure names, to be called during
  plug-in initialization.

  Passing ``None`` unsets the function.

  This function's behavior is identical to `Gimp.PlugIn.do_init_procedures`.
  See `Gimp.PlugIn` for more information.
  """
  global _INIT_PROCEDURES_FUNC
  _INIT_PROCEDURES_FUNC = func


def set_quit_func(func: Optional[Callable] = None):
  """Sets a function to be called before a plug-in terminates.

  Passing ``None`` unsets the function.

  See `Gimp.PlugIn` for more information.
  """
  global _QUIT_FUNC
  _QUIT_FUNC = func


def main():
  """Initializes and runs the plug-in.

  Call this function at the very end of your main plug-in script.
  """
  # noinspection PyPep8Naming
  PyPlugIn = _create_plugin_class()

  # noinspection PyUnresolvedReferences
  Gimp.main(PyPlugIn.__gtype__, sys.argv)


def _create_plugin_class(class_name='PyPlugIn', bases=(Gimp.PlugIn,)):
  class_dict = {}

  class_dict['do_query_procedures'] = _do_query_procedures
  class_dict['do_create_procedure'] = _do_create_procedure

  if not _USE_LOCALE:
    class_dict['do_set_i18n'] = _disable_locale

  if _INIT_PROCEDURES_FUNC:
    class_dict['do_init_procedures'] = _INIT_PROCEDURES_FUNC

  if _QUIT_FUNC:
    class_dict['do_quit'] = _QUIT_FUNC

  return type(
    class_name,
    bases,
    class_dict,
  )


def _do_query_procedures(_plugin_instance):
  return list(_PROCEDURE_NAMES_AND_DATA)


def _do_create_procedure(plugin_instance, proc_name):
  if proc_name in _PROCEDURE_NAMES_AND_DATA:
    proc_dict = _PROCEDURE_NAMES_AND_DATA[proc_name]
  else:
    return None

  if not inspect.isclass(proc_dict['procedure_type']):
    raise TypeError(f"{proc_dict['procedure_type']} is not a valid class type")

  procedure_wrapper = _get_procedure_wrapper(
    proc_dict['procedure'],
    proc_dict['procedure_type'],
    proc_dict['init_ui'],
    proc_dict['init_gegl'],
  )

  if issubclass(proc_dict['procedure_type'], Gimp.ExportProcedure):
    procedure = proc_dict['procedure_type'].new(
      plugin_instance,
      proc_name,
      proc_dict['pdb_procedure_type'],
      proc_dict['export_metadata'],
      procedure_wrapper,
      proc_dict['run_data'],
    )
  elif issubclass(proc_dict['procedure_type'], Gimp.BatchProcedure):
    procedure = proc_dict['procedure_type'].new(
      plugin_instance,
      proc_name,
      proc_dict['interpreter_name'],
      proc_dict['pdb_procedure_type'],
      procedure_wrapper,
      proc_dict['run_data'],
    )
  elif issubclass(proc_dict['procedure_type'], Gimp.VectorLoadProcedure):
    procedure = proc_dict['procedure_type'].new(
      plugin_instance,
      proc_name,
      proc_dict['pdb_procedure_type'],
      proc_dict['extract_func'],
      proc_dict['extract_data'],
      procedure_wrapper,
      proc_dict['run_data'],
    )
  else:
    procedure = proc_dict['procedure_type'].new(
      plugin_instance,
      proc_name,
      proc_dict['pdb_procedure_type'],
      procedure_wrapper,
      proc_dict['run_data'],
    )

  if proc_dict['arguments'] is not None:
    parsed_arguments = _parse_and_check_parameters(proc_dict['arguments'])

    for name, params in parsed_arguments.items():
      param_type = params.pop(0)
      _get_add_param_func(procedure, param_type, 'argument')(name, *params)

  if proc_dict['return_values'] is not None:
    parsed_return_values = _parse_and_check_parameters(proc_dict['return_values'])

    for name, params in parsed_return_values.items():
      param_type = params.pop(0)
      _get_add_param_func(procedure, param_type, 'return_value')(name, *params)

  if proc_dict['auxiliary_arguments'] is not None:
    parsed_auxiliary_arguments = _parse_and_check_parameters(proc_dict['auxiliary_arguments'])

    for name, params in parsed_auxiliary_arguments.items():
      param_type = params.pop(0)
      _get_add_param_func(procedure, param_type, 'aux_argument')(name, *params)

  if proc_dict['menu_label'] is not None:
    procedure.set_menu_label(proc_dict['menu_label'])

  menu_path = proc_dict['menu_path']
  if menu_path is not None:
    if isinstance(menu_path, str):
      procedure.add_menu_path(menu_path)
    elif isinstance(menu_path, Iterable):
      for path in menu_path:
        procedure.add_menu_path(path)
    else:
      raise TypeError(f'menu path "{menu_path}" must be a string or an iterable')

  if proc_dict['image_types'] is not None:
    procedure.set_image_types(proc_dict['image_types'])

  if proc_dict['sensitivity_mask'] is not None:
    procedure.set_sensitivity_mask(proc_dict['sensitivity_mask'])

  if proc_dict['documentation'] is not None:
    if len(proc_dict['documentation']) == 2:
      procedure.set_documentation(*proc_dict['documentation'], proc_name)
    elif len(proc_dict['documentation']) == 3:
      procedure.set_documentation(*proc_dict['documentation'])
    else:
      raise ValueError('documentation must be a tuple of 2 or 3 elements')

  if proc_dict['attribution'] is not None:
    procedure.set_attribution(*proc_dict['attribution'])

  if proc_dict['additional_init'] is not None:
    proc_dict['additional_init'](procedure)

  return procedure


def _get_add_param_func(procedure, param_type, param_group):
  try:
    return getattr(procedure, f'add_{param_type}_{param_group}')
  except AttributeError:
    raise ValueError(f'type "{param_type}" is not valid')


def _disable_locale(_plugin_instance, _name):
  return False


def _get_procedure_wrapper(func, procedure_type, init_ui, init_gegl):
  @functools.wraps(func)
  def func_wrapper(*procedure_and_args):
    procedure = procedure_and_args[0]
    config = procedure_and_args[-2]

    if procedure_type == Gimp.ImageProcedure:
      run_mode = procedure_and_args[1]
    else:
      run_mode = next(
        (config.get_property(prop.name)
         for prop in config.list_properties() if prop.name == 'run-mode'),
        Gimp.RunMode.NONINTERACTIVE)

    if init_ui and run_mode == Gimp.RunMode.INTERACTIVE:
      GimpUi.init(procedure.get_name())

    if init_gegl:
      Gegl.init()

    initnotifier.notifier.emit('start-procedure')

    return_values = func(*procedure_and_args)

    if return_values is None:
      return_values = []
    elif not isinstance(return_values, tuple):
      return_values = [return_values]
    else:
      return_values = list(return_values)

    if not return_values or not isinstance(return_values[0], Gimp.PDBStatusType):
      exit_status = Gimp.PDBStatusType.SUCCESS
    else:
      exit_status = return_values.pop(0)

    if exit_status in [Gimp.PDBStatusType.CALLING_ERROR, Gimp.PDBStatusType.EXECUTION_ERROR]:
      error = GLib.Error(return_values[0]) if return_values else GLib.Error()
      formatted_return_values = procedure.new_return_values(exit_status, error)
    else:
      formatted_return_values = procedure.new_return_values(exit_status, GLib.Error())
      if formatted_return_values.length() > 1:
        for i in reversed(range(1, formatted_return_values.length())):
          if i - 1 < len(return_values):
            formatted_return_values.remove(i)
            formatted_return_values.insert(i, return_values[i - 1])

    return formatted_return_values

  return func_wrapper
