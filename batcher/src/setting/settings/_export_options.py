from __future__ import annotations

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from . import _base

__all__ = [
  'ExportOptionsSetting',
]


class ExportOptionsSetting(_base.Setting):
  """Class for settings holding file export options.

  Allowed GIMP PDB types:
  * `Gimp.ExportOptions`

  Message IDs for invalid values:
  * ``'invalid_value'``: The `Gimp.ExportOptions` instance is not valid.
  """

  _DEFAULT_DEFAULT_VALUE = None

  _ALLOWED_PDB_TYPES = [Gimp.ExportOptions]

  _ALLOWED_GUI_TYPES = []
