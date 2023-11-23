"""Placeholder objects replaced with real GIMP objects when calling GIMP PDB
procedures during batch processing.

The placeholder objects are defined in the `PLACEHOLDERS` dictionary.
"""

from typing import Callable, List, Union, Type

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import pygimplib as pg

from src import background_foreground
from src.gui import placeholders as gui_placeholders


class Placeholder:
  
  def __init__(self, name: str, display_name: str, replacement_func: Callable):
    self._name = name
    self._display_name = display_name
    self._replacement_func = replacement_func

  @property
  def name(self) -> str:
    return self._name
  
  @property
  def display_name(self) -> str:
    return self._display_name
  
  def replace_args(self, *args):
    return self._replacement_func(*args)


def _get_current_image(batcher):
  return batcher.current_image


def _get_current_layer(batcher):
  return batcher.current_raw_item


_PLACEHOLDERS_RAW_LIST = [
  ('current_image', _('Current Image'), _get_current_image),
  ('current_layer', _('Current Layer'), _get_current_layer),
  ('background_layer', _('Background Layer'), background_foreground.get_background_layer),
  ('foreground_layer', _('Foreground Layer'), background_foreground.get_foreground_layer),
]


PLACEHOLDERS = {args[0]: Placeholder(*args) for args in _PLACEHOLDERS_RAW_LIST}
"""Mapping of a placeholder name to a placeholder object.

The following placeholder objects are defined:

* ``PLACEHOLDERS['current_image']``: The image currently being processed.

* ``PLACEHOLDERS['current_layer']``: The layer currently being processed in the
  current image. This placeholder is used for PDB procedures containing
  `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item` parameters.

* ``PLACEHOLDERS['background_layer']``: The layer positioned immediately after
  the currently processed layer.

* ``PLACEHOLDERS['foreground_layer']``: The layer positioned immediately before
  the currently processed layer.
"""


class PlaceholderSetting(pg.setting.Setting):
   
  _ALLOWED_GUI_TYPES = [gui_placeholders.PlaceholdersComboBoxPresenter]
  _ALLOWED_PLACEHOLDERS = []

  def _get_pdb_type(self, pdb_type):
    # Avoid errors when creating placeholder settings. Placeholders cannot be
    # registered to the PDB anyway.
    return None
  
  @classmethod
  def get_allowed_placeholder_names(cls) -> List[str]:
    """Returns a list of allowed names of placeholders for this setting class.
    """
    return list(cls._ALLOWED_PLACEHOLDERS)
  
  @classmethod
  def get_allowed_placeholders(cls) -> List[Placeholder]:
    """Returns a list of allowed placeholder objects for this setting class.
    """
    return [
      placeholder for placeholder_name, placeholder in PLACEHOLDERS.items()
      if placeholder_name in cls._ALLOWED_PLACEHOLDERS]
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid placeholder.')
  
  def _validate(self, value):
    if value not in self._ALLOWED_PLACEHOLDERS:
      raise pg.setting.SettingValueError(
        pg.setting.value_to_str_prefix(value) + self.error_messages['invalid_value'])


class PlaceholderImageSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_image'
  _ALLOWED_PLACEHOLDERS = ['current_image']


class PlaceholderDrawableSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderLayerSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderItemSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


def get_replaced_arg(arg, batcher: 'src.core.Batcher'):
  """If ``arg`` is a placeholder object, returns a real object replacing the
  placeholder. Otherwise, ``arg`` is returned unchanged.

  Arguments after ``args`` are required arguments for actions and are used to
  determine the real object that replaces the placeholder.

  ``batcher`` is a `core.Batcher` instance holding necessary data for the
  placeholder replacement.
  """
  try:
    placeholder = PLACEHOLDERS[arg]
  except KeyError:
    raise ValueError(f'invalid placeholder value "{arg}"')
  else:
    return placeholder.replace_args(batcher)


def get_placeholder_type_name_from_pdb_type(
      pdb_type: Union[GObject.GType, Type[GObject.GObject]],
) -> Union[str, None]:
  """Returns the name of a `pygimplib.setting.Setting` subclass representing a
  placeholder from the given GIMP PDB parameter type.

  Args:
    pdb_type:
      A `GObject.GObject` subclass or a `GObject.GType` instance representing a
      GIMP PDB parameter.

  Returns:
    String as a human-readable name of a `pygimplib.setting.Setting` subclass
    representing a placeholder if ``pdb_type`` matches an identifier, or
    ``None`` otherwise.
  """
  gtype = pdb_type

  if hasattr(pdb_type, '__gtype__'):
    gtype = pdb_type.__gtype__

  try:
    return _PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES[gtype]
  except (KeyError, TypeError):
    return None


_PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES = {
  Gimp.Image.__gtype__: pg.setting.SETTING_TYPES[PlaceholderImageSetting],
  Gimp.Item.__gtype__: pg.setting.SETTING_TYPES[PlaceholderItemSetting],
  Gimp.Drawable.__gtype__: pg.setting.SETTING_TYPES[PlaceholderDrawableSetting],
  Gimp.Layer.__gtype__: pg.setting.SETTING_TYPES[PlaceholderLayerSetting],
}
