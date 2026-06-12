from __future__ import annotations

import ast

from gi.repository import GLib
from gi.repository import GObject

from src import utils

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'BytesSetting',
]


class BytesSetting(_base.Setting):
  """Class for settings storing byte sequences as `GLib.Bytes` (``GBytes``)
  instances.

  Allowed GIMP PDB types:
  * `GLib.Bytes`

  Default value:
    An empty `GLib.Bytes` instance (`GLib.Bytes.get_data()` returns ``None``).
  """

  _DEFAULT_DEFAULT_VALUE = GLib.Bytes.new()

  _ALLOWED_PDB_TYPES = [GLib.Bytes]

  _REGISTRABLE_TYPE_NAME = 'bytes'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.g_bytes_entry]

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, str):
      return GLib.Bytes.new(utils.escaped_string_to_bytes(raw_value, remove_overflow=True))
    elif isinstance(raw_value, bytes):
      return GLib.Bytes.new(raw_value)
    elif isinstance(raw_value, list):
      try:
        # Assume a list of valid integers.
        return GLib.Bytes.new(raw_value)
      except (TypeError, ValueError, OverflowError):
        if len(raw_value) == 2 and isinstance(raw_value[1], str):
          try:
            # Assume `raw_value` to be a list of
            # [length as string, octal-escaped string].
            return GLib.Bytes.new(ast.literal_eval(f'b"{raw_value[1]}"'))
          except Exception:
            return GLib.Bytes.new()
        else:
          return GLib.Bytes.new()
    else:
      return raw_value

  def _value_to_raw(self, value):
    return list(value.get_data())

  def _validate(self, file):
    if not isinstance(file, GLib.Bytes):
      return 'invalid byte sequence', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._pdb_description,
      GObject.ParamFlags.READWRITE,
    ]
