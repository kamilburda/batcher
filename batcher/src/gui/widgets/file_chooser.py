"""Widget for choosing a single file or folder."""

from typing import Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.gui import utils as gui_utils_

__all__ = [
  'FileChooser',
]


class FileChooser(Gtk.Box):
  """Class defining a GTK widget for choosing a single file or folder.

  Signals:
    changed:
      The user changed the selected file or folder.

      Signal arguments:
        selected_file: The currently selected file as a `GFile` instance.
  """

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, (Gio.File,))}

  _SPACING = 4

  def __init__(
        self,
        file_action,
        initial_value=None,
        *args,
        **kwargs,
  ):
    super().__init__(*args, **kwargs)

    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._SPACING)

    self._text_entry = None
    self._file_chooser = None

    self._button_browse = Gtk.Button(
      image=Gtk.Image.new_from_icon_name('folder', Gtk.IconSize.BUTTON),
      tooltip_text=_('Browse'),
    )

    if initial_value is not None and initial_value.get_path() is not None:
      initial_text = initial_value.get_path()
    else:
      initial_text = ''

    self._text_entry = Gtk.Entry(text=initial_text)
    self._text_entry.set_position(-1)

    self._button_browse.connect('clicked', self._on_button_browse_clicked, file_action)
    self._text_entry.connect('notify::text', self._emit_changed_event)

    self.pack_start(self._text_entry, True, True, 0)
    self.pack_start(self._button_browse, False, False, 0)

    self.show_all()

  def _on_button_browse_clicked(self, _button, file_action):
    if file_action == Gimp.FileChooserAction.OPEN:
      action = Gtk.FileChooserAction.OPEN
    elif file_action == Gimp.FileChooserAction.SAVE:
      action = Gtk.FileChooserAction.SAVE
    elif file_action == Gimp.FileChooserAction.SELECT_FOLDER:
      action = Gtk.FileChooserAction.SELECT_FOLDER
    elif file_action == Gimp.FileChooserAction.CREATE_FOLDER:
      action = Gtk.FileChooserAction.CREATE_FOLDER
    else:
      action = Gtk.FileChooserAction.SAVE

    if file_action in [Gimp.FileChooserAction.SELECT_FOLDER, Gimp.FileChooserAction.CREATE_FOLDER]:
      title = _('Select a Folder')
    else:
      title = _('Select a File')

    file_dialog = Gtk.FileChooserNative(
      title=title,
      action=action,
      do_overwrite_confirmation=False,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self),
    )

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.ACCEPT:
      path = file_dialog.get_filename()
      if path:
        self.set_file(path)

    file_dialog.destroy()

  def _emit_changed_event(self, *_args, **_kwargs):
    self.emit('changed', self.get_file())

  def get_file(self) -> Union[Gio.File, None]:
    return Gio.file_new_for_path(self._text_entry.get_text())

  def set_file(self, file_or_path: Union[Gio.File, str, None]):
    if file_or_path is None:
      file = Gio.file_new_for_path('')
    elif isinstance(file_or_path, str):
      file = Gio.file_new_for_path(file_or_path)
    else:
      file = file_or_path

    self._text_entry.set_text(file.get_path() if file.get_path() is not None else '')
    # Place the cursor at the end of the text entry.
    self._text_entry.set_position(-1)


GObject.type_register(FileChooser)
