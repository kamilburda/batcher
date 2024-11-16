"""API to create and manage plug-in settings."""

from __future__ import annotations

import collections
from collections.abc import Iterable
import copy
import importlib
import inspect
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Union, Tuple, Type

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

from .. import pdbutils as pgpdbutils
from .. import utils as pgutils

from . import meta as meta_
from . import persistor as persistor_
from . import presenter as presenter_
# Despite being unused, `presenters_gtk` must be imported so that the GUI
# classes defined there are properly registered and `SETTING_GUI_TYPES` is filled.
# noinspection PyUnresolvedReferences
from . import presenters_gtk
from . import utils as utils_


_SETTING_TYPES = meta_.SETTING_TYPES
_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES


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
  * ``'value-changed'``:
    invoked after `set_value()` or `reset()` is called and before events of
    type ``'after-set-value'`` or ``'after-reset'``.

  * ``'value-not-valid'``:
    invoked when setting value validation is performed (usually when
    `set_value()` is called) and the new value is not valid. Some subclasses
    may trigger this event at other times, e.g. when deleting an invalid
    array element index in `ArraySetting`s.

    The following positional arguments must be specified by an event handler:

    * ``message`` (required): The message.
    * ``message_id``: String ID of the message acting as a type (e.g. value is
      above a maximum value, or generally that a value is not valid).
    * ``details``: Traceback providing details about where the failed validation
      originated.

  * ``'before-set-value'``: invoked before `set_value()` is called.

  * ``'after-set-value'``: invoked after `set_value()` is called.

  * ``'before-reset'``: invoked before `reset()` is called.

  * ``'after-reset'``: invoked after `reset()` is called.

  * ``'before-set-gui'``: invoked before `set_gui()` is called.

  * ``'after-set-gui'``: invoked after `set_gui()` is called.

  * ``'before-load'``:
    invoked before loading a setting via `Setting.load()` or `Group.load()`
    if the setting is within a group.

  * ``'after-load'``:
    invoked after loading a setting via `Setting.load()` or `Group.load()`
    if the setting is within a group.

  * ``'before-save'``:
    invoked before saving a setting via `Setting.save()` or `Group.save()`
    if the setting is within a group.

  * ``'after-save'``:
    invoked after saving a setting via `Setting.save()` or `Group.save()` if
    the setting is within a group.

  * ``'gui-visible-changed'``: invoked after `Setting.gui.set_visible()` is
    called.

  * ``'gui-sensitive-changed'``: invoked after `Setting.gui.set_sensitive()` is
    called.

  If you need to create a custom `Setting` subclass and your plug-in is
  composed of multiple modules, you must ensure that the module where your
  subclass is defined is imported (i.e. the module is kept in the memory).
  Otherwise, the subclass will not be recognized as a valid setting type.
  """
  
  DEFAULT_VALUE = type('DefaultValue', (), {})()
  
  _ABSTRACT = True
  
  _ALLOWED_PDB_TYPES = []

  _REGISTRABLE_TYPE_NAME = None

  _ALLOWED_GUI_TYPES = []

  _DEFAULT_DEFAULT_VALUE = None
  
  def __init__(
        self,
        name: str,
        default_value=DEFAULT_VALUE,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        pdb_type: Union[GObject.GType, Type[GObject.GObject], str, None] = 'automatic',
        gui_type: Union[Type[presenter_.Presenter], str, None] = 'automatic',
        gui_type_kwargs: Optional[Dict] = None,
        auto_update_gui_to_setting: bool = True,
        tags: Optional[Iterable[str]] = None,
  ):
    """Initializes a new setting.
    
    Args:
      name:
        Setting name. See the `name` property for more information.
      default_value:
        Default setting value. During instantiation, the default value is
        validated. Usually, a `Setting` subclass defines its own default value
        appropriate for that subclass.
      display_name:
        See the `display_name` property.
      description:
        See the `description` property.
      pdb_type:
        A `GObject.GType` instance (e.g. `GObject.TYPE_INT` representing
        integers), a subclass of `GObject.GObject` (e.g. `Gimp.Image`),
        a string as the name of a `GObject.GType` (e.g. ``'gint'``,
        ``'GimpImage'``), ``None`` or ``'automatic'``. If set to
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
      gui_type_kwargs:
        Keyword arguments for instantiating a particular GUI widget. See the
        `setting.Presenter._create_widget()` method in particular
        `setting.Presenter` subclasses for available keyword arguments.
      auto_update_gui_to_setting:
        If ``True``, the setting value is automatically updated if the GUI
        value is updated. If ``False``, the setting must be updated manually by
        calling `Setting.gui.update_setting_value()` when needed.

        This parameter does not have any effect if the GUI type used in
        this setting cannot provide automatic GUI-to-setting update.
      tags:
        An iterable container (list, set, etc.) of arbitrary strings attached to
        the setting. Tags can be used to e.g. iterate over a specific subset of
        settings.
    """
    utils_.SettingParentMixin.__init__(self)
    utils_.SettingEventsMixin.__init__(self)
    
    utils_.check_setting_name(name)
    self._name = name

    self._is_valid = True
    
    self._default_value = self._resolve_default_value(default_value)
    
    self._value = self._copy_value(self._default_value)
    
    self._display_name = utils_.get_processed_display_name(display_name, self._name)
    self._description = utils_.get_processed_description(description, self._display_name)

    self._pdb_type = self._get_pdb_type(pdb_type)
    self._pdb_name = utils_.get_pdb_name(self._name)
    
    self._setting_value_synchronizer = presenter_.SettingValueSynchronizer()
    self._setting_value_synchronizer.apply_gui_value_to_setting = self._apply_gui_value_to_setting
    
    self._gui_type = self._get_gui_type(gui_type)
    self._gui_type_kwargs = gui_type_kwargs

    self._gui = presenter_.NullPresenter(
      self,
      None,
      self._setting_value_synchronizer,
      auto_update_gui_to_setting=auto_update_gui_to_setting,
    )
    
    self._tags = set(tags) if tags is not None else set()

    self._validate_value(self._value)
  
  @property
  def name(self) -> str:
    """A string that identifies the setting.

    The name must be unique within a `setting.Group` instance. If it is not, you
    may call `uniquify_name()` to modify the name to be unique within that
    group.
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
  def value_for_pdb(self):
    """The setting value in a format appropriate to be used as a PDB procedure
    argument.

    `value_for_pdb` is identical to `value` for almost all `Setting` subclasses.

    Values for some `Setting` types, such as array types, must be converted to a
    type compatible with the GIMP PDB, e.g. a list of float values to
    `Gimp.DoubleArray` for an `ArraySetting` instance.
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
  def is_valid(self):
    """``True`` if the setting value is valid, ``False`` otherwise.

    This property is set on each call to `set_value()` or upon instantiation.
    """
    return self._is_valid

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
  def gui_type(self) -> Type[presenter_.Presenter]:
    """The type of the setting GUI widget.

    This is a `setting.Presenter` class.

    This property is useful if you need to obtain the GUI type information
    passed to `__init__()` before `set_gui()` is called on this setting (at
    which point the setting GUI is still uninitialized).
    """
    return self._gui_type

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
  def pdb_type(self) -> Union[GObject.GType, Type[GObject.GObject], None]:
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
  def get_allowed_pdb_types(cls):
    """Returns the list of allowed PDB types for this setting type."""
    return list(cls._ALLOWED_PDB_TYPES)
  
  @classmethod
  def get_allowed_gui_types(cls) -> List[Type[presenter_.Presenter]]:
    """Returns the list of allowed GUI types for this setting type."""
    return [meta_.process_setting_gui_type(type_or_name) for type_or_name in cls._ALLOWED_GUI_TYPES]
  
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
    
    Before the assignment, the value is validated. If the value is not valid,
    the ``'value-not-valid'`` event is triggered.
    
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
        gui_type_kwargs: Optional[Dict] = None,
        copy_previous_value: bool = True,
        copy_previous_visible: bool = True,
        copy_previous_sensitive: bool = True,
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
        GUI had are disconnected. The state of the previous GUI is still
        preserved.
      widget:
        A native GUI widget.

        If ``gui_type`` is ``'automatic'``, ``widget`` is ignored.
        If ``gui_type`` is not ``'automatic'`` and ``widget`` is ``None``,
        `ValueError` is raised.
      auto_update_gui_to_setting:
        See the ``auto_update_gui_to_setting`` parameter in `__init__()`.
      gui_type_kwargs:
        Keyword arguments for instantiating a particular `setting.Presenter`
        subclass. If ``None``, the ``gui_type_kwargs`` parameter specified in
        `__init__()` is used instead.
      copy_previous_value:
        See `pygimplib.setting.Presenter.__init__()`.
      copy_previous_visible:
        See `pygimplib.setting.Presenter.__init__()`.
      copy_previous_sensitive:
        See `pygimplib.setting.Presenter.__init__()`.
    """
    if gui_type != 'automatic' and widget is None:
      raise ValueError('widget cannot be None if gui_type is not "automatic"')
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
      processed_gui_type = meta_.process_setting_gui_type(gui_type)

    if gui_type_kwargs is None:
      gui_type_kwargs = self._gui_type_kwargs

    self._gui = processed_gui_type(
      self,
      widget,
      setting_value_synchronizer=self._setting_value_synchronizer,
      auto_update_gui_to_setting=auto_update_gui_to_setting,
      create_widget_kwargs=gui_type_kwargs,
      previous_presenter=self._gui,
      copy_previous_value=copy_previous_value,
      copy_previous_visible=copy_previous_visible,
      copy_previous_sensitive=copy_previous_sensitive,
    )
    
    self.invoke_event('after-set-gui')

  def uniquify_name(self, group: 'setting.Group'):
    """Modifies the ``name`` attribute to be unique within all immediate
    children of the specified ``group``.

    See `pygimplib.setting.utils.get_unique_setting_name` for more information.
    """
    self._name = utils_.get_unique_setting_name(self.name, group)

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

  def validate(self, value) -> Union[None, ValueNotValidData]:
    """Validates the given ``value`` for this setting.

    If ``value`` is valid, ``None`` is returned, otherwise a `ValueNotValidData`
    tuple is returned, containing a message and an ID describing the problem.
    """
    value_not_valid_args = self._validate(value)

    if value_not_valid_args is not None:
      if not isinstance(value_not_valid_args, Iterable) or isinstance(value_not_valid_args, str):
        value_not_valid_args = (value_not_valid_args,)

      if len(value_not_valid_args) > 2:
        value_not_valid_args = value_not_valid_args[:2]

      return ValueNotValidData(*value_not_valid_args)
    else:
      return value_not_valid_args
  
  def can_be_used_in_pdb(self) -> bool:
    """Returns ``True`` if the setting can be used as a GIMP PDB parameter,
    ``False`` otherwise.

    This method returns ``True`` if the `pdb_type` property is not ``None``,
    i.e. the setting has a valid PDB type assigned.

    Note that this does not mean that the setting value can be used when
    registering a plug-in, only that it can be passed as a parameter to a PDB
    procedure. To determine if the setting can be used for plug-in registration,
    use `get_pdb_param()`.
    """
    return self._pdb_type is not None
  
  def get_pdb_param(self) -> Union[List, None]:
    """Returns a list of setting attribute values usable as a GIMP PDB
    parameter when registering a GIMP plug-in.

    If the setting cannot be used for plug-in registration, ``None`` is
    returned.

    If the setting's `pdb_type` is explicitly set to ``None``,
    then the registration is disabled, i.e. ``None`` is also returned.
    """
    if self._REGISTRABLE_TYPE_NAME is not None and self.can_be_used_in_pdb():
      return self._get_pdb_param()
    else:
      return None
  
  def to_dict(self) -> Dict:
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
    """
    settings_dict = {}
    
    for key, val in self._dict_on_init.items():
      if key == 'gui_type' and val is not None and not isinstance(val, str):
        try:
          gui_type_name = _SETTING_GUI_TYPES[val]
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
        settings_dict[key] = self._value_to_raw(val)
      elif key == 'tags':
        settings_dict[key] = list(val)
      else:
        settings_dict[key] = val
    
    settings_dict.update({
      'name': self.name,
      'value': self._value_to_raw(self.value),
      'type': _SETTING_TYPES[type(self)],
    })
    
    return settings_dict

  @classmethod
  def get_default_default_value(cls):
    """Returns the hard-coded default value for this setting class."""
    if not callable(cls._DEFAULT_DEFAULT_VALUE):
      return cls._DEFAULT_DEFAULT_VALUE
    else:
      return cls._DEFAULT_DEFAULT_VALUE()

  def _validate(self, value) -> Union[None, List, Tuple]:
    """Checks whether the specified value is valid. If the value is not valid,
    the ``'value-not-valid'`` event is triggered.

    Override this method in subclasses to provide subclass-specific
    validation. If a value is not valid, the overriden method must return a
    tuple consisting of at least a message and a message ID (a string
    indicating the type of message). If a value is valid, the overriden
    method must return ``None``.
    """
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
  
  def _value_to_raw(self, value):
    """Converts the given value to a value that can be saved.
    
    The converted value is returned, or the original value if no conversion is
    necessary.
    
    This method is called in `to_dict()` and is applied on the `value` and
    `default_value` properties.
    """
    return value
  
  def _validate_and_assign_value(self, value):
    self._validate_value(value)
    self._assign_value(value)

  def _validate_value(self, value):
    self._is_valid = True

    value_not_valid_args = self._validate(value)

    if value_not_valid_args is not None:
      if not isinstance(value_not_valid_args, Iterable) or isinstance(value_not_valid_args, str):
        value_not_valid_args = (value_not_valid_args,)

      self._handle_failed_validation(*value_not_valid_args, value=value)

  def _handle_failed_validation(
        self, message, message_id, prepend_value=True, value=None):
    self._is_valid = False

    formatted_traceback = pgutils.get_traceback(stack_levels_to_keep=-2)

    if prepend_value:
      processed_message = f'"{value}": {message}'
    else:
      processed_message = message

    self.invoke_event(
      'value-not-valid',
      processed_message,
      message_id,
      formatted_traceback,
    )
  
  def _apply_gui_value_to_setting(self, value):
    self._validate_and_assign_value(value)
    self.invoke_event('value-changed')
  
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
    if isinstance(pdb_type, str):
      if pdb_type == 'automatic':
        return self._get_default_pdb_type()
      else:
        try:
          processed_pdb_type = GObject.GType.from_name(pdb_type)
        except RuntimeError:
          processed_pdb_type = None
    else:
      processed_pdb_type = pdb_type

    if processed_pdb_type is None:
      return None

    if self._is_pdb_type_allowed(processed_pdb_type):
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

  def _is_pdb_type_allowed(self, pdb_type):
    allowed_gtypes = [
      allowed_type.__gtype__ if hasattr(allowed_type, '__gtype__') else allowed_type
      for allowed_type in self._ALLOWED_PDB_TYPES]

    if hasattr(pdb_type, '__gtype__'):
      gtype = pdb_type.__gtype__
    else:
      gtype = pdb_type

    return gtype in allowed_gtypes

  def _get_pdb_param(self):
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
        processed_gui_type = meta_.process_setting_gui_type(gui_type)
        
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
  
  def to_dict(self):
    settings_dict = super().to_dict()
    
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
  
  def _value_to_raw(self, value):
    raw_value = value
    
    if self._before_value_save is not None:
      if len(inspect.getfullargspec(self._before_value_save).args) == 1:
        raw_value = self._before_value_save(value)
      else:
        raw_value = self._before_value_save(value, self)
    else:
      raw_value = repr(value)
    
    return raw_value
  
  @staticmethod
  def _validate_function(func, name):
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
  
  Message IDs for invalid values:
    * ``'below_min'``: The value assigned is less than `min_value`.
    * ``'below_pdb_min'``: The value assigned is less than `pdb_min_value`.
    * ``'above_max'``: The value assigned is greater than `max_value`.
    * ``'above_pdb_max'``: The value assigned is greater than `pdb_max_value`.
  """
  
  _ABSTRACT = True

  _PDB_TYPES_AND_MINIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MININT,
    GObject.TYPE_UINT: 0,
    GObject.TYPE_DOUBLE: -GLib.MAXDOUBLE,
  }
  """Mapping of PDB types to minimum values allowed for each type.
  
  For example, the minimum value allowed for type `GObject.TYPE_INT` would be
  `GLib.MININT`.
  """

  _PDB_TYPES_AND_MAXIMUM_VALUES = {
    GObject.TYPE_INT: GLib.MAXINT,
    GObject.TYPE_UINT: GLib.MAXUINT,
    GObject.TYPE_DOUBLE: GLib.MAXDOUBLE,
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
  
  def _validate(self, value):
    if self.min_value is not None and value < self.min_value:
      return f'value cannot be less than {self.min_value}', 'below_min'

    if self.pdb_min_value is not None and value < self.pdb_min_value:
      return f'value cannot be less than {self.pdb_min_value}', 'below_pdb_min'

    if self.max_value is not None and value > self.max_value:
      return f'value cannot be greater than {self.max_value}', 'above_max'

    if self.pdb_max_value is not None and value > self.pdb_max_value:
      return f'value cannot be greater than {self.pdb_max_value}', 'above_pdb_max'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._min_value if self._min_value is not None else self._pdb_min_value,
      self._max_value if self._max_value is not None else self._pdb_max_value,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

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
  * `GObject.TYPE_INT`
  
  Default value: 0
  """
  
  _ALIASES = ['integer']
  
  _ALLOWED_PDB_TYPES = [GObject.TYPE_INT]

  _REGISTRABLE_TYPE_NAME = 'int'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.int_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0


class UintSetting(NumericSetting):
  """Class for unsigned integer settings.

  Allowed GIMP PDB types:
  * `GObject.TYPE_UINT`

  Default value: 0
  """

  _ALIASES = ['unsigned_integer']

  _ALLOWED_PDB_TYPES = [GObject.TYPE_UINT]

  _REGISTRABLE_TYPE_NAME = 'uint'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.int_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0


class DoubleSetting(NumericSetting):
  """Class for double (double-precision floating-point numbers) settings.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_DOUBLE`
  
  Default value: 0.0
  """

  _ALIASES = ['float']
  
  _ALLOWED_PDB_TYPES = [GObject.TYPE_DOUBLE]

  _REGISTRABLE_TYPE_NAME = 'double'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.double_spin_button]

  _DEFAULT_DEFAULT_VALUE = 0.0


class BoolSetting(Setting):
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

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]


class EnumSetting(Setting):
  """Class for settings wrapping an enumerated type (`GObject.GEnum` subclass).

  Allowed GIMP PDB types:
  * any `GObject.GEnum` subclass (e.g. `Gimp.RunMode`)

  Default value: The first item defined for the specified `GObject.GEnum`
    subclass (e.g. `Gimp.RunMode.INTERACTIVE`).
  """

  _REGISTRABLE_TYPE_NAME = 'enum'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.enum_combo_box]

  # `0` acts as a fallback in case `enum_type` has no values, which should not occur.
  _DEFAULT_DEFAULT_VALUE = lambda self: next(iter(self.enum_type.__enum_values__.values()), 0)

  _SUPPORTED_MODULES_WITH_ENUMS = {
    'Gimp': 'gi.repository.Gimp',
    'Gegl': 'gi.repository.Gegl',
    'GimpUi': 'gi.repository.GimpUi',
    'GObject': 'gi.repository.GObject',
    'GLib': 'gi.repository.GLib',
    'Gio': 'gi.repository.Gio',
  }

  def __init__(
        self,
        name: str,
        enum_type: Union[Type[GObject.GEnum], GObject.GType, str],
        excluded_values: Optional[Iterable[GObject.GEnum]] = None,
        **kwargs,
  ):
    """Initializes an `EnumSetting` instance.

    If ``pdb_type`` is specified as a keyword argument, it is ignored and
    always set to ``enum_type``.

    Args:
      name:
        Setting name. See the `name` property for more information.
      enum_type:
        Enumerated type as a `GObject.GEnum` subclass or a string representing
        the module path plus name of a `GObject.GEnum` subclass, e.g.
        ``'gi.repository.Gimp.RunMode'`` for `Gimp.RunMode`.
      excluded_values:
        List of enumerated values to be excluded from the setting GUI. This is
        useful in case this setting is used in a GIMP PDB procedure not
        supporting particular value(s).
      **kwargs:
        Additional keyword arguments that can be passed to the parent class'
        `__init__()`.
    """
    self._enum_type = self._process_enum_type(enum_type)
    self._excluded_values = self._process_excluded_values(excluded_values)

    kwargs['pdb_type'] = self._enum_type

    super().__init__(name, **kwargs)

  @property
  def enum_type(self) -> Type[GObject.GEnum]:
    """`GObject.GEnum` subclass whose values are used as setting values."""
    return self._enum_type

  @property
  def excluded_values(self) -> List[GObject.GEnum]:
    """`GObject.GEnum` values excluded from the setting GUI."""
    return self._excluded_values

  def to_dict(self):
    settings_dict = super().to_dict()

    settings_dict['enum_type'] = self.enum_type.__gtype__.name

    if 'excluded_values' in settings_dict:
      settings_dict['excluded_values'] = [int(value) for value in self.excluded_values]

    return settings_dict

  def _assign_value(self, value):
    self._value = self.enum_type(value)

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, int) and raw_value in self.enum_type.__enum_values__:
      return self.enum_type(raw_value)
    else:
      return raw_value

  def _value_to_raw(self, value):
    return int(value)

  def _validate(self, value):
    try:
      self.enum_type(value)
    except ValueError:
      return 'invalid value', 'invalid_value'

    if isinstance(value, GObject.GEnum) and not isinstance(value, self.enum_type):
      return (
        f'enumerated value has an invalid type "{type(value)}"',
        'invalid_type',
        False)

  def _get_pdb_type(self, pdb_type):
    return self._enum_type

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._enum_type,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  def _process_enum_type(self, enum_type):
    if isinstance(enum_type, GObject.GType):
      processed_enum_type = enum_type.name
    else:
      processed_enum_type = enum_type

    if isinstance(processed_enum_type, str):
      module_path, enum_class_name = self._get_enum_type_from_string(processed_enum_type)

      if not module_path or not enum_class_name:
        raise TypeError(f'"{processed_enum_type}" is not a valid GObject.GEnum type')

      module_with_enum = importlib.import_module(module_path)
      processed_enum_type = getattr(module_with_enum, enum_class_name)

    if not inspect.isclass(processed_enum_type):
      raise TypeError(f'{processed_enum_type} is not a class')

    if not issubclass(processed_enum_type, GObject.GEnum):
      raise TypeError(f'{processed_enum_type} is not a subclass of GObject.GEnum')

    return processed_enum_type

  def _process_excluded_values(self, excluded_values):
    if excluded_values is not None:
      return [self.enum_type(value) for value in excluded_values]
    else:
      return []

  def _get_enum_type_from_string(self, enum_type_str):
    # HACK: We parse the `GType` name to obtain the `GEnum` instance. Is there
    #  a more elegant way?
    for module_name, module_path in self._SUPPORTED_MODULES_WITH_ENUMS.items():
      if enum_type_str.startswith(module_name):
        return module_path, enum_type_str[len(module_name):]

    return None, None


class StringSetting(Setting):
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


class ChoiceSetting(Setting):
  """Class for settings with a limited number of values, accessed by their
  associated names.
  
  Allowed GIMP PDB types:
  * `GObject.TYPE_STRING`
  
  Default value: Name of the first item passed to the ``items`` parameter in
  `ChoiceSetting.__init__()`.
  
  To access an item value:

    setting.items[item name]
  
  To access an item display name:

    setting.items_display_names[item name]
  
  Raises:
    ValueError:
      The same numeric value was assigned to multiple items, or an uneven
      number of elements was passed to the ``items`` parameter in `__init__()`.
    KeyError:
      Invalid key for the `items` or `items_display_names` property.
  
  Message IDs for invalid values:
    * ``'invalid_value'``: The value assigned is not one of the items in this
      setting if the ``items`` parameter passed to `__init__()` was not empty.
    * ``'invalid_default_value'``: Item name is not valid (not found in the
      ``items`` parameter in `__init__()`) if the ``items`` parameter passed to
      `__init__()` was not empty.
  """

  _ALLOWED_PDB_TYPES = [GObject.TYPE_STRING]

  _REGISTRABLE_TYPE_NAME = 'choice'

  _ALLOWED_GUI_TYPES = [
    _SETTING_GUI_TYPES.combo_box,
    _SETTING_GUI_TYPES.radio_button_box,
    _SETTING_GUI_TYPES.choice_combo_box,
  ]

  _DEFAULT_DEFAULT_VALUE = lambda self: next(iter(self._items), '')
  
  def __init__(
        self,
        name: str,
        items: Optional[
          Union[
            List[Tuple[str, str]],
            List[Tuple[str, str, int]],
            List[Tuple[str, str, int, str]],
            Gimp.Choice]
        ] = None,
        procedure: Optional[Union[Gimp.Procedure, str]] = None,
        **kwargs,
  ):
    """Initializes a `ChoiceSetting` instance.

    Args:
      items:
        A list of (item name, item display name) tuples, (item name,
        item display name, item value) tuples or a `Gimp.Choice` instance
        filled with possible choices. For 2-element tuples, item values are
        assigned automatically, starting with 0. Use 3-element tuples to
        assign explicit item values. Values must be unique and specified in
        each tuple. Use only 2- or only 3-element tuples, they cannot be
        combined.
        If ``items`` is ``None`` or an empty list, any string can be assigned
        to this setting. This is a workaround to allow settings of this type
        to be created from GIMP PDB parameters as currently there is no way to
        obtain a list of choices from PDB parameters.
      procedure:
        A `Gimp.Procedure` instance, or name thereof, whose PDB parameter having
        the name ``name`` contains possible choices.
    """
    self._procedure = self._process_procedure(procedure)
    self._procedure_config = self._create_procedure_config(self._procedure)

    self._items, self._items_by_value, self._items_display_names, self._items_help, self._choice = (
      self._create_item_attributes(items))
    
    super().__init__(name, **kwargs)
  
  @property
  def items(self) -> Dict[str, int]:
    """A dictionary of (item name, item value) pairs."""
    return self._items

  @property
  def items_by_value(self) -> Dict[int, str]:
    """A dictionary of (item value, item name) pairs."""
    return self._items_by_value

  @property
  def items_display_names(self) -> Dict[str, str]:
    """A dictionary of (item name, item display name) pairs.
    
    Item display names can be used e.g. as combo box items in the GUI.
    """
    return self._items_display_names

  @property
  def items_help(self) -> Dict[str, str]:
    """A dictionary of (item name, item help) pairs.

    Item help describes the item in more detail.
    """
    return self._items_help

  @property
  def procedure(self) -> Union[Gimp.Procedure, None]:
    """A `Gimp.Procedure` instance containing the `Gimp.Choice` instance for
    this setting.
    """
    return self._procedure

  @property
  def procedure_config(self) -> Union[Gimp.ProcedureConfig, None]:
    """A `Gimp.ProcedureConfig` instance containing the `Gimp.Choice` instance
    for this setting.
    """
    return self._procedure_config

  def to_dict(self):
    settings_dict = super().to_dict()

    if 'items' in settings_dict:
      if settings_dict['items'] is None:
        settings_dict['items'] = []
      elif isinstance(settings_dict['items'], Gimp.Choice):
        settings_dict['items'] = [
          [
            name,
            self._choice.get_label(name),
            self._choice.get_id(name),
            self._choice.get_help(name),
          ]
          for name in self._choice.list_nicks()
        ]
      else:
        settings_dict['items'] = [list(elements) for elements in settings_dict['items']]

    if 'procedure' in settings_dict:
      if settings_dict['procedure'] is not None:
        settings_dict['procedure'] = self._procedure.get_name()

    return settings_dict

  def get_name(self) -> str:
    """Returns the item name corresponding to the current setting value.

    This is a more convenient and less verbose alternative to

      setting.items_by_value(setting.value)
    """
    return self._items_by_value[self.value]
  
  def get_item_display_names_and_values(self) -> List[Tuple[str, int]]:
    """Returns a list of (item display name, item value) tuples."""
    display_names_and_values = []
    for item_name, item_value in zip(self._items_display_names.values(), self._items.values()):
      display_names_and_values.append((item_name, item_value))
    return display_names_and_values
  
  def _resolve_default_value(self, default_value):
    if isinstance(default_value, type(Setting.DEFAULT_VALUE)):
      # We assume that at least one item exists (this is handled before this
      # method) and thus the default value is valid.
      return super()._resolve_default_value(default_value)
    else:
      if self._items:
        if default_value in self._items:
          return default_value
        else:
          self._handle_failed_validation(
            f'invalid default value "{default_value}"; must be one of {list(self._items)}',
            'invalid_default_value',
            prepend_value=False,
          )
      else:
        return default_value

  def _validate(self, item_name):
    if self._items and item_name not in self._items:
      return f'invalid item name; valid values: {list(self._items)}', 'invalid_value'

  @staticmethod
  def _process_procedure(procedure) -> Union[Gimp.Procedure, None]:
    if procedure is None:
      return None
    elif isinstance(procedure, Gimp.Procedure):
      return procedure
    elif isinstance(procedure, str):
      if Gimp.get_pdb().procedure_exists(procedure):
        return Gimp.get_pdb().lookup_procedure(procedure)
    else:
      raise TypeError('procedure must be None, a string or a Gimp.Procedure instance')

  @staticmethod
  def _create_procedure_config(procedure):
    if procedure is not None:
      return procedure.create_config()
    else:
      return None

  @staticmethod
  def _create_item_attributes(input_items):
    items = {}
    items_by_value = {}
    items_display_names = {}
    items_help = {}

    if not input_items:
      return items, items_by_value, items_display_names, items_help, Gimp.Choice.new()

    if isinstance(input_items, Gimp.Choice):
      for name in input_items.list_nicks():
        value = input_items.get_id(name)
        items[name] = value
        items_by_value[value] = name
        items_display_names[name] = input_items.get_label(name)
        items_help[name] = input_items.get_help(name)

      return items, items_by_value, items_display_names, items_help, input_items

    if all(len(elem) == 2 for elem in input_items):
      for i, (item_name, item_display_name) in enumerate(input_items):
        if item_name in items:
          raise ValueError('cannot use the same name for multiple items - they must be unique')

        items[item_name] = i
        items_by_value[i] = item_name
        items_display_names[item_name] = item_display_name
        items_help[item_name] = ''
    elif all(len(elem) in [3, 4] for elem in input_items):
      for item in input_items:
        if len(item) == 3:
          item_name, item_display_name, item_value = item
          item_help = ''
        else:
          item_name, item_display_name, item_value, item_help = item

        if item_name in items:
          raise ValueError('cannot use the same name for multiple items - they must be unique')

        if item_value in items_by_value:
          raise ValueError('cannot set the same value for multiple items - they must be unique')

        items[item_name] = item_value
        items_by_value[item_value] = item_name
        items_display_names[item_name] = item_display_name
        items_help[item_name] = item_help
    else:
      raise ValueError(
        'wrong number of tuple elements in items - must be only 2- or only 3-element tuples')

    choice = Gimp.Choice.new()
    for item in zip(items.items(), items_display_names.values(), items_help.values()):
      (name, value), display_name, help_ = item
      choice.add(name, value, display_name, help_)

    return items, items_by_value, items_display_names, items_help, choice

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._choice,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]


class ImageSetting(Setting):
  """Class for settings holding `Gimp.Image` objects.
  
  This class accepts as a value a file path to the image or image ID.
  If calling `to_dict()`, the image file path is returned or ``None`` if the
  image does not exist in the file system.
  
  Allowed GIMP PDB types:
  * `Gimp.Image`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The image assigned is invalid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Image]

  _REGISTRABLE_TYPE_NAME = 'image'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.image_combo_box]

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
    value = raw_value
    
    if isinstance(raw_value, int):
      value = Gimp.Image.get_by_id(raw_value)
    elif isinstance(raw_value, str):
      value = pgpdbutils.find_image_by_filepath(raw_value)
    
    return value
  
  def _value_to_raw(self, value):
    if value is not None and value.get_file() is not None:
      raw_value = value.get_file().get_path()
    else:
      raw_value = None
    
    return raw_value
  
  def _validate(self, image):
    if not self._none_ok and image is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if image is not None and not image.is_valid():
      return 'invalid image', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      GObject.ParamFlags.READWRITE,
    ]


class GimpItemSetting(Setting):
  """Abstract class for settings storing GIMP items - layers, channels, paths.
  
  This class accepts as a value one of the following:
  * a tuple (image file path, item type, item path) where item type is the name
    of the item's GIMP class (e.g. ``'Layer'``).
  * a tuple (item type, item ID). Item ID is are assigned by GIMP.
  * a `Gimp.Item` instance.

  If calling `to_dict()`, a tuple (image file path, item type, item path) is
  returned.
  """
  
  _ABSTRACT = True

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
  
  def _value_to_raw(self, value):
    return self._item_to_path(value)

  def _get_item_from_image_and_item_path(self, image_filepath, item_type_name, item_path):
    image = pgpdbutils.find_image_by_filepath(image_filepath)

    if image is None:
      return None

    return pgpdbutils.get_item_from_image_and_item_path(image, item_type_name, item_path)

  def _item_to_path(self, item):
    return pgpdbutils.get_item_as_path(item)

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      GObject.ParamFlags.READWRITE,
    ]


class ItemSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Item` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Item`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The item assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Item]

  _REGISTRABLE_TYPE_NAME = 'item'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.item_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _validate(self, item):
    if not self._none_ok and item is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if item is not None and not isinstance(item, Gimp.Item):
      return 'invalid item', 'invalid_value'


class DrawableSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Drawable` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Drawable`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The drawable assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Drawable]

  _REGISTRABLE_TYPE_NAME = 'drawable'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.drawable_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _validate(self, drawable):
    if not self._none_ok and drawable is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if drawable is not None and not drawable.is_drawable():
      return 'invalid drawable', 'invalid_value'


class LayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Layer` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Layer`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The layer assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Layer]

  _REGISTRABLE_TYPE_NAME = 'layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.layer_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _validate(self, layer):
    if not self._none_ok and layer is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if layer is not None and not layer.is_layer():
      return 'invalid layer', 'invalid_value'


class GroupLayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.GroupLayer` instances.

  Allowed GIMP PDB types:
  * `Gimp.GroupLayer`

  Message IDs for invalid values:
  * ``'invalid_value'``: The group layer assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.GroupLayer]

  _REGISTRABLE_TYPE_NAME = 'group_layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.group_layer_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, layer):
    if not self._none_ok and layer is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if layer is not None and not layer.is_group_layer():
      return 'invalid group layer', 'invalid_value'


class TextLayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.TextLayer` instances.

  Allowed GIMP PDB types:
  * `Gimp.TextLayer`

  Message IDs for invalid values:
  * ``'invalid_value'``: The text layer assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.TextLayer]

  _REGISTRABLE_TYPE_NAME = 'text_layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.text_layer_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, layer):
    if not self._none_ok and layer is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if layer is not None and not layer.is_text_layer():
      return 'invalid text layer', 'invalid_value'


class LayerMaskSetting(GimpItemSetting):
  """Class for settings holding `Gimp.LayerMask` instances.

  When serializing to a source, the setting value as returned by
  `Setting.to_dict()` corresponds to the layer path the layer mask is
  attached to.

  Allowed GIMP PDB types:
  * `Gimp.LayerMask`

  Message IDs for invalid values:
  * ``'invalid_value'``: The layer mask assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.LayerMask]

  _REGISTRABLE_TYPE_NAME = 'layer_mask'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.layer_mask_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, drawable):
    if not self._none_ok and drawable is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if drawable is not None and not drawable.is_layer_mask():
      return 'invalid layer mask', 'invalid_value'

  def _get_item_from_image_and_item_path(self, image_filepath, item_type_name, item_path):
    layer = super()._get_item_from_image_and_item_path(image_filepath, item_type_name, item_path)

    if layer is not None:
      return layer.get_mask()
    else:
      return None

  def _item_to_path(self, item):
    if item is None:
      return None

    layer = Gimp.Layer.from_mask(item)
    if layer is not None:
      return super()._item_to_path(layer)
    else:
      return None


class ChannelSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Channel` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Channel`

  Message IDs for invalid values:
  * ``'invalid_value'``: The channel assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Channel]

  _REGISTRABLE_TYPE_NAME = 'channel'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.channel_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _validate(self, channel):
    if not self._none_ok and channel is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if channel is not None and not channel.is_channel():
      return 'invalid channel', 'invalid_value'


class SelectionSetting(ChannelSetting):
  """Class for settings holding the current selection.
  
  A selection in GIMP is internally represented as a `Gimp.Channel` instance.
  Unlike `ChannelSetting`, this setting does not support GUI (there is no need
  for GUI).
  
  Allowed GIMP PDB types:
  * `Gimp.Selection`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The channel assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Selection]

  _REGISTRABLE_TYPE_NAME = 'selection'

  _ALLOWED_GUI_TYPES = []


class PathSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Path` instances.
  
  Allowed GIMP PDB types:
  * `Gimp.Path`
  
  Message IDs for invalid values:
  * ``'invalid_value'``: The path assigned is not valid.
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Path]

  _REGISTRABLE_TYPE_NAME = 'path'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.path_combo_box]
  
  def _copy_value(self, value):
    return value
  
  def _validate(self, path):
    if not self._none_ok and path is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if path is not None and not path.is_path():
      return 'invalid path', 'invalid_value'


