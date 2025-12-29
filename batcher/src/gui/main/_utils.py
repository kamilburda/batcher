"""Utility functions used in `gui.main`."""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import core
from src.gui import utils as gui_utils_
from src.gui import utils_grid as gui_utils_grid_


def get_batcher_class(item_type):
  if item_type == 'image':
    return core.ImageBatcher
  elif item_type == 'layer':
    return core.LayerBatcher
  else:
    raise ValueError('item_type must be either "image" or "layer"')


class ImportExportOptionsDialog:

  _MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR = 650

  _CONTENTS_BORDER_WIDTH = 6

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  def __init__(
        self,
        import_export_settings,
        title=None,
        parent=None,
  ):
    self._import_export_settings = import_export_settings
    self._title = title
    self._parent = parent

    self._init_gui()

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
      parent=self._parent,
      resizable=False,
      attached_to=gui_utils_.get_toplevel_window(self._parent),
      transient_for=gui_utils_.get_toplevel_window(self._parent),
    )

    self._button_reset_response_id = 1
    self._button_reset = self._dialog.add_button(_('_Reset'), self._button_reset_response_id)

    self._button_reset.connect('clicked', self._on_button_reset_clicked)

    self._dialog.connect('delete-event', lambda *_args: self._dialog.hide_on_delete())
    self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._grid = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )
    self._grid.show()

    self._import_export_settings.initialize_gui(only_null=True)

    label_width_chars = gui_utils_grid_.get_max_label_width_from_settings(
      self._import_export_settings)

    for row_index, setting in enumerate(self._import_export_settings):
      gui_utils_grid_.attach_label_to_grid(
        self._grid,
        setting,
        row_index,
        width_chars=label_width_chars,
        max_width_chars=label_width_chars,
        include_name_in_tooltip=False,
      )

      gui_utils_grid_.attach_widget_to_grid(
        self._grid, setting, row_index, include_name_in_tooltip=False)

    self._scrolled_window_viewport = Gtk.Viewport(shadow_type=Gtk.ShadowType.NONE)
    self._scrolled_window_viewport.add(self._grid)
    self._scrolled_window_viewport.show()

    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
      max_content_height=self._MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR,
    )
    self._scrolled_window.add(self._scrolled_window_viewport)
    self._scrolled_window.show()

    self._dialog.vbox.pack_start(self._scrolled_window, False, False, 0)
    self._dialog.vbox.set_border_width(self._CONTENTS_BORDER_WIDTH)

    self._dialog.connect('close', self._on_dialog_close)
    self._dialog.connect('response', self._on_dialog_response)

  @property
  def widget(self):
    return self._dialog

  def _on_dialog_close(self, _dialog):
    self._dialog.hide()

  def _on_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.CLOSE:
      self._dialog.hide()

  def _on_button_reset_clicked(self, _button):
    self._import_export_settings.reset()
