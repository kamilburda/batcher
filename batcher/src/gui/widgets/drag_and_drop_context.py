"""Class providing drag-and-drop capability to any GTK widget."""

import collections
from collections.abc import Iterable
from typing import Callable, List, Optional, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'DragAndDropContext',
]


class DragAndDropContext:
  """Simplified means to add drag-and-drop capability to a `Gtk.Widget`."""

  _AUTOSCROLL_DISTANCE_PIXELS = 30
  _AUTOSCROLL_AMOUNT_PIXELS = 10
  _AUTOSCROLL_BASE_TIMEOUT_INTERVAL = 5

  def __init__(self):
    self._drag_type = self._get_unique_drag_type()

    self._widgets_and_event_ids = collections.defaultdict(dict)

    self._autoscroll_event_id = None
    self._scroll_timeout_interval = 1000
    self._should_scroll_upwards = True

  def setup_drag(
        self,
        widget: Gtk.Widget,
        get_drag_data_func: Callable,
        drag_data_received_func: Callable,
        get_drag_data_args: Optional[Iterable] = None,
        drag_data_received_args: Optional[Iterable] = None,
        get_drag_icon_func: Callable = None,
        get_drag_icon_func_args: Optional[Iterable] = None,
        destroy_drag_icon_func: Callable = None,
        destroy_drag_icon_func_args: Optional[Iterable] = None,
        dest_widget: Optional[Gtk.Widget] = None,
        dest_defaults: Gtk.DestDefaults = Gtk.DestDefaults.ALL,
        target_flags: Gtk.TargetFlags = 0,
        additional_dest_targets: Optional[List] = None,
        scrollable_for_auto_scroll: Union[
          Gtk.Scrollable, Gtk.ScrolledWindow, None] = None,
        process_cursor_position_for_scrollable_func: Optional[Callable] = None,
  ):
    """Enables dragging for the specified `Gtk.widget` instance.

    The displayed ``widget`` is used as the drag icon.

    Args:
      widget:
        Widget to enable dragging for.
      get_drag_data_func:
        Function returning data as a string describing the dragged widget.
      drag_data_received_func:
        Function processing the data returned by ``get_drag_data_func``.
      get_drag_data_args:
        Optional positional arguments for ``get_drag_data_func``.
      drag_data_received_args:
        Optional positional arguments for ``drag_data_received_func``.
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
      dest_widget:
        Optional different widget to use as the drag destination. You may e.g.
        use a child of ``widget`` as a drag destination to limit the area where
        ``widget`` can be dropped.
      dest_defaults:
        `Gtk.DestDefaults` used for the drag destination.
      target_flags:
        `Gtk.TargetFlags` used for both drag source and destination.
      additional_dest_targets:
        Additional `Gtk.TargetEntry` instances for the drag destination.
      scrollable_for_auto_scroll:
        Optional `Gtk.Scrollable` or `Gtk.ScrolledWindow` related to
        ``widget`` which will be auto-scrolled vertically when the cursor is
        placed near the scrollable's edges while a widget is being dragged.
      process_cursor_position_for_scrollable_func:
        Optional function that processes (or replaces) the x- and y-coordinates
        returned by the ``drag-motion`` signal. The function accepts all
        arguments passed to a ``drag-motion`` signal handler, plus
        ``scrollable_for_auto_scroll``.
    """
    if get_drag_data_args is None:
      get_drag_data_args = ()

    if drag_data_received_args is None:
      drag_data_received_args = ()

    if dest_widget is None:
      dest_widget = widget

    if additional_dest_targets is None:
      additional_dest_targets = []

    self._widgets_and_event_ids[widget]['drag-data-get'] = widget.connect(
      'drag-data-get',
      self._on_widget_drag_data_get,
      get_drag_data_func,
      get_drag_data_args)
    widget.drag_source_set(
      Gdk.ModifierType.BUTTON1_MASK,
      [Gtk.TargetEntry.new(self._drag_type, target_flags, 0)],
      Gdk.DragAction.MOVE)

    self._widgets_and_event_ids[widget]['drag-data-received'] = dest_widget.connect(
      'drag-data-received',
      self._on_widget_drag_data_received,
      drag_data_received_func,
      *drag_data_received_args)
    dest_widget.drag_dest_set(
      dest_defaults,
      [
        Gtk.TargetEntry.new(self._drag_type, target_flags, 0),
        *additional_dest_targets,
      ],
      Gdk.DragAction.MOVE)

    if get_drag_icon_func is not None:
      self._widgets_and_event_ids[widget]['drag-begin'] = widget.connect(
        'drag-begin',
        get_drag_icon_func,
        *(get_drag_icon_func_args if get_drag_icon_func_args is not None else ()))
      if destroy_drag_icon_func is not None:
        self._widgets_and_event_ids[widget]['drag-end'] = widget.connect(
          'drag-end',
          destroy_drag_icon_func,
          *(destroy_drag_icon_func_args if destroy_drag_icon_func_args is not None else ()))

    # Implementation taken from:
    # https://gitlab.gnome.org/GNOME/gimp/-/blob/master/app/widgets/gimpcontainertreeview-dnd.c
    if scrollable_for_auto_scroll is not None:
      self._widgets_and_event_ids[widget]['drag-motion'] = widget.connect(
        'drag-motion',
        self._on_scrollable_drag_motion,
        scrollable_for_auto_scroll,
        process_cursor_position_for_scrollable_func,
      )
      self._widgets_and_event_ids[widget]['drag-failed'] = widget.connect(
        'drag-failed',
        self._on_scrollable_drag_failed,
      )
      self._widgets_and_event_ids[widget]['drag-leave'] = widget.connect(
        'drag-leave',
        self._on_scrollable_drag_leave,
      )
      self._widgets_and_event_ids[widget]['drag-drop'] = widget.connect(
        'drag-drop',
        self._on_scrollable_drag_drop,
      )

  def remove_drag(self, widget: Gtk.Widget):
    """Removes drag-and-drop capability from the specified `Gtk.widget`
    instance.

    The widget must have its drag-and-drop capability enabled via
    `setup_drag()`. Otherwise, `ValueError` is raised.

    Args:
      widget: Widget to remove drag-and-drop capability from.
    """
    if widget not in self._widgets_and_event_ids:
      raise ValueError(
        f'widget {widget} was not set up with this DragAndDropContext instance: {self}')

    widget_events = self._widgets_and_event_ids.pop(widget)

    widget.disconnect(widget_events['drag-data-get'])
    widget.drag_source_unset()

    widget.disconnect(widget_events['drag-data-received'])
    widget.drag_dest_unset()

    if 'drag-begin' in widget_events:
      widget.disconnect(widget_events['drag-begin'])

    if 'drag-end' in widget_events:
      widget.disconnect(widget_events['drag-end'])

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
        get_drag_data_args,
  ):
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
        drag_data_received_func,
        *drag_data_received_args,
  ):
    drag_data_received_func(selection_data, *drag_data_received_args)

  def _on_scrollable_drag_motion(
        self,
        widget,
        drag_context,
        cursor_x,
        cursor_y,
        timestamp,
        scrollable,
        process_cursor_position_func,
  ):
    allocation = scrollable.get_allocation()

    if process_cursor_position_func is not None:
      cursor_x, cursor_y = process_cursor_position_func(
        widget,
        drag_context,
        cursor_x,
        cursor_y,
        timestamp,
        scrollable,
      )

    if cursor_y is None:
      # This can happen if `process_cursor_position_func` was not able to
      # process/replace the coordinates for some reason.
      return

    if (cursor_y < self._AUTOSCROLL_DISTANCE_PIXELS
        or cursor_y > (allocation.height - self._AUTOSCROLL_DISTANCE_PIXELS)):
      if cursor_y < self._AUTOSCROLL_DISTANCE_PIXELS:
        distance = min(-cursor_y, -1)
      else:
        distance = max(allocation.height - cursor_y, 1)

      self._scroll_timeout_interval = self._AUTOSCROLL_BASE_TIMEOUT_INTERVAL * abs(distance)
      self._should_scroll_upwards = distance < 0

      if self._autoscroll_event_id is None:
        self._autoscroll_event_id = GLib.timeout_add(
          self._scroll_timeout_interval,
          self._scroll_by_distance,
          scrollable,
        )
    else:
      if self._autoscroll_event_id is not None:
        GLib.source_remove(self._autoscroll_event_id)
        self._autoscroll_event_id = None

  def _on_scrollable_drag_failed(self, _widget, _drag_context, _drag_result):
    if self._autoscroll_event_id is not None:
      GLib.source_remove(self._autoscroll_event_id)
      self._autoscroll_event_id = None

  def _on_scrollable_drag_leave(self, _widget, _drag_context, _timestamp):
    if self._autoscroll_event_id is not None:
      GLib.source_remove(self._autoscroll_event_id)
      self._autoscroll_event_id = None

  def _on_scrollable_drag_drop(
        self,
        _widget,
        _drag_context,
        _cursor_x,
        _cursor_y,
        _timestamp,
  ):
    if self._autoscroll_event_id is not None:
      GLib.source_remove(self._autoscroll_event_id)
      self._autoscroll_event_id = None

  def _scroll_by_distance(self, scrollable):
    adjustment = scrollable.get_vadjustment()

    if self._should_scroll_upwards:
      new_value = adjustment.get_value() - self._AUTOSCROLL_AMOUNT_PIXELS
    else:
      new_value = adjustment.get_value() + self._AUTOSCROLL_AMOUNT_PIXELS

    new_value = min(max(new_value, adjustment.get_lower()), adjustment.get_upper())

    adjustment.set_value(new_value)

    if self._autoscroll_event_id is not None:
      GLib.source_remove(self._autoscroll_event_id)

      self._autoscroll_event_id = GLib.timeout_add(
        self._scroll_timeout_interval,
        self._scroll_by_distance,
        scrollable,
      )
