from __future__ import annotations

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'ColorSetting',
]


class ColorSetting(_base.Setting):
  """Class for settings holding `Gegl.Color` instances or a list of values
  representing `Gegl.Color`.

  If you need to instantiate a `ColorSetting` before registering a plug-in
  procedure, pass a list of values. Otherwise, you may experience crashes due to
  a missing call to `Gegl.init()`, or warnings about already registered GEGL
  operations when calling `Gegl.init()` prematurely.

  Allowed GIMP PDB types:
  * `Gegl.Color`

  Default value: `[0.0, 0.0, 0.0, 1.0]` (black color).

  Message IDs for invalid values:
  * ``'invalid_value'``:
    The color assigned is not a `Gegl.Color` instance or a list/tuple.
  """

  _ALLOWED_PDB_TYPES = [Gegl.Color]

  _REGISTRABLE_TYPE_NAME = 'color'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.color_button]

  # Return the list in a function to ensure returning a copy.
  _DEFAULT_DEFAULT_VALUE = lambda self: [0.0, 0.0, 0.0, 1.0]

  def __init__(
        self,
        name: str,
        has_alpha: bool = True,
        **kwargs,
  ):
    self._has_alpha = has_alpha

    super().__init__(name, **kwargs)

  @classmethod
  def get_value_as_color(cls, value):
    """Returns the specified value converted to a `Gegl.Color` instance."""
    if isinstance(value, (list, tuple)):
      color = Gegl.Color()

      if len(value) >= 4:
        color.set_rgba(*value[:4])

      return color
    else:
      return value

  @property
  def has_alpha(self) -> bool:
    """Returns ``True`` if this color setting supports the alpha channel."""
    return self._has_alpha

  @property
  def value_for_pdb(self):
    """Setting value converted to a `Gegl.Color` instance."""
    return self.get_value_as_color(self._value)

  def _value_to_raw(self, value):
    if isinstance(value, Gegl.Color):
      color = value.get_rgba()
      return [color.red, color.green, color.blue, color.alpha]
    else:
      return value

  def _validate(self, color):
    if not isinstance(color, (Gegl.Color, list, tuple)):
      return 'invalid color', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._has_alpha,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]
