"""Widget for updating file format-specific options."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


__all__ = [
  'FileFormatOptionsBox',
]


class FileFormatOptionsBox(Gtk.Box):

  def __init__(
        self,
        initial_header_title=None,
        header_spacing=8,
        row_spacing=3,
        column_spacing=8,
        max_width_for_options=500,
        max_height_for_options=500,
  ):
    super().__init__()

    self._initial_header_title = initial_header_title
    self._row_spacing = row_spacing
    self._column_spacing = column_spacing
    self._header_spacing = header_spacing
    self._max_width_for_options = max_width_for_options
    self._max_height_for_options = max_height_for_options

    self._init_gui()

  def fill_file_formats_and_options(self, file_formats_and_options):
    # self._grid = Gtk.Grid(
    #   row_spacing=row_spacing,
    #   column_spacing=column_spacing,
    # )
    pass

  def set_file_format(self, file_format):
    # Display options for `file_format` if recognized
    # Create a new grid if there isn't one for `file_format` and `file_format` is recognized
    pass

  def _init_gui(self):
    self._label_header = Gtk.Label(
      label=self._initial_header_title,
      xalign=0.0,
    )

    self._grids_per_file_format = {}

    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
      max_content_width=self._max_width_for_options,
      max_content_height=self._max_height_for_options,
    )

    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.set_spacing(self._header_spacing)

    self.pack_start(self._label_header, False, False, 0)
    self.pack_start(self._scrolled_window, False, False, 0)
