"""API to create and manage plug-in settings."""

from collections.abc import Iterable
import copy
import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Union, Tuple, Type

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
from gi.repository import GObject

from .. import path as pgpath
from .. import pdbutils as pgpdbutils
from .. import utils as pgutils

from . import meta as meta_
from . import persistor as persistor_
from . import presenter as presenter_
# Despite being unused, `presenters_gtk` must be imported so that the GUI
# classes defined there are properly registered and `SettingGuiTypes` is filled.
# noinspection PyUnresolvedReferences
from . import presenters_gtk
from . import utils as utils_


SettingTypes = meta_.SettingTypes
"""Class whose attributes are mapped to `setting.Setting` subclasses.

The attribute names are a more human-readable alternative to `setting.Setting`
subclass names and are used as strings when saving or loading setting data from
a persistent source.
"""

SettingGuiTypes = meta_.SettingGuiTypes
"""Class whose attributes are mapped to `setting.Presenter` subclasses.

The attribute names are a more human-readable alternative to `setting.Presenter`
subclass names and are used as strings when saving or loading setting data from
a persistent source.
"""


# FIXME: Rework this
PDB_TYPES_TO_SETTING_TYPES_MAP = {
  # gimpenums.PDB_INT32: 'int',
  # gimpenums.PDB_INT16: 'int',
  # gimpenums.PDB_INT8: 'int',
  # gimpenums.PDB_FLOAT: 'float',
  # gimpenums.PDB_STRING: 'string',
  #
  # gimpenums.PDB_IMAGE: 'image',
  # gimpenums.PDB_ITEM: 'item',
  # gimpenums.PDB_DRAWABLE: 'drawable',
  # gimpenums.PDB_LAYER: 'layer',
  # gimpenums.PDB_CHANNEL: 'channel',
  # gimpenums.PDB_SELECTION: 'selection',
  # gimpenums.PDB_VECTORS: 'vectors',
  #
  # gimpenums.PDB_COLOR: 'color',
  # gimpenums.PDB_PARASITE: 'parasite',
  # gimpenums.PDB_DISPLAY: 'display',
  #
  # gimpenums.PDB_INT32ARRAY: {'type': 'array', 'element_type': 'int'},
  # gimpenums.PDB_INT16ARRAY: {'type': 'array', 'element_type': 'int'},
  # gimpenums.PDB_INT8ARRAY: {'type': 'array', 'element_type': 'int'},
  # gimpenums.PDB_FLOATARRAY: {'type': 'array', 'element_type': 'float'},
  # gimpenums.PDB_STRINGARRAY: {'type': 'array', 'element_type': 'string'},
  # gimpenums.PDB_COLORARRAY: {'type': 'array', 'element_type': 'color'},
}


