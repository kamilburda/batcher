import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src.gui import widgets as gui_widgets_

from . import _base


__all__ = [
  'ComboBoxPresenter',
  'RadioButtonBoxPresenter',
  'PropChoiceComboBoxPresenter',
  'GimpUiIntComboBoxPresenter',
  'EnumComboBoxPresenter',
]


class ComboBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.ComboBox` widgets.

  The combo boxes contain two columns - displayed text and a numeric value
  associated with the text.

  Value: Item selected in the combo box.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    self._name_to_row_index_mapping = {}
    self._row_index_to_name_mapping = {}

    model = Gtk.ListStore(GObject.TYPE_STRING)

    for index, (name, label) in enumerate(zip(setting.items, setting.items_display_names.values())):
      self._name_to_row_index_mapping[name] = index
      self._row_index_to_name_mapping[index] = name
      model.append((label if label is not None else '',))

    combo_box = Gtk.ComboBox(
      model=model,
      active=self._name_to_row_index_mapping[setting.default_value])

    renderer_text = Gtk.CellRendererText()
    combo_box.pack_start(renderer_text, True)
    combo_box.add_attribute(renderer_text, 'text', 0)

    return combo_box

  def get_value(self):
    return self._row_index_to_name_mapping[self._widget.get_active()]

  def _set_value(self, value):
    self._widget.set_active(self._name_to_row_index_mapping[value])


class RadioButtonBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for a group of `Gtk.RadioButton` widgets.

  Value: Item corresponding to the active radio button.
  """

  _VALUE_CHANGED_SIGNAL = 'active-button-changed'

  def _create_widget(self, setting, **kwargs):
    self._name_to_row_index_mapping = {}
    self._row_index_to_name_mapping = {}

    self._widget = gui_widgets_.RadioButtonBox(**kwargs)
    self._widget.set_tooltip_text(setting.description)

    for index, (name, label) in enumerate(zip(setting.items, setting.items_display_names.values())):
      self._widget.add(label)

      self._name_to_row_index_mapping[name] = index
      self._row_index_to_name_mapping[index] = name

    return self._widget

  def get_value(self):
    return self._row_index_to_name_mapping[self._widget.get_active()]

  def _set_value(self, value):
    self._widget.set_active(self._name_to_row_index_mapping[value])


class PropChoiceComboBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `GimpUi.StringComboBox` widgets displaying
  a set of string choices.

  This presenter updates the underlying setting on initialization as these
  `GimpUi` combo boxes are set to a valid value when they are created.

  Value: Item selected in the combo box.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.update_setting_value(force=True)

  def _create_widget(self, setting, **kwargs):
    return GimpUi.prop_choice_combo_box_new(setting.procedure_config, setting.name)

  def get_value(self):
    return self._widget.get_active()

  def _set_value(self, value):
    self._widget.set_active(value)


class GimpUiIntComboBoxPresenter(_base.GtkPresenter):
  """Abstract `setting.Presenter` subclass for widget classes inheriting from
  `GimpUi.IntComboBox` .

  These classes have a modified ``connect()`` method with different interface
  and the signal handler being triggered even when setting the initial value,
  which is undesired.
  """

  _ABSTRACT = True

  def _connect_value_changed_event(self):
    self._event_handler_id = Gtk.ComboBox.connect(
      self._widget, self._VALUE_CHANGED_SIGNAL, self._on_value_changed)


class EnumComboBoxPresenter(GimpUiIntComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.EnumComboBox` widgets.

  Value: Item selected in the enum combo box.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    combo_box = GimpUi.EnumComboBox.new_with_model(GimpUi.EnumStore.new(setting.enum_type))

    for excluded_value in setting.excluded_values:
      del combo_box.get_model()[int(excluded_value)]

    # If the default value is not valid, `set_active` returns `False`,
    # but otherwise does not result in errors.
    combo_box.set_active(int(setting.default_value))

    return combo_box

  def get_value(self):
    return self._widget.get_active().value

  def _set_value(self, value):
    self._widget.set_active(value)
