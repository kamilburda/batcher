"""Classes to keep settings and their associated GUI widgets in sync."""

from __future__ import annotations

import abc
from typing import Dict, Optional

from .. import utils as pgutils

from . import meta as meta_

__all__ = [
  'Presenter',
  'NullPresenter',
]


class SettingValueSynchronizer:
  """Helper class allowing `setting.Setting` and `setting.Presenter` instances
  to keep their values in sync.
  """
  
  def __init__(self):
    self.apply_setting_value_to_gui = pgutils.empty_func
    self.apply_gui_value_to_setting = pgutils.empty_func


class Presenter(metaclass=meta_.PresenterMeta):
  """Wrapper of a GUI widget (button, window, etc.) for `setting.Setting`
  instances.
  
  Various widget have different attributes or methods to access and/or modify
  their appearance and behavior. This class provides a unified interface to
  access several such properties, particularly the "value" of a widget,
  its visible or sensitive state. The value represents the state of the
  widget that is synchronized with the corresponding setting. For example,
  the checked/unchecked state of a checkbox would be treated as a value,
  and it would be synchronized with a `setting.BoolSetting` instance.

  Subclasses of `Presenter` can wrap any attribute of a widget as a value.
  Specifically, accessing and modifying the value must be defined in the
  `get_value()` and `_set_value()` methods, respectively. The value does not
  have to be a "typical" property, e.g. the checked state of a check button,
  but also e.g. the label of the check button.
  
  Instances of this class should not be created directly. Instead, use the
  `setting.Setting.gui` property to access a setting's `Presenter` instance.
  """
  
  _ABSTRACT = True
  
  _VALUE_CHANGED_SIGNAL = None
  """Object that indicates the type of event to connect to a GUI widget.
  
  Once the event is triggered, it assigns the widget value to the setting 
  value. If this attribute is ``None``, no event can be connected.
  """
  
  def __init__(
        self,
        setting: 'setting.Setting',
        widget=None,
        setting_value_synchronizer: Optional[SettingValueSynchronizer] = None,
        auto_update_gui_to_setting: bool = True,
        create_widget_kwargs: Optional[Dict] = None,
        previous_presenter: Presenter = None,
        copy_previous_value: bool = True,
        copy_previous_visible: bool = True,
        copy_previous_sensitive: bool = True,
  ):
    """Initializes a `Presenter` instance.

    You should not instantiate a `Presenter` class directly. A `Presenter`
    instance is accessible via the `setting.Setting.gui` propperty.

    Args:
      setting:
        A `setting.Setting` instance.
      widget:
        A GUI widget to be wrapped by this class.

        If ``widget`` is ``None``, a new widget is created automatically. If
        the specific `Presenter` subclass does not support creating a widget,
        pass an existing widget.
      setting_value_synchronizer:
       A `SettingValueSynchronizer` instance to synchronize values between
       ``setting`` and this instance.
      auto_update_gui_to_setting:
        If ``True``, ``setting.value`` is updated automatically if the GUI
        value is updated. This parameter does not have any effect if:
          * the `Presenter` class cannot provide automatic GUI-to-setting
            update, or

          * ``previous_presenter`` is not ``None`` and the automatic
            GUI-to-setting update was disabled in that presenter.
      create_widget_kwargs:
        Keyword arguments used when creating ``widget``. See the
        `setting.Presenter._create_widget()` method in particular
        `setting.Presenter` subclasses for available keyword arguments.
      previous_presenter:
        `Presenter` instance that was previously assigned to ``setting`` (as
        the ``setting.gui`` attribute). The state from that `Presenter`
        instance will be copied to this object. If ``previous_presenter`` is
        ``None``, only ``setting.value`` will be copied to this instance.
      copy_previous_value:
        If ``True``, the value from ``previous_presenter`` is copied if not
        ``None``, otherwise ``setting.value`` is copied.
      copy_previous_visible:
        If ``True``, the visible state from ``previous_presenter`` is copied.
      copy_previous_sensitive:
        If ``True``, the sensitive state from ``previous_presenter`` is copied.
    """
    self._setting = setting
    self._widget = widget

    if setting_value_synchronizer is not None:
      self._setting_value_synchronizer = setting_value_synchronizer
    else:
      self._setting_value_synchronizer = SettingValueSynchronizer()
    
    if auto_update_gui_to_setting:
      self._value_changed_signal = self._VALUE_CHANGED_SIGNAL
    else:
      self._value_changed_signal = None

    self._ignore_on_value_changed = False

    self._setting_value_synchronizer.apply_setting_value_to_gui = self._apply_setting_value_to_gui

    if create_widget_kwargs is None:
      create_widget_kwargs = {}

    if self._widget is None:
      self._widget = self._create_widget(setting, **create_widget_kwargs)

      if self._widget is None:
        raise ValueError(
          (f'cannot instantiate class "{type(self).__qualname__}": attribute "widget" is None'
           ' and this class does not support the creation of a GUI widget'))

    if previous_presenter is not None:
      self._copy_state(
        previous_presenter, copy_previous_value, copy_previous_visible, copy_previous_sensitive)
    else:
      if copy_previous_value:
        self._setting_value_synchronizer.apply_setting_value_to_gui(self._setting.value)

    if self._value_changed_signal is not None:
      self._connect_value_changed_event()
  
  @property
  def setting(self):
    """The `setting.Setting` instance synchronized with this presenter."""
    return self._setting
  
  @property
  def widget(self):
    """The underlying GUI widget."""
    return self._widget
  
  @property
  def gui_update_enabled(self) -> bool:
    """Returns ``True`` if this presenter can be automatically synchronized with
    ``setting.value``, ``False`` otherwise.
    """
    return self._value_changed_signal is not None
  
  @abc.abstractmethod
  def get_sensitive(self) -> bool:
    """Returns the sensitive state of `Presenter.widget`."""
    pass
  
  @abc.abstractmethod
  def set_sensitive(self, sensitive: bool):
    """Sets the sensitive state of `Presenter.widget`."""
    pass
  
  @abc.abstractmethod
  def get_visible(self) -> bool:
    """Returns the visible state of `Presenter.widget`."""
    pass
  
  @abc.abstractmethod
  def set_visible(self, visible: bool):
    """Sets the visible state of `Presenter.widget`."""
    pass
  
  def update_setting_value(self, force: bool = False):
    """Manually assigns the GUI widget value, entered by the user, to the
    setting value.

    If ``force`` is ``False``, this method will have no effect if this object
    updates its setting value automatically. Otherwise, the setting value
    will be updated regardless of whether the automatic GUI-to-setting update
    is enabled or not. Passing ``force=True`` is useful if the widget is
    internally assigned a valid value on instantiation while the setting
    retains its own value.
    """
    # The `is_value_empty` check makes sure that settings with empty values
    # which are not allowed will be properly invalidated.
    if self._value_changed_signal is None or self._setting.is_value_empty() or force:
      self._update_setting_value()
  
  def auto_update_gui_to_setting(self, enabled: bool):
    """Enables or disables automatic GUI update.
    
    If ``enabled`` is ``True`` and the `Presenter` subclass does not support
    automatic GUI update, `ValueError` is raised.
    """
    if enabled and self._VALUE_CHANGED_SIGNAL is None:
      raise ValueError(f'class "{type(self).__qualname__}" does not support automatic GUI update')
    
    if enabled:
      self._value_changed_signal = self._VALUE_CHANGED_SIGNAL
      self._connect_value_changed_event()
    else:
      self._value_changed_signal = None
      self._disconnect_value_changed_event()
  
  def _create_widget(self, setting: 'setting.Setting', **kwargs):
    """Instantiates and returns a new GUI widget using the attributes in the
    specified `setting.Setting` instance (e.g. display name as GUI label).
    
    ``None`` is returned if the `Presenter` subclass does not support widget
    creation.
    """
    return None
  
  @abc.abstractmethod
  def get_value(self):
    """Returns the value of the GUI widget."""
    pass
  
  @abc.abstractmethod
  def _set_value(self, value):
    """Sets the value of the GUI widget.
    
    If the value passed is one of the empty values allowed for the corresponding
    setting and the widget cannot handle the value, this method must wrap
    the empty value into a safe value (that the widget can handle).
    """
    pass
  
  def _copy_state(
        self,
        previous_presenter,
        copy_previous_value,
        copy_previous_visible,
        copy_previous_sensitive,
  ):
    if copy_previous_value:
      # noinspection PyProtectedMember
      self._set_value(previous_presenter.get_value())
    if copy_previous_visible:
      self.set_visible(previous_presenter.get_visible())
    if copy_previous_sensitive:
      self.set_sensitive(previous_presenter.get_sensitive())

    if not previous_presenter.gui_update_enabled:
      self._value_changed_signal = None

  def _update_setting_value(self):
    """Assigns the GUI widget value, entered by the user, to the setting value.
    """
    self._setting_value_synchronizer.apply_gui_value_to_setting(self.get_value())
  
  @abc.abstractmethod
  def _connect_value_changed_event(self):
    """Connects the `_on_value_changed` event handler to the GUI widget using
    the `_value_changed_signal` attribute.
    
    Because the way event handlers are connected varies in each GUI framework,
    subclass this class and override this method for the GUI framework you use.
    """
    pass
  
  @abc.abstractmethod
  def _disconnect_value_changed_event(self):
    """Disconnects the `_on_value_changed` event handler from the GUI widget.
    
    Because the way event handlers are disconnected varies in each GUI
    framework, subclass this class and override this method for the GUI
    framework you use.
    """
    pass
  
  def _on_value_changed(self, *args):
    """Event handler that automatically updates the value of the setting.
    
    The event is triggered when the user changes the value of the GUI widget.
    """
    if not self._ignore_on_value_changed:
      self._update_setting_value()
  
  def _apply_setting_value_to_gui(self, value):
    """Assigns the setting value to the GUI widget. Used by the setting when
    its `set_value()` method is called.
    """
    self._ignore_on_value_changed = True

    self._set_value(value)

    self._ignore_on_value_changed = False