class Setting(utils_.SettingParentMixin, utils_.SettingEventsMixin, metaclass=meta_.SettingMeta):
  """Abstract class representing a plug-in setting.
  
  A `Setting` allows you to:
  * store and use setting values as variables,
  * create and manage a GUI widget tied to the setting value,
  * load and save settings,
  * connect event handlers in your application code when a specific condition is
    met (e.g. the setting value is changed, the setting is reset, loaded,
    saved).

  Use an appropriate subclass of `Setting` for a particular data type. Most
  subclasses offer the following additional features:
  * the ability to register the setting to the GIMP procedural database (PDB) as
    a plug-in parameter,
  * automatic validation of input values,
  * a readily available GUI widget, keeping the GUI and the setting value in
    sync.
  
  To support saving setting values to a setting source (e.g. to a file),
  the `to_dict()` method must return a dictionary whose keys are always
  strings and values are one of the following types: ``int``, ``float``,
  ``bool``, ``str``, ``list``, ``dict`` or ``None``. Container types -
  ``list`` and ``dict`` - can contain nested lists or dictionaries. While
  persisting plug-in settings is available in GIMP, you can easily store a
  hierarchy of settings (grouped under `setting.Group` instances).
  
  When calling `Setting.load()`, `set_value()` is called to override the `value`
  attribute with the value from the setting source. Other attributes, if they
  exist in the source for this setting, are ignored.
  
  `Setting.set_value()` must accept one of the types acceptable in `to_dict()`,
  in addition to a type supported by a particular subclass. For example,
  `ImageSetting.set_value()` must support passing a string (representing the
  image file path) or an ID (assigned by GIMP) beside a `Gimp.Image` instance.

  The `GenericSetting` class can store a value of an arbitrary type. Use this
  subclass sparingly as it lacks the additional features available for other
  `Setting` subclasses mentioned above.
  
  Settings can contain event handlers that are triggered when a setting property
  changes, e.g. `value` (when `set_value()` is called). This way, for example,
  other settings can be updated automatically according to the new value of the
  modified setting.

  The following specific event types are invoked for settings:
  * ``'value-changed'``: invoked after `set_value()` or `reset()` is called
    and before events of type ``'after-set-value'`` or ``'after-reset'``.

  * ``'before-set-value'``: invoked before `set_value()` is called.

  * ``'after-set-value'``: invoked after `set_value()` is called.

  * ``'before-reset'``: invoked before `reset()` is called.

  * ``'after-reset'``: invoked after `reset()` is called.

  * ``'before-set-gui'``: invoked before `set_gui()` is called.

  * ``'after-set-gui'``: invoked after `set_gui()` is called.

  * ``'before-load'``: invoked before loading a setting via `Setting.load()`
    or `Group.load()` if the setting is within a group.

  * ``'after-load'``: invoked after loading a setting via `Setting.load()` or
    `Group.load()` if the setting is within a group.

  * ``'before-save'``: invoked before saving a setting via `Setting.save()` or
    `Group.save()` if the setting is within a group.

  * ``'after-save'``: invoked after saving a setting via `Setting.save()` or
    `Group.save()` if the setting is within a group.
  
  If a setting subclass supports "empty" values, such values will not be
  considered invalid when used as default values. However, empty values will be
  treated as invalid when assigning one of such values to the setting after
  instantiation. Examples of empty values include "Choose an item" for
  `ChoiceSetting` instances. Empty values are useful when users must choose a
  different value, yet no valid value is a good candidate for a default value.
  
  If you need to create a custom `Setting` subclass and your plug-in is
  composed of multiple modules, you must ensure that the module where your
  subclass is defined is imported (i.e. the module is kept in the memory).
  Otherwise, the subclass will not be recognized as a valid setting type.
  """
  
  DEFAULT_VALUE = type('DefaultValue', (), {})()
  
  _ABSTRACT = True
  
  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = []

  _DEFAULT_DEFAULT_VALUE = None

  _EMPTY_VALUES = []
  
  def __init__(
        self,
        name: str,
        default_value=DEFAULT_VALUE,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        pdb_type: Union[
          GObject.GObject, Type[GObject.GObject], GObject.GType, str, None,
        ] = 'automatic',
        gui_type: Union[Type[presenter_.Presenter], str, None] = 'automatic',
        allow_empty_values: bool = False,
        auto_update_gui_to_setting: bool = True,
        setting_sources: Union[Dict, List, None] = None,
        error_messages: Optional[Dict[Any, str]] = None,
        tags: Optional[Iterable[str]] = None,
  ):
    """Initializes a new setting.
    
    Args:
      name:
        Setting name. See the `name` property for more information.
      default_value:
        Default setting value. During instantiation, the default value is
        validated. If one of the so-called "empty values" (specific to each
        setting class) is passed as the default value, default value validation
        is not performed. If omitted, a subclass-specific default value is
        assigned.
      display_name:
        See the `display_name` property.
      description:
        See the `description` property.
      pdb_type:
        A `GObject.GType` instance (e.g. `GObject.TYPE_INT` representing
        integers), an instance or subclass of `GObject.GObject` (e.g.
        `Gimp.Image`), a string as the name of a GObject type (e.g.
        ``'gint'``, ``'GimpImage'``), ``None`` or ``'automatic'``. If set to
        ``'automatic'``, the first GIMP PDB type in the list of allowed PDB
        types for a particular `Setting` subclass is chosen. If no allowed
        PDB types are defined for that subclass, the setting cannot be
        registered as a PDB parameter ( ``None`` is assigned).
      gui_type:
        Type of GUI widget to be created by `set_gui()`. Each subclass allows
        only specific GUI types. The list of accepted GUI types per subclass
        can be obtained by calling `get_allowed_gui_types()`. Specifying an
        invalid type causes `ValueError` to be raised.

        If ``gui_type`` is ``'automatic'`` (the default), the first GUI type is
        chosen from `get_allowed_gui_types()`. If there are no allowed GUI
        types for that subclass, no widget is created for this setting.

        If ``gui_type`` is ``None``, no widget is created for this setting.
      allow_empty_values:
        If ``False`` and an empty value is passed to `set_value()`, then the
        value is considered invalid. Otherwise, the value is considered valid.
      auto_update_gui_to_setting:
        If ``True``, the setting value is automatically updated if the GUI
        value is updated. If ``False``, the setting must be updated manually by
        calling `Setting.gui.update_setting_value()` when needed.

        This parameter does not have any effect if the GUI type used in
        this setting cannot provide automatic GUI-to-setting update.
      setting_sources:
        See the `setting_sources` property.
      error_messages:
        A dictionary containing (message name, message contents) pairs. Use
        this to pass custom error messages. This way, you may also override
        default error messages defined in classes.
      tags:
        An iterable container (list, set, etc.) of arbitrary strings attached to
        the setting. Tags can be used to e.g. iterate over a specific subset of
        settings.
    """
    utils_.SettingParentMixin.__init__(self)
    utils_.SettingEventsMixin.__init__(self)
    
    utils_.check_setting_name(name)
    self._name = name
    
    self._default_value = self._resolve_default_value(default_value)
    
    self._value = self._copy_value(self._default_value)
    
    self._allow_empty_values = allow_empty_values
    self._empty_values = list(self._EMPTY_VALUES)
    
    self._display_name = utils_.get_processed_display_name(display_name, self._name)
    self._description = utils_.get_processed_description(description, self._display_name)
    
    self._pdb_type = self._get_pdb_type(pdb_type)
    self._pdb_name = utils_.get_pdb_name(self._name)
    
    self._setting_sources = setting_sources
    
    self._setting_value_synchronizer = presenter_.SettingValueSynchronizer()
    self._setting_value_synchronizer.apply_gui_value_to_setting = self._apply_gui_value_to_setting
    
    self._gui_type = self._get_gui_type(gui_type)
    self._gui = presenter_.NullPresenter(
      self,
      None,
      self._setting_value_synchronizer,
      auto_update_gui_to_setting=auto_update_gui_to_setting)
    
    self._error_messages = {}
    self._init_error_messages()
    if error_messages is not None:
      self._error_messages.update(error_messages)
    
    self._tags = set(tags) if tags is not None else set()
    
    if self._should_validate_default_value():
      self._validate_default_value()
  
  @property
  def name(self) -> str:
    """A string that identifies the setting.
    
    The name must be unique within a `setting.Group` instance.
    """
    return self._name
  
  @property
  def value(self):
    """The setting value.
    
    To modify the value, call `set_value()`.
    
    `value` is initially set to the `default_value` property.
    """
    return self._value
  
  @property
  def default_value(self):
    """Initial setting value or value assigned after calling `reset()`.
    
    If not specified or if `DEFAULT_VALUE` is passed explicitly on `__init__()`,
    a default value is assigned automatically. The default value depends on the
    particular setting subclass (defaulting to ``None`` if a subclass does
    not specify it). Note that it is still a good practice to specify default
    values explicitly when creating a setting.
    """
    return self._default_value
  
  @property
  def gui(self) -> presenter_.Presenter:
    """The setting GUI widget.
    
    This is a `setting.Presenter` instance wrapping a native widget.
    
    With `gui`, you may modify GUI-specific attributes such as visibility or
    sensitivity using a unified interface. You can also access the native GUI
    widget via ``gui.widget``.
    """
    return self._gui
  
  @property
  def display_name(self) -> str:
    """Setting name in a human-readable format. Useful e.g. as GUI labels or
    menu items.
    """
    return self._display_name
  
  @property
  def description(self) -> str:
    """Setting description.
    
    This is usually `display_name` plus additional information in parentheses
    (such as boundaries for numeric values).
    
    You may use this when registering the setting as a plug-in parameter to the
    GIMP Procedural Database (PDB) as description.
    
    If `display_name` contains underscores and a `Setting` subclass uses
    `display_name` to generate the description, the underscores are removed.
    """
    return self._description
  
  @property
  def pdb_type(self) -> Union[GObject.GType, None]:
    """GIMP PDB parameter type.
    
    Use this property when registering the setting as a plug-in parameter to the
    GIMP PDB.
    
    In `Setting` subclasses, only specific PDB types are allowed. Refer to the
    documentation of the subclasses for the list of allowed PDB types.
    """
    return self._pdb_type
  
  @property
  def pdb_name(self) -> str:
    """Setting name as it appears in the GIMP PDB as a PDB parameter name."""
    return self._pdb_name
  
  @property
  def setting_sources(self) -> Union[Dict, List, None]:
    """Groups of setting sources to use when loading or saving the setting.
    
    If ``None``, default settings sources as returned by
    `setting.persistor.Persistor.get_default_setting_sources()` are used.
    """
    return self._setting_sources
  
  @property
  def error_messages(self) -> Dict[Any, str]:
    """A dictionary of error messages.
    
    The dictionary contains (message name, message contents) pairs which can
    be used e.g. if a value assigned to the setting is not valid. You can add
    your own error messages and assign them to one of the "default" error
    messages (such as ``'invalid_value'`` in several `Setting` subclasses)
    depending on the context in which the value assigned is invalid.
    """
    return self._error_messages
  
  @property
  def tags(self) -> Set[str]:
    """A mutable set of arbitrary tags attached to the setting.
    
    Tags can be used to e.g. iterate over a specific subset of settings.
    
    Some classes in the `setting` package may exploit specific tag names to
    skip settings. For example, if you call `setting.Group.reset()` and
    `tags` contains ``'ignore_reset'``, then the setting will not be reset.
    Specific tags and their effect are documented in the corresponding
    methods in the `setting` package.
    """
    return self._tags
  
  @classmethod
  def get_allowed_pdb_types(cls) -> List:
    """Returns the list of allowed PDB types for this setting type."""
    return list(cls._ALLOWED_PDB_TYPES)
  
  @classmethod
  def get_allowed_gui_types(cls) -> List[Type[presenter_.Presenter]]:
    """Returns the list of allowed GUI types for this setting type."""
    return [process_setting_gui_type(type_or_name) for type_or_name in cls._ALLOWED_GUI_TYPES]
  
  def __str__(self) -> str:
    return pgutils.stringify_object(self, self.name)
  
  def __repr__(self) -> str:
    return pgutils.reprify_object(self, self.name)
  
  def get_path(self, relative_path_group: Union['setting.Group', str, None] = None) -> str:
    """Returns the full path of this setting.

    This is a wrapper method for `setting.utils.get_setting_path()`. Consult
    the method for more information.
    """
    return utils_.get_setting_path(self, relative_path_group)
  
  def set_value(self, value):
    """Sets the setting value.
    
    Before the assignment, the value is validated. If the value is invalid,
    `SettingValueError` is raised.
    
    The value of the GUI widget is also updated. Even if the setting has no
    widget assigned, the value is recorded. Once a widget is assigned to
    the setting, the recorded value is copied over to the widget.
    
    The following event handlers are invoked:
    * ``'before-set-value'``: before assigning the value,
    * ``'value-changed'`` and ``'after-set-value'`` (in this order): after
      assigning the value.
    
    Note: This is a method and not a property because of the additional overhead
    introduced by validation, GUI updating and event handling. `value` still
    remains a property for the sake of brevity.
    """
    self.invoke_event('before-set-value')
    
    value = self._raw_to_value(value)
    
    self._validate_and_assign_value(value)
    self._setting_value_synchronizer.apply_setting_value_to_gui(value)
    
    self.invoke_event('value-changed')
    self.invoke_event('after-set-value')
  
  def reset(self):
    """Resets setting value to its default value.
    
    This is different from
    
      setting.set_value(setting.default_value)
    
    in that `reset()` does not validate the default value.
    
    The following event handlers are invoked:
    * ``'before-reset'``: before resetting,
    * ``'value-changed'`` and ``'after-reset'`` (in this order): after
      resetting.
    
    `reset()` also updates the setting's GUI widget.
    
    If the default value is an empty container (list, dict, ...), resetting
    works properly. If the default value is a non-empty container, it is the
    responsibility of the caller to ensure that the default value does not get
    modified, for example by connecting a ``'before-reset'`` event that sets the
    value to the correct default value before resetting.
    """
    self.invoke_event('before-reset')
    
    self._value = self._copy_value(self._default_value)
    self._setting_value_synchronizer.apply_setting_value_to_gui(self._value)
    
    self.invoke_event('value-changed')
    self.invoke_event('after-reset')
  
  def apply_to_gui(self):
    """Manually applies the current setting value to the setting's GUI widget.
    """
    self._setting_value_synchronizer.apply_setting_value_to_gui(self._value)
  
  def set_gui(
        self,
        gui_type: Union[Type[presenter_.Presenter], str, None] = 'automatic',
        widget=None,
        auto_update_gui_to_setting: bool = True,
  ):
    """Creates a new `setting.Presenter` instance (holding a GUI widget) for
    this setting or removes the GUI.
    
    The state of the previous GUI object is copied to the new GUI object (such
    as its value, visibility and sensitivity).
    
    Args:
      gui_type:
        `setting.Presenter` type to wrap ``widget`` in.

        When calling this method, ``gui_type`` does not have to be one of the
        allowed GUI types specified in the setting.

        If ``gui_type`` is ``'automatic'``, a GUI object of the type specified
        in the `gui_type` parameter in `__init__()` is created.

        To specify an existing GUI widget, pass a specific ``gui_type`` and the
        widget in ``widget``. This is useful if you wish to use the GUI widget
        for multiple settings or for other purposes outside this setting.

        If ``gui_type`` is ``None``, the GUI is removed and any events the
        GUI had are disconnected. The state of the old GUI is still preserved.
      widget:
        A native GUI widget.

        If ``gui_type`` is ``'automatic'``, ``widget`` is ignored.
        If ``gui_type`` is not ``'automatic'`` and ``widget`` is ``None``,
        `ValueError` is raised.
      auto_update_gui_to_setting:
        See the ``auto_update_gui_to_setting`` parameter in `__init__()`.
    """
    if gui_type != 'automatic' and widget is None:
      raise ValueError('widget cannot be None if gui_type is "automatic"')
    if gui_type == 'automatic' and widget is not None:
      raise ValueError('gui_type cannot be "automatic" if widget is not None')
    
    self.invoke_event('before-set-gui')
    
    if gui_type == 'automatic':
      processed_gui_type = self._gui_type
    elif gui_type is None:
      processed_gui_type = presenter_.NullPresenter
      # We need to disconnect the "GUI changed" event before removing the GUI.
      self._gui.auto_update_gui_to_setting(False)
    else:
      processed_gui_type = process_setting_gui_type(gui_type)
    
    self._gui = processed_gui_type(
      self,
      widget,
      setting_value_synchronizer=self._setting_value_synchronizer,
      old_presenter=self._gui,
      auto_update_gui_to_setting=auto_update_gui_to_setting)
    
    self.invoke_event('after-set-gui')
  
  def load(self, *args, **kwargs) -> persistor_.PersistorResult:
    """Loads a value for the current setting from the specified setting
    source(s).
    
    See `setting.Persistor.load()` for information on parameters.
    
    If the `tags` property contains ``'ignore_load'``, this method will have no
    effect.
    """
    return persistor_.Persistor.load([self], *args, **kwargs)
  
  def save(self, *args, **kwargs) -> persistor_.PersistorResult:
    """Saves the current setting value to the specified setting source(s).
    
    See `setting.Persistor.save()` for information on parameters.

    If the `tags` property contains ``'ignore_save'``, this method will have no
    effect.
    """
    return persistor_.Persistor.save([self], *args, **kwargs)
  
  def is_value_empty(self) -> bool:
    """Returns ``True`` if the setting value is one of the empty values defined
    for the setting class, ``False`` otherwise.
    """
    return self._is_value_empty(self._value)
  
  def can_be_registered_to_pdb(self) -> bool:
    """Returns ``True`` if the setting can be registered as a GIMP PDB
    parameter, ``False`` otherwise.

    This method returns ``True`` if the `pdb_type` property is not ``None``,
    i.e. the setting has a valid PDB type assigned.
    """
    return self._pdb_type is not None
  
  def get_pdb_param(self) -> Union[List[Dict[str, Any]], None]:
    """Returns a list of dictionaries representing GIMP PDB parameters for the
    setting.

    The dictionary can be passed as keyword arguments when creating a
    `GObject.Property` instance used for registering PDB parameters for a
    GIMP plug-in.

    Most `Setting` subclasses return a list of only one dictionary, meaning the
    setting is represented by one PDB parameter. Most notably, `ArraySetting`
    returns two parameters, the first being the array length and the other being
    the array contents.
    
    If the setting does not support any PDB type, ``None`` is returned.
    """
    if self.can_be_registered_to_pdb():
      return [
        dict(
          name=self.pdb_name,
          type=self.pdb_type,
          default=self.default_value,
          nick=self.display_name,
          blurb=self.description,
        )]
    else:
      return None
  
  def to_dict(self, source_type: str = 'persistent') -> Dict:
    """Returns a dictionary representing the setting, appropriate for saving the
    setting (e.g. via `Setting.save()`).
    
    The dictionary contains (attribute name, attribute value) pairs.
    Specifically, the dictionary contains:
    * ``name`` - the `name` property,
    * ``value`` - the `value` property,
    * ``type`` - a stringified, human-readable name of the `Setting` subclass,
    * all keyword argument names and values passed to `__init__()` that were
      used to instantiate the setting.
    
    The dictionary can only contain keys as strings and values of one of the
    following types: ``int``, ``float``, ``bool``, ``str``, ``list``,
    ``dict``, ``None``.
    
    A `Setting` subclass may return different values for the same setting
    attributes depending on the value of ``source_type``. If a subclass
    utilizes ``source_type``, it is mentioned in the subclass' documentation.
    """
    settings_dict = {}
    
    for key, val in self._dict_on_init.items():
      if key == 'gui_type' and val is not None and not isinstance(val, str):
        try:
          gui_type_name = SettingGuiTypes[val]
        except TypeError:
          raise TypeError(
            (f'"gui_type" does not have a valid value: "{val}";'
             ' the value must be one of the setting.Presenter classes'))
        
        settings_dict['gui_type'] = gui_type_name
      elif key == 'pdb_type':
        if isinstance(val, GObject.GType):
          settings_dict['pdb_type'] = val.name
        elif hasattr(val, '__gtype__'):
          settings_dict['pdb_type'] = val.__gtype__.name
        elif isinstance(val, str) or val is None:
          settings_dict['pdb_type'] = val
        else:
          raise TypeError(f'"pdb_type" does not have a valid value: "{val}"')
      elif key == 'default_value':
        settings_dict[key] = self._value_to_raw(val, source_type)
      elif key == 'tags':
        settings_dict[key] = list(val)
      else:
        settings_dict[key] = val
    
    settings_dict.update({
      'name': self.name,
      'value': self._value_to_raw(self.value, source_type),
      'type': SettingTypes[type(self)],
    })
    
    return settings_dict
  
  def _validate(self, value):
    """Checks whether the specified value is valid. If the value is not valid,
    `SettingValueError` is raised.
    """
    pass
  
  def _init_error_messages(self):
    """Initializes custom error messages in the `error_messages` property."""
    pass
  
  def _copy_value(self, value):
    """Creates a shallow copy of the specified value.
    
    By default, iterables (except strings) are copied, otherwise the original
    objects are returned.
    
    Override this method in case copying must be handled differently.
    """
    if isinstance(value, Iterable) and not isinstance(value, str):
      return copy.copy(value)
    else:
      return value
  
  def _assign_value(self, value):
    """Assigns specified value to the `_value` attribute after validation.
    
    Override this method in subclasses if other modifications to the `_value`
    attribute must be made other than mere assignment.
    """
    self._value = value
  
  def _is_value_empty(self, value):
    return value in self._empty_values
  
  def _raw_to_value(self, raw_value):
    """Converts the given value to a type or format compatible with a particular
    `Setting` subclass.
    
    The converted value is returned, or the original value if no conversion is
    necessary.
    
    This method is called:
    * in `set_value()` before `_validate_and_assign_value()` (applied to
      `value`),
    * during `__init__()` when the method is applied to `default_value`.
    """
    return raw_value
  
  def _value_to_raw(self, value, source_type):
    """Converts the given value to a value that can be saved.
    
    The converted value is returned, or the original value if no conversion is
    necessary.
    
    This method is called in `to_dict()` and is applied on the `value` and
    `default_value` properties.
    
    ``source_type`` is the setting source type passed to `to_dict()`. This
    parameter may be used to convert the input value to a different format
    depending on its value.
    """
    return value
  
  def _validate_and_assign_value(self, value):
    if not self._allow_empty_values:
      self._validate_setting(value)
    else:
      if not self._is_value_empty(value):
        self._validate_setting(value)
    
    self._assign_value(value)
  
  def _apply_gui_value_to_setting(self, value):
    self._validate_and_assign_value(value)
    self.invoke_event('value-changed')
  
  def _validate_setting(self, value):
    try:
      self._validate(value)
    except SettingValueError as e:
      raise SettingValueError(str(e), setting=self)
  
  def _should_validate_default_value(self):
    return not self._is_value_empty(self._default_value)
  
  def _validate_default_value(self):
    """Checks whether the default value of the setting is valid. If the default
    value is invalid, `SettingValueError` is raised.
    """
    try:
      self._validate(self._default_value)
    except SettingValueError as e:
      raise SettingDefaultValueError(str(e), setting=self)
  
  def _resolve_default_value(self, default_value):
    if isinstance(default_value, type(self.DEFAULT_VALUE)):
      if not callable(self._DEFAULT_DEFAULT_VALUE):
        default_default_value = self._DEFAULT_DEFAULT_VALUE
      else:
        default_default_value = self._DEFAULT_DEFAULT_VALUE()

      # This ensures that the `DEFAULT_VALUE` object is not included in
      # `to_dict()` to avoid errors when persisting the setting.
      if 'default_value' in self._dict_on_init:
        self._dict_on_init['default_value'] = default_default_value
      
      return default_default_value
    else:
      return self._raw_to_value(default_value)
  
  def _get_pdb_type(self, pdb_type):
    if isinstance(pdb_type, str) and pdb_type != 'automatic':
      try:
        processed_pdb_type = GObject.GType.from_name(pdb_type)
      except RuntimeError:
        processed_pdb_type = None
    else:
      processed_pdb_type = pdb_type

    if processed_pdb_type == 'automatic':
      return self._get_default_pdb_type()
    elif processed_pdb_type is None:
      return None
    elif processed_pdb_type in self._ALLOWED_PDB_TYPES:
      return processed_pdb_type
    else:
      raise ValueError(
        (f'GIMP PDB type "{pdb_type}" not allowed;'
         f' must be "automatic" or one of {self._ALLOWED_PDB_TYPES}'))
  
  def _get_default_pdb_type(self):
    if self._ALLOWED_PDB_TYPES:
      return self._ALLOWED_PDB_TYPES[0]
    else:
      return None
  
  def _get_gui_type(self, gui_type):
    gui_type_to_return = None
    
    if gui_type is None:
      gui_type_to_return = presenter_.NullPresenter
    else:
      allowed_gui_types = self.get_allowed_gui_types()
      
      if gui_type == 'automatic':
        if allowed_gui_types:
          gui_type_to_return = allowed_gui_types[0]
        else:
          gui_type_to_return = presenter_.NullPresenter
      else:
        processed_gui_type = process_setting_gui_type(gui_type)
        
        if processed_gui_type in allowed_gui_types:
          gui_type_to_return = processed_gui_type
        elif processed_gui_type == presenter_.NullPresenter:
          gui_type_to_return = processed_gui_type
        else:
          raise ValueError(
            (f'{self.name}: invalid GUI type "{processed_gui_type}";'
             f' must be one of {allowed_gui_types}'))
    
    return gui_type_to_return


