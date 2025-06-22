from __future__ import annotations

from collections.abc import Iterable
from typing import List, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'UnitSetting',
]


class UnitSetting(_base.Setting):
  """Class for settings storing `Gimp.Unit` instances.

  Allowed GIMP PDB types:
  * `Gimp.Unit`

  Default value: A `Gimp.Unit.pixel()` instance representing pixels.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Unit]

  _REGISTRABLE_TYPE_NAME = 'unit'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.unit_combo_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: Gimp.Unit.pixel()

  _BUILT_IN_UNITS = None

  def __init__(self, name: str, show_pixels: bool = True, show_percent: bool = True, **kwargs):
    self._show_pixels = show_pixels
    self._show_percent = show_percent

    # We use id() instead of relying on hashes as hashes may either be
    # unavailable or, when using stubs, result in 0 hash for all these objects.
    self._built_in_units = self.get_built_in_units()

    super().__init__(name, **kwargs)

  @classmethod
  def get_built_in_units(cls):
    if cls._BUILT_IN_UNITS is None:
      cls._BUILT_IN_UNITS = {
        Gimp.Unit.inch().get_id(): 'inch',
        Gimp.Unit.mm().get_id(): 'mm',
        Gimp.Unit.percent().get_id(): 'percent',
        Gimp.Unit.pica().get_id(): 'pica',
        Gimp.Unit.pixel().get_id(): 'pixel',
        Gimp.Unit.point().get_id(): 'point',
      }

    return cls._BUILT_IN_UNITS

  @classmethod
  def raw_data_to_unit(cls, raw_value: Union[Iterable, str]):
    if isinstance(raw_value, str):
      if hasattr(Gimp.Unit, raw_value):
        return getattr(Gimp.Unit, raw_value)()
      else:
        return raw_value
    elif isinstance(raw_value, Iterable):
      return Gimp.Unit.new(*raw_value)
    else:
      return raw_value

  @classmethod
  def unit_to_raw_data(cls, unit, built_in_units) -> Union[List, str]:
    if unit.get_id() in built_in_units:
      return built_in_units[unit.get_id()]
    else:
      return [
        unit.get_name(),
        unit.get_factor(),
        unit.get_digits(),
        unit.get_symbol(),
        unit.get_abbreviation(),
      ]

  @property
  def show_pixels(self):
    """``True`` if pixels should be displayed as a unit for the setting's GUI,
    ``False`` otherwise.
    """
    return self._show_pixels

  @property
  def show_percent(self):
    """``True`` if percentage should be displayed as a unit for the setting's
    GUI, ``False`` otherwise.
    """
    return self._show_percent

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._show_pixels,
      self._show_percent,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  def _validate(self, unit):
    if unit is None or not isinstance(unit, Gimp.Unit):
      return 'invalid unit', 'invalid_value'

  def _raw_to_value(self, raw_value: Union[Iterable, str]):
    return self.raw_data_to_unit(raw_value)

  def _value_to_raw(self, unit: Gimp.Unit) -> Union[List, str]:
    return self.unit_to_raw_data(unit, self._built_in_units)
