"""Widget for placeholder GIMP objects (images, layers) such as "Current image".

During processing, these placeholders are replaced with real objects.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import setting as setting_
from src.gui import utils as gui_utils_


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
    combo_box = Gtk.ComboBoxText.new()

    for index, placeholder in enumerate(setting.get_placeholders()):
      self._indexes_and_placeholder_names[index] = placeholder.name
      self._placeholder_names_and_indexes[placeholder.name] = index

      combo_box.append_text(placeholder.display_name)

    combo_box.set_active(self._placeholder_names_and_indexes[setting.default_value])

    return combo_box
  
  def get_value(self):
    return self._indexes_and_placeholder_names[self._widget.get_active()]
  
  def _set_value(self, value):
    self._widget.set_active(self._placeholder_names_and_indexes[value])


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
