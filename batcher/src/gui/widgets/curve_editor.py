"""Widget for `Gimp.Curve` instances."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import item_box as item_box_
from . import radio_button_box as radio_button_box_


__all__ = [
  'CurveEditor',
]


class CurveEditor(Gtk.Box):
  """Subclass of `Gtk.Box` to edit `Gimp.Curve` instances interactively.

  The class allows adjusting `Gimp.Curve` attributes, including the curve type,
  points, point types and samples.

  Points and samples in this widget are represented as integers in the range
  of 0-255. These values are scaled to 0.0-1.0 when the `get_curve()` method is
  called when a `Gimp.Curve` instance is returned.

  While `Gimp.Curve` allows setting a higher number of samples than 256, this
  widget limits the number of samples to 256 for easier usage.

  Signals:
    curve-changed: The curve was modified by the user.
  """
  
  __gsignals__ = {'curve-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  _SAMPLE_SIZE = 256
  _MIN_POINT_VALUE = 0
  _MAX_POINT_VALUE = 255

  _VBOX_SPACING = 3
  _POINT_BOX_SPACING = 3

  def __init__(self, curve: Gimp.Curve):
    super().__init__()

    self._curve = curve

    self._should_invoke_curve_changed_signal = True

    self._init_gui(curve)

  def get_curve(self) -> Gimp.Curve:
    """Returns a `Gimp.Curve` instance based on the values in the widget."""
    return self._curve
  
  def set_curve(self, curve: Gimp.Curve):
    """Fills the widget with attributes from the specified `Gimp.Curve`
    instance.
    """
    self._should_invoke_curve_changed_signal = False

    self._curve = Gimp.Curve.new()
    self._curve.set_curve_type(curve.get_curve_type())

    self._radio_button_box_curve_type.set_active(
      self._curve_types_and_indexes[curve.get_curve_type()])

    if curve.get_curve_type() == Gimp.CurveType.SMOOTH:
      self._points_array_box.clear()

      for index in range(curve.get_n_points()):
        x, y = curve.get_point(index)

        self._points_array_box.add_item((
          int(x * (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE) + self._MIN_POINT_VALUE),
          int(y * (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE) + self._MIN_POINT_VALUE),
          curve.get_point_type(index),
        ))
    elif curve.get_curve_type() == Gimp.CurveType.FREE:
      values = [
        int(
          (curve.get_sample(index / (self._SAMPLE_SIZE - 1))
           * (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE))
          + self._MIN_POINT_VALUE
        )
        for index in range(self._SAMPLE_SIZE)
      ]
      self._samples_array_box.set_values(values)

    self._should_invoke_curve_changed_signal = True

  def _init_gui(self, curve):
    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.set_spacing(self._VBOX_SPACING)

    self._curve_types = {
      Gimp.CurveType.SMOOTH: _('Smooth curve'),
      Gimp.CurveType.FREE: _('Freehand curve'),
    }
    self._curve_types_and_indexes = {}

    self._radio_button_box_curve_type = radio_button_box_.RadioButtonBox()
    for index, (curve_type, curve_type_name) in enumerate(self._curve_types.items()):
      self._radio_button_box_curve_type.add(curve_type_name)
      self._curve_types_and_indexes[curve_type] = index

    self._points_array_box = item_box_.ArrayBox(
      (self._MIN_POINT_VALUE, self._MIN_POINT_VALUE, Gimp.CurvePointType.SMOOTH),
      min_size=0,
      max_size=None,
      enable_reorder=False,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._points_array_box.on_add_item = self._add_widget_for_point
    self._points_array_box.on_remove_item = self._remove_widget_for_point

    self._samples_array_box = item_box_.ArrayBox(
      self._MIN_POINT_VALUE,
      min_size=self._SAMPLE_SIZE,
      max_size=self._SAMPLE_SIZE,
      enable_reorder=False,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._samples_array_box.on_add_item = self._add_widget_for_sample

    self.pack_start(self._radio_button_box_curve_type, False, False, 0)
    self.pack_start(self._points_array_box, False, False, 0)
    self.pack_start(self._samples_array_box, False, False, 0)

    self.set_curve(curve)

    self._connect_changed_events()

  def _add_widget_for_point(self, value, _index):
    x, y, point_type = value

    point = self._curve.add_point(
      (x - self._MIN_POINT_VALUE) / (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE),
      (y - self._MIN_POINT_VALUE) / (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE),
    )
    self._curve.set_point_type(point, point_type)

    # for point_ in range(self._curve.get_n_points()):
    #   print(point_, self._curve.get_point(point_), self._curve.get_point_type(point_))

    spin_scale_x = GimpUi.SpinScale(
      adjustment=Gtk.Adjustment(
        value=x,
        lower=self._MIN_POINT_VALUE,
        upper=self._MAX_POINT_VALUE,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
    )

    spin_scale_y = GimpUi.SpinScale(
      adjustment=Gtk.Adjustment(
        value=y,
        lower=self._MIN_POINT_VALUE,
        upper=self._MAX_POINT_VALUE,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
    )

    point_type_combo_box = GimpUi.EnumComboBox.new_with_model(
      GimpUi.EnumStore.new(Gimp.CurvePointType))
    point_type_combo_box.set_active(int(point_type))

    point_box = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._POINT_BOX_SPACING,
    )
    point_box.pack_start(spin_scale_x, True, True, 0)
    point_box.pack_start(spin_scale_y, True, True, 0)
    point_box.pack_start(point_type_combo_box, False, False, 0)

    spin_scale_x.connect(
      'value-changed', self._on_point_spin_scale_value_changed, point, spin_scale_x, spin_scale_y)
    spin_scale_x.connect('value-changed', self._on_curve_changed)

    spin_scale_y.connect(
      'value-changed', self._on_point_spin_scale_value_changed, point, spin_scale_x, spin_scale_y)
    spin_scale_y.connect('value-changed', self._on_curve_changed)

    # Use the `connect` method from `Gtk.ComboBox` as `GimpUi.EnumComboBox`
    # overrides that method with a different signature.
    Gtk.ComboBox.connect(
      point_type_combo_box, 'changed', self._on_point_type_combo_box_changed, point)
    Gtk.ComboBox.connect(point_type_combo_box, 'changed', self._on_curve_changed)

    return point_box, point

  def _on_point_spin_scale_value_changed(self, _spin_scale, point, spin_scale_x, spin_scale_y):
    self._curve.set_point(
      point,
      ((spin_scale_x.get_value_as_int() - self._MIN_POINT_VALUE)
       / (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE)),
      ((spin_scale_y.get_value_as_int() - self._MIN_POINT_VALUE)
       / (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE)),
    )

  def _on_point_type_combo_box_changed(self, combo_box, point):
    self._curve.set_point_type(point, Gimp.CurvePointType(combo_box.get_active().value))

  def _remove_widget_for_point(self, index):
    self._curve.delete_point(index)

  def _add_widget_for_sample(self, value, index):
    if index is None:
      index = len(self._samples_array_box.items) - 1

    spin_scale = GimpUi.SpinScale(
      adjustment=Gtk.Adjustment(
        value=value,
        lower=self._MIN_POINT_VALUE,
        upper=self._MAX_POINT_VALUE,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
      hexpand=True,
    )

    spin_scale.connect('value-changed', self._on_sample_spin_scale_value_changed, index)
    spin_scale.connect('value-changed', self._on_curve_changed)

    return spin_scale, index

  def _on_sample_spin_scale_value_changed(self, spin_scale, index):
    self._curve.set_sample(
      index / (self._SAMPLE_SIZE - 1),
      ((spin_scale.get_value_as_int() - self._MIN_POINT_VALUE)
       / (self._MAX_POINT_VALUE - self._MIN_POINT_VALUE)),
    )

  def _connect_changed_events(self):
    self._radio_button_box_curve_type.connect(
      'active-button-changed', self._on_radio_button_box_curve_type_changed)

    self._radio_button_box_curve_type.connect('active-button-changed', self._on_curve_changed)
    self._points_array_box.connect('array-box-changed', self._on_curve_changed)

  def _on_radio_button_box_curve_type_changed(self, _widget):
    active_index = self._radio_button_box_curve_type.get_active()

    if active_index == self._curve_types_and_indexes[Gimp.CurveType.SMOOTH]:
      self._curve.set_curve_type(Gimp.CurveType.SMOOTH)

      self._samples_array_box.hide()
      self._points_array_box.show()
    elif active_index == self._curve_types_and_indexes[Gimp.CurveType.FREE]:
      self._curve.set_curve_type(Gimp.CurveType.FREE)

      self._points_array_box.hide()
      self._samples_array_box.show()

  def _on_curve_changed(self, _widget, *_args, **_kwargs):
    if self._should_invoke_curve_changed_signal:
      self.emit('curve-changed')


GObject.type_register(CurveEditor)
