from __future__ import annotations

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'DisplaySetting',
]


class DisplaySetting(_base.Setting):
  """Class for settings holding `Gimp.Display` instances.

  `Gimp.Display` instances cannot be loaded or saved. Therefore, `to_dict()`
  returns a dictionary whose ``'value'`` and ``'default_value'`` keys are
  ``None``.

  Allowed GIMP PDB types:
  * `Gimp.Display`

  Message IDs for invalid values:
  * ``'invalid_value'``: The display assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Display]

  _REGISTRABLE_TYPE_NAME = 'display'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.display_spin_button]

  def __init__(
        self,
        name: str,
        none_ok: bool = True,
        **kwargs,
  ):
    self._none_ok = none_ok

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  def _copy_value(self, value):
    return value

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, int):
      return Gimp.Display.get_by_id(raw_value)
    else:
      return raw_value

  def _value_to_raw(self, value):
    # There is no way to recover `Gimp.Display` objects from a persistent
    # source, hence return ``None``.
    return None

  def _validate(self, display):
    if display is not None and not display.is_valid():
      return 'invalid display', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      GObject.ParamFlags.READWRITE,
    ]
