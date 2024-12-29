"""Wrapper of ``Gimp.get_pdb()`` to simplify invoking GIMP PDB procedures."""

from __future__ import annotations

import abc
from typing import List, Optional

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject


__all__ = [
  'pdb',
  'GeglProcedure',
  'GimpPDBProcedure',
  'PDBProcedure',
  'PDBProcedureError',
]


class _PyPDB:

  def __init__(self):
    self._last_status = None
    self._last_error = None

    self._proc_cache = {}

  @property
  def last_status(self):
    """Exit status of the last `GimpPDBProcedure` invoked by this class."""
    return self._last_status

  @property
  def last_error(self):
    """Error message of the last `GimpPDBProcedure` invoked by this class."""
    return self._last_error

  def __getattr__(self, name: str) -> PDBProcedure:
    proc_name = self._process_procedure_name(name)

    if self._gimp_pdb_procedure_exists(proc_name):
      return self._get_proc_by_name(proc_name, GimpPDBProcedure)
    elif self._gegl_operation_exists(proc_name):
      return self._get_proc_by_name(proc_name, GeglProcedure)
    else:
      raise AttributeError(f'procedure "{proc_name}" does not exist')

  def __getitem__(self, name: str) -> PDBProcedure:
    proc_name = self._process_procedure_name(name)

    if self._gimp_pdb_procedure_exists(proc_name):
      return self._get_proc_by_name(proc_name, GimpPDBProcedure)
    elif self._gegl_operation_exists(proc_name):
      return self._get_proc_by_name(proc_name, GeglProcedure)
    else:
      raise KeyError(f'procedure "{proc_name}" does not exist')

  def __contains__(self, name: Optional[str]) -> bool:
    if name is None:
      return False

    proc_name = self._process_procedure_name(name)

    return self._gimp_pdb_procedure_exists(proc_name) or self._gegl_operation_exists(proc_name)

  @staticmethod
  def list_all_gegl_operations():
    return Gegl.list_operations()

  @staticmethod
  def list_all_gimp_pdb_procedures():
    return Gimp.get_pdb().query_procedures(*([''] * 8))

  def list_all_procedure_names(self) -> List[str]:
    return self.list_all_gegl_operations() + self.list_all_gimp_pdb_procedures()

  def remove_from_cache(self, name: str):
    """Removes a `PDBProcedure` instance matching ``name`` from the internal
    cache.

    This method is only ever useful for testing purposes.

    No action is taken if there is no procedure matching ``name`` in the cache.
    """
    proc_name = self._process_procedure_name(name)

    try:
      del self._proc_cache[proc_name]
    except KeyError:
      pass

  def _get_proc_by_name(self, proc_name, proc_class):
    if proc_name not in self._proc_cache:
      self._proc_cache[proc_name] = proc_class(self, proc_name)

    return self._proc_cache[proc_name]

  @staticmethod
  def _gimp_pdb_procedure_exists(proc_name):
    return Gimp.get_pdb().procedure_exists(proc_name)

  @staticmethod
  def _gegl_operation_exists(proc_name):
    return Gegl.has_operation(proc_name)

  @staticmethod
  def _process_procedure_name(name):
    return name.replace('__', ':').replace('_', '-')


class PDBProcedure(metaclass=abc.ABCMeta):

  def __init__(self, pypdb_instance, name):
    self._pypdb_instance = pypdb_instance
    self._name = name

  @abc.abstractmethod
  def __call__(self, **kwargs):
    """Calls the procedure.

    All procedure arguments must be specified as keyword arguments (unless
    defined otherwise in subclasses).

    If any keyword argument is omitted, the default value is used for that
    argument as defined in the procedure.

    All underscore characters  (``_``) in argument names are automatically
    replaced by ``-``.
    """
    pass

  @property
  @abc.abstractmethod
  def arguments(self):
    pass

  @property
  @abc.abstractmethod
  def aux_arguments(self):
    pass

  @property
  @abc.abstractmethod
  def return_values(self):
    pass

  @property
  @abc.abstractmethod
  def authors(self):
    pass

  @property
  @abc.abstractmethod
  def blurb(self):
    pass

  @property
  @abc.abstractmethod
  def copyright(self):
    pass

  @property
  @abc.abstractmethod
  def date(self):
    pass

  @property
  @abc.abstractmethod
  def help(self):
    pass

  @property
  @abc.abstractmethod
  def menu_label(self):
    pass

  @property
  @abc.abstractmethod
  def menu_paths(self):
    pass

  @property
  def name(self):
    """The procedure name.

    The name can be used to access a `PDBProcedure` instance as `pdb[<name>]`.
    """
    return self._name

  @abc.abstractmethod
  def create_config(self):
    """Creates a procedure config filled with default values."""
    pass


