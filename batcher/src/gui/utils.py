"""Utility functions for the GUI."""

from collections.abc import Iterable
import os
import re
import struct
import sys
from typing import Tuple, Union
import urllib.parse

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango


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

    return absolute_widget_position[0], absolute_widget_position[
                                          1] + widget_allocation.height
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
    icon, _was_symbolic = icon_info.load_symbolic_for_context(
      widget.get_style_context())

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
    if
    w.get_window() is not None and w not in windows_to_ignore and w.get_mapped()
  )


def get_paths_from_clipboard(clipboard):
  text = clipboard.wait_for_text()
  if text is not None:
    return [path for path in text.splitlines() if os.path.exists(path)]

  selection_data = clipboard.wait_for_contents(Gdk.Atom.intern('CF_HDROP', False))
  returned_paths = _get_paths_from_windows_cf_hdrop(selection_data)
  if returned_paths is not None:
    return returned_paths

  selection_data = clipboard.wait_for_contents(Gdk.Atom.intern('text/uri-list', False))
  returned_paths = _get_paths_from_text_uri_list(selection_data)
  if returned_paths is not None:
    return returned_paths

  return []


def get_paths_from_drag_data(selection_data):
  if selection_data.get_target().name() == 'text/uri-list':
    returned_paths = _get_paths_from_text_uri_list(selection_data)
    if returned_paths is not None:
      return returned_paths

  if selection_data.get_target().name() == 'CF_HDROP':
    returned_paths = _get_paths_from_windows_cf_hdrop(selection_data)
    if returned_paths is not None:
      return returned_paths

  return []


def _get_paths_from_windows_cf_hdrop(selection_data):
  if selection_data is not None:
    # The code is based on: https://stackoverflow.com/a/77205658
    data = selection_data.get_data()
    if data:
      # https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/ns-shlobj_core-dropfiles
      windows_dropfiles_struct_for_cf_hdrop_format_size_bytes = 20
      offset, _x_coord, _y_coord, _is_nonclient, is_unicode = struct.unpack(
        'Illii', data[:windows_dropfiles_struct_for_cf_hdrop_format_size_bytes])
      decoded_data = data[offset:].decode('utf-16' if is_unicode else 'ansi')

      return [path for path in decoded_data.split('\0') if os.path.exists(path)]

  return None


def _get_paths_from_text_uri_list(selection_data):
  if selection_data is not None:
    # More info: https://www.iana.org/assignments/media-types/text/uri-list
    data = selection_data.get_data()
    if data:
      decoded_data = urllib.parse.unquote(data, encoding=sys.getfilesystemencoding())

      paths = []
      for raw_path in decoded_data.split('\r\n'):
        path = raw_path.replace('/0', '')
        path = re.sub(r'^file:/+', r'', path)

        if path:
          if os.name != 'nt':
            path = f'/{path}'

          if os.path.exists(path):
            paths.append(path)

      return paths

  return None


def create_placeholder_widget(spacing=5):
  hbox = Gtk.Box(
    orientation=Gtk.Orientation.HORIZONTAL,
    spacing=spacing,
  )

  hbox.pack_start(
    Gtk.Image.new_from_icon_name(GimpUi.ICON_DIALOG_WARNING, Gtk.IconSize.BUTTON),
    False,
    False,
    0)

  label = Gtk.Label(
    use_markup=True,
    label=_('Cannot be modified'),
    xalign=0.0,
    yalign=0.5,
  )

  hbox.pack_start(label, False, False, 0)

  return hbox