class GenericSetting(Setting):
  """Class for settings storing arbitrary data.
  
  Since there are limitations on the types of values that can be saved to a
  setting source (see the description for `Setting` for the supported types),
  it is strongly recommended that you provide ``value_set`` and
  ``value_save`` parameters to `GenericSetting.__init__()`. The functions
  must ensure the setting value will be loaded and saved properly. If
  ``value_save`` is ``None``, the value is converted to a string via `repr()`
  as fallback. Such a string will very likely not be usable in your
  application when loading the setting.
  """
  
  def __init__(
        self,
        name: str,
        value_set: Optional[Callable] = None,
        value_save: Optional[Callable] = None,
        **kwargs,
  ):
    """Initializes a `GenericSetting` instance.

    Args:
      value_set:
        Function invoked at the beginning of `set_value()`. The function
        allows converting values of other types or formats, particularly when
        loading value for this setting from a source that allows storing only
        several value types. The function accepts one or two positional
        parameters - the input value and this setting instance (the latter
        can be omitted if not needed).
      value_save:
        Function invoked at the beginning of `to_dict()`. The function should
        ensure that the setting value is converted to a type supported by
        setting sources. The function accepts one or two positional
        parameters - the current setting value and this setting instance (the
        latter can be omitted if not needed).
    """
    self._before_value_set = value_set
    self._before_value_save = value_save
    
    self._validate_function(self._before_value_set, 'value_set')
    self._validate_function(self._before_value_save, 'value_save')
    
    super().__init__(name, **kwargs)
  
  def to_dict(self, *args, **kwargs):
    settings_dict = super().to_dict(*args, **kwargs)
    
    settings_dict.pop('value_set', None)
    settings_dict.pop('value_save', None)
    
    return settings_dict
  
  def _raw_to_value(self, raw_value):
    value = raw_value
    
    if self._before_value_set is not None:
      if len(inspect.getfullargspec(self._before_value_set).args) == 1:
        value = self._before_value_set(raw_value)
      else:
        value = self._before_value_set(raw_value, self)
    
    return value
  
  def _value_to_raw(self, value, source_type):
    raw_value = value
    
    if self._before_value_save is not None:
      if len(inspect.getfullargspec(self._before_value_save).args) == 1:
        raw_value = self._before_value_save(value)
      else:
        raw_value = self._before_value_save(value, self)
    else:
      raw_value = repr(value)
    
    return raw_value
  
  def _validate_function(self, func, name):
    if func is None:
      return
    
    if not callable(func):
      raise TypeError(f'{name} must be callable')
    
    if len(inspect.getfullargspec(func).args) not in [1, 2]:
      raise TypeError(f'{name} function must have 1 or 2 positional parameters')


