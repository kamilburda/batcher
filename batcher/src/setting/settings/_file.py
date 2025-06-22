from __future__ import annotations

from typing import Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'FileSetting',
]


class FileSetting(_base.Setting):
  """Class for settings storing files or directories as `Gio.File` instances
  (``GFile`` type).

  Allowed GIMP PDB types:
  * `Gio.File`

  Default value:
    A `Gio.File` instance with no path (`Gio.File.get_uri()` returns ``None``).
  """

  _DEFAULT_DEFAULT_VALUE = lambda self: Gio.file_new_for_uri('')

  _ALLOWED_PDB_TYPES = [Gio.File]

  _REGISTRABLE_TYPE_NAME = 'file'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.file_chooser]

  def __init__(
        self,
        name: str,
        action: Union[Gimp.FileChooserAction, int],
        none_ok: bool = True,
        set_default_if_not_exists: bool = False,
        **kwargs,
  ):
    self._action = self._process_action(action)
    self._none_ok = none_ok
    self._set_default_if_not_exists = set_default_if_not_exists

    super().__init__(name, **kwargs)

  @property
  def action(self) -> Gimp.FileChooserAction:
    """The `Gimp.FileChooserAction` associated with this setting, indicating
    whether to open or save a file or a folder.

    This property is used to determine the appropriate GUI widget.
    """
    return self._action

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  @property
  def set_default_if_not_exists(self):
    """If ``True`` and the file is not valid (does not exist), it will be
    replaced by the default value. Applies only when interacting with the
    setting via GUI.
    """
    return self._set_default_if_not_exists

  def to_dict(self):
    settings_dict = super().to_dict()

    settings_dict['action'] = int(self._action)

    return settings_dict

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, str):
      return Gio.file_new_for_uri(raw_value)
    elif raw_value is None:
      if self._none_ok:
        return None
      else:
        return Gio.file_new_for_uri('')
    else:
      return raw_value

  def _value_to_raw(self, value):
    if value is not None:
      return value.get_uri()
    else:
      return value

  def _validate(self, file):
    if not self._none_ok and not isinstance(file, Gio.File):
      return 'invalid file', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._action,
      self._none_ok,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  @staticmethod
  def _process_action(action):
    if isinstance(action, int):
      try:
        return Gimp.FileChooserAction(action)
      except Exception:
        return action
    else:
      return action
