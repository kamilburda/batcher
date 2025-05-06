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
        default_value,
        min_value,
        max_value,
        default_unit,
        percent_unit,
        percent_placeholder_names,
        percent_placeholder_labels,
        widget_spacing=5,
  ):
    super().__init__()

    self._default_value = default_value
    self._min_value = min_value
    self._max_value = max_value
    self._default_unit = default_unit
    self._percent_unit = percent_unit
    self._percent_placeholder_names = percent_placeholder_names
    self._percent_placeholder_labels = percent_placeholder_labels
    self._widget_spacing = widget_spacing

    self._init_gui()

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._widget_spacing)

    self._spin_button = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=self._default_value,
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
    self._percent_object_label = Gtk.Label(label='from')
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

    self._spin_button.connect('value-changed', self._on_spin_button_changed)
    self._unit_combo_box.connect('changed', self._on_unit_combo_box_changed)
    self._percent_object_combo_box.connect('changed', self._on_percent_object_combo_box_changed)

    self.pack_start(self._spin_button, False, False, 0)
    self.pack_start(self._unit_combo_box, False, False, 0)
    self.pack_start(self._percent_object_box, False, False, 0)

  def _on_spin_button_changed(self, _spin_button):
    self.emit('value-changed')

  def _on_unit_combo_box_changed(self, _combo_box):
    self._show_hide_percent_object_box()

    self.emit('value-changed')

  def _on_percent_object_combo_box_changed(self, _combo_box):
    self.emit('value-changed')

  def _show_hide_percent_object_box(self):
    if self._unit_combo_box.get_active() == self._percent_unit:
      self._percent_object_box.show()
    else:
      self._percent_object_box.hide()

  def get_value(self):
    return {
      'value': self._spin_button.get_value(),
      'unit': self._unit_combo_box.get_active(),
      'percent_object': self._percent_object_combo_box.get_active_id(),
    }

  def set_value(self, data):
    if 'value' in data:
      self._spin_button.set_value(data['value'])

    if data.get('unit') is not None:
      self._unit_combo_box.set_active(data['unit'])

    if data.get('percent_object') is not None:
      self._percent_object_combo_box.set_active_id(data['percent_object'])
