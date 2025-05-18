"""Widget for setting a dimension value (e.g. width or height)."""

import gi
from gi.repository import GLib
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk


__all__ = [
  'DimensionBox',
]


class DimensionBox(Gtk.Box):

  __gsignals__ = {'value-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        default_pixel_value,
        default_percent_value,
        default_other_value,
        min_value,
        max_value,
        default_unit,
        pixel_unit,
        percent_unit,
        percent_placeholder_names,
        percent_placeholder_labels,
        widget_spacing=5,
  ):
    super().__init__()

    self._default_pixel_value = default_pixel_value
    self._default_percent_value = default_percent_value
    self._default_other_value = default_other_value
    self._min_value = min_value
    self._max_value = max_value
    self._default_unit = default_unit
    self._pixel_unit = pixel_unit
    self._percent_unit = percent_unit
    self._percent_placeholder_names = percent_placeholder_names
    self._percent_placeholder_labels = percent_placeholder_labels
    self._widget_spacing = widget_spacing

    self._current_pixel_value = self._default_pixel_value
    self._current_percent_value = self._default_percent_value
    self._current_other_value = self._default_other_value

    self._previous_other_unit = None

    self._init_gui()

  def get_value(self):
    return {
      'pixel_value': self._current_pixel_value,
      'percent_value': self._current_percent_value,
      'other_value': self._current_other_value,
      'unit': self._unit_combo_box.get_active(),
      'percent_object': self._percent_object_combo_box.get_active_id(),
    }

  def set_value(self, data):
    if data.get('unit') is not None:
      with GObject.signal_handler_block(
            self._unit_combo_box, self._on_unit_combo_box_changed_handler_id):
        self._unit_combo_box.set_active(data['unit'])

    if 'pixel_value' in data:
      self._current_pixel_value = data['pixel_value']

    if 'percent_value' in data:
      self._current_percent_value = data['percent_value']

    if 'other_value' in data:
      self._current_other_value = data['other_value']

    self._set_spin_button_value(recalculate_other_value=False)

    self._previous_other_unit = self._unit_combo_box.get_active()

    if data.get('percent_object') is not None:
      with GObject.signal_handler_block(
            self._percent_object_combo_box, self._on_percent_object_combo_box_changed_handler_id):
        self._percent_object_combo_box.set_active_id(data['percent_object'])

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._widget_spacing)

    self._spin_button = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=self._default_pixel_value,
        lower=self._min_value if self._min_value is not None else -GLib.MAXDOUBLE,
        upper=self._max_value if self._max_value is not None else GLib.MAXDOUBLE,
        step_increment=1,
        page_increment=10,
      ),
      digits=2,
      numeric=True,
    )

    self._unit_store = GimpUi.UnitStore.new(1)
    self._unit_store.set_has_percent(True)
    self._unit_store.set_has_pixels(True)

    self._unit_combo_box = GimpUi.UnitComboBox.new_with_model(self._unit_store)

    self._percent_object_model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)

    for index, (name, label) in enumerate(
          zip(self._percent_placeholder_names, self._percent_placeholder_labels)):
      self._percent_object_model.append((name, label if label is not None else ''))

    self._percent_object_combo_box = Gtk.ComboBox(
      model=self._percent_object_model,
      active=0,
      id_column=0,
    )

    self._renderer_text = Gtk.CellRendererText()
    self._percent_object_combo_box.pack_start(self._renderer_text, True)
    self._percent_object_combo_box.add_attribute(self._renderer_text, 'text', 1)
    self._percent_object_combo_box.show_all()

    # FOR TRANSLATORS: Think of e.g. "x% from the current image" when translating this.
    self._percent_object_label = Gtk.Label(label=_('from'))
    self._percent_object_label.show_all()

    self._percent_object_box = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._widget_spacing,
    )
    self._percent_object_box.set_no_show_all(True)
    self._percent_object_box.pack_start(self._percent_object_label, False, False, 0)
    self._percent_object_box.pack_start(self._percent_object_combo_box, False, False, 0)

    if len(self._unit_store) > 0:
      self._unit_combo_box.set_active(self._default_unit)
      self._show_hide_percent_object_box()

    if len(self._percent_object_model) > 0:
      self._percent_object_combo_box.set_active(0)

    self._on_spin_button_changed_handler_id = self._spin_button.connect(
      'value-changed', self._on_spin_button_changed)
    self._on_unit_combo_box_changed_handler_id = self._unit_combo_box.connect(
      'changed', self._on_unit_combo_box_changed)
    self._on_percent_object_combo_box_changed_handler_id = self._percent_object_combo_box.connect(
      'changed', self._on_percent_object_combo_box_changed)

    self.pack_start(self._spin_button, False, False, 0)
    self.pack_start(self._unit_combo_box, False, False, 0)
    self.pack_start(self._percent_object_box, False, False, 0)

  def _on_spin_button_changed(self, _spin_button):
    active_unit = self._unit_combo_box.get_active()
    value = self._spin_button.get_value()

    if active_unit == self._percent_unit:
      self._current_percent_value = value
    elif active_unit == self._pixel_unit:
      self._current_pixel_value = value
    else:
      self._current_other_value = value

    self.emit('value-changed')

  def _on_unit_combo_box_changed(self, _combo_box):
    self._show_hide_percent_object_box()

    self._set_spin_button_value()

    self._previous_other_unit = self._unit_combo_box.get_active()

    self.emit('value-changed')

  def _on_percent_object_combo_box_changed(self, _combo_box):
    self.emit('value-changed')

  def _show_hide_percent_object_box(self):
    if self._unit_combo_box.get_active() == self._percent_unit:
      self._percent_object_box.show()
    else:
      self._percent_object_box.hide()

  def _set_spin_button_value(self, recalculate_other_value=True):
    with GObject.signal_handler_block(self._spin_button, self._on_spin_button_changed_handler_id):
      active_unit = self._unit_combo_box.get_active()

      if active_unit == self._percent_unit:
        self._spin_button.set_value(self._current_percent_value)
      elif active_unit == self._pixel_unit:
        self._spin_button.set_value(self._current_pixel_value)
      else:
        if self._previous_other_unit is not None and recalculate_other_value:
          inch_value = self._other_value_to_inch(
            self._current_other_value, self._previous_other_unit)
          self._current_other_value = self._inch_to_other_value(inch_value, active_unit)

          self._spin_button.set_value(self._current_other_value)
        else:
          self._spin_button.set_value(self._current_other_value)

  @staticmethod
  def _other_value_to_inch(other_value, unit):
    factor = unit.get_factor()

    if factor != 0.0:
      return other_value / factor
    else:
      return other_value

  @staticmethod
  def _inch_to_other_value(inch_value, unit):
    return inch_value * unit.get_factor()