class GimpPDBProcedure(PDBProcedure):

  def __init__(self, pypdb_instance, name):
    self._proc = Gimp.get_pdb().lookup_procedure(name)

    super().__init__(pypdb_instance, name)

  def __call__(self, **kwargs):
    """Calls a GIMP PDB procedure.

    All arguments must be specified as keyword arguments.

    Return values from the procedure are returned as a tuple of values. If the
    procedure does not define any return value, ``None`` is returned.
    """
    config = self._create_config_for_call(**kwargs)

    result = self._proc.run(config)

    if result is None:
      return None

    result_list = [result.index(i) for i in range(result.length())]

    last_status = None
    last_error = None

    if len(result_list) > 0:
      if isinstance(result_list[0], Gimp.PDBStatusType):
        last_status = result_list.pop(0)

    if len(result_list) > 0:
      if last_status not in [Gimp.PDBStatusType.SUCCESS, Gimp.PDBStatusType.PASS_THROUGH]:
        last_error = result_list.pop(0)

    self._pypdb_instance._last_status = last_status
    self._pypdb_instance._last_error = last_error

    if (last_status is not None
        and last_status not in [Gimp.PDBStatusType.SUCCESS, Gimp.PDBStatusType.PASS_THROUGH]):
      raise PDBProcedureError(last_error, last_status)

    if result_list:
      if len(result_list) == 1:
        return result_list[0]
      else:
        return result_list
    else:
      return None

  @property
  def proc(self):
    """`Gimp.Procedure` instance wrapped by this class."""
    return self._proc

  @property
  def arguments(self):
    return self._proc.get_arguments()

  @property
  def aux_arguments(self):
    return self._proc.get_aux_arguments()

  @property
  def return_values(self):
    return self._proc.get_return_values()

  @property
  def authors(self):
    return self._proc.get_authors()

  @property
  def blurb(self):
    return self._proc.get_blurb()

  @property
  def copyright(self):
    return self._proc.get_copyright()

  @property
  def date(self):
    return self._proc.get_date()

  @property
  def help(self):
    return self._proc.get_help()

  @property
  def menu_label(self):
    return self._proc.get_menu_label()

  @property
  def menu_paths(self):
    return self._proc.get_menu_paths()

  def create_config(self):
    return self._proc.create_config()

  def _create_config_for_call(self, **proc_kwargs):
    config = self.create_config()

    args = self.arguments

    args_and_names = {arg.name: arg for arg in args}

    for arg_name, arg_value in proc_kwargs.items():
      processed_arg_name = arg_name.replace('_', '-')

      try:
        arg = args_and_names[processed_arg_name]
      except KeyError:
        raise PDBProcedureError(
          f'argument "{processed_arg_name}" does not exist',
          Gimp.PDBStatusType.CALLING_ERROR)

      arg_type_name = arg.value_type.name
      config_set_property = _get_set_property_func_for_gimp_pdb_procedure(arg_type_name, config)
      config_set_property(processed_arg_name, arg_value)

    return config