class ColorSetting(Setting):
  """Class for settings holding `Gegl.Color` instances.
  
  Allowed GIMP PDB types:
  * `Gegl.Color`
  
  Default value: `Gegl.Color` instance with RGBA color `(0.0, 0.0, 0.0, 1.0)`.

  Message IDs for invalid values:
  * ``'invalid_value'``: The color assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gegl.Color]

  _REGISTRABLE_TYPE_NAME = 'color'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.color_button]

  # Create default value dynamically to avoid potential errors on GIMP startup.
  _DEFAULT_DEFAULT_VALUE = lambda self: Gegl.Color.new('black')

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list):
      color = Gegl.Color()

      if len(raw_value) >= 4:
        color.set_rgba(*raw_value[:4])

      return color
    else:
      return raw_value
  
  def _value_to_raw(self, value):
    color = value.get_rgba()
    return [color.red, color.green, color.blue, color.alpha]
  
  def _validate(self, color):
    if not isinstance(color, Gegl.Color):
      return 'invalid color', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      True,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]


class DisplaySetting(Setting):
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
    if not self._none_ok and display is None:
      return 'None is not allowed for this setting', 'invalid_value'

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


class ParasiteSetting(Setting):
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

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.parasite_box]

  # Create default value dynamically to avoid potential errors on GIMP startup.
  _DEFAULT_DEFAULT_VALUE = (
    lambda self: Gimp.Parasite.new(self.name if self.name else self.DEFAULT_PARASITE_NAME, 0, b''))

  def _copy_value(self, value):
    return value
  
  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, list):
      return Gimp.Parasite.new(*raw_value)
    else:
      return raw_value
  
  def _value_to_raw(self, value):
    return [value.get_name(), value.get_flags(), value.get_data()]
  
  def _validate(self, parasite):
    if not isinstance(parasite, Gimp.Parasite):
      return 'invalid parasite', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      GObject.ParamFlags.READWRITE,
    ]


class FileSetting(Setting):
  """Class for settings storing files or directories as `Gio.File` instances
  (``GFile`` type).

  Allowed GIMP PDB types:
  * `Gio.File`

  Default value:
    A `Gio.File` instance with no path (`Gio.File.get_path()` returns ``None``).
  """

  _DEFAULT_DEFAULT_VALUE = lambda self: Gio.file_new_for_path('')

  _ALLOWED_PDB_TYPES = [Gio.File]

  _REGISTRABLE_TYPE_NAME = 'file'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.g_file_entry]

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, str):
      return Gio.file_new_for_path(raw_value)
    elif raw_value is None:
      return Gio.file_new_for_path('')
    else:
      return raw_value

  def _value_to_raw(self, value):
    return value.get_path()

  def _validate(self, file_):
    if not isinstance(file_, Gio.File):
      return 'invalid file', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      GObject.ParamFlags.READWRITE,
    ]


class ExportOptionsSetting(Setting):
  """Class for settings holding file export options.

  Allowed GIMP PDB types:
  * `Gimp.ExportOptions`

  Message IDs for invalid values:
  * ``'invalid_value'``: The `Gimp.ExportOptions` instance is not valid.
  """

  _DEFAULT_DEFAULT_VALUE = None

  _ALLOWED_PDB_TYPES = [Gimp.ExportOptions]

  _ALLOWED_GUI_TYPES = []


class BytesSetting(Setting):
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
      return GLib.Bytes.new(pgutils.escaped_string_to_bytes(raw_value, remove_overflow=True))
    elif isinstance(raw_value, bytes):
      return GLib.Bytes.new(raw_value)
    elif isinstance(raw_value, list):  # Presumably list of valid integers
      try:
        return GLib.Bytes.new(raw_value)
      except (TypeError, ValueError, OverflowError):
        return GLib.Bytes.new()
    else:
      return raw_value

  def _value_to_raw(self, value):
    return list(value.get_data())

  def _validate(self, file_):
    if not isinstance(file_, GLib.Bytes):
      return 'invalid byte sequence', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      GObject.ParamFlags.READWRITE,
    ]


class GimpResourceSetting(Setting):
  """Abstract class for settings storing `Gimp.Resource` instances (brushes,
  fonts, etc.).

  Default value:
    If ``default_to_context`` is ``False``, the default value is ``None``.
    If ``default_to_context`` is ``True``, it is the currently active resource
    obtainable via `Gimp.context_get_<resource_type>()`.

  Message IDs for invalid values:
  * ``'invalid_value'``: The resource is not valid.
  """

  _ABSTRACT = True

  _DEFAULT_DEFAULT_VALUE = None

  def __init__(
        self,
        name: str,
        resource_type: Union[GObject.GType, Type[GObject.GObject]],
        none_ok: bool = True,
        default_to_context: bool = True,
        **kwargs,
  ):
    self._resource_type = resource_type
    self._none_ok = none_ok
    self._default_to_context = default_to_context

    if self._default_to_context:
      kwargs['default_value'] = self._get_default_value_from_gimp_context()

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  @property
  def default_to_context(self):
    """If ``True``, `the default setting value is inferred from the GIMP
    context (the currently active resource) and the ``default_value`` parameter
    in `__init__()` is ignored.
    """
    return self._none_ok

  def _get_default_value_from_gimp_context(self):
    return None

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

      return resource
    else:
      return raw_value

  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
      }
    else:
      return None

  def _validate(self, resource):
    if not self._none_ok and resource is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if resource is not None and not resource.is_valid():
      return 'invalid resource', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      self._default_value,
      self._default_to_context,
      GObject.ParamFlags.READWRITE,
    ]


class BrushSetting(GimpResourceSetting):
  """Class for settings storing brushes.
  
  Allowed GIMP PDB types:
  * `Gimp.Brush`

  Default value: ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Brush]

  _REGISTRABLE_TYPE_NAME = 'brush'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.brush_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Brush, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_brush()
  
  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
        'angle': resource.get_angle().angle,
        'aspect_ratio': resource.get_aspect_ratio().aspect_ratio,
        'hardness': resource.get_hardness().hardness,
        'radius': resource.get_radius().radius,
        'shape': int(resource.get_shape().shape),
        'spacing': resource.get_spacing(),
        'spikes': resource.get_spikes().spikes,
      }
    else:
      return None


class FontSetting(GimpResourceSetting):
  """Class for settings storing fonts.
  
  Allowed GIMP PDB types:
  * `Gimp.Font`
  
  Default value: ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Font]

  _REGISTRABLE_TYPE_NAME = 'font'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.font_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Font, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_font()


class GradientSetting(GimpResourceSetting):
  """Class for settings storing gradients.
  
  Allowed GIMP PDB types:
  * `Gimp.Gradient`
  
  Default value: ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Gradient]

  _REGISTRABLE_TYPE_NAME = 'gradient'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.gradient_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Gradient, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_gradient()


class PaletteSetting(GimpResourceSetting):
  """Class for settings storing color palettes.
  
  Allowed GIMP PDB types:
  * `Gimp.Palette`
  
  Default value: ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Palette]

  _REGISTRABLE_TYPE_NAME = 'palette'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.palette_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Palette, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_palette()

  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
        'columns': resource.get_columns(),
      }
    else:
      return None


class PatternSetting(GimpResourceSetting):
  """Class for settings storing patterns.
  
  Allowed GIMP PDB types:
  * `Gimp.Pattern`
  
  Default value: ``None``
  """
  
  _ALLOWED_PDB_TYPES = [Gimp.Pattern]

  _REGISTRABLE_TYPE_NAME = 'pattern'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.pattern_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Pattern, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_pattern()


class UnitSetting(Setting):
  """Class for settings storing `Gimp.Unit` instances.

  Allowed GIMP PDB types:
  * `Gimp.Unit`

  Default value: A `Gimp.Unit.pixel()` instance representing pixels.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Unit]

  _REGISTRABLE_TYPE_NAME = 'unit'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.unit_combo_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: Gimp.Unit.pixel()

  def __init__(self, name: str, show_pixels: bool = True, show_percent: bool = True, **kwargs):
    self._show_pixels = show_pixels
    self._show_percent = show_percent

    self._built_in_units = {
      Gimp.Unit.inch(): 'inch',
      Gimp.Unit.mm(): 'mm',
      Gimp.Unit.percent(): 'percent',
      Gimp.Unit.pica(): 'pica',
      Gimp.Unit.pixel(): 'pixel',
      Gimp.Unit.point(): 'point',
    }

    super().__init__(name, **kwargs)

  @property
  def show_pixels(self):
    """``True`` if pixels should be displayed as a unit for the setting's GUI,
    ``False`` otherwise.
    """
    return self._show_pixels

  @property
  def show_percent(self):
    """``True`` if percentage should be displayed as a unit for the setting's
    GUI, ``False`` otherwise.
    """
    return self._show_percent

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._show_pixels,
      self._show_percent,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]

  def _validate(self, unit):
    if unit is None or not isinstance(unit, Gimp.Unit):
      return 'invalid unit', 'invalid_value'

  def _raw_to_value(self, raw_value: Union[Iterable, str]):
    if isinstance(raw_value, str):
      if hasattr(Gimp.Unit, raw_value):
        return getattr(Gimp.Unit, raw_value)()
      else:
        return raw_value
    elif isinstance(raw_value, Iterable):
      return Gimp.Unit.new(*raw_value)
    else:
      return raw_value

  def _value_to_raw(self, unit: Gimp.Unit) -> Union[List, str]:
    if unit in self._built_in_units:
      return self._built_in_units[unit]
    else:
      return [
        unit.get_name(),
        unit.get_factor(),
        unit.get_digits(),
        unit.get_symbol(),
        unit.get_abbreviation(),
      ]


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
  type (e.g. `Gimp.DoubleArray` for float arrays), then the array setting can
  be registered to the GIMP PDB. To disable registration, pass ``pdb_type=None``
  in `Setting.__init__()` as one normally would. The PDB type of individual
  elements cannot be customized as it appears that the GIMP API provides a fixed
  element type for each array type (e.g. `GObject.TYPE_DOUBLE` for
  `Gimp.DoubleArray`).
  
  Validation of setting values is performed for each element individually.

  If the input value to `set_value()` is not an iterable, it is wrapped in a
  tuple. Thus, if validation fails, ``'invalid_value'`` message ID is never
  returned.
  
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
  * `Gimp.Int32Array`
  * `Gimp.DoubleArray`
  * `GObject.TYPE_STRV` (string array)
  * object arrays, i.e. arrays containing GIMP objects (e.g. images, layers,
    channels, ...).
  
  Default value: `()`
  
  Message IDs for invalid values:
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
  
  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.array_box]

  _DEFAULT_DEFAULT_VALUE = ()

  _NATIVE_ARRAY_PDB_TYPES: Dict[Type[Setting], Tuple[GObject.GType, GObject.GType]]
  _NATIVE_ARRAY_PDB_TYPES = {
    IntSetting: (Gimp.Int32Array, GObject.TYPE_INT, 'int32_array'),
    DoubleSetting: (Gimp.DoubleArray, GObject.TYPE_DOUBLE, 'double_array'),
    StringSetting: (GObject.TYPE_STRV, GObject.TYPE_STRING, 'string_array'),
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
        ``element_type`` is ``'int'``), you can optionally pass
        ``element_min_value=<value>`` to set the minimum value for all integer
        array elements.
        If ``element_pdb_type`` is specified, it will be ignored as each array
        type has one allowed PDB type for individual elements (e.g.
        `GObject.TYPE_DOUBLE` for `Gimp.DoubleArray`).
    """
    self._element_type = meta_.process_setting_type(element_type)
    self._min_size = min_size if min_size is not None else 0
    self._max_size = max_size
    
    self._element_kwargs = {
      key[len('element_'):]: value for key, value in kwargs.items()
      if key.startswith('element_')}

    if 'pdb_type' in self._element_kwargs:
      # Enforce a pre-set value for `element_pdb_type` as it appears that the
      # GIMP API allows only one type per array type.
      self._element_kwargs['pdb_type'] = self._get_default_element_pdb_type()
    
    self._reference_element = self._create_reference_element()

    if 'default_value' not in self._element_kwargs:
      self._element_kwargs['default_value'] = self._reference_element.default_value
    else:
      # noinspection PyProtectedMember
      self._element_kwargs['default_value'] = self._reference_element._raw_to_value(
        self._element_kwargs['default_value'])

    for key, value in self._element_kwargs.items():
      pgutils.create_read_only_property(self, f'element_{key}', value)
    
    self._elements = []
    
    array_kwargs = {key: value for key, value in kwargs.items() if not key.startswith('element_')}
    
    super().__init__(name, **array_kwargs)

  @property
  def value(self):
    """The array (setting value) as a tuple."""
    # This ensures that this property is always up-to-date no matter what events
    # are connected to individual elements.
    self._value = self._array_as_tuple()
    return self._value

  @property
  def value_for_pdb(self):
    """The array (setting value) in a format appropriate to be used as a PDB
    procedure argument.

    Certain array types as GIMP PDB procedure parameters (such as
    `Gimp.DoubleArray`) cannot accept a Python list/tuple and must be
    converted to the appropriate GObject-compatible type. The `value`
    property ensures that the array is converted to a GObject-compatible type.

    To access the array as a Python-like structure, use the `value` property
    returning the array values as a tuple. If you need to work directly with
    array elements as `Setting` instances, use `get_elements()`.
    """
    # This ensures that this property is always up-to-date no matter what events
    # are connected to individual elements.
    self._value = self._array_as_tuple()
    return array_as_pdb_compatible_type(self._value, self.element_type)

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

  def get_pdb_param(self) -> Union[List, None]:
    if self.can_be_used_in_pdb():
      if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
        return [
          self._NATIVE_ARRAY_PDB_TYPES[self.element_type][2],
          self._pdb_name,
          self._display_name,
          self._description,
          GObject.ParamFlags.READWRITE,
        ]
      elif self._reference_element.can_be_used_in_pdb():
        return [
          'core_object_array',
          self._pdb_name,
          self._display_name,
          self._description,
          self._reference_element.pdb_type,
          GObject.ParamFlags.READWRITE,
        ]
      else:
        return None
    else:
      return None

  def to_dict(self) -> Dict:
    settings_dict = super().to_dict()
    
    for key, val in settings_dict.items():
      if key == 'element_default_value':
        # noinspection PyProtectedMember
        settings_dict[key] = self._reference_element._value_to_raw(val)
      elif key == 'element_type':
        settings_dict[key] = _SETTING_TYPES[type(self._reference_element)]
    
    return settings_dict
  
  def __getitem__(self, index_or_slice: Union[int, slice]) -> Union[Setting, List[Setting]]:
    """Returns an array element at the specified index, or a list of elements
    if given a slice.
    """
    return self._elements[index_or_slice]
  
  def __delitem__(self, index: int):
    """Removes an array element at the specified index."""
    if len(self._elements) == self._min_size:
      self._handle_failed_validation(
        f'cannot delete any more elements - at least {self._min_size} elements must be present',
        'delete_below_min_size',
        prepend_value=False,
      )
    
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
      self._handle_failed_validation(
        f'cannot add any more elements - at most {self._max_size} elements are allowed',
        'add_above_max_size',
        prepend_value=False,
      )
    
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
    """Returns a list of array elements as `Setting` instances."""
    return list(self._elements)
  
  def _raw_to_value(self, raw_value_array):
    if isinstance(raw_value_array, Iterable) and not isinstance(raw_value_array, str):
      # noinspection PyProtectedMember
      return tuple(
        self._reference_element._raw_to_value(raw_value)
        for raw_value in raw_value_array)
    else:
      # Convert to a safe value so that subsequent post-processing does not fail.
      return (raw_value_array,)
  
  def _value_to_raw(self, value_array):
    # noinspection PyProtectedMember
    return [
      self._reference_element._value_to_raw(value)
      for value in value_array]
  
  def _validate(self, value_array):
    if not hasattr(value_array, '__len__'):
      value_array = list(value_array)

    if self._min_size < 0:
      self._handle_failed_validation(
        f'minimum size ({self._min_size}) cannot be negative',
        'negative_min_size',
        prepend_value=False,
      )
    elif self._max_size is not None and self._min_size > self._max_size:
      self._handle_failed_validation(
        f'minimum size ({self._min_size}) cannot be greater than maximum size ({self._max_size})',
        'min_size_greater_than_max_size',
        prepend_value=False,
      )
    elif self._min_size > len(value_array):
      self._handle_failed_validation(
        (f'minimum size ({self._min_size}) cannot be greater'
         f' than the length of the value ({len(value_array)})'),
        'min_size_greater_than_value_length',
        prepend_value=False,
      )
    elif self._max_size is not None and self._max_size < len(value_array):
      self._handle_failed_validation(
        (f'maximum size ({self._max_size}) cannot be less'
         f' than the length of the value ({len(value_array)})'),
        'max_size_less_than_value_length',
        prepend_value=False,
      )
    
    for value in value_array:
      # noinspection PyProtectedMember
      self._reference_element._validate(value)
    self._reference_element.reset()
  
  def _assign_value(self, value_array):
    self._elements.clear()

    for value in value_array:
      element = self._create_element(value)
      self._elements.append(element)

    self._value = self._array_as_tuple()
  
  def _apply_gui_value_to_setting(self, value):
    # No assignment takes place to prevent breaking the sync between the array
    # and the GUI.
    self.invoke_event('value-changed')
  
  def _copy_value(self, value):
    self._elements = [self._create_element(element_value) for element_value in value]
    return self._array_as_tuple()
  
  def _get_default_pdb_type(self):
    if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
      return self._NATIVE_ARRAY_PDB_TYPES[self.element_type][0]
    elif self._reference_element.can_be_used_in_pdb():
      return GObject.GType.from_name('GimpCoreObjectArray')
    else:
      return None

  def _get_default_element_pdb_type(self):
    if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
      return self._NATIVE_ARRAY_PDB_TYPES[self.element_type][1]
    elif self._reference_element.can_be_used_in_pdb():
      return self._reference_element.pdb_type
    else:
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
  
  def _array_as_tuple(self):
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
    """If ``True``, ``None`` is treated as a valid value when calling
    `set_value()`.
    """
    return self._nullable
  
  def _validate(self, value):
    if value is None and not self._nullable:
      return (
        'cannot assign a null value (None) if the setting is not nullable',
        'value_is_none',
        False,
      )


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
  
  def _value_to_raw(self, value):
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
  
  def _value_to_raw(self, value):
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


def get_setting_type_and_kwargs(
      gtype: GObject.GType,
      pdb_param_info: Optional[GObject.ParamSpec] = None,
      pdb_procedure: Optional[Gimp.Procedure] = None,
) -> Union[Tuple[Type[Setting], Dict[str, Any]], None]:
  """Given a GIMP PDB parameter type, returns the corresponding `Setting`
  subclass and keyword arguments passable to its ``__init__()`` method.

  Some of the keyword arguments passable may be positional arguments, such as
  ``enum_type`` for `EnumSetting`.

  If ``gtype`` does not match any `setting.Setting` subclass, ``None`` is
  returned.

  Args:
    gtype:
      `GObject.GType` instance representing a GIMP PDB parameter.
    pdb_param_info:
      Object representing GIMP PDB parameter information, obtainable via
      `Gimp.Procedure.get_arguments()`. This is used to infer the element type
      for an object array argument (images, layers, etc.) and to help obtain
      keyword arguments for `ChoiceSetting`. If ``None``,
      the `StringSetting` type will be returned instead.
    pdb_procedure:
      If not ``None``, it is a `Gimp.Procedure` instance allowing to infer
      string choices for the `ChoiceSetting` type. If ``None``,
      the `StringSetting` type will be returned instead.

  Returns:
    Tuple of (`setting.Setting` subclass, dictionary of keyword arguments to be
    passed to ``__init__()`` for the returned `setting.Setting` subclass), or
    ``None`` if there is no matching `setting.Setting` subclass for ``gtype``.
  """
  if gtype in meta_.GTYPES_AND_SETTING_TYPES:
    if (pdb_param_info is not None
        and isinstance(pdb_param_info, Gimp.ParamChoice)
        and pdb_procedure is not None):
      return (
        ChoiceSetting,
        dict(
          items=None,
          procedure=pdb_procedure,
          gui_type=_SETTING_GUI_TYPES.choice_combo_box))
    else:
      # If multiple `GType`s map to the same `Setting` subclass, use the
      # `Setting` subclass registered (i.e. declared) the earliest.
      setting_type = meta_.GTYPES_AND_SETTING_TYPES[gtype][0]

      # Explicitly pass `gtype` as a `pdb_type` so that e.g. an `IntSetting`
      # instance can have its minimum and maximum values properly adjusted.
      return setting_type, dict(pdb_type=gtype)
  elif hasattr(gtype, 'parent') and gtype.parent == GObject.GEnum.__gtype__:
    return EnumSetting, dict(enum_type=gtype)
  elif gtype in _ARRAY_GTYPES_TO_SETTING_TYPES:
    return _ARRAY_GTYPES_TO_SETTING_TYPES[gtype]
  elif (hasattr(gtype, 'name')
        and gtype.name == 'GimpCoreObjectArray'
        and pdb_param_info is not None):
    return get_array_setting_type_from_gimp_core_object_array(pdb_param_info)
  else:
    return None


def get_array_setting_type_from_gimp_core_object_array(
      pdb_param_info: GObject.ParamSpec,
) -> Union[Tuple[Type[ArraySetting], Dict[str, Any]], None]:
  # HACK: Rely on the parameter name to infer the correct underlying object type.
  if pdb_param_info.name == 'images':
    return ArraySetting, dict(element_type=ImageSetting)
  elif pdb_param_info.name == 'drawables':
    return ArraySetting, dict(element_type=DrawableSetting)
  elif pdb_param_info.name == 'layers':
    return ArraySetting, dict(element_type=LayerSetting)
  elif pdb_param_info.name == 'channels':
    return ArraySetting, dict(element_type=ChannelSetting)
  elif pdb_param_info.name == 'paths':
    return ArraySetting, dict(element_type=PathSetting)
  elif pdb_param_info.name == 'children':
    return ArraySetting, dict(element_type=ItemSetting)
  else:
    return None


def array_as_pdb_compatible_type(
      values: Tuple[Any, ...],
      element_setting_type: Optional[Type[Setting]] = None,
) -> Union[Tuple[Any, ...], Gimp.Int32Array, Gimp.DoubleArray]:
  """Returns an array suitable to be passed to a GIMP PDB procedure."""
  if element_setting_type == IntSetting:
    array = GObject.Value(Gimp.Int32Array)
    Gimp.value_set_int32_array(array, values)
    return array.get_boxed()
  elif element_setting_type == DoubleSetting:
    array = GObject.Value(Gimp.DoubleArray)
    Gimp.value_set_double_array(array, values)
    return array.get_boxed()
  else:
    return values


ValueNotValidData = collections.namedtuple('ValueNotValidData', ['message', 'id'])


_ARRAY_GTYPES_TO_SETTING_TYPES = {
  Gimp.Int32Array.__gtype__: (ArraySetting, dict(element_type=IntSetting)),
  Gimp.DoubleArray.__gtype__: (ArraySetting, dict(element_type=DoubleSetting)),
  GObject.TYPE_STRV: (ArraySetting, dict(element_type=StringSetting)),
}


__all__ = [
  'get_setting_type_and_kwargs',
  'get_array_setting_type_from_gimp_core_object_array',
  'array_as_pdb_compatible_type',
  'ValueNotValidData',
]

for name_, class_ in inspect.getmembers(sys.modules[__name__], inspect.isclass):
  if issubclass(class_, Setting):
    __all__.append(name_)
