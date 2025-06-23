import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import utils

from . import _base


__all__ = [
  'GBytesEntryPresenter',
]


class GBytesEntryPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Entry` widgets used to store raw
  bytes.

  Value: Raw bytes as a `GLib.Bytes` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    widget = Gtk.Entry(text=utils.bytes_to_escaped_string(setting.value.get_data()))
    widget.set_position(-1)

    return widget

  def get_value(self):
    return GLib.Bytes.new(
      utils.escaped_string_to_bytes(self._widget.get_text(), remove_overflow=True))

  def _set_value(self, value):
    self._widget.set_text(utils.bytes_to_escaped_string(value.get_data()))
    # Place the cursor at the end of the text entry.
    self._widget.set_position(-1)
