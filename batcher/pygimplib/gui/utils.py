"""Miscellaneous utility functions related to GTK widgets."""

from typing import Tuple, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

__all__ = [
  'get_toplevel_window',
  'label_fits_text',
  'get_label_full_text_width',
  'menu_popup_below_widget',
  'get_position_below_widget',
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
    Gdk.Gravity.SOUTH,
    Gdk.Gravity.NORTH,
    None,
  )


def get_position_below_widget(widget: Gtk.Widget) -> Union[Tuple, None]:
  """Returns x and y coordinates of the lower left corner for ``widget``
  relative to the widget's top-level window.

  If the widget has no top-level window associated, ``None`` is returned.
  """
  toplevel_window = get_toplevel_window(widget)

  if toplevel_window is not None:
    toplevel_window_position = toplevel_window.get_window().get_origin()
    widget_allocation = widget.get_allocation()
    return (
      toplevel_window_position.x + widget_allocation.x,
      toplevel_window_position.y + widget_allocation.y + widget_allocation.height)
  else:
    return None
