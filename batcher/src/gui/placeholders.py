"""Widget for placeholder GIMP objects (images, layers) such as "Current image".

During processing, these placeholders are replaced with real objects.
"""

from src import setting as setting_
from src.gui import utils as gui_utils_
from src.gui import widgets as gui_widgets_


class PlaceholdersComboBoxPresenter(setting_.GtkPresenter):
  """`setting.presenter.Presenter` subclass for `Gtk.ComboBoxText`
  representing `placeholders.Placeholder` instances.
  
  Value: `placeholders.Placeholder` instance selected in the combo box.
  """
  
  _VALUE_CHANGED_SIGNAL = 'changed'

  def __init__(self, *args, **kwargs):
    self._indexes_and_placeholder_names = {}
    self._placeholder_names_and_indexes = {}

    super().__init__(*args, **kwargs)
  
  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.PlaceholdersComboBox(
      placeholders=setting.get_placeholders(),
      default_placeholder_name=setting.default_value,
    )
  
  def get_value(self):
    return self._widget.get_value()
  
  def _set_value(self, value):
    self._widget.set_value(value)


class UnsupportedParameterPresenter(setting_.GtkPresenter):

  def __init__(self, *args, **kwargs):
    self._value = None

    super().__init__(*args, **kwargs)

  def _create_widget(self, setting, **kwargs):
    return gui_utils_.create_placeholder_widget()

  def get_value(self):
    return self._value

  def _set_value(self, value):
    self._value = value
