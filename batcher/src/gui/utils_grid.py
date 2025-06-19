"""Utility functions for the GUI related to attaching setting GUI to a grid."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import setting as setting_
from src import setting_classes
from src.gui import placeholders as gui_placeholders_


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
  if not _should_display_setting_display_name_in_grid(setting):
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
      width_chars_for_check_button_labels=25,
):
  widget_to_attach = setting.gui.widget

  if isinstance(setting.gui, setting_.SETTING_GUI_TYPES.null):
    widget_to_attach = gui_placeholders_.create_placeholder_widget()
  else:
    if (isinstance(setting, setting_.ArraySetting)
        and not setting.element_type.get_allowed_gui_types()):
      widget_to_attach = gui_placeholders_.create_placeholder_widget()

  widget_to_attach.set_hexpand(True)

  if _should_display_setting_display_name_in_grid(setting):
    final_column_index = column_index
    final_width = width
  else:
    final_column_index = column_index_for_widget_without_label
    final_width = width_for_widget_without_label

    if set_name_as_tooltip and _has_setting_display_name(setting):
      widget_to_attach.set_tooltip_text(setting.name)

    if isinstance(setting.gui, setting_.CheckButtonPresenter):
      widget_to_attach.get_child().set_width_chars(width_chars_for_check_button_labels)

  grid.attach(widget_to_attach, final_column_index, row_index, final_width, height)


def _should_display_setting_display_name_in_grid(setting):
  presenters_with_no_label = (
    setting_.CheckButtonPresenter,
    setting_classes.FileFormatOptionsPresenter,
  )

  if isinstance(setting.gui, presenters_with_no_label):
    return False
  elif isinstance(setting, setting_classes.CoordinatesSetting):
    return setting.show_display_name
  else:
    return True


def _has_setting_display_name(setting):
  return setting.display_name is not None and setting.display_name.strip()
