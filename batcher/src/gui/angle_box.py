"""Widget for setting an angle."""

import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk


__all__ = [
  'AngleBox',
]


class AngleBox(Gtk.Box):

  __gsignals__ = {'value-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        default_value,
        default_unit,
        units,
        widget_spacing=5,
  ):
    super().__init__()

    self._default_value = default_value
    self._default_unit = default_unit
    self._widget_spacing = widget_spacing

    self._current_value = self._default_value
    self._previous_unit = None

    self._units = units

    self._init_gui()

  def get_value(self):
    return {
      'value': self._current_value,
      'unit': self._unit_combo_box.get_active_id(),
    }

  def set_value(self, data):
    if data.get('unit') is not None:
      with GObject.signal_handler_block(
            self._unit_combo_box, self._on_unit_combo_box_changed_handler_id):
        self._unit_combo_box.set_active_id(data['unit'])

    if 'value' in data:
      self._current_value = data['value']

    self._set_spin_button_value()

    self._previous_unit = self._unit_combo_box.get_active_id()

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._widget_spacing)

    self._spin_button = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=self._default_value,
        lower=-GLib.MAXDOUBLE,
        upper=GLib.MAXDOUBLE,
        step_increment=1,
        page_increment=10,
      ),
      digits=2,
      numeric=True,
    )

    self._unit_model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
    for unit in self._units.values():
      self._unit_model.append((unit.name, unit.display_name))

    self._unit_combo_box = Gtk.ComboBox(
      model=self._unit_model,
      active=0,
      id_column=0,
    )

    self._renderer_text = Gtk.CellRendererText()
    self._unit_combo_box.pack_start(self._renderer_text, True)
    self._unit_combo_box.add_attribute(self._renderer_text, 'text', 1)
    self._unit_combo_box.show_all()

    if len(self._unit_model) > 0:
      self._unit_combo_box.set_active_id(self._default_unit)

    self._on_spin_button_changed_handler_id = self._spin_button.connect(
      'value-changed', self._on_spin_button_changed)
    self._on_unit_combo_box_changed_handler_id = self._unit_combo_box.connect(
      'changed', self._on_unit_combo_box_changed)

    self.pack_start(self._spin_button, False, False, 0)
    self.pack_start(self._unit_combo_box, False, False, 0)

  def _on_spin_button_changed(self, _spin_button):
    self._current_value = self._spin_button.get_value()

    self.emit('value-changed')

  def _on_unit_combo_box_changed(self, _combo_box):
    self._set_spin_button_value()

    self._previous_unit = self._unit_combo_box.get_active_id()

    self.emit('value-changed')

  def _set_spin_button_value(self):
    with GObject.signal_handler_block(self._spin_button, self._on_spin_button_changed_handler_id):
      if self._previous_unit is not None:
        active_unit = self._unit_combo_box.get_active_id()
        radian_value = self._other_value_to_radian(self._current_value, self._previous_unit)
        self._current_value = self._radian_to_other_value(radian_value, active_unit)

        self._spin_button.set_value(self._current_value)
      else:
        self._spin_button.set_value(self._current_value)

  def _other_value_to_radian(self, other_value, unit):
    scaling_factor = self._units[unit].scaling_factor

    if scaling_factor != 0.0:
      return other_value / scaling_factor
    else:
      return other_value

  def _radian_to_other_value(self, radian_value, unit):
    return radian_value * self._units[unit].scaling_factor


GObject.type_register(AngleBox)