class NumericSetting(Setting):
  """Abstract class for numeric settings - integers and floats.
  
  When assigning a value, this class checks for the upper and lower bounds if
  they are set.
  
  Raises:
    SettingValueError:
      Raised if one of the following conditions is met:

        * the `min_value` property is not ``None`` and the value assigned is
          less than `min_value`,

        * the `pdb_min_value` property is not ``None`` and the value assigned is
          less than `pdb_min_value`,

        * the `max_value` property is not ``None`` and the value assigned is
          greater than `max_value`,

        * the `pdb_max_value` property is not ``None`` and the value assigned is
          greater than `pdb_max_value`.
  
  Error messages:
    * ``'below_min'``: The value assigned is less than `min_value`.
    * ``'below_pdb_min'``: The value assigned is less than `pdb_min_value`.
    * ``'above_max'``: The value assigned is greater than `max_value`.
    * ``'above_pdb_max'``: The value assigned is greater than `pdb_max_value`.
  """
  
  _ABSTRACT = True

  _PDB_TYPES_AND_MINIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MININT,
    GObject.TYPE_UINT: 0,
    GObject.TYPE_INT64: GLib.MININT64,
    GObject.TYPE_UINT64: 0,
    GObject.TYPE_LONG: GLib.MINLONG,
    GObject.TYPE_ULONG: 0,
    GObject.TYPE_DOUBLE: -GLib.MAXDOUBLE,
    GObject.TYPE_FLOAT: -GLib.MAXFLOAT,
  }
  """Mapping of PDB types to minimum values allowed for each type.
  
  For example, the minimum value allowed for type `GObject.TYPE_INT` would be
  `GLib.MININT`.
  """

  _PDB_TYPES_AND_MAXIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MAXINT,
    GObject.TYPE_UINT: GLib.MAXUINT,
    GObject.TYPE_INT64: GLib.MAXINT64,
    GObject.TYPE_UINT64: GLib.MAXUINT64,
    GObject.TYPE_LONG: GLib.MAXLONG,
    GObject.TYPE_ULONG: GLib.MAXULONG,
    GObject.TYPE_DOUBLE: GLib.MAXDOUBLE,
    GObject.TYPE_FLOAT: GLib.MAXFLOAT,
  }
  """Mapping of PDB types to maximum values allowed for each type.
  
  For example, the maximum value allowed for type `GObject.TYPE_INT` would be
  `GLib.MAXINT`.
  """
  
  def __init__(self, name: str, min_value=None, max_value=None, **kwargs):
    self._min_value = min_value
    self._max_value = max_value

    # We need to define these attributes before the parent's `__init__()` as
    # some methods require these attributes to be defined during `__init__()`.
    pdb_type = super()._get_pdb_type(
      kwargs.get('pdb_type', inspect.signature(Setting.__init__).parameters['pdb_type'].default))
    self._pdb_min_value = self._PDB_TYPES_AND_MINIMUM_VALUES.get(pdb_type, None)
    self._pdb_max_value = self._PDB_TYPES_AND_MAXIMUM_VALUES.get(pdb_type, None)

    self._check_min_and_max_values_against_pdb_min_and_max_values()

    super().__init__(name, **kwargs)
  
  @property
  def min_value(self) -> Union[int, float, None]:
    """Minimum allowed numeric value.
    
    If ``None``, no checks for a minimum value are performed.
    """
    return self._min_value
  
  @property
  def max_value(self) -> Union[int, float, None]:
    """Maximum allowed numeric value.
    
    If ``None``, no checks for a maximum value are performed.
    """
    return self._max_value

  @property
  def pdb_min_value(self) -> Union[int, float, None]:
    """Minimum numeric value as allowed by the `pdb_type`.

    This property represents the lowest possible value this setting can have
    given the `pdb_type`. `min_value` thus cannot be lower than this value.

    If ``None``, no checks for a minimum value are performed.
    """
    return self._pdb_min_value

  @property
  def pdb_max_value(self) -> Union[int, float, None]:
    """Maximum numeric value as allowed by the `pdb_type`.

    This property represents the highest possible value this setting can have
    given the `pdb_type`. `max_value` thus cannot be greater than this value.

    If ``None``, no checks for a maximum value are performed.
    """
    return self._pdb_max_value

  def get_pdb_param(self) -> Union[List[Dict[str, Any]], None]:
    """Returns a list of dictionaries representing GIMP PDB parameters for the
    setting.

    In addition to items provided by `Setting.get_pdb_param()`, this method adds
    ``'minimum'`` and ``'maximum'`` if the `min_value` and `max_value` property
    is not ``None``, respectively.
    """
    pdb_params = super().get_pdb_param()

    if pdb_params is not None:
      if self.min_value is not None:
        pdb_params[0]['minimum'] = self.min_value

      if self.max_value is not None:
        pdb_params[0]['maximum'] = self.max_value

      return pdb_params
    else:
      return None

  def _init_error_messages(self):
    self.error_messages['below_min'] = (
      _('Value cannot be less than {}.').format(self.min_value))

    self.error_messages['below_pdb_min'] = (
      _('Value cannot be less than {}.').format(self.pdb_min_value))

    self.error_messages['above_max'] = (
      _('Value cannot be greater than {}.').format(self.max_value))

    self.error_messages['above_pdb_max'] = (
      _('Value cannot be greater than {}.').format(self.pdb_max_value))
  
  def _validate(self, value):
    if self.min_value is not None and value < self.min_value:
      raise SettingValueError(utils_.value_to_str_prefix(value) + self.error_messages['below_min'])

    if self.pdb_min_value is not None and value < self.pdb_min_value:
      raise SettingValueError(
        utils_.value_to_str_prefix(value) + self.error_messages['below_pdb_min'])

    if self.max_value is not None and value > self.max_value:
      raise SettingValueError(utils_.value_to_str_prefix(value) + self.error_messages['above_max'])

    if self.pdb_max_value is not None and value > self.pdb_max_value:
      raise SettingValueError(
        utils_.value_to_str_prefix(value) + self.error_messages['above_pdb_max'])

  def _check_min_and_max_values_against_pdb_min_and_max_values(self):
    if (self.min_value is not None
        and self.pdb_min_value is not None
        and self.min_value < self.pdb_min_value):
      raise ValueError(
        f'minimum value {self.min_value} cannot be less than {self.pdb_min_value}')

    if (self.max_value is not None
        and self.pdb_max_value is not None
        and self.max_value > self.pdb_max_value):
      raise ValueError(
        f'maximum value {self.max_value} cannot be greater than {self.pdb_max_value}')


class IntSetting(NumericSetting):
  """Class for integer settings.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_INT` (default)
  * `GObject.TYPE_UINT`
  * `GObject.TYPE_INT64`
  * `GObject.TYPE_UINT64`
  * `GObject.TYPE_LONG`
  * `GObject.TYPE_ULONG`
  
  Default value: 0
  """
  
  _ALIASES = ['integer']
  
  _ALLOWED_PDB_TYPES = [
    GObject.TYPE_INT,
    GObject.TYPE_UINT,
    GObject.TYPE_INT64,
    GObject.TYPE_UINT64,
    GObject.TYPE_LONG,
    GObject.TYPE_ULONG,
  ]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.int_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0


class FloatSetting(NumericSetting):
  """Class for float settings.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_DOUBLE` (default)
  * `GObject.TYPE_FLOAT`
  
  Default value: 0.0
  """
  
  _ALLOWED_PDB_TYPES = [GObject.TYPE_DOUBLE, GObject.TYPE_FLOAT]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.float_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0.0


class BoolSetting(Setting):
  """Class for boolean settings.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_BOOLEAN`
  
  Default value: ``False``
  """
  
  _ALIASES = ['boolean', 'true_false', 'yes_no']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_BOOLEAN]

  _ALLOWED_GUI_TYPES = [
    SettingGuiTypes.check_button,
    SettingGuiTypes.check_button_no_text,
    SettingGuiTypes.check_menu_item,
    SettingGuiTypes.expander,
  ]

  _DEFAULT_DEFAULT_VALUE = False
  
  def _assign_value(self, value):
    self._value = bool(value)


