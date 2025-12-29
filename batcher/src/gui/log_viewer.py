"""Widget for displaying messages logged during batch processing."""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import constants
from src.gui import utils as gui_utils_


class LogViewer:

  _DIALOG_BORDER_WIDTH = 8
  _CONTENTS_MIN_WIDTH = 600
  _CONTENTS_MIN_HEIGHT = 300

  _MAX_MESSAGE_LINES = 20_000

  def __init__(self, parent):
    self._parent = parent

    self._scrolled_window = Gtk.ScrolledWindow(
      width_request=self._CONTENTS_MIN_WIDTH,
      height_request=self._CONTENTS_MIN_HEIGHT,
      shadow_type=Gtk.ShadowType.IN,
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vexpand=True,
    )

    self._text_buffer = Gtk.TextBuffer()

    self._text_view = Gtk.TextView(
      buffer=self._text_buffer,
      editable=False,
      wrap_mode=Gtk.WrapMode.WORD,
      cursor_visible=False,
      pixels_above_lines=1,
      pixels_below_lines=1,
      pixels_inside_wrap=0,
      left_margin=5,
      right_margin=5,
    )

    self._scrolled_window.add(self._text_view)

    self._dialog = GimpUi.Dialog(
      title=_('Logs'),
      parent=parent,
      destroy_with_parent=True,
      resizable=True,
      border_width=self._DIALOG_BORDER_WIDTH,
      attached_to=gui_utils_.get_toplevel_window(self._parent),
      transient_for=gui_utils_.get_toplevel_window(self._parent),
    )

    self._dialog.vbox.pack_start(self._scrolled_window, True, True, 0)

    self._dialog.connect('delete-event', lambda *_args: self._dialog.hide_on_delete())
    self._dialog.add_button(_('_Save to File'), Gtk.ResponseType.OK)
    self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._text_view.connect('size-allocate', self._on_text_view_size_allocate)

    self._dialog.connect('close', self._on_dialog_close)
    self._dialog.connect('response', self._on_dialog_response)

  @property
  def widget(self):
    return self._dialog

  def add_message(self, message):
    self._text_buffer.insert(self._text_buffer.get_end_iter(), message, -1)

    num_lines = self._text_buffer.get_line_count()

    if num_lines > self._MAX_MESSAGE_LINES:
      self._text_buffer.delete(
        self._text_buffer.get_iter_at_line(0),
        self._text_buffer.get_iter_at_line(num_lines - self._MAX_MESSAGE_LINES))

  def _on_text_view_size_allocate(self, _text_view, _allocation):
    self._text_view.scroll_to_iter(
      self._text_buffer.get_end_iter(),
      0.0,
      False,
      0.0,
      0.0,
    )

  def _on_dialog_close(self, _dialog):
    self._dialog.hide()

  def _on_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      self._save_logs_to_file()
    elif response_id == Gtk.ResponseType.CLOSE:
      self._dialog.hide()

  def _save_logs_to_file(self):
    file_dialog = Gtk.FileChooserNative(
      title=_('Save Logs to File'),
      action=Gtk.FileChooserAction.SAVE,
      do_overwrite_confirmation=True,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self._dialog),
    )

    log_file_ext = '.log'

    filter_log = Gtk.FileFilter()
    filter_log.set_name(_('Log file'))
    filter_log.add_pattern(f'*{log_file_ext}')
    file_dialog.add_filter(filter_log)

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.ACCEPT:
      filepath = file_dialog.get_filename()

      if filepath is not None:
        with open(filepath, 'w', encoding=constants.TEXT_FILE_ENCODING) as file:
          file.write(
            self._text_buffer.get_text(
              self._text_buffer.get_start_iter(),
              self._text_buffer.get_end_iter(),
              False,
            )
          )

    file_dialog.destroy()
