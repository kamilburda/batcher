from __future__ import annotations

import ast

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import utils

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'ParasiteSetting',
]


class ParasiteSetting(_base.Setting):
  """Class for settings holding `Gimp.Parasite` instances.

  Allowed GIMP PDB types:
  * `Gimp.Parasite`

  Default value: `Gimp.Parasite` instance with name equal to the setting
  name, no flags and empty data (``''``).

  Message IDs for invalid values:
  * ``'invalid_value'``: The value is not a `Gimp.Parasite` instance.
  """

  DEFAULT_PARASITE_NAME = 'parasite'
  """Default parasite name in case it is empty. The parasite name cannot be
  empty as that will lead to an error on instantiation.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Parasite]

  _REGISTRABLE_TYPE_NAME = 'parasite'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.parasite_editor]

  # Create default value dynamically to avoid potential errors on GIMP startup.
  _DEFAULT_DEFAULT_VALUE = (
    lambda self: Gimp.Parasite.new(self.name if self.name else self.DEFAULT_PARASITE_NAME, 0, b''))

  def _copy_value(self, value):
    return value

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list):
      if len(raw_value) == 3:
        try:
          return Gimp.Parasite.new(*raw_value)
        except Exception:
          return raw_value
      elif len(raw_value) == 4:
        try:
          return Gimp.Parasite.new(
            raw_value[0],
            int(raw_value[1]),
            # Assume an octal-escaped string.
            ast.literal_eval(f'b"{raw_value[3]}"'),
          )
        except Exception:
          return raw_value
    else:
      return raw_value

  def _value_to_raw(self, value):
    return [value.get_name(), value.get_flags(), value.get_data()]

  def _value_to_string(self):
    return (
      f'"{self.value.get_name()}"'
      f' {self.value.get_flags()}'
      f' {len(self.value.get_data())}'
      f' "{utils.bytes_to_octal_escaped_string(self.value.get_data())}"')

  def _validate(self, parasite):
    if not isinstance(parasite, Gimp.Parasite):
      return 'invalid parasite', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._pdb_description,
      GObject.ParamFlags.READWRITE,
    ]