class NullPresenter(Presenter):
  """`Presenter` subclass whose methods do nothing.
  
  This class is attached to `setting.Setting` instances with no `Presenter`
  instance specified upon its instantiation.
  
  This class also stores the GUI state. In case a proper `Presenter` instance
  is assigned to the setting, the GUI state is copied over to the new instance.
  """
  
  # Make `NullPresenter` pretend to update GUI automatically.
  _VALUE_CHANGED_SIGNAL = 'null_signal'

  _NULL_WIDGET = type('NullWidget', (), {})()
  
  def __init__(self, setting, widget, *args, **kwargs):
    """Initializes a `NullPresenter` instance.

    ``widget`` is ignored.

    See `Presenter.__init__()` for more information on other parameters.
    """
    self._value = None
    self._sensitive = True
    self._visible = True
    
    super().__init__(setting, self._NULL_WIDGET, *args, **kwargs)
  
  def get_sensitive(self):
    return self._sensitive
  
  def set_sensitive(self, sensitive):
    self._sensitive = sensitive
  
  def get_visible(self):
    return self._visible
  
  def set_visible(self, visible):
    self._visible = visible
  
  def update_setting_value(self, force=False):
    pass
  
  def get_value(self):
    return self._value
  
  def _set_value(self, value):
    self._value = value
  
  def _connect_value_changed_event(self):
    pass
  
  def _disconnect_value_changed_event(self):
    pass
