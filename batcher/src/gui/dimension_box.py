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
        default_percent_property,
        default_other_value,
        min_value,
        max_value,
        default_unit,
        pixel_unit,
        percent_unit,
        percent_placeholder_names,
        percent_placeholder_labels,
        percent_property_names,
        percent_property_labels,
        percent_placeholder_attribute_map,
        widget_spacing=5,
  ):
    super().__init__()

    self._default_pixel_value = default_pixel_value
    self._default_percent_value = default_percent_value
    self._default_percent_property = default_percent_property
    self._default_other_value = default_other_value
    self._min_value = min_value
    self._max_value = max_value
    self._default_unit = default_unit
    self._pixel_unit = pixel_unit
    self._percent_unit = percent_unit
    self._percent_placeholder_names = percent_placeholder_names
    self._percent_placeholder_labels = percent_placeholder_labels
    self._percent_property_names = percent_property_names
    self._percent_property_labels = percent_property_labels
    self._percent_placeholder_attribute_map = percent_placeholder_attribute_map
    self._widget_spacing = widget_spacing

    self._current_pixel_value = self._default_pixel_value
    self._current_percent_value = self._default_percent_value
    self._current_percent_property = self._default_percent_property
    self._current_other_value = self._default_other_value

    self._previous_other_unit = None

    self._percent_placeholders_to_groups = {}
    for key_tuple in percent_placeholder_attribute_map:
      for key in key_tuple:
        self._percent_placeholders_to_groups[key] = key_tuple

    self._init_gui()

  def get_value(self):
    return {
      'pixel_value': self._current_pixel_value,
      'percent_value': self._current_percent_value,
      'other_value': self._current_other_value,
      'unit': self._unit_combo_box.get_active(),
      'percent_object': self._percent_object_combo_box.get_active_id(),
      'percent_property': self._current_percent_property,
    }

  def set_value(self, data):
    if data.get('unit') is not None:
      with GObject.signal_handler_block(
            self._unit_combo_box, self._on_unit_combo_box_changed_handler_id):
        self._unit_combo_box.set_active(data['unit'])

    self._show_hide_percent_object_box()

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

    if data.get('percent_property') is not None:
      self._current_percent_property = data['percent_property']

    self._show_hide_percent_property_combo_boxes()
    self._set_percent_property_values()

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

    self._renderer_text_object = Gtk.CellRendererText()
    self._percent_object_combo_box.pack_start(self._renderer_text_object, True)
    self._percent_object_combo_box.add_attribute(self._renderer_text_object, 'text', 1)
    self._percent_object_combo_box.show_all()

    self._percent_object_label = Gtk.Label(
      label=_('Property:'),
      margin_start=2,
    )
    self._percent_object_label.show_all()

    self._create_percent_property_combo_boxes()

    self._percent_object_box = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._widget_spacing,
    )
    self._percent_object_box.set_no_show_all(True)
    self._percent_object_box.pack_start(self._percent_object_label, False, False, 0)
    self._percent_object_box.pack_start(self._percent_object_combo_box, False, False, 0)
    for combo_box in self._combo_boxes_per_percent_placeholder_group.values():
      self._percent_object_box.pack_start(combo_box, False, False, 0)

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

    self._property_combo_box_changed_handler_ids = {}
    for key, combo_box in self._combo_boxes_per_percent_placeholder_group.items():
      self._property_combo_box_changed_handler_ids[key] = combo_box.connect(
        'changed', self._on_percent_property_combo_box_changed)

    self._show_and_set_percent_property_based_on_percent_object()

    self.pack_start(self._spin_button, False, False, 0)
    self.pack_start(self._unit_combo_box, False, False, 0)
    self.pack_start(self._percent_object_box, False, False, 0)

  def _create_percent_property_combo_boxes(self):
    self._models_per_percent_placeholder_group = {}
    self._combo_boxes_per_percent_placeholder_group = {}

    for percent_placeholder_group, properties in self._percent_placeholder_attribute_map.items():
      model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)

      for index, (name, label) in enumerate(
            zip(self._percent_property_names, self._percent_property_labels)):
        if name in properties:
          model.append((name, label if label is not None else ''))

      combo_box = Gtk.ComboBox(
        model=model,
        active=0,
        id_column=0,
      )

      renderer_text = Gtk.CellRendererText()
      combo_box.pack_start(renderer_text, True)
      combo_box.add_attribute(renderer_text, 'text', 1)
      combo_box.show_all()
      combo_box.set_no_show_all(True)

      self._models_per_percent_placeholder_group[percent_placeholder_group] = model
      self._combo_boxes_per_percent_placeholder_group[percent_placeholder_group] = combo_box

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
    self._show_and_set_percent_property_based_on_percent_object()

    self.emit('value-changed')

  def _on_percent_property_combo_box_changed(self, _combo_box):
    percent_object = self._percent_object_combo_box.get_active_id()
    placeholder_group = self._percent_placeholders_to_groups[percent_object]

    self._current_percent_property[placeholder_group] = (
      self._combo_boxes_per_percent_placeholder_group[placeholder_group].get_active_id())

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

  def _show_and_set_percent_property_based_on_percent_object(self):
    placeholder_group = self._show_hide_percent_property_combo_boxes()

    with GObject.signal_handler_block(
          self._combo_boxes_per_percent_placeholder_group[placeholder_group],
          self._property_combo_box_changed_handler_ids[placeholder_group]):
      self._combo_boxes_per_percent_placeholder_group[placeholder_group].set_active_id(
        self._current_percent_property[placeholder_group])

  def _show_hide_percent_property_combo_boxes(self):
    percent_object = self._percent_object_combo_box.get_active_id()
    percent_placeholder_group = self._percent_placeholders_to_groups[percent_object]

    for key in self._percent_placeholder_attribute_map:
      if key != percent_placeholder_group:
        self._combo_boxes_per_percent_placeholder_group[key].hide()

    self._combo_boxes_per_percent_placeholder_group[percent_placeholder_group].show()

    return percent_placeholder_group

  def _set_percent_property_values(self):
    for percent_placeholder_group in self._percent_placeholder_attribute_map:
      with GObject.signal_handler_block(
            self._combo_boxes_per_percent_placeholder_group[percent_placeholder_group],
            self._property_combo_box_changed_handler_ids[percent_placeholder_group]):
        self._combo_boxes_per_percent_placeholder_group[percent_placeholder_group].set_active_id(
          self._current_percent_property[percent_placeholder_group])

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


GObject.type_register(DimensionBox)
