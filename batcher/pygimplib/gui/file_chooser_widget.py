"""`Gtk.FileChooserWidget` subclass that retains current directory after hiding
and re-showing the widget.
"""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class FileChooserWidget(Gtk.FileChooserWidget):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._last_valid_folder = None

    self.connect('map', self._on_file_chooser_widget_map)
    self.connect('current-folder-changed', self._on_file_chooser_widget_current_folder_changed)

  def set_current_folder(self, value):
    self._last_valid_folder = value

    super().set_current_folder(value)

  def _on_file_chooser_widget_map(self, widget):
    if self._last_valid_folder is not None:
      super().set_current_folder(self._last_valid_folder)

  def _on_file_chooser_widget_current_folder_changed(self, widget):
    new_folder = self.get_current_folder()
    if new_folder is not None:
      self._last_valid_folder = new_folder


GObject.type_register(FileChooserWidget)
