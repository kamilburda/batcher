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
  
  def setup_drag(
        self,
        widget: Gtk.Widget,
        get_drag_data_func: Callable,
        drag_data_receive_func: Callable,
        get_drag_data_args: Optional[Iterable] = None,
        drag_data_receive_args: Optional[Iterable] = None,
        get_drag_icon_func: Callable = None,
        get_drag_icon_func_args: Optional[Iterable] = None,
        destroy_drag_icon_func: Callable = None,
        destroy_drag_icon_func_args: Optional[Iterable] = None,
  ):
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
      get_drag_icon_func:
        Function to generate an icon when the dragging begins. If omitted, the
        default icon assigned by the application will be used.
        This function requires two arguments - the widget for which the dragging
        is initiated (equivalent to ``widget``), and a `Gdk.DragContext`
        instance.
      get_drag_icon_func_args:
        Optional additional positional arguments for ``get_drag_icon_func``.
      destroy_drag_icon_func:
        Function to destroy a drag icon created by ``get_drag_icon_func``. Only
        applicable if ``get_drag_icon_func`` is not ``None``.
      destroy_drag_icon_func_args:
        Optional additional positional arguments for ``destroy_drag_icon_func``.
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

    if get_drag_icon_func is not None:
      widget.connect(
        'drag-begin',
        get_drag_icon_func,
        *(get_drag_icon_func_args if get_drag_icon_func_args is not None else ()))
      if destroy_drag_icon_func is not None:
        widget.connect(
          'drag-end',
          destroy_drag_icon_func,
          *(destroy_drag_icon_func_args if destroy_drag_icon_func_args is not None else ()))
  
  def _get_unique_drag_type(self):
    return f'{type(self).__qualname__}_{id(self)}'
  
  @staticmethod
  def _on_widget_drag_data_get(
        _widget,
        _drag_context,
        selection_data,
        _info,
        _timestamp,
        get_drag_data_func,
        get_drag_data_args):
    selection_data.set(selection_data.get_target(), 8, get_drag_data_func(*get_drag_data_args))
  
  @staticmethod
  def _on_widget_drag_data_received(
        _widget,
        _drag_context,
        _drop_x,
        _drop_y,
        selection_data,
        _info,
        _timestamp,
        drag_data_receive_func,
        *drag_data_receive_args):
    drag_data_receive_func(selection_data.get_data(), *drag_data_receive_args)
