"""Widget for updating file format-specific options."""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.gui import utils_grid as gui_utils_grid_


__all__ = [
  'FileFormatOptionsBox',
]


class FileFormatOptionsBox(Gtk.Box):

  _LABELS_WIDTH_CHARS = 30
  _LABELS_MAX_WIDTH_CHARS = 40

  def __init__(
        self,
        row_spacing=3,
        column_spacing=8,
        spacing_between_file_formats=8,
        left_margin=12,
  ):
    super().__init__()

    self._row_spacing = row_spacing
    self._column_spacing = column_spacing
    self._spacing_between_file_formats = spacing_between_file_formats
    self._left_margin = left_margin

    self._widgets_per_file_format = {}
    # We use this to detect if a `setting.Group` instance holding
    # file format options changed, in which case we need to create a new
    # `Gtk.Grid`.
    self._file_format_options_dict = {}

    self._init_gui()

  def set_active_file_formats(self, active_file_formats, file_format_options):
    for child in self.get_children():
      self.remove(child)

    for active_file_format, file_format_options_item in (
          zip(active_file_formats, file_format_options)):
      if self._should_create_new_widget(
            active_file_format, file_format_options_item, self._widgets_per_file_format):
        self._widgets_per_file_format[active_file_format] = self._create_widget_for_file_format(
          active_file_format, file_format_options_item)
        self._file_format_options_dict[active_file_format] = file_format_options_item

      self.pack_start(self._widgets_per_file_format[active_file_format], False, False, 0)

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.set_spacing(self._spacing_between_file_formats)

    self.show_all()

  def _should_create_new_widget(self, active_file_format, file_format_options, dict_):
    return (
      active_file_format not in dict_
      or file_format_options != self._file_format_options_dict.get(active_file_format)
    )

  def _create_widget_for_file_format(self, active_file_format, file_format_options):
    expander = Gtk.Expander(
      use_markup=True,
      expanded=True,
    )
    # FOR TRANSLATORS: Think of e.g. "PNG options" when translating this.
    file_format_options_text = _('{} options').format(active_file_format.upper())
    expander.set_label(f'<b>{file_format_options_text}</b>')

    if file_format_options:
      child_widget = self._create_grid_for_file_format(file_format_options)
    else:
      child_widget = self._create_label_message_for_file_format(file_format_options)

    expander.add(child_widget)
    expander.show_all()

    expander.get_label_widget().set_xalign(0.0)
    expander.get_label_widget().set_width_chars(self._LABELS_WIDTH_CHARS)
    expander.get_label_widget().set_max_width_chars(self._LABELS_MAX_WIDTH_CHARS)

    return expander

  def _create_grid_for_file_format(self, file_format_options):
    grid = Gtk.Grid(
      row_spacing=self._row_spacing,
      column_spacing=self._column_spacing,
      margin_start=self._left_margin,
      margin_top=self._spacing_between_file_formats,
      margin_bottom=self._spacing_between_file_formats,
    )

    file_format_options.initialize_gui(only_null=True)

    for row_index, setting in enumerate(file_format_options):
      gui_utils_grid_.attach_label_to_grid(grid, setting, row_index)
      gui_utils_grid_.attach_widget_to_grid(grid, setting, row_index)

    return grid

  def _create_label_message_for_file_format(self, file_format_options):
    label_message = Gtk.Label(
      xalign=0.5,
      use_markup=True,
      use_underline=False,
      width_chars=self._LABELS_WIDTH_CHARS,
      max_width_chars=self._LABELS_MAX_WIDTH_CHARS,
      wrap=True,
      margin_top=self._spacing_between_file_formats,
      margin_bottom=self._spacing_between_file_formats,
    )
    label_message.show_all()

    if file_format_options is None:
      label_message.set_label('<i>{}</i>'.format(_('File format not recognized')))
    else:
      label_message.set_label('<i>{}</i>'.format(_('File format has no options')))

    return label_message


GObject.type_register(FileFormatOptionsBox)
