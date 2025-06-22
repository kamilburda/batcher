from __future__ import annotations

import inspect
from typing import Union

from gi.repository import GLib
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'NumericSetting',
  'IntSetting',
  'UintSetting',
  'DoubleSetting',
]


class NumericSetting(_base.Setting):
  """Abstract class for numeric settings - integers and floats.

  When assigning a value, this class checks for the upper and lower bounds if
  they are set.

  Message IDs for invalid values:
    * ``'below_min'``: The value assigned is less than `min_value`.
    * ``'below_pdb_min'``: The value assigned is less than `pdb_min_value`.
    * ``'above_max'``: The value assigned is greater than `max_value`.
    * ``'above_pdb_max'``: The value assigned is greater than `pdb_max_value`.
  """

  _ABSTRACT = True

  _PDB_TYPES_AND_MINIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MININT,
    GObject.TYPE_UINT: 0,
    GObject.TYPE_DOUBLE: -GLib.MAXDOUBLE,
  }
  """Mapping of PDB types to minimum values allowed for each type.
  
  For example, the minimum value allowed for type `GObject.TYPE_INT` would be
  `GLib.MININT`.
  """

  _PDB_TYPES_AND_MAXIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MAXINT,
    GObject.TYPE_UINT: GLib.MAXUINT,
    GObject.TYPE_DOUBLE: GLib.MAXDOUBLE,
  }
  """Mapping of PDB types to maximum values allowed for each type.
  
  For example, the maximum value allowed for type `GObject.TYPE_INT` would be
  `GLib.MAXINT`.
  """

  def __init__(self, name: str, min_value=None, max_value=None, **kwargs):
    self._min_value = min_value
    self._max_value = max_value

    # We need to define these attributes before the parent's `__init__()` as
    # some methods require these attributes to be defined during `__init__()`.
    pdb_type = super()._get_pdb_type(
      kwargs.get('pdb_type', inspect.signature(_base.Setting.__init__).parameters['pdb_type'].default))
    self._pdb_min_value = self._PDB_TYPES_AND_MINIMUM_VALUES.get(pdb_type, None)
    self._pdb_max_value = self._PDB_TYPES_AND_MAXIMUM_VALUES.get(pdb_type, None)

    self._check_min_and_max_values_against_pdb_min_and_max_values()

    super().__init__(name, **kwargs)

  @property
  def min_value(self) -> Union[int, float, None]:
    """Minimum allowed numeric value.

    If ``None``, no checks for a minimum value are performed.
    """
    return self._min_value

  @property
  def max_value(self) -> Union[int, float, None]:
    """Maximum allowed numeric value.

    If ``None``, no checks for a maximum value are performed.
    """
    return self._max_value

  @property
  def pdb_min_value(self) -> Union[int, float, None]:
    """Minimum numeric value as allowed by the `pdb_type`.

    This property represents the lowest possible value this setting can have
    given the `pdb_type`. `min_value` thus cannot be lower than this value.

    If ``None``, no checks for a minimum value are performed.
    """
    return self._pdb_min_value

  @property
  def pdb_max_value(self) -> Union[int, float, None]:
    """Maximum numeric value as allowed by the `pdb_type`.

    This property represents the highest possible value this setting can have
    given the `pdb_type`. `max_value` thus cannot be greater than this value.

    If ``None``, no checks for a maximum value are performed.
    """
    return self._pdb_max_value

  def _validate(self, value):
    if self.min_value is not None and value < self.min_value:
      return f'value cannot be less than {self.min_value}', 'below_min'

    if self.pdb_min_value is not None and value < self.pdb_min_value:
      return f'value cannot be less than {self.pdb_min_value}', 'below_pdb_min'

    if self.max_value is not None and value > self.max_value:
      return f'value cannot be greater than {self.max_value}', 'above_max'

    if self.pdb_max_value is not None and value > self.pdb_max_value:
      return f'value cannot be greater than {self.pdb_max_value}', 'above_pdb_max'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._min_value if self._min_value is not None else self._pdb_min_value,
      self._max_value if self._max_value is not None else self._pdb_max_value,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  def _check_min_and_max_values_against_pdb_min_and_max_values(self):
    if (self.min_value is not None
        and self.pdb_min_value is not None
        and self.min_value < self.pdb_min_value):
      raise ValueError(
        f'minimum value {self.min_value} cannot be less than {self.pdb_min_value}')

    if (self.max_value is not None
        and self.pdb_max_value is not None
        and self.max_value > self.pdb_max_value):
      raise ValueError(
        f'maximum value {self.max_value} cannot be greater than {self.pdb_max_value}')


class IntSetting(NumericSetting):
  """Class for integer settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_INT`

  Default value: 0
  """

  _ALIASES = ['integer']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_INT]

  _REGISTRABLE_TYPE_NAME = 'int'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.int_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0


class UintSetting(NumericSetting):
  """Class for unsigned integer settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_UINT`

  Default value: 0
  """

  _ALIASES = ['unsigned_integer']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_UINT]

  _REGISTRABLE_TYPE_NAME = 'uint'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.int_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0


class DoubleSetting(NumericSetting):
  """Class for double (double-precision floating-point numbers) settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_DOUBLE`

  Default value: 0.0
  """

  _ALIASES = ['float']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_DOUBLE]

  _REGISTRABLE_TYPE_NAME = 'double'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.double_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0.0
