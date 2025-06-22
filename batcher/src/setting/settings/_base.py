"""API to create and manage plug-in settings."""

from __future__ import annotations

from collections.abc import Iterable
import copy
from typing import Dict, List, Optional, Set, Union, Tuple, Type

from gi.repository import GObject

from src import utils

from .. import meta as meta_
from .. import persistor as persistor_
from .. import presenter as presenter_
from .. import utils as utils_


_SETTING_TYPES = meta_.SETTING_TYPES
_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'Setting',
]


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

  * ``'gui-attached-to-grid'``: invoked after the setting GUI is attached to a
    `Gtk.Grid` (such as via `gui.utils_grid.attach_widget_to_grid()`).

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
        gui_kwargs: Optional[Dict] = None,
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
      gui_kwargs:
        Keyword arguments when instantiating a `setting.Presenter` associated
        with this setting. ``gui_kwargs`` is used within `Setting.__init__()`
        and every time `set_gui()` is called.
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

    self._gui_kwargs = gui_kwargs
    self._gui_type = self._get_gui_type(gui_type)
    self._gui_type_kwargs = gui_type_kwargs

    null_presenter_kwargs = dict(
      widget=None,
      setting_value_synchronizer=self._setting_value_synchronizer,
      auto_update_gui_to_setting=auto_update_gui_to_setting,
    )
    if self._gui_kwargs:
      null_presenter_kwargs.update(self._gui_kwargs)

    self._gui = presenter_.NullPresenter(self, **null_presenter_kwargs)

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

  def __str__(self) -> str:
    return utils.stringify_object(self, self.name)

  def __repr__(self) -> str:
    return utils.reprify_object(self, self.name)

  def get_path(self, relative_path_group: Union['src.setting.Group', str, None] = None) -> str:
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
        gui_kwargs: Optional[Dict] = None,
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
      gui_kwargs:
        Keyword arguments when instantiating a `setting.Presenter` associated
        with this setting. If ``None``, the ``gui_kwargs`` parameter specified
        in `__init__()` is used instead.
      gui_type_kwargs:
        Keyword arguments for instantiating a widget associated with a
        `setting.Presenter` subclass. If ``None``, the ``gui_type_kwargs``
        parameter specified in `__init__()` is used instead.
      copy_previous_value:
        See `setting.Presenter.__init__()`.
      copy_previous_visible:
        See `setting.Presenter.__init__()`.
      copy_previous_sensitive:
        See `setting.Presenter.__init__()`.
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

    if gui_kwargs is None:
      gui_kwargs = self._gui_kwargs

    if gui_type_kwargs is None:
      gui_type_kwargs = self._gui_type_kwargs

    processed_gui_kwargs = dict(
      widget=widget,
      setting_value_synchronizer=self._setting_value_synchronizer,
      auto_update_gui_to_setting=auto_update_gui_to_setting,
      create_widget_kwargs=gui_type_kwargs,
      previous_presenter=self._gui,
      copy_previous_value=copy_previous_value,
      copy_previous_visible=copy_previous_visible,
      copy_previous_sensitive=copy_previous_sensitive,
    )
    if gui_kwargs:
      processed_gui_kwargs.update(gui_kwargs)

    self._gui = processed_gui_type(self, **processed_gui_kwargs)

    self.invoke_event('after-set-gui')

  def uniquify_name(self, group: 'src.setting.Group'):
    """Modifies the ``name`` attribute to be unique within all immediate
    children of the specified ``group``.

    See `setting.utils.get_unique_setting_name` for more information.
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

  def validate(self, value) -> Union[None, utils_.ValueNotValidData]:
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

      return utils_.ValueNotValidData(*value_not_valid_args)
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

  def get_allowed_gui_types(self) -> List[Type[presenter_.Presenter]]:
    """Returns the list of allowed GUI types for this setting type."""
    return [
      meta_.process_setting_gui_type(type_or_name) for type_or_name in self._ALLOWED_GUI_TYPES]

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
        settings_dict[key] = self._do_value_to_raw(val)
      elif key == 'tags':
        settings_dict[key] = list(val)
      else:
        settings_dict[key] = val

    settings_dict.update({
      'name': self.name,
      'value': self._do_value_to_raw(self.value),
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
    validation. If a value is not valid, the overridden method must return a
    tuple consisting of at least a message and a message ID (a string
    indicating the type of message). If a value is valid, the overridden
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

  def _do_value_to_raw(self, value):
    try:
      return self._value_to_raw(value)
    except Exception as e:
      raise type(e)(f'{str(e)}; setting: "{self.get_path()}"') from e

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

    formatted_traceback = utils.get_traceback(stack_levels_to_keep=-2)

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
      resolved_default_value = self._raw_to_value(default_value)

      # This ensures that the processed value is used in `to_dict()` rather than
      # the raw value to avoid errors when persisting the setting.
      if 'default_value' in self._dict_on_init:
        self._dict_on_init['default_value'] = resolved_default_value

      return resolved_default_value

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
