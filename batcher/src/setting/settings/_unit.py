from __future__ import annotations

from collections.abc import Iterable
from typing import List, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
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

  _AVAILABLE_UNITS = None

  def __init__(self, name: str, show_pixels: bool = True, show_percent: bool = True, **kwargs):
    self._show_pixels = show_pixels
    self._show_percent = show_percent

    super().__init__(name, **kwargs)

  @classmethod
  def get_available_units(cls):
    if cls._AVAILABLE_UNITS is None:
      unit_store = GimpUi.UnitStore.new(1)
      unit_store.set_has_percent(True)
      unit_store.set_has_pixels(True)

      try:
        unit_column_index = next(iter(
          index for index in range(unit_store.get_n_columns())
          if unit_store.get_column_type(index) == Gimp.Unit.__gtype__
        ))
      except StopIteration:
        # Fall back to units pre-defined in the GIMP API.
        cls._AVAILABLE_UNITS = {
          Gimp.Unit.inch().get_abbreviation(): Gimp.Unit.inch(),
          Gimp.Unit.mm().get_abbreviation(): Gimp.Unit.mm(),
          Gimp.Unit.percent().get_abbreviation(): Gimp.Unit.percent(),
          Gimp.Unit.pica().get_abbreviation(): Gimp.Unit.pica(),
          Gimp.Unit.pixel().get_abbreviation(): Gimp.Unit.pixel(),
          Gimp.Unit.point().get_abbreviation(): Gimp.Unit.point(),
        }
      else:
        cls._AVAILABLE_UNITS = {}
        for row in unit_store:
          unit = row[unit_column_index]
          cls._AVAILABLE_UNITS[unit.get_abbreviation()] = unit

    return cls._AVAILABLE_UNITS

  @classmethod
  def raw_data_to_unit(cls, raw_value: Union[Iterable, str]):
    if isinstance(raw_value, str):
      # Maintain backwards compatibility
      if hasattr(Gimp.Unit, raw_value):
        return getattr(Gimp.Unit, raw_value)()
      elif raw_value in cls.get_available_units():
        return cls.get_available_units()[raw_value]
      else:
        return raw_value
    elif isinstance(raw_value, (list, tuple)):
      if len(raw_value) >= 5:
        unit_abbreviation = raw_value[-1]
        if unit_abbreviation in cls.get_available_units():
          return cls.get_available_units()[unit_abbreviation]
        else:
          return Gimp.Unit.new(*raw_value)
      else:
        return Gimp.Unit.new(*raw_value)
    elif isinstance(raw_value, Iterable):
      return Gimp.Unit.new(*raw_value)
    else:
      return raw_value

  @classmethod
  def unit_to_raw_data(cls, unit: Gimp.Unit) -> Union[List, str]:
    if unit.get_abbreviation() in cls.get_available_units():
      return unit.get_abbreviation()
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
      self._pdb_description,
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
    return self.unit_to_raw_data(unit)
