"""Widget for placeholder GIMP objects (images, layers) such as "Current layer".

During processing, these placeholders are replaced with real objects.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg


class PlaceholdersComboBoxPresenter(pg.setting.GtkPresenter):
  """`pygimplib.setting.presenter.Presenter` subclass for `Gtk.ComboBoxText`
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

    for index, placeholder in enumerate(setting.get_allowed_placeholders()):
      self._indexes_and_placeholder_names[index] = placeholder.name
      self._placeholder_names_and_indexes[placeholder.name] = index

      combo_box.append_text(placeholder.display_name)

    combo_box.set_active(self._placeholder_names_and_indexes[setting.default_value])

    return combo_box
  
  def _get_value(self):
    return self._indexes_and_placeholder_names[self._widget.get_active()]
  
  def _set_value(self, value):
    self._widget.set_active(self._placeholder_names_and_indexes[value])
