"""Widget for setting image resolution in DPI."""

import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk


__all__ = [
  'ResolutionBox',
]


class ResolutionBox(Gtk.Box):

  __gsignals__ = {'value-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        default_x,
        default_y,
        widget_spacing=7,
  ):
    super().__init__()

    self._default_x = default_x
    self._default_y = default_y
    self._widget_spacing = widget_spacing

    self._init_gui()

  def get_value(self):
    return {
      'x': self._spin_button_x.get_value(),
      'y': self._spin_button_y.get_value(),
    }

  def set_value(self, data):
    if 'x' in data:
      with GObject.signal_handler_block(
            self._spin_button_x,
            self._on_spin_button_x_value_changed_handler_id):
        self._spin_button_x.set_value(data['x'])

    if 'y' in data:
      with GObject.signal_handler_block(
            self._spin_button_y,
            self._on_spin_button_y_value_changed_handler_id):
        self._spin_button_y.set_value(data['y'])

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._widget_spacing)

    # FOR TRANSLATORS: "X" represents the X-axis.
    self._label_x = Gtk.Label(label=_('X'))
    # FOR TRANSLATORS: "Y" represents the Y-axis.
    self._label_y = Gtk.Label(label=_('Y'))

    self._spin_button_x = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=self._default_x,
        lower=0.0,
        upper=GLib.MAXDOUBLE,
        step_increment=1,
        page_increment=10,
      ),
      digits=2,
      numeric=True,
    )

    self._spin_button_y = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=self._default_y,
        lower=0.0,
        upper=GLib.MAXDOUBLE,
        step_increment=1,
        page_increment=10,
      ),
      digits=2,
      numeric=True,
    )

    self.pack_start(self._label_x, False, False, 0)
    self.pack_start(self._spin_button_x, False, False, 0)
    self.pack_start(self._label_y, False, False, 0)
    self.pack_start(self._spin_button_y, False, False, 0)

    self._on_spin_button_x_value_changed_handler_id = self._spin_button_x.connect(
      'value-changed', self._on_spin_button_value_changed)
    self._on_spin_button_y_value_changed_handler_id = self._spin_button_y.connect(
      'value-changed', self._on_spin_button_value_changed)

  def _on_spin_button_value_changed(self, _spin_button):
    self.emit('value-changed')


GObject.type_register(ResolutionBox)
