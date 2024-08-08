"""Widget for groups of radio buttons (`Gtk.RadioButton`)."""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'RadioButtonBox',
]


class RadioButtonBox(Gtk.Box):
  """Subclass of `Gtk.Box` to select one of related radio buttons.

  Signals:
    active-button-changed:
      The active radio button was changed interactively by the user.
  """

  __gsignals__ = {'active-button-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(self, orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL, spacing: int = 3):
    super().__init__()

    self.set_orientation(orientation)
    self.set_spacing(spacing)

    self._radio_group = None
    self._buttons = []

  def add(self, label: str) -> Gtk.RadioButton:
    """Adds a new radio button with the specified label."""
    if self._radio_group is None:
      button = Gtk.RadioButton.new_with_label(self._radio_group, label)
    else:
      button = Gtk.RadioButton.new_with_label_from_widget(self._radio_group, label)

    button.connect('toggled', self._on_radio_button_toggled)

    self.pack_start(button, False, False, 0)

    self._buttons.append(button)

    self._radio_group = button

    return button

  def get_active(self) -> int:
    """Returns the index of the active radio button, starting from 0.
    """
    return next(
      iter(index for index, button in enumerate(self._buttons) if button.get_active()),
      0)

  def set_active(self, index: int):
    """Sets a button being placed in the `index` order (starting from 0) as the
    active button.

    If the index is not valid, this method has no effect.
    """
    if 0 <= index < len(self._buttons):
      self._buttons[index].set_active(True)

  def _on_radio_button_toggled(self, button):
    if button.get_active():
      self.emit('active-button-changed')
