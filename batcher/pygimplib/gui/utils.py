"""Miscellaneous utility functions related to GTK widgets."""

from collections.abc import Iterable
from typing import Tuple, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

__all__ = [
  'get_toplevel_window',
  'label_fits_text',
  'get_label_full_text_width',
  'menu_popup_below_widget',
  'get_position_below_widget',
  'get_absolute_widget_position',
  'get_icon_pixbuf',
  'has_any_window_focus',
]


def get_toplevel_window(widget: Gtk.Widget) -> Union[Gtk.Window, None]:
  """Return the toplevel `Gtk.Window` for the specified widget, or ``None`` if
  the widget has no such window.
  """
  toplevel_widget = widget.get_toplevel()
  if isinstance(toplevel_widget, Gtk.Window):
    return toplevel_widget
  else:
    return None


def label_fits_text(label: Gtk.Label, use_markup: bool = True) -> bool:
  """Returns ``True`` if the specified `Gtk.Label` is wide enough to display the
  entire text, ``False`` otherwise.

  If ``use_markup`` is ``True``, the label text is treated as marked-up text.
  """
  return (label.get_layout().get_pixel_size()[0]
          >= get_label_full_text_width(label, use_markup))


def get_label_full_text_width(label: Gtk.Label, use_markup: bool = True) -> int:
  """Returns the pixel width of the label text.

  If ``use_markup`` is ``True``, the label text is treated as marked-up text.
  """
  full_text_layout = Pango.Layout.new(label.get_pango_context())
  
  if use_markup:
    full_text_layout.set_markup_with_accel(label.get_label(), -1, '_')
  else:
    full_text_layout.set_text(label.get_text())
  
  return full_text_layout.get_pixel_size()[0]


def menu_popup_below_widget(menu: Gtk.Menu, widget: Gtk.Widget):
  """Displays a `Gtk.Menu` popup below the specified `Gtk.Widget`."""
  menu.popup_at_widget(
    widget,
    Gdk.Gravity.SOUTH_WEST,
    Gdk.Gravity.NORTH_WEST,
    None,
  )


def get_position_below_widget(widget: Gtk.Widget) -> Union[Tuple, None]:
  """Returns absolute x and y coordinates of the lower left corner for
  ``widget``.

  If the widget has no top-level window associated, ``None`` is returned.
  """
  absolute_widget_position = get_absolute_widget_position(widget)

  if absolute_widget_position is not None:
    widget_allocation = widget.get_allocation()

    return absolute_widget_position[0], absolute_widget_position[1] + widget_allocation.height
  else:
    return None


def get_absolute_widget_position(widget: Gtk.Widget) -> Union[Tuple, None]:
  """Returns absolute x and y coordinates of ``widget``.

  If the widget has no top-level window associated, ``None`` is returned.
  """
  toplevel_window = get_toplevel_window(widget)

  if toplevel_window is not None:
    toplevel_window_position = toplevel_window.get_window().get_origin()

    widget_coordinates = widget.translate_coordinates(toplevel_window, 0, 0)
    if widget_coordinates is not None:
      widget_x, widget_y = widget_coordinates
    else:
      widget_allocation = widget.get_allocation()
      widget_x, widget_y = widget_allocation.x, widget_allocation.y

    return (
      toplevel_window_position.x + widget_x,
      toplevel_window_position.y + widget_y)
  else:
    return None


def get_icon_pixbuf(
      icon_name: str,
      widget: Gtk.Widget,
      icon_size: Gtk.IconSize,
) -> Union[GdkPixbuf.Pixbuf, None]:
  """Returns an icon as a pixbuf, or ``None`` if the icon name does not exist.

  ``widget`` is used to set the icon theme and style appropriate for the widget.

  ``icon_size`` should be one of the recognized `Gtk.IconSize` values.
  """
  icon_theme = Gtk.IconTheme.get_for_screen(widget.get_screen())
  icon_size_lookup_result = Gtk.icon_size_lookup(icon_size)

  icon_info = icon_theme.lookup_icon_for_scale(
    icon_name,
    min(icon_size_lookup_result.width, icon_size_lookup_result.height),
    widget.get_scale_factor(),
    Gtk.IconLookupFlags.FORCE_SYMBOLIC)

  if icon_info is not None:
    icon, _was_symbolic = icon_info.load_symbolic_for_context(widget.get_style_context())

    return icon
  else:
    return None


def has_any_window_focus(windows_to_ignore: Iterable[Gtk.Window] = None):
  """Returns ``True`` if any displayed window associated with the current
  plug-in has focus, ``False`` otherwise.

  You may ignore specific `Gtk.Window`s when calling this function by specifying
  the ``windows_to_ignore`` iterable.
  """
  if windows_to_ignore is None:
    windows_to_ignore = []

  return any(
    (w.get_window().get_state() & Gdk.WindowState.FOCUSED)
    for w in Gtk.Window.list_toplevels()
    if w.get_window() is not None and w not in windows_to_ignore and w.get_mapped()
  )