class GeglProcedure(PDBProcedure):

  def __init__(self, pypdb_instance, name):
    self._filter_properties = Gegl.Operation.list_properties(name)

    self._drawable_param = Gimp.param_spec_drawable(
      'drawable-', 'Drawable', 'Drawable', False, GObject.ParamFlags.READWRITE)
    self._blend_mode_param = GObject.param_spec_enum(
      'blend-mode-',
      'Blend mode',
      'Blend mode',
      Gimp.LayerMode.__gtype__,
      Gimp.LayerMode.REPLACE,
      GObject.ParamFlags.READWRITE,
    )
    self._opacity_param = GObject.param_spec_double(
      'opacity-', 'Opacity', 'Opacity', 0.0, 1.0, 1.0, GObject.ParamFlags.READWRITE)
    self._merge_filter_param = GObject.param_spec_boolean(
      'merge-filter-', 'Merge filter', 'Merge filter', False, GObject.ParamFlags.READWRITE)
    self._visible_param = GObject.param_spec_boolean(
      'visible-', 'Visible', 'Visible', True, GObject.ParamFlags.READWRITE)
    self._filter_name_param = GObject.param_spec_string(
      'name-', 'Filter name', 'Filter name', '', GObject.ParamFlags.READWRITE)

    self._keys = {key: None for key in Gegl.Operation.list_keys(name)}
    self._properties = {prop.get_name(): prop for prop in self._get_properties()}

    super().__init__(pypdb_instance, name)

  def __call__(self, *args, **kwargs):
    """Applies a layer effect (drawable filter, GEGL operation) on the specified
    drawable.

    Beside arguments defined by the GEGL operation, you may specify the
    following additional keyword arguments, all of which have a trailing ``_``:

    * ``drawable_`` - The ``Gimp.Drawable`` instance to apply the layer effect
      to. This argument may be specified as the first and the only positional
      argument.
    *  ``merge_filter_`` - If ``False`` (default), the layer effect is applied
      non-destructively and the filter is returned. If ``True``, the layer
      effect is immediately merged into the drawable and ``None`` is returned.
    * ``blend_mode_`` - The `Gimp.LayerMode` to apply to the layer effect.
    * ``opacity_`` - The opacity of the layer effect.
    * ``visible_`` - If ``True`` (default), the layer effect is visible. If
      ``False``, the layer effect is not visible.
    * ``name_`` - A custom name for the layer effect. If an empty string, the
      default name of the layer effect is assigned.

    All arguments must be specified as keyword arguments, except the
    ``drawable_`` argument, which may be specified as the first and the only
    positional argument.
    """
    processed_kwargs = {name.replace('_', '-'): value for name, value in kwargs.items()}

    if 'drawable-' in processed_kwargs:
      drawable = processed_kwargs.pop('drawable-')
    else:
      if not args or not isinstance(args[0], Gimp.Drawable):
        raise PDBProcedureError(
          ('if the "drawable_" parameter is not specified as a keyword argument, it must be'
           ' specified as the first and only positional argument'),
          Gimp.PDBStatusType.CALLING_ERROR)

      drawable = args[0]

    blend_mode = processed_kwargs.pop('blend-mode-', self._blend_mode_param.default_value)
    opacity = processed_kwargs.pop('opacity-', self._opacity_param.default_value)
    merge_filter = processed_kwargs.pop('merge-filter-', self._merge_filter_param.default_value)
    visible = processed_kwargs.pop('visible-', self._visible_param.default_value)
    name = processed_kwargs.pop('name-', self._filter_name_param.default_value)

    drawable_filter = Gimp.DrawableFilter.new(drawable, self.name, name)
    drawable_filter.set_blend_mode(blend_mode)
    drawable_filter.set_opacity(opacity)
    drawable_filter.set_visible(visible)
    drawable_filter.update()

    config = drawable_filter.get_config()

    properties_from_config = {prop.get_name(): prop for prop in config.list_properties()}

    for arg_name, arg_value in processed_kwargs.items():
      if arg_name not in self._properties:
        raise PDBProcedureError(
          f'argument "{arg_name}" does not exist or is not supported',
          Gimp.PDBStatusType.CALLING_ERROR)

      # Silently skip properties not supported in GIMP as the procedure
      # may still finish successfully.
      if arg_name not in properties_from_config:
        continue

      should_transform_enum_to_choice = (
        isinstance(self._properties[arg_name], GObject.ParamSpecEnum)
        and isinstance(properties_from_config[arg_name], (Gimp.ParamChoice, Gimp.ParamSpecChoice)))

      # GIMP internally transforms GEGL enum values to `Gimp.Choice` values:
      #  https://gitlab.gnome.org/GNOME/gimp/-/merge_requests/2008
      if should_transform_enum_to_choice:
        processed_value = (
          self._properties[arg_name].get_default_value().__enum_values__[arg_value].value_nick)
      else:
        processed_value = arg_value

      config.set_property(arg_name, processed_value)

    if merge_filter:
      drawable.merge_filter(drawable_filter)

      return None
    else:
      drawable.append_filter(drawable_filter)

      return drawable_filter

  @property
  def arguments(self):
    return list(self._properties.values())

  @property
  def aux_arguments(self):
    return []

  @property
  def return_values(self):
    return []

  @property
  def authors(self):
    return ''

  @property
  def blurb(self):
    if 'description' in self._keys:
      return Gegl.Operation.get_key(self.name, 'description')
    else:
      return ''

  @property
  def copyright(self):
    return ''

  @property
  def date(self):
    return ''

  @property
  def help(self):
    return ''

  @property
  def menu_label(self):
    if 'title' in self._keys:
      return Gegl.Operation.get_key(self.name, 'title')
    else:
      return ''

  @property
  def menu_paths(self):
    return []

  def create_config(self):
    """This subclass does not support config creation, hence this method returns
    ``None``.
    """
    return None

  def _get_properties(self):
    return [
      self._drawable_param,
      *self._filter_properties,
      self._blend_mode_param,
      self._opacity_param,
      self._merge_filter_param,
      self._visible_param,
      self._filter_name_param,
    ]


def _get_set_property_func_for_gimp_pdb_procedure(arg_type_name, config):
  if arg_type_name == 'GimpCoreObjectArray':
    return config.set_core_object_array
  elif arg_type_name == 'GimpColorArray':
    return config.set_color_array
  else:
    return config.set_property


class PDBProcedureError(Exception):

  def __init__(self, message, status):
    super().__init__(message)

    self.message = message
    self.status = status

  def __str__(self):
    return str(self.message)


pdb = _PyPDB()
