import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import setting_classes
from src.gui import placeholders as gui_placeholders_

import pygimplib as pg


def attach_label_to_grid(
      grid, setting, row_index, column_index=0, width=1, height=1, max_width_chars=40):
  if isinstance(
        setting.gui, (pg.setting.CheckButtonPresenter, setting_classes.FileFormatOptionsPresenter)):
    return

  label = Gtk.Label(
    xalign=0.0,
    yalign=0.5,
    max_width_chars=max_width_chars,
    wrap=True,
  )

  if _has_setting_display_name(setting):
    label.set_text(setting.display_name)
    label.set_tooltip_text(setting.name)
  else:
    label.set_text(setting.name)

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
):
  widget_to_attach = setting.gui.widget

  if isinstance(setting.gui, pg.setting.SETTING_GUI_TYPES.null):
    widget_to_attach = gui_placeholders_.create_placeholder_widget()
  else:
    if (isinstance(setting, pg.setting.ArraySetting)
        and not setting.element_type.get_allowed_gui_types()):
      widget_to_attach = gui_placeholders_.create_placeholder_widget()

  widget_to_attach.set_hexpand(True)

  if not isinstance(
        setting.gui, (pg.setting.CheckButtonPresenter, setting_classes.FileFormatOptionsPresenter)):
    final_column_index = column_index
    final_width = width
  else:
    final_column_index = column_index_for_widget_without_label
    final_width = width_for_widget_without_label

    if _has_setting_display_name(setting):
      widget_to_attach.set_tooltip_text(setting.name)

  grid.attach(widget_to_attach, final_column_index, row_index, final_width, height)


def _has_setting_display_name(setting):
  return setting.display_name is not None and setting.display_name.strip()
