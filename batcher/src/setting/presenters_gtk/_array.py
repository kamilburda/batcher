from src.gui import widgets as gui_widgets_

from . import _base


__all__ = [
  'ArrayBoxPresenter',
]


class ArrayBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `gui.ArrayBox` widgets.

  Value: Tuple of values of type ``element_type`` specified in the
  `setting.ArraySetting` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'array-box-changed'
  _ITEM_CHANGED_SIGNAL = 'array-box-item-changed'

  def __init__(self, *args, **kwargs):
    self._item_changed_event_handler_id = None
    self._array_elements_with_events = set()

    super().__init__(*args, **kwargs)

  def update_setting_value(self, force=False):
    super().update_setting_value(force=force)

    for array_element in self._setting.get_elements():
      array_element.gui.update_setting_value(force=force)

  def _connect_value_changed_event(self):
    super()._connect_value_changed_event()

    self._item_changed_event_handler_id = self._widget.connect(
      self._ITEM_CHANGED_SIGNAL, self._on_item_changed)

  def _disconnect_value_changed_event(self):
    super()._disconnect_value_changed_event()

    self._widget.disconnect(self._item_changed_event_handler_id)
    self._item_changed_event_handler_id = None

  def _create_widget(self, setting, **kwargs):
    def _add_existing_element(array_element_value, index):
      return self._add_array_element(setting[index], array_box)

    def _add_new_element(array_element_value, index):
      array_element = setting.add_element(value=array_element_value)
      return self._add_array_element(array_element, array_box)

    def _reorder_element(orig_position, new_position):
      setting.reorder_element(orig_position, new_position)

    def _remove_element(position):
      self._array_elements_with_events.remove(setting[position])
      del setting[position]

    array_box = gui_widgets_.ArrayBox(
      setting.element_default_value,
      setting.min_size,
      setting.max_size,
      propagate_natural_width=True,
      propagate_natural_height=True,
      **kwargs,
    )

    array_box.on_add_item = _add_existing_element

    for element_index in range(len(setting)):
      array_box.add_item(setting[element_index].value, element_index)

    array_box.on_add_item = _add_new_element
    array_box.on_reorder_item = _reorder_element
    array_box.on_remove_item = _remove_element

    return array_box

  def get_value(self):
    return tuple(array_element.value for array_element in self._setting.get_elements())

  def _set_value(self, value):
    def _add_existing_element(array_element_value, index):
      return self._add_array_element(self._setting[index], self._widget)

    orig_on_add_item = self._widget.on_add_item
    self._widget.on_add_item = _add_existing_element

    self._widget.set_values(value)

    self._widget.on_add_item = orig_on_add_item

  def _on_item_changed(self, *args):
    self._setting_value_synchronizer.apply_gui_value_to_setting(self.get_value())

  def _add_array_element(self, array_element, array_box):
    def _on_array_box_item_changed(_array_element):
      array_box.emit('array-box-item-changed')

    array_element.set_gui()

    if array_element not in self._array_elements_with_events:
      array_element.connect_event('value-changed', _on_array_box_item_changed)
      self._array_elements_with_events.add(array_element)

    return array_element.gui.widget
