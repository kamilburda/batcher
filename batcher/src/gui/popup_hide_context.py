"""Class simplifying hiding a popup window based on user actions."""

from typing import Callable, List, Optional

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg


class PopupHideContext:
  """Class providing a simplified interface for connecting events to hide a
  popup window.

  If a user presses a button outside the popup or focuses out of the widget
  that spawned the popup, the popup is hidden.
  """
  
  def __init__(
        self,
        popup_to_hide: Gtk.Window,
        popup_owner_widget: Gtk.Widget,
        hide_callback: Optional[Callable] = None,
        widgets_to_exclude_from_triggering_hiding: Optional[List[Gtk.Widget]] = None,
  ):
    """Initializes the context.

    Args:
      popup_to_hide:
        A `Gtk.Window` instance representing a popup to hide.
      popup_owner_widget:
        A `Gtk.Widget` instance that spawned the popup.
      hide_callback:
        A function to hide the popup.
        If ``None``, ``popup_to_hide.hide()`` is used to hide the popup.
      widgets_to_exclude_from_triggering_hiding:
        An optional list of widgets that should not trigger popup hiding when a
        button is pressed.
    """
    self._popup_to_hide = popup_to_hide
    self._popup_owner_widget = popup_owner_widget
    self._hide_callback = (
      hide_callback if hide_callback is not None else self._popup_to_hide.hide)
    self._widgets_to_exclude_from_triggering_hiding = widgets_to_exclude_from_triggering_hiding
    
    self._button_press_emission_hook_id = None
    self._toplevel_configure_event_id = None
    self._toplevel_position = None
    self._widgets_with_entered_pointers = set()

  def enable(self):
    """Connects events to hide the popup."""
    self._popup_owner_widget.connect(
      'focus-out-event', self._on_popup_owner_widget_focus_out_event)
    self._popup_to_hide.connect('show', self._on_popup_to_hide_show)
    self._popup_to_hide.connect('hide', self._on_popup_to_hide_hide)

    if self._widgets_to_exclude_from_triggering_hiding is not None:
      for widget in self._widgets_to_exclude_from_triggering_hiding:
        self._exclude_widget_from_hiding_with_button_press(widget)
  
  def _exclude_widget_from_hiding_with_button_press(self, widget):
    widget.connect('enter-notify-event', self._on_widget_enter_notify_event)
    widget.connect('leave-notify-event', self._on_widget_leave_notify_event)
  
  def _on_popup_owner_widget_focus_out_event(self, widget, event):
    self._hide_callback()

  def _on_popup_to_hide_show(self, popup):
    self._connect_button_press_events_for_hiding()

  def _on_popup_to_hide_hide(self, popup):
    self._disconnect_button_press_events_for_hiding()

  def _connect_button_press_events_for_hiding(self):
    self._button_press_emission_hook_id = GObject.add_emission_hook(
      self._popup_owner_widget,
      'button-press-event',
      self._on_emission_hook_button_press_event)

    toplevel = pg.gui.utils.get_toplevel_window(self._popup_owner_widget)
    if toplevel is not None:
      toplevel.get_group().add_window(self._popup_to_hide)
      # Button presses on the window decoration cannot be intercepted via the
      # `'button-press-event'` emission hooks, hence this workaround.
      self._toplevel_configure_event_id = toplevel.connect(
        'configure-event', self._on_toplevel_configure_event)
      self._toplevel_position = toplevel.get_position()

  def _disconnect_button_press_events_for_hiding(self):
    if self._button_press_emission_hook_id is not None:
      GObject.remove_emission_hook(
        self._popup_owner_widget,
        'button-press-event',
        self._button_press_emission_hook_id)

    toplevel = pg.gui.utils.get_toplevel_window(self._popup_owner_widget)
    if (toplevel is not None
        and self._toplevel_configure_event_id is not None
        and toplevel.handler_is_connected(self._toplevel_configure_event_id)):
      toplevel.disconnect(self._toplevel_configure_event_id)
      self._toplevel_configure_event_id = None

  def _on_emission_hook_button_press_event(self, widget, event):
    if self._widgets_with_entered_pointers:
      return True
    else:
      self._hide_callback()
      return False
  
  def _on_toplevel_configure_event(self, toplevel, event):
    if self._toplevel_position != toplevel.get_position():
      self._hide_callback()
    
    self._toplevel_position = toplevel.get_position()
  
  def _on_widget_enter_notify_event(self, widget, event):
    self._widgets_with_entered_pointers.add(widget)
  
  def _on_widget_leave_notify_event(self, widget, event):
    self._widgets_with_entered_pointers.discard(widget)
