"""Utility functions for the GUI related to attaching setting GUI to a grid."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.gui import utils as gui_utils_


def attach_label_to_grid(
      grid,
      setting,
      row_index,
      column_index=0,
      width=1,
      height=1,
      width_chars=20,
      max_width_chars=40,
      set_name_as_tooltip=True,
):
  if not setting.gui.show_display_name:
    return

  label = Gtk.Label(
    xalign=0.0,
    yalign=0.5,
    width_chars=width_chars,
    max_width_chars=max_width_chars,
    wrap=True,
  )
  label.show()

  if _has_setting_display_name(setting):
    label.set_text(setting.display_name)
    if set_name_as_tooltip:
      label.set_tooltip_text(setting.name)
  else:
    label.set_text(setting.name)

  label.set_sensitive(setting.gui.get_sensitive())

  setting.connect_event(
    'gui-sensitive-changed', lambda _setting: label.set_sensitive(setting.gui.get_sensitive()))

  grid.attach(label, column_index, row_index, width, height)


def attach_widget_to_grid(
      grid,
      setting,
      row_index,
      column_index=1,
      width=1,
      height=1,
      column_index_for_widget_without_label=0,
      width_for_widget_without_label=2,
      set_name_as_tooltip=True,
):
  widget_to_attach = setting.gui.widget

  if setting.gui.is_null():
    widget_to_attach = gui_utils_.create_placeholder_widget()

  widget_to_attach.set_hexpand(True)

  if setting.gui.show_display_name:
    final_column_index = column_index
    final_width = width
  else:
    final_column_index = column_index_for_widget_without_label
    final_width = width_for_widget_without_label

    if set_name_as_tooltip and _has_setting_display_name(setting):
      widget_to_attach.set_tooltip_text(setting.name)

  setting.invoke_event('gui-attached-to-grid')

  grid.attach(widget_to_attach, final_column_index, row_index, final_width, height)


def _has_setting_display_name(setting):
  return setting.display_name is not None and setting.display_name.strip()