class ChoiceSetting(Setting):
  """Class for settings with a limited number of values, accessed by their
  associated names.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_INT`
  
  Default value: Name of the first item passed to the ``items`` parameter in
  `ChoiceSetting.__init__()`.
  
  To access an item value:

    setting.items[item name]
  
  To access an item display name:

    setting.items_display_names[item name]
  
  Raises:
    SettingValueError:
      See ``'invalid_value'`` error message below.
    SettingDefaultValueError:
      See ``'invalid_default_value'`` error message below.
    ValueError:
      No items were specified, the same value was assigned to multiple items,
      or an uneven number of elements was passed to the ``items`` parameter
      in `__init__()`.
    KeyError:
      Invalid key for the `items` or `items_display_names` property.
  
  Error messages:
    * ``'invalid_value'``: The value assigned is not one of the items in this
      setting.
    * ``'invalid_default_value'``: Item name is invalid (not found in the
      ``items`` parameter in `__init__()`).
  """
  
  _ALIASES = ['options']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_INT]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.combo_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: next((name for name in self._items), None)
  
  def __init__(
        self,
        name: str,
        items: Union[List[Tuple[str, str]], List[Tuple[str, str, int]]],
        empty_value: Optional[str] = None,
        **kwargs,
  ):
    """Initializes a `ChoiceSetting` instance.

    Args:
      items:
        A list of either (item name, item display name) tuples
        or (item name, item display name, item value) tuples. For 2-element
        tuples, item values are assigned automatically, starting with 0. Use
        3-element tuples to assign explicit item values. Values must be unique
        and specified in each tuple. Use only 2- or only 3-element tuples, they
        cannot be combined.
      empty_value:
        See the `empty_value` property.
      default_value:
        Default item name (identifier). Unlike other `Setting` subclasses,
        `ChoiceSetting` accepts a valid item name for the ``default_value``
        parameter instead of a numeric value.
    """
    self._items, self._items_display_names, self._item_values = self._create_item_attributes(items)
    
    # This member gets overridden during parent class instantiation, but can
    # still be accessible before the instantiation if need be.
    self._error_messages = {
      'invalid_value': (
        _('Invalid item value; valid values: {}').format(list(self._item_values))),
      'invalid_default_value': (
        f'invalid identifier for the default value; must be one of {list(self._items)}'),
    }
    
    if 'error_messages' in kwargs:
      self._error_messages.update(kwargs['error_messages'])
    kwargs['error_messages'] = self._error_messages
    
    self._empty_value = self._get_empty_value(empty_value)
    
    super().__init__(name, **kwargs)
    
    self._empty_values.append(self._empty_value)
    
    self._items_description = self._get_items_description()
  
  @property
  def description(self) -> str:
    return f'{self._description} {self._items_description}'
  
  @property
  def items(self) -> Dict[str, int]:
    """A dictionary of (item name, item value) pairs.
    
    An item name uniquely identifies each item. An item value is the
    corresponding integer value.
    """
    return self._items
  
  @property
  def items_display_names(self) -> Dict[str, str]:
    """A dictionary of (item name, item display name) pairs.
    
    Item display names can be used e.g. as combo box items in the GUI.
    """
    return self._items_display_names
  
  @property
  def empty_value(self) -> Union[str, None]:
    """Item name designated as the empty value.
    
    By default, the setting does not have an empty value.
    """
    return self._empty_value
  
  def to_dict(self, *args, **kwargs):
    settings_dict = super().to_dict(*args, **kwargs)
    
    settings_dict['items'] = [list(elements) for elements in settings_dict['items']]
    
    return settings_dict
  
  def is_item(self, *item_names: str) -> bool:
    """Returns ``True`` if the setting value is set to one the specified items,
    ``False`` otherwise.
    
    If only one item is specified, this is a more convenient and less verbose
    alternative to:

      setting.value == setting.items[item_name]
    
    If multiple items are specified, this is equivalent to:
    
      setting.value in (setting.items[name1], setting.items[name2], ...)
    """
    return any(self.value == self.items[item_name] for item_name in item_names)
  
  def set_item(self, item_name: str):
    """Sets the specified item as the setting value.
    
    This is a more convenient and less verbose alternative to
      
      setting.set_value(setting.items[item_name])
    """
    self.set_value(self.items[item_name])
  
  def get_item_display_names_and_values(self) -> List[Tuple[str, int]]:
    """Returns a list of (item display name, item value) tuples."""
    display_names_and_values = []
    for item_name, item_value in zip(self._items_display_names.values(), self._items.values()):
      display_names_and_values.append((item_name, item_value))
    return display_names_and_values
  
  def _resolve_default_value(self, default_value):
    if isinstance(default_value, type(Setting.DEFAULT_VALUE)):
      default_default_value = super()._resolve_default_value(default_value)

      if default_default_value is not None:
        return self._items[default_default_value]
      else:
        return default_default_value
    else:
      if default_value in self._items:
        # `default_value` is passed as a string (identifier), while the actual
        # value (integer) must be passed to the setting initialization.
        return self._items[default_value]
      else:
        raise SettingDefaultValueError(self._error_messages['invalid_default_value'])
  
  def _validate(self, value):
    if (value not in self._item_values
        or (not self._allow_empty_values and self._is_value_empty(value))):
      raise SettingValueError(
        utils_.value_to_str_prefix(value) + self.error_messages['invalid_value'])
  
  def _get_items_description(self):
    items_description = ''
    items_sep = ', '
    
    for value, display_name in zip(self._items.values(), self._items_display_names.values()):
      description = utils_.get_processed_description(None, display_name)
      items_description += f'{description} ({value}){items_sep}'
    items_description = items_description[:-len(items_sep)]

    return f'{{ {items_description} }}'

  @staticmethod
  def _create_item_attributes(input_items):
    items = {}
    items_display_names = {}
    item_values = set()

    if not input_items:
      raise ValueError('must specify at least one item')
    if all(len(elem) == 2 for elem in input_items):
      for i, (item_name, item_display_name) in enumerate(input_items):
        items[item_name] = i
        items_display_names[item_name] = item_display_name
        item_values.add(i)
    elif all(len(elem) == 3 for elem in input_items):
      for item_name, item_display_name, item_value in input_items:
        if item_value in item_values:
          raise ValueError('cannot set the same value for multiple items - they must be unique')

        items[item_name] = item_value
        items_display_names[item_name] = item_display_name
        item_values.add(item_value)
    else:
      raise ValueError(
        'wrong number of tuple elements in items - must be only 2- or only 3-element tuples')

    return items, items_display_names, item_values

  def _get_empty_value(self, empty_value_name):
    if empty_value_name is not None:
      if empty_value_name in self._items:
        return self._items[empty_value_name]
      else:
        raise ValueError(
          f'invalid identifier for the empty value; must be one of {list(self._items)}')
    else:
      return None


class StringSetting(Setting):
  """Class for string settings.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_STRING`
  
  Default value: ``''``
  """
  
  _ALIASES = ['str']
  
  _ALLOWED_PDB_TYPES = [GObject.TYPE_STRING]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.entry]

  _DEFAULT_DEFAULT_VALUE = ''


class ImageSetting(Setting):
  """Class for settings holding `Gimp.Image` objects.
  
  This class accepts as a value a file path to the image or image ID.
  If calling `to_dict(source_type='session')`, image ID is returned for `value`
  and `default_value`.
  If calling `to_dict()` with any other value for `source_type`, the image file
  path is returned or ``None`` if the image does not exist in the file system.
  
  Allowed GIMP PDB types:
  * `Gimp.Image`
  
  Error messages:
  * ``'invalid_value'``: The image assigned is invalid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Image]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.image_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid image.')
  
  def _raw_to_value(self, raw_value):
    value = raw_value
    
    if isinstance(raw_value, int):
      value = Gimp.Image.get_by_id(raw_value)
    elif isinstance(raw_value, str):
      value = pgpdbutils.find_image_by_filepath(raw_value)
    
    return value
  
  def _value_to_raw(self, value, source_type):
    raw_value = value
    
    if source_type == 'session':
      raw_value = value.get_id()
    else:
      if value is not None and value.get_file() is not None:
        raw_value = value.get_file().get_path()
      else:
        raw_value = None
    
    return raw_value
  
  def _validate(self, image):
    if image is not None and not image.is_valid():
      raise SettingValueError(
        utils_.value_to_str_prefix(image) + self.error_messages['invalid_value'])


class GimpItemSetting(Setting):
  """Abstract class for settings storing GIMP items - layers, channels, vectors.
  
  This class accepts as a value one of the following:
  * a tuple (image file path, item type, item path) where item type is the name
    of the item's GIMP class (e.g. ``'Layer'``).
  * a tuple (item type, item ID). Item ID is are assigned by GIMP.
  * a `Gimp.Item` instance.
  
  If calling ``to_dict(source_type='session')``, a tuple (item type, item ID) is
  returned for `value` and `default_value`.
  If calling `to_dict()` with any other value for ``source_type``, a tuple
  (image file path, item type, item path) is returned.
  """
  
  _ABSTRACT = True
  
  def _raw_to_value(self, raw_value):
    value = raw_value
    
    if isinstance(raw_value, list):
      if len(raw_value) == 3:
        value = self._get_item_from_image_and_item_path(*raw_value)
      else:
        raise ValueError(
          ('lists as values for GIMP item settings must contain'
           f' exactly 3 elements (has {len(raw_value)})'))
    elif isinstance(raw_value, int):
      value = Gimp.Item.get_by_id(raw_value)
    
    return value
  
  def _value_to_raw(self, value, source_type):
    if source_type == 'session':
      return self._get_item_as_id(value)
    else:
      return pgpdbutils.get_item_as_path(value)
  
  @staticmethod
  def _get_item_from_image_and_item_path(image_filepath, item_type_name, item_path):
    image = pgpdbutils.find_image_by_filepath(image_filepath)

    if image is None:
      return None
    
    return pgpdbutils.get_item_from_image_and_item_path(image, item_type_name, item_path)
  
  @staticmethod
  def _get_item_as_id(item):
    if item is not None:
      return item.get_id()
    else:
      return None


class ItemSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Item` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Item`
  
  Error messages:
  * ``'invalid_value'``: The item assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Item]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.item_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid item.')
  
  def _validate(self, item):
    if item is not None and not isinstance(item, Gimp.Item):
      raise SettingValueError(
        utils_.value_to_str_prefix(item) + self.error_messages['invalid_value'])


class DrawableSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Drawable` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Drawable`
  
  Error messages:
  * ``'invalid_value'``: The drawable assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Drawable]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.drawable_combo_box]
  
  def _copy_value(self, value):
    return value

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid drawable.')
  
  def _validate(self, drawable):
    if drawable is not None and not drawable.is_drawable():
      raise SettingValueError(
        utils_.value_to_str_prefix(drawable) + self.error_messages['invalid_value'])


class LayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Layer` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Layer`
  
  Error messages:
  * ``'invalid_value'``: The layer assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Layer]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.layer_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid layer.')
  
  def _validate(self, layer):
    if layer is not None and not layer.is_layer():
      raise SettingValueError(
        utils_.value_to_str_prefix(layer) + self.error_messages['invalid_value'])


class ChannelSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Channel` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Channel`

  Error messages:
  * ``'invalid_value'``: The channel assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Channel]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.channel_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid channel.')
  
  def _validate(self, channel):
    if channel is not None and not channel.is_channel():
      raise SettingValueError(
        utils_.value_to_str_prefix(channel) + self.error_messages['invalid_value'])


class SelectionSetting(ChannelSetting):
  """Class for settings holding the current selection.
  
  A selection in GIMP is internally represented as a `Gimp.Channel` instance.
  Unlike `ChannelSetting`, this setting does not support GUI (there is no need
  for GUI).
  
  Allowed GIMP PDB types:
  * `Gimp.Selection`
  
  Error messages:
  * ``'invalid_value'``: The channel assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Selection]

  _ALLOWED_GUI_TYPES = []


class VectorsSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Vectors` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Vectors`
  
  Error messages:
  * ``'invalid_value'``: The vectors instance assigned is not valid.
  """
  
  _ALIASES = ['path']
  
  _ALLOWED_PDB_TYPES = [Gimp.Vectors]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.vectors_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid vectors.')
  
  def _validate(self, vectors):
    if vectors is not None and not vectors.is_vectors():
      raise SettingValueError(
        utils_.value_to_str_prefix(vectors) + self.error_messages['invalid_value'])


class ColorSetting(Setting):
  """Class for settings holding `Gimp.RGB` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.RGB`
  
  Default value: `Gimp.RGB` instance with color `(0, 0, 0)` and alpha set to 0.
  
  Error messages:
  * ``'invalid_value'``: The color assigned is not valid.
  """

  _ALIASES = ['rgb', 'RGB']

  _ALLOWED_PDB_TYPES = [Gimp.RGB]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.color_button]

  # Create default value dynamically to avoid potential errors on GIMP startup.
  _DEFAULT_DEFAULT_VALUE = lambda self: Gimp.RGB()
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid color.')
  
  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list):
      color = Gimp.RGB()

      if len(raw_value) >= 3:
        color.set(*(item / 255 for item in raw_value[:3]))

      if len(raw_value) >= 4:
        color.set_alpha(raw_value[3] / 255)

      return color
    else:
      return raw_value
  
  def _value_to_raw(self, value, source_type):
    return [int(value.r * 255), int(value.g * 255), int(value.b * 255), int(value.a * 255)]
  
  def _validate(self, color):
    if not isinstance(color, Gimp.RGB):
      raise SettingValueError(
        utils_.value_to_str_prefix(color) + self.error_messages['invalid_value'])


class DisplaySetting(Setting):
  """Class for settings holding `Gimp.Display` instances.
  
  `Gimp.Display` instances cannot be loaded or saved. Therefore, `to_dict()`
  returns a dictionary whose ``'value'`` and ``'default_value'`` keys are
  ``None``.
  
  Allowed GIMP PDB types:
  * `Gimp.Display`
  
  Error messages:
  * ``'invalid_value'``: The display assigned is not valid.
  
  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Display]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.display_spin_button]

  _EMPTY_VALUES = [None]
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid display.')
  
  def _value_to_raw(self, value, source_type):
    # There is no way to restore `Gimp.Display` objects, hence return ``None``.
    return None
  
  def _validate(self, display):
    if not display.is_valid():
      raise SettingValueError(
        utils_.value_to_str_prefix(display) + self.error_messages['invalid_value'])


class ParasiteSetting(Setting):
  """Class for settings holding `Gimp.Parasite` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Parasite`
  
  Default value: `Gimp.Parasite` instance with name equal to the setting
  name, no flags and empty data (``''``).
  
  Error messages:
  * ``'invalid_value'``: The value is not a `Gimp.Parasite` instance.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Parasite]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.parasite_box]

  # Create default value dynamically to avoid potential errors on GIMP startup.
  _DEFAULT_DEFAULT_VALUE = lambda self: Gimp.Parasite.new(self.name, 0, b'')
  
  def _copy_value(self, value):
    return value
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid parasite.')
  
  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list):
      return Gimp.Parasite.new(*raw_value)
    else:
      return raw_value
  
  def _value_to_raw(self, value, source_type):
    return [value.get_name(), value.get_flags(), value.get_data()]
  
  def _validate(self, parasite):
    if not isinstance(parasite, Gimp.Parasite):
      raise SettingValueError(
        utils_.value_to_str_prefix(parasite) + self.error_messages['invalid_value'])


class ValidatableStringSetting(StringSetting):
  """Abstract class for string settings which are meant to be validated with one
  of the `path.StringValidator` subclasses.
  
  To determine whether the string is valid, `is_valid()` from the corresponding
  subclass is called.
  
  Error messages:
    This class contains empty messages for error statuses from the specified
    `path.StringValidator` subclass. Normally, if the value (string) assigned
    is invalid, status messages returned from `is_valid()` are used. If
    desired, you may fill the error messages with custom messages which
    override the status messages from the method. See
    `path.FileValidatorErrorStatuses` for available error statuses.
  """
  
  _ABSTRACT = True
  
  def __init__(self, name: str, string_validator_class: Type[pgpath.StringValidator], **kwargs):
    """Initializes a `ValidatableStringSetting` instance.
    
    Args:
      string_validator_class:
        `path.StringValidator` subclass used to validate the value assigned to
        this object.
    """
    self._string_validator = string_validator_class
    
    super().__init__(name, **kwargs)
  
  def _init_error_messages(self):
    for status in pgpath.FileValidatorErrorStatuses.ERROR_STATUSES:
      self.error_messages[status] = ''
  
  def _validate(self, string_):
    is_valid, status_messages = self._string_validator.is_valid(string_)
    if not is_valid:
      new_status_messages = []
      for status, status_message in status_messages:
        if self.error_messages[status]:
          new_status_messages.append(self.error_messages[status])
        else:
          new_status_messages.append(status_message)
      
      raise SettingValueError(
        utils_.value_to_str_prefix(string_)
        + '\n'.join([message for message in new_status_messages]))


class FileExtensionSetting(ValidatableStringSetting):
  """Class for settings storing file extensions as strings.
  
  The `path.FileExtensionValidator` subclass is used to determine whether the
  file extension is valid.
  
  Empty values:
  * ``''``
  """
  
  _ALLOWED_GUI_TYPES = [
    SettingGuiTypes.entry,
    SettingGuiTypes.file_extension_entry,
  ]

  _EMPTY_VALUES = ['']
  
  def __init__(self, name, adjust_value=False, **kwargs):
    """Additional parameters:
    
    adjust_value:
      if ``True``, process the new value when `set_value()` is
      called. This involves removing leading '.' characters and converting the
      file extension to lowercase.
    """
    super().__init__(name, pgpath.FileExtensionValidator, **kwargs)
    
    if adjust_value:
      self._assign_value = self._adjust_value
  
  def _adjust_value(self, value):
    self._value = value.lstrip('.')


class DirpathSetting(ValidatableStringSetting):
  """Class for settings storing directory paths as strings.
  
  The `path.DirpathValidator` subclass is used to determine whether the
  directory path is valid.
  
  Empty values:
  * ``None``
  * ``''``
  """
  
  _ALIASES = ['directory']
  
  _ALLOWED_GUI_TYPES = [
    SettingGuiTypes.folder_chooser_widget,
    SettingGuiTypes.folder_chooser_button,
  ]

  _EMPTY_VALUES = [None, '']
  
  def __init__(self, name, **kwargs):
    super().__init__(name, pgpath.DirpathValidator, **kwargs)


class GimpResourceSetting(Setting):
  """Abstract class for settings storing `Gimp.Resource` instances (brushes,
  fonts, etc.).

  Default value: ``None``

  Empty values:
  * ``None``

  Error messages:
  * ``'invalid_value'``: The resource is not valid.
  """

  _ABSTRACT = True

  _DEFAULT_DEFAULT_VALUE = None

  _EMPTY_VALUES = [None]

  def __init__(
        self,
        name: str,
        resource_type: Union[GObject.GType, Type[GObject.GObject]],
        **kwargs,
  ):
    self._resource_type = resource_type

    super().__init__(name, **kwargs)

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid resource.')

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, dict):
      raw_value_copy = dict(raw_value)

      name = raw_value_copy.pop('name', None)

      if name is None:
        return None

      resource = self._resource_type.get_by_name(name)

      if resource is None:
        return None

      for key, value in raw_value_copy.items():
        set_property_func = getattr(resource, f'set_{key}', None)
        if set_property_func is not None:
          set_property_func(value)
      else:
        return None
    else:
      return raw_value

  def _value_to_raw(self, resource, source_type):
    return {
      'name': resource.get_name(),
    }

  def _validate(self, resource):
    if not resource.is_valid():
      raise SettingValueError(
        utils_.value_to_str_prefix(resource) + self.error_messages['invalid_value'])


class BrushSetting(GimpResourceSetting):
  """Class for settings storing brushes.
  
  Allowed GIMP PDB types:
  * `Gimp.Brush`

  Default value: ``None``

  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Brush]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.brush_select_button]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Brush, **kwargs)
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid brush.')
  
  def _value_to_raw(self, resource, source_type):
    return {
      'name': resource.get_name(),
      'angle': resource.get_angle(),
      'aspect_ratio': resource.get_aspect_ratio(),
      'hardness': resource.get_hardness(),
      'radius': resource.get_radius(),
      'shape': resource.get_shape(),
      'spacing': resource.get_spacing(),
      'spikes': resource.get_spikes(),
    }


class FontSetting(GimpResourceSetting):
  """Class for settings storing fonts.
  
  Allowed GIMP PDB types:
  * `Gimp.Font`
  
  Default value: ``None``

  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Font]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.font_select_button]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Font, **kwargs)

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid font.')


