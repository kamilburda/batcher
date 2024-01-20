"""Placeholder objects replaced with real GIMP objects when calling GIMP PDB
procedures during batch processing.

The placeholder objects are defined in the `PLACEHOLDERS` dictionary.
"""

from typing import Callable, List, Optional, Union, Type

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


def _get_current_image(setting, batcher):
  return batcher.current_image


def _get_current_layer(setting, batcher):
  return batcher.current_raw_item


def _get_current_layer_for_array(setting, batcher):
  return (_get_current_layer(setting, batcher),)


def _get_background_layer_for_array(setting, batcher):
  return (background_foreground.get_background_layer(batcher),)


def _get_foreground_layer_for_array(setting, batcher):
  return (background_foreground.get_foreground_layer(batcher),)


def _get_value_for_unsupported_parameter(setting, batcher):
  return getattr(setting, 'default_param_value', None)


_PLACEHOLDERS_RAW_LIST = [
  ('current_image', _('Current Image'), _get_current_image),
  ('current_layer', _('Current Layer'), _get_current_layer),
  ('current_layer_for_array', _('Current Layer'), _get_current_layer_for_array),
  ('background_layer', _('Background Layer'), background_foreground.get_background_layer),
  ('background_layer_for_array', _('Background Layer'), _get_background_layer_for_array),
  ('foreground_layer', _('Foreground Layer'), background_foreground.get_foreground_layer),
  ('foreground_layer_for_array', _('Foreground Layer'), _get_foreground_layer_for_array),
  ('unsupported_parameter', '', _get_value_for_unsupported_parameter),
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
  
  def _validate(self, value):
    if value not in self._ALLOWED_PLACEHOLDERS:
      return 'invalid placeholder', 'invalid_value'


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


class PlaceholderArraySetting(PlaceholderSetting):

  def __init__(self, name, element_type, **kwargs):
    super().__init__(name, **kwargs)

    self._element_type = pg.setting.process_setting_type(element_type)

  @property
  def element_type(self) -> Type[pg.setting.Setting]:
    return self._element_type

  def to_dict(self):
    settings_dict = super().to_dict()

    settings_dict['element_type'] = pg.setting.SETTING_TYPES[self._element_type]

    return settings_dict


class PlaceholderDrawableArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _ALLOWED_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
  ]


class PlaceholderLayerArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _ALLOWED_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
  ]


class PlaceholderItemArraySetting(PlaceholderArraySetting):

  _DEFAULT_DEFAULT_VALUE = 'current_layer_for_array'
  _ALLOWED_PLACEHOLDERS = [
    'current_layer_for_array',
    'background_layer_for_array',
    'foreground_layer_for_array',
  ]


class PlaceholderUnsupportedParameterSetting(PlaceholderSetting):

  _DEFAULT_DEFAULT_VALUE = 'unsupported_parameter'
  _ALLOWED_GUI_TYPES = [gui_placeholders.UnsupportedParameterPresenter]
  _ALLOWED_PLACEHOLDERS = [
    'unsupported_parameter',
  ]

  def __init__(self, name, default_param_value=None, **kwargs):
    self._default_param_value = default_param_value

    super().__init__(name, **kwargs)

  @property
  def default_param_value(self):
    return self._default_param_value


def get_replaced_value(setting: PlaceholderSetting, batcher: 'src.core.Batcher'):
  """Returns a valid value replacing the placeholder value.

  ``setting`` is the placeholder setting whose ``value`` property is replaced.

  ``batcher`` is a `core.Batcher` instance holding data that may be used
  depending on the subclass of ``setting``.

  `KeyError` is raised if the placeholder value is not one of the keys in
  `PLACEHOLDERS`.
  """
  try:
    placeholder = PLACEHOLDERS[setting.value]
  except KeyError:
    raise ValueError(f'invalid placeholder value "{setting.value}"')
  else:
    return placeholder.replace_args(setting, batcher)


def get_placeholder_type_name_from_pdb_type(
      pdb_type: Union[GObject.GType, Type[GObject.GObject]],
      pdb_param_info: Optional[GObject.ParamSpec] = None,
) -> Union[str, None]:
  """Returns the name of a `pygimplib.setting.Setting` subclass representing a
  placeholder from the given GIMP PDB parameter type.

  Args:
    pdb_type:
      A `GObject.GObject` subclass or a `GObject.GType` instance representing a
      GIMP PDB parameter.
    pdb_param_info:
      Object representing GIMP PDB parameter information, obtainable via
      `Gimp.Procedure.get_arguments()`. This is used to infer the element type
      for a `Gimp.ObjectArray` argument.

  Returns:
    String as a human-readable name of a `pygimplib.setting.Setting` subclass
    representing a placeholder if ``pdb_type`` matches an identifier, or
    ``None`` otherwise.
  """
  key = pdb_type

  if hasattr(pdb_type, '__gtype__'):
    key = pdb_type.__gtype__

  if key == Gimp.ObjectArray.__gtype__ and pdb_param_info is not None:
    _array_type, setting_dict = (
      pg.setting.get_array_setting_type_from_gimp_object_array(pdb_param_info))
    key = (key, setting_dict['element_type'])

  try:
    placeholder_type_name = _PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES[key]
  except (KeyError, TypeError):
    return None
  else:
    return placeholder_type_name


_PDB_TYPES_TO_PLACEHOLDER_TYPE_NAMES = {
  Gimp.Image.__gtype__: pg.setting.SETTING_TYPES[PlaceholderImageSetting],
  Gimp.Item.__gtype__: pg.setting.SETTING_TYPES[PlaceholderItemSetting],
  Gimp.Drawable.__gtype__: pg.setting.SETTING_TYPES[PlaceholderDrawableSetting],
  Gimp.Layer.__gtype__: pg.setting.SETTING_TYPES[PlaceholderLayerSetting],
  (Gimp.ObjectArray.__gtype__, pg.setting.LayerSetting): (
    pg.setting.SETTING_TYPES[PlaceholderLayerArraySetting]),
  (Gimp.ObjectArray.__gtype__, pg.setting.DrawableSetting): (
    pg.setting.SETTING_TYPES[PlaceholderDrawableArraySetting]),
  (Gimp.ObjectArray.__gtype__, pg.setting.ItemSetting): (
    pg.setting.SETTING_TYPES[PlaceholderItemArraySetting]),
}
