from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'BoolSetting',
]


class BoolSetting(_base.Setting):
  """Class for boolean settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_BOOLEAN`

  Default value: ``False``
  """

  _ALIASES = ['boolean', 'true_false', 'yes_no']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_BOOLEAN]

  _REGISTRABLE_TYPE_NAME = 'boolean'

  _ALLOWED_GUI_TYPES = [
    _SETTING_GUI_TYPES.check_button,
    _SETTING_GUI_TYPES.check_menu_item,
    _SETTING_GUI_TYPES.expander,
  ]

  _DEFAULT_DEFAULT_VALUE = False

  def _assign_value(self, value):
    self._value = bool(value)

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list) and len(raw_value) == 1:
      data = raw_value[0]

      if data == 'yes':
        return True
      elif data == 'no':
        return False
      elif data == 'true':
        return True
      elif data == 'false':
        return False
      else:
        return raw_value
    else:
      return raw_value

  def _value_to_string(self, value):
    return 'yes' if value else 'no'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._pdb_description,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]
