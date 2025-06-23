import os

from gi.repository import Gio

from src.gui import widgets as gui_widgets_

from . import _base


__all__ = [
  'FileChooserPresenter',
]


class FileChooserPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `gui.FileChooser` widgets used
  to store file or folder paths as `Gio.File` instances.

  Value: Current file or folder path as a `Gio.File` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, width_chars=30, show_clear_button=True, **kwargs):
    return gui_widgets_.FileChooser(
      setting.action,
      setting.value,
      setting.display_name,
      width_chars=width_chars,
      show_clear_button=show_clear_button,
    )

  def get_value(self):
    return self._widget.get_file()

  def _set_value(self, value):
    if not self.setting.set_default_if_not_exists:
      self._widget.set_file(value)
    else:
      if value is not None and os.path.isdir(value.get_path()):
        self._widget.set_file(value)
      else:
        default_directory = self.setting.default_value
        if default_directory is not None and os.path.isdir(default_directory.get_path()):
          self._widget.set_file(default_directory)
        else:
          self._widget.set_file(Gio.file_new_for_uri(''))
