from __future__ import annotations

from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'StringSetting',
]


class StringSetting(_base.Setting):
  """Class for string settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_STRING`

  Default value: ``''``
  """

  _ALIASES = ['str']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_STRING]

  _REGISTRABLE_TYPE_NAME = 'string'

  _ALLOWED_GUI_TYPES = [
    _SETTING_GUI_TYPES.entry,
    _SETTING_GUI_TYPES.label,
  ]

  _DEFAULT_DEFAULT_VALUE = ''

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]
