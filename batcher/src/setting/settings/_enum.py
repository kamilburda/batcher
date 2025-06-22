from __future__ import annotations

from collections.abc import Iterable
import importlib
import inspect
from typing import List, Optional, Union, Tuple, Type

from gi.repository import GObject

from src import utils
from src import pypdb
from src.pypdb import pdb

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'EnumSetting',
]


class EnumSetting(_base.Setting):
  """Class for settings wrapping an enumerated type (`GObject.GEnum` subclass).

  Allowed GIMP PDB types:
  * any `GObject.GEnum` subclass (e.g. `Gimp.RunMode`)

  Default value: The first item defined for the specified `GObject.GEnum`
    subclass (e.g. `Gimp.RunMode.INTERACTIVE`).
  """

  _REGISTRABLE_TYPE_NAME = 'enum'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.enum_combo_box]

  # `0` acts as a fallback in case `enum_type` has no values, which should not occur.
  _DEFAULT_DEFAULT_VALUE = lambda self: next(iter(utils.get_enum_values(self.enum_type)), 0)

  _SUPPORTED_MODULES_WITH_ENUMS = {
    'Gimp': 'gi.repository.Gimp',
    'Gegl': 'gi.repository.Gegl',
    'GimpUi': 'gi.repository.GimpUi',
    'GObject': 'gi.repository.GObject',
    'GLib': 'gi.repository.GLib',
    'Gio': 'gi.repository.Gio',
  }

  def __init__(
        self,
        name: str,
        enum_type: Union[
          Type[GObject.GEnum],
          GObject.GType,
          str,
          Tuple[pypdb.PDBProcedure, GObject.ParamSpec],
          Tuple[str, str],
        ],
        excluded_values: Optional[Iterable[GObject.GEnum]] = None,
        **kwargs,
  ):
    """Initializes an `EnumSetting` instance.

    If ``pdb_type`` is specified as a keyword argument, it is ignored and
    always set to ``enum_type``.

    Args:
      name:
        Setting name. See the `name` property for more information.
      enum_type:
        Enumerated type. The type can be specified in one of the following ways:

        * a `GObject.GEnum` subclass,
        * a `GObject.GType` instance representing the enumerated type,
        * a string representing the module path plus name of a `GObject.GEnum`
          subclass, e.g. ``'gi.repository.Gimp.RunMode'`` for `Gimp.RunMode`,
        * a tuple of ``(pypdb.PDBProcedure, GObject.ParamSpec)`` instances,
          the first representing a PDB procedure and the second representing one
          of its properties.
        * a tuple of ``(PDB procedure name, property name)`` strings
          representing a PDB procedure argument.
      excluded_values:
        List of enumerated values to be excluded from the setting GUI. This is
        useful in case this setting is used in a GIMP PDB procedure not
        supporting particular value(s).
      **kwargs:
        Additional keyword arguments that can be passed to the parent class'
        `__init__()`.
    """
    self._enum_type, self._procedure, self._procedure_param = self._process_enum_type(enum_type)
    self._excluded_values = self._process_excluded_values(excluded_values)

    kwargs['pdb_type'] = self._enum_type

    super().__init__(name, **kwargs)

  @property
  def enum_type(self) -> Type[GObject.GEnum]:
    """`GObject.GEnum` subclass whose values are used as setting values."""
    return self._enum_type

  @property
  def procedure(self) -> Union[pypdb.PDBProcedure, None]:
    """A PDB procedure containing the enum in this setting, or ``None`` if not
    specified.
    """
    return self._procedure

  @property
  def procedure_param(self) -> Union[GObject.ParamSpec, None]:
    """A property representing the enum in this setting, or ``None`` if not
    specified.
    """
    return self._procedure_param

  @property
  def excluded_values(self) -> List[GObject.GEnum]:
    """`GObject.GEnum` values excluded from the setting GUI."""
    return self._excluded_values

  def to_dict(self):
    settings_dict = super().to_dict()

    if self._procedure is not None and self._procedure_param is not None:
      settings_dict['enum_type'] = [self._procedure.name, self._procedure_param.name]
    else:
      settings_dict['enum_type'] = self.enum_type.__gtype__.name

    if 'excluded_values' in settings_dict:
      settings_dict['excluded_values'] = [int(value) for value in self.excluded_values]

    return settings_dict

  def _assign_value(self, value):
    self._value = self.enum_type(value)

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, int):
      try:
        return self.enum_type(raw_value)
      except Exception:
        return raw_value
    else:
      return raw_value

  def _value_to_raw(self, value):
    return int(value)

  def _validate(self, value):
    try:
      self.enum_type(value)
    except ValueError:
      return 'invalid value', 'invalid_value'

    if isinstance(value, GObject.GEnum) and not isinstance(value, self.enum_type):
      return (
        f'enumerated value has an invalid type "{type(value)}"',
        'invalid_type',
        False)

  def _get_pdb_type(self, pdb_type):
    return self._enum_type

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._enum_type,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  def _process_enum_type(self, enum_type):
    procedure = None
    procedure_param = None

    if inspect.isclass(enum_type) and issubclass(enum_type, GObject.GEnum):
      processed_enum_type = enum_type
    elif isinstance(enum_type, GObject.GType) or isinstance(enum_type, str):
      if isinstance(enum_type, GObject.GType):
        processed_enum_type = enum_type.name
      else:
        processed_enum_type = enum_type

      module_path, enum_class_name = self._get_enum_type_from_string(processed_enum_type)

      if not module_path or not enum_class_name:
        raise TypeError(f'"{processed_enum_type}" is not a valid GObject.GEnum type')

      module_with_enum = importlib.import_module(module_path)
      processed_enum_type = getattr(module_with_enum, enum_class_name)
    elif isinstance(enum_type, (tuple, list)) and len(enum_type) == 2:
      if isinstance(enum_type[0], str):
        if enum_type[0] in pdb:
          procedure = pdb[enum_type[0]]
      else:
        procedure = enum_type[0]

      if procedure is not None:
        if isinstance(enum_type[1], str):
          procedure_param = next(
            iter(prop for prop in procedure.arguments if prop.name == enum_type[1]),
            None)
        else:
          procedure_param = enum_type[1]

      if procedure_param is not None:
        # For PyGObject >= 3.50.0, `default_value` returns an int rather than
        # an enum value. `get_default_value()` is not available in < 3.50.0.
        if hasattr(procedure_param, 'get_default_value'):
          enum_default_value = procedure_param.get_default_value()
        else:
          enum_default_value = procedure_param.default_value

        processed_enum_type = type(enum_default_value)
      else:
        raise TypeError(
          f'procedure "{enum_type[0]}" or its property "{enum_type[1]}"'
          ' does not exist')
    else:
      raise TypeError(
        f'"{enum_type}" is not a supported type to derive a GObject.GEnum type from')

    if not inspect.isclass(processed_enum_type):
      raise TypeError(f'{processed_enum_type} is not a class')

    if not issubclass(processed_enum_type, GObject.GEnum):
      raise TypeError(f'{processed_enum_type} is not a subclass of GObject.GEnum')

    return processed_enum_type, procedure, procedure_param

  def _process_excluded_values(self, excluded_values):
    if excluded_values is not None:
      return [self.enum_type(value) for value in excluded_values]
    else:
      return []

  def _get_enum_type_from_string(self, enum_type_str):
    # HACK: We parse the `GType` name to obtain the `GEnum` instance. Is there
    #  a more elegant way?
    for module_name, module_path in self._SUPPORTED_MODULES_WITH_ENUMS.items():
      if enum_type_str.startswith(module_name):
        return module_path, enum_type_str[len(module_name):]

    return None, None