class GradientSetting(GimpResourceSetting):
  """Class for settings storing gradients.
  
  Allowed GIMP PDB types:
  * `Gimp.Gradient`
  
  Default value: ``None``

  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Gradient]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.gradient_select_button]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Gradient, **kwargs)

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid gradient.')


class PaletteSetting(GimpResourceSetting):
  """Class for settings storing color palettes.
  
  Allowed GIMP PDB types:
  * `Gimp.Palette`
  
  Default value: ``None``

  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Palette]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.palette_select_button]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Palette, **kwargs)

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid palette.')

  def _value_to_raw(self, resource, source_type):
    return {
      'name': resource.get_name(),
      'columns': resource.get_columns(),
    }


class PatternSetting(GimpResourceSetting):
  """Class for settings storing patterns.
  
  Allowed GIMP PDB types:
  * `Gimp.Pattern`
  
  Default value: ``None``

  Empty values:
  * ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Pattern]

  _ALLOWED_GUI_TYPES = [SettingGuiTypes.pattern_select_button]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Pattern, **kwargs)

  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid pattern.')


class ArraySetting(Setting):
  """Class for settings storing arrays of the specified type.
  
  Array settings can be registered to the GIMP PDB and have their own readily
  available GUI for adding, modifying and removing elements.
  
  Values of array settings are tuples whose elements are of the specified
  setting type.
  
  Any setting type can be passed on initialization of the array setting.
  However, only specific array types can be registered to the GIMP PDB or have
  their own GUI. For registrable array types, see the allowed GIMP PDB types
  below.

  If the ``element_type`` specified during instantiation has a matching GObject
  type (e.g. `Gimp.FloatArray` for float arrays), then the array setting can
  be registered to the GIMP PDB. To disable registration, pass ``pdb_type=None``
  in `Setting.__init__()` as one normally would.
  
  Validation of setting values is performed for each element individually.
  
  Array settings are useful for manipulating PDB array parameters or for
  storing a collection of values of the same type. For more fine-grained control
  (collection of values of different type, different GUI, etc.), use
  `setting.Group` instead.

  The following additional event types are invoked in `ArraySetting` instances:

  * ``'before-add-element'``: Invoked when calling `add_element()` immediately
    before adding an array element.

  * ``'after-add-element'``: Invoked when calling `add_element()` immediately
    after adding an array element.

  * ``'before-reorder-element'``: Invoked when calling `reorder_element()`
    immediately before reordering an array element.

  * ``'after-reorder-element'``: Invoked when calling `reorder_element()`
    immediately after reordering an array element.

  * ``'before-delete-element'``: Invoked when calling `remove_element()` or
    `__delitem__()` immediately before removing an array element.

  * ``'after-delete-element'``: Invoked when calling `remove_element()` or
    `__delitem__()` immediately after removing an array element.

  Allowed GIMP PDB types:
  TODO
  
  Default value: `()`
  
  Error messages:
  * ``'invalid_value'``: The value is not a tuple or an iterable container.
  * ``'negative_min_size'``: `min_size` is negative.
  * ``'min_size_greater_than_max_size'``: `min_size` is greater than `max_size`.
  * ``'min_size_greater_than_value_length'``: `min_size` is greater than the
    length of the value.
  * ``'max_size_less_than_value_length'``: `max_size` is less than the length of
    the value.
  * ``'delete_below_min_size'``: deleting an element causes the array to have
    fewer than `min_size` elements.
  * ``'add_above_max_size'``: adding an element causes the array to have more
    than `max_size` elements.
  """
  
  ELEMENT_DEFAULT_VALUE = type('DefaultElementValue', (), {})()
  
  _ALLOWED_GUI_TYPES = [SettingGuiTypes.array_box]

  _DEFAULT_DEFAULT_VALUE = ()

  _ARRAY_PDB_TYPES = {
    IntSetting: (GObject.TYPE_INT, Gimp.Int32Array),
    FloatSetting: (GObject.TYPE_FLOAT, Gimp.FloatArray),
    ColorSetting: (Gimp.RGB, Gimp.RGBArray),
    StringSetting: (GObject.TYPE_STRING, GObject.TYPE_STRV),
  }
  
  def __init__(
        self,
        name: str,
        element_type: Union[str, Type[Setting]],
        min_size: Optional[int] = 0,
        max_size: Optional[int] = None,
        **kwargs,
  ):
    """Initializes an `ArraySetting` instance.

    All parameters prefixed with ``'element_'`` (see ``**kwargs below``) will
    be created in the array setting as read-only properties.
    ``element_default_value`` will always be created.

    Args:
      name:
        See ``name`` in `Setting.__init__()`.
      element_type:
        A `Setting` subclass or the name of a `Setting` subclass determining
        the type of each array element.

        Passing `ArraySetting` is also possible, allowing to create
        multidimensional arrays. Note that in that case, required parameters
        for elements of each subsequent dimension must be specified and must
        have an extra ``'element_'`` prefix. For example, for the second
        dimension of a 2D array, `element_element_type` must also be specified.
      min_size:
        Minimum array size. If ``None``, the minimum size will be 0.
      max_size:
        Maximum array size. If ``None``, there is no upper limit on the array
        size.
      **kwargs:
        Additional keyword arguments for `Setting.__init__()`, plus all
        parameters that would be passed to the `Setting` class defined by
        ``element_type``. The arguments for the latter must be prefixed with
        ``element_`` - for example, for arrays containing integers (i.e.
        ``element_type`` is ``IntSetting``), you can optionally pass
        ``element_min_value=<value>`` to set minimum value for all integer
        array elements.
    """
    self._element_type = process_setting_type(element_type)
    self._min_size = min_size if min_size is not None else 0
    self._max_size = max_size
    
    self._element_kwargs = {
      key[len('element_'):]: value for key, value in kwargs.items()
      if key.startswith('element_')}
    
    self._reference_element = self._create_reference_element()
    
    if 'default_value' not in self._element_kwargs:
      self._element_kwargs['default_value'] = self._reference_element.default_value
    else:
      self._element_kwargs['default_value'] = self._reference_element._raw_to_value(
        self._element_kwargs['default_value'])
    
    for key, value in self._element_kwargs.items():
      pgutils.create_read_only_property(self, f'element_{key}', value)
    
    self._elements = []
    
    array_kwargs = {key: value for key, value in kwargs.items() if not key.startswith('element_')}
    
    super().__init__(name, **array_kwargs)
  
  @property
  def value(self):
    # This ensures that this property is always up-to-date no matter what events
    # are connected to individual elements.
    self._value = self._get_element_values()
    return self._value
  
  @property
  def element_type(self) -> Type[Setting]:
    """Setting type of array elements."""
    return self._element_type
  
  @property
  def min_size(self) -> int:
    """The minimum array size."""
    return self._min_size
  
  @property
  def max_size(self) -> Union[int, None]:
    """The maximum array size.
    
    If ``None``, the array size is unlimited.
    """
    return self._max_size
  
  def to_dict(self, *args, **kwargs):
    settings_dict = super().to_dict(*args, **kwargs)
    
    source_type = kwargs.get('source_type', 'persistent')
    
    for key, val in settings_dict.items():
      if key == 'element_default_value':
        settings_dict[key] = self._reference_element._value_to_raw(val, source_type)
      elif key == 'element_type':
        settings_dict[key] = SettingTypes[type(self._reference_element)]
    
    return settings_dict
  
  def __getitem__(self, index: int):
    """Returns an array element at the specified index."""
    return self._elements[index]
  
  def __delitem__(self, index: int):
    """Removes an array element at the specified index."""
    if len(self._elements) == self._min_size:
      raise SettingValueError(self.error_messages['delete_below_min_size'].format(self._min_size))
    
    self.invoke_event('before-delete-element', index)
    
    del self._elements[index]
    
    self.invoke_event('after-delete-element')
  
  def __len__(self) -> int:
    """Returns the number of elements of the array."""
    return len(self._elements)
  
  def add_element(self, index: Optional[int] = None, value=ELEMENT_DEFAULT_VALUE) -> Setting:
    """Adds a new element with the specified value at the specified index
    (starting from 0).
    
    If ``index`` is ``None``, the value is appended at the end of the array.

    If ``value`` is `ELEMENT_DEFAULT_VALUE`, the default value of the
    underlying `element_type` is used.
    """
    if len(self._elements) == self._max_size:
      raise SettingValueError(self.error_messages['add_above_max_size'].format(self._max_size))
    
    if isinstance(value, type(self.ELEMENT_DEFAULT_VALUE)):
      value = self._reference_element.default_value
    
    self.invoke_event('before-add-element', index, value)
    
    element = self._create_element(value)
    
    if index is None:
      self._elements.append(element)
      insertion_index = -1
    else:
      self._elements.insert(index, element)
      insertion_index = index if index >= 0 else index - 1
    
    self.invoke_event('after-add-element', insertion_index, value)
    
    return element
  
  def reorder_element(self, index: int, new_index: int):
    """Changes the order of an array element at ``index`` to a new position
    specified by ``new_index``.

    Both indexes start from 0.
    """
    self.invoke_event('before-reorder-element', index)
    
    element = self._elements.pop(index)
  
    if new_index < 0:
      new_index = max(len(self._elements) + new_index + 1, 0)
    
    self._elements.insert(new_index, element)
    
    self.invoke_event('after-reorder-element', index, new_index)
  
  def remove_element(self, index: int):
    """Removes an element at the specified index.
    
    This method is an alias to `__delitem__`.
    """
    self.__delitem__(index)
  
  def get_elements(self) -> List[Setting]:
    """Returns a list of array elements in this setting."""
    return list(self._elements)
  
  def get_pdb_param(
        self, length_name: Optional[str] = None, length_description: Optional[str] = None,
  ) -> Union[List[Tuple[GObject.GType, str, str]], None]:
    """Returns a list of two tuples, describing the length of the array and the
    array itself, as GIMP PDB parameters - PDB type, name and description.
    
    If the underlying `element_type` does not support any PDB type, ``None`` is
    returned.
    
    To customize the name and description of the length parameter,
    pass ``length_name`` and ``length_description``, respectively. Passing
    ``None`` creates the name and/or the description automatically.
    """
    if self.can_be_registered_to_pdb():
      if length_name is None:
        length_name = f'{self.name}-length'
      
      if length_description is None:
        length_description = _('Number of elements in "{}"').format(self.name)
      
      return [
        (GObject.TYPE_INT, length_name, length_description),
        (self.pdb_type,
         self.name,
         self.description)
      ]
    else:
      return None
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Not an array.')
    self.error_messages['negative_min_size'] = _(
      'Minimum size ({}) cannot be negative.')
    self.error_messages['min_size_greater_than_max_size'] = _(
      'Minimum size ({}) cannot be greater than maximum size ({}).')
    self.error_messages['min_size_greater_than_value_length'] = _(
      'Minimum size ({}) cannot be greater than the length of the value ({}).')
    self.error_messages['max_size_less_than_value_length'] = _(
      'Maximum size ({}) cannot be less than the length of the value ({}).')
    self.error_messages['delete_below_min_size'] = _(
      'Cannot delete any more elements - at least {} elements must be present.')
    self.error_messages['add_above_max_size'] = _(
      'Cannot add any more elements - at most {} elements are allowed.')
  
  def _raw_to_value(self, raw_value_array):
    if isinstance(raw_value_array, Iterable) and not isinstance(raw_value_array, str):
      return tuple(
        self._reference_element._raw_to_value(raw_value)
        for raw_value in raw_value_array)
    else:
      # Let `_validate()` raise error
      return raw_value_array
  
  def _value_to_raw(self, value_array, source_type):
    return [
      self._reference_element._value_to_raw(value, source_type)
      for value in value_array]
  
  def _validate(self, value_array):
    if not isinstance(value_array, Iterable) or isinstance(value_array, str):
      raise SettingValueError(
        utils_.value_to_str_prefix(value_array) + self.error_messages['invalid_value'])

    if not hasattr(value_array, '__len__'):
      value_array = list(value_array)

    if self._min_size < 0:
      raise SettingValueError(
        self.error_messages['negative_min_size'].format(self._min_size))
    elif self._max_size is not None and self._min_size > self._max_size:
      raise SettingValueError(
        self.error_messages['min_size_greater_than_max_size'].format(
          self._min_size, self._max_size))
    elif self._min_size > len(value_array):
      raise SettingValueError(
        self.error_messages['min_size_greater_than_value_length'].format(
          self._min_size, len(value_array)))
    elif self._max_size is not None and self._max_size < len(value_array):
      raise SettingValueError(
        self.error_messages['max_size_less_than_value_length'].format(
          self._max_size, len(value_array)))
    
    for value in value_array:
      self._reference_element._validate(value)
    self._reference_element.reset()
  
  def _assign_value(self, value_array):
    elements = []
    exceptions = []
    exception_occurred = False
    
    for value in value_array:
      try:
        elements.append(self._create_element(value))
      except SettingValueError as e:
        exceptions.append(e)
        exception_occurred = True
    
    if exception_occurred:
      raise SettingValueError('\n'.join([str(e) for e in exceptions]))
    
    self._elements = elements
    self._value = self._get_element_values()
  
  def _apply_gui_value_to_setting(self, value):
    # No assignment takes place to prevent breaking the sync between the array
    # and the GUI.
    self.invoke_event('value-changed')
  
  def _copy_value(self, value):
    self._elements = [self._create_element(element_value) for element_value in value]
    return self._get_element_values()
  
  def _get_default_pdb_type(self):
    if hasattr(self, '_element_pdb_type'):
      if self._element_pdb_type in self._ARRAY_PDB_TYPES:
        return self._ARRAY_PDB_TYPES[self._element_pdb_type]
    elif self._element_type._ALLOWED_PDB_TYPES:
      return self._ARRAY_PDB_TYPES[self._element_type._ALLOWED_PDB_TYPES[0]]
    
    return None
  
  def _create_reference_element(self):
    """Creates a reference element to access and validate the element default
    value.
    """
    # Rely on the underlying element setting type to perform validation of the
    # default value.
    return self._element_type(name='element', **dict(self._element_kwargs, gui_type=None))
  
  def _create_element(self, value):
    kwargs = dict(
      dict(
        name='element',
        display_name='',
        pdb_type=None),
      **self._element_kwargs)
    
    setting = self._element_type(**kwargs)
    setting.set_value(value)
    
    return setting
  
  def _get_element_values(self):
    return tuple(setting.value for setting in self._elements)


class ContainerSetting(Setting):
  """Abstract class for settings representing container types.
  
  Container settings can hold items of arbitrary type, but cannot be
  registered to the GIMP PDB and do not have a GUI widget. Use `ArraySetting`
  if you need to pass the items to a GIMP PDB procedure and allow adjusting
  the item values via GUI.
  
  If you intend to save container settings to a setting source, make sure each
  item is of one of the types specified in the description of
  `Setting.to_dict()`. Otherwise, saving may fail.
  
  Optionally, when assigning, the value can be nullable (``None``) instead of
  always a container.
  """
  
  _ABSTRACT = True
  
  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = []
  
  def __init__(self, name: str, nullable: bool = False, **kwargs):
    """Initializes a `ContainerSetting` instance.

    Args:
      nullable:
        See the `nullable` property.
    """
    super().__init__(name, **kwargs)
    
    self._nullable = nullable
  
  @property
  def nullable(self) -> bool:
    """If ``True``, ``None`` is treated as a valid value when calling `set_value()`.
    """
    return self._nullable
  
  def _init_error_messages(self):
    self.error_messages['value_is_none'] = _(
      'Cannot assign a null value (None) if the setting is not nullable.')
  
  def _validate(self, value):
    if value is None and not self._nullable:
      raise SettingValueError(
        utils_.value_to_str_prefix(value) + self.error_messages['value_is_none'])


class ListSetting(ContainerSetting):
  """Class for settings representing lists (mutable sequences of elements)."""
  
  _DEFAULT_DEFAULT_VALUE = []
  
  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, list) and raw_value is not None:
      return list(raw_value)
    else:
      return raw_value


class TupleSetting(ContainerSetting):
  """Class for settings representing tuples (immutable sequences of elements).
  """
  
  _DEFAULT_DEFAULT_VALUE = ()
  
  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, tuple) and raw_value is not None:
      return tuple(raw_value)
    else:
      return raw_value
  
  def _value_to_raw(self, value, source_type):
    return list(value)


class SetSetting(ContainerSetting):
  """Class for settings representing sets (mutable unordered collections of
  elements).
  """
  
  _DEFAULT_DEFAULT_VALUE = set()
  
  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, set) and raw_value is not None:
      return set(raw_value)
    else:
      return raw_value
  
  def _value_to_raw(self, value, source_type):
    return list(value)


class DictSetting(ContainerSetting):
  """Class for settings representing dictionaries (collections of key-value
  pairs).
  """
  
  _ALIASES = ['dictionary', 'map']
  
  _DEFAULT_DEFAULT_VALUE = {}
  
  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, dict) and raw_value is not None:
      return dict(raw_value)
    else:
      return raw_value


class SettingValueError(Exception):
  """Exception class raised when assigning an invalid value to a `Setting`
  instance.
  """
  
  def __init__(self, message, setting=None, settings=None, messages=None):
    self.setting = setting
    self.settings = settings
    self.messages = messages
    
    super().__init__(message)


class SettingDefaultValueError(SettingValueError):
  """Exception class raised when the default value specified during the
  `Setting` instance initialization is invalid.
  """
  
  pass


def process_setting_type(setting_type_or_name: Union[Type[Setting], str]) -> Type[Setting]:
  """Returns a `Setting` class based on the input type or name.
  
  ``setting_type_or_name`` can be a `Setting` class or a string
  representing the class name or one of its aliases in `SettingTypes`.
  
  `ValueError` is raised if ``setting_type_or_name`` is not valid.
  """
  return _process_type(
    setting_type_or_name,
    SettingTypes,
    (f'setting type "{setting_type_or_name}" is not recognized; refer to'
     ' pygimplib.setting.SettingTypes for the supported setting types and their'
     ' aliases'))


def process_setting_gui_type(
      setting_gui_type_or_name: Union[Type[presenter_.Presenter], str],
) -> Type[presenter_.Presenter]:
  """Returns a `setting.Presenter` class based on the input type or name.
  
  ``setting_gui_type_or_name`` can be a `setting.Presenter` class or a string
  representing the class name or one of its aliases in `SettingGuiTypes`.
  
  `ValueError` is raised if ``setting_gui_type_or_name`` is not valid.
  """
  return _process_type(
    setting_gui_type_or_name,
    SettingGuiTypes,
    (f'setting GUI type "{setting_gui_type_or_name}" is not recognized; refer to'
     ' pygimplib.setting.SettingGuiTypes for the supported setting GUI types'
     ' and their aliases'))


def _process_type(type_or_name, type_map, error_message):
  try:
    type_map[type_or_name]
  except TypeError:
    raise TypeError(error_message)
  
  if isinstance(type_or_name, str):
    return type_map[type_or_name]
  else:
    return type_or_name


__all__ = [
  'SettingTypes',
  'SettingGuiTypes',
  'PDB_TYPES_TO_SETTING_TYPES_MAP',
  'SettingValueError',
  'SettingDefaultValueError',
  'process_setting_type',
  'process_setting_gui_type',
  'Setting',
]

for name, class_ in inspect.getmembers(sys.modules[__name__], inspect.isclass):
  if issubclass(class_, Setting) and class_ is not Setting:
    __all__.append(name)
