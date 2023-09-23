"""Class providing drag-and-drop capability to any GTK widget."""

from collections.abc import Iterable
from typing import Callable, Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'DragAndDropContext',
]


class DragAndDropContext:
  """Class adding drag-and-drop capability to a `Gtk.Widget`."""
  
  def __init__(self):
    self._drag_type = self._get_unique_drag_type()
    self._last_widget_dest_drag = None
  
  def setup_drag(
        self,
        widget: Gtk.Widget,
        get_drag_data_func: Callable,
        drag_data_receive_func: Callable,
        get_drag_data_args: Optional[Iterable] = None,
        drag_data_receive_args: Optional[Iterable] = None,
        scrolled_window: Optional[Gtk.ScrolledWindow] = None):
    """Enables dragging for the specified `Gtk.widget` instance.

    The displayed ``widget`` is used as the drag icon.

    Args:
      widget:
        Widget to enable dragging for.
      get_drag_data_func:
        Function returning data as a string describing the dragged widget.
      drag_data_receive_func:
        Function processing the data returned by ``get_drag_data_func``.
      get_drag_data_args:
        Optional positional arguments for ``get_drag_data_func``.
      drag_data_receive_args:
        Optional positional arguments for ``drag_data_receive_func``.
      scrolled_window:
        If ``widget`` is wrapped inside a `Gtk.ScrolledWindow`, you may
        specify this scrolled window instance so that a default GTK drag icon
        is assigned if ``widget`` is partially hidden inside the scrolled
        window.
    """
    if get_drag_data_args is None:
      get_drag_data_args = ()
    
    if drag_data_receive_args is None:
      drag_data_receive_args = ()
    
    widget.connect(
      'drag-data-get',
      self._on_widget_drag_data_get,
      get_drag_data_func,
      get_drag_data_args)
    widget.drag_source_set(
      Gdk.ModifierType.BUTTON1_MASK,
      [Gtk.TargetEntry.new(self._drag_type, 0, 0)],
      Gdk.DragAction.MOVE)
    
    widget.connect(
      'drag-data-received',
      self._on_widget_drag_data_received,
      drag_data_receive_func,
      *drag_data_receive_args)
    widget.drag_dest_set(
      Gtk.DestDefaults.ALL,
      [Gtk.TargetEntry.new(self._drag_type, 0, 0)],
      Gdk.DragAction.MOVE)
    
    widget.connect('drag-begin', self._on_widget_drag_begin, scrolled_window)
    widget.connect('drag-motion', self._on_widget_drag_motion)
    widget.connect('drag-failed', self._on_widget_drag_failed)
  
  def _get_unique_drag_type(self):
    return f'{type(self).__qualname__}_{id(self)}'
  
  @staticmethod
  def _on_widget_drag_data_get(
        widget,
        drag_context,
        selection_data,
        info,
        timestamp,
        get_drag_data_func,
        get_drag_data_args):
    selection_data.set(selection_data.get_target(), 8, get_drag_data_func(*get_drag_data_args))
  
  @staticmethod
  def _on_widget_drag_data_received(
        widget,
        drag_context,
        drop_x,
        drop_y,
        selection_data,
        info,
        timestamp,
        drag_data_receive_func,
        *drag_data_receive_args):
    drag_data_receive_func(selection_data.get_data(), *drag_data_receive_args)
  
  def _on_widget_drag_begin(self, widget, drag_context, scrolled_window):
    drag_icon_pixbuf = self._get_drag_icon_pixbuf(widget, scrolled_window)
    if drag_icon_pixbuf is not None:
      widget.drag_source_set_icon_pixbuf(drag_icon_pixbuf)
  
  def _on_widget_drag_motion(self, widget, drag_context, drop_x, drop_y, timestamp):
    self._last_widget_dest_drag = widget
  
  def _on_widget_drag_failed(self, widget, drag_context, result):
    if self._last_widget_dest_drag is not None:
      self._last_widget_dest_drag.drag_unhighlight()
      self._last_widget_dest_drag = None
  
  def _get_drag_icon_pixbuf(self, widget, scrolled_window):
    if widget.get_window() is None:
      return
    
    if (scrolled_window is not None
        and self._are_items_partially_hidden_because_of_visible_horizontal_scrollbar(
              scrolled_window)):
      return None
    
    self._setup_widget_to_add_border_to_drag_icon(widget)
    
    while Gtk.events_pending():
      Gtk.main_iteration()
    
    widget_allocation = widget.get_allocation()

    drag_icon_pixbuf = Gdk.pixbuf_get_from_window(
      widget.get_window(),
      0,
      0,
      widget_allocation.width,
      widget_allocation.height)
    
    self._restore_widget_after_creating_drag_icon(widget)
    
    return drag_icon_pixbuf
  
  @staticmethod
  def _are_items_partially_hidden_because_of_visible_horizontal_scrollbar(scrolled_window):
    return (
      scrolled_window.get_hscrollbar() is not None
      and scrolled_window.get_hscrollbar().get_mapped())
  
  def _setup_widget_to_add_border_to_drag_icon(self, widget):
    self._remove_focus_outline(widget)
    self._add_border(widget)
  
  @staticmethod
  def _remove_focus_outline(widget):
    if widget.has_focus():
      widget.set_can_focus(False)
  
  @staticmethod
  def _add_border(widget):
    widget.drag_highlight()
  
  def _restore_widget_after_creating_drag_icon(self, widget):
    self._add_focus_outline(widget)
    self._remove_border(widget)
  
  @staticmethod
  def _add_focus_outline(widget):
    widget.set_can_focus(True)
  
  @staticmethod
  def _remove_border(widget):
    widget.drag_unhighlight()
