import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from . import _base


__all__ = [
  'UnitComboBoxPresenter',
]


class UnitComboBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `GimpUi.UnitComboBox` widgets.

  Value: A `Gimp.Unit` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def __init__(self, *args, **kwargs):
    self._unit_store = None

    super().__init__(*args, **kwargs)

  def _create_widget(self, setting, **kwargs):
    self._unit_store = GimpUi.UnitStore.new(1)
    self._unit_store.set_has_percent(setting.show_percent)
    self._unit_store.set_has_pixels(setting.show_pixels)

    combo_box = GimpUi.UnitComboBox.new_with_model(self._unit_store)

    combo_box.set_active(setting.value)

    return combo_box

  def get_value(self):
    return self._widget.get_active()

  def _set_value(self, value):
    self._widget.set_active(value)
