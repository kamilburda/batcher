"""Widget for choosing a placeholder value."""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'PlaceholdersComboBox',
]


class PlaceholdersComboBox(Gtk.Box):
  """Class defining a widget for choosing a placeholder value.

  Placeholders are replaced with real arguments during batch processing. For
  some placeholders, extra widget(s) are displayed, representing additional
  parameters.

  Signals:
    changed:
      The user changed the selected combo box item.
  """

  _HBOX_SPACING = 3

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        placeholders,
        default_placeholder,
        *args,
        **kwargs,
  ):
    super().__init__(*args, **kwargs)

    self._placeholders = placeholders
    self._default_placeholder = default_placeholder

    self._indexes_and_placeholder_names = {}
    self._placeholder_names_and_indexes = {}

    self._init_gui()

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._HBOX_SPACING)

    self._placeholder_names_and_settings = {}

    for placeholder in self._placeholders:
      settings = placeholder.create_settings_from_arguments()
      settings.initialize_gui()
      for setting in settings:
        setting.gui.set_visible(True)
        setting.connect_event('value-changed', self._on_setting_changed)

      self._placeholder_names_and_settings[placeholder.name] = settings

    self._create_combo_box()

    self.pack_start(self._combo_box, True, True, 0)

    self._combo_box.connect('changed', self._on_combo_box_changed)

  def get_value(self):
    placeholder_name = self._indexes_and_placeholder_names[self._combo_box.get_active()]
    settings = self._placeholder_names_and_settings[placeholder_name]

    if settings:
      return {
        'name': placeholder_name,
        **settings.get_values(),
      }
    else:
      return placeholder_name

  def set_value(self, value):
    if isinstance(value, dict):
      placeholder_name = value['name']

      settings = self._placeholder_names_and_settings[placeholder_name]
      for setting_name, setting_value in value.items():
        if setting_name == 'name':
          continue

        settings[setting_name].set_value(setting_value)

      self._combo_box.set_active(self._placeholder_names_and_indexes[placeholder_name])
    else:
      self._combo_box.set_active(self._placeholder_names_and_indexes[value])

  def _create_combo_box(self):
    self._combo_box = Gtk.ComboBoxText.new()

    for index, placeholder in enumerate(self._placeholders):
      self._indexes_and_placeholder_names[index] = placeholder.name
      self._placeholder_names_and_indexes[placeholder.name] = index

      self._combo_box.append_text(placeholder.display_name)

    self._combo_box.set_active(self._placeholder_names_and_indexes[self._default_placeholder])

  def _on_combo_box_changed(self, _combo_box):
    placeholder_name = self._indexes_and_placeholder_names[self._combo_box.get_active()]
    settings = self._placeholder_names_and_settings[placeholder_name]

    for child in self.get_children():
      if child == self._combo_box:
        continue

      self.remove(child)

    for setting in settings:
      self.pack_start(setting.gui.widget, False, False, 0)

    self.emit('changed')

  def _on_setting_changed(self, _setting):
    self.emit('changed')


GObject.type_register(PlaceholdersComboBox)
