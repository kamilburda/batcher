import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import builtin_actions as builtin_actions_
from src import placeholders as placeholders_
from src import renamer as renamer_
from src import setting as setting_
from src.gui import widgets as gui_widgets_
from src.gui.entry import entries as entries_


__all__ = [
  'ExtendedEntryPresenter',
  'FileExtensionEntryPresenter',
  'NamePatternEntryPresenter',
  'DimensionBoxPresenter',
  'AngleBoxPresenter',
  'AnchorBoxPresenter',
  'CoordinatesBoxPresenter',
  'FileFormatOptionsPresenter',
]


class ExtendedEntryPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `gui.ExtendedEntry` widgets.

  Value: Text in the entry.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def get_value(self):
    text = self._widget.get_text()
    return text if text is not None else ''

  def _set_value(self, value):
    self._widget.assign_text(value if value is not None else '', enable_undo=True)


class FileExtensionEntryPresenter(ExtendedEntryPresenter):
  """`setting.Presenter` subclass for `gui.entries.FileExtensionEntry` widgets.

  Value: Text in the entry.
  """

  def _create_widget(self, setting, import_or_export='export', **kwargs):
    return entries_.FileExtensionEntry(import_or_export=import_or_export)


class NamePatternEntryPresenter(ExtendedEntryPresenter):
  """`setting.Presenter` subclass for
  `gui.entries.NamePatternEntry` widgets.

  Value: Text in the entry.
  """

  def _create_widget(self, setting, **kwargs):
    return entries_.NamePatternEntry(renamer_.get_field_descriptions())


class DimensionBoxPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `gui.DimensionBox` widgets.

  Value: A dictionary representing data obtained from a `gui.DimensionBox`.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, **kwargs):
    dimension_box = gui_widgets_.DimensionBox(
      default_pixel_value=setting.value['pixel_value'],
      default_percent_value=setting.value['percent_value'],
      default_percent_property=setting.value['percent_property'],
      default_other_value=setting.value['other_value'],
      min_value=setting.min_value,
      max_value=setting.max_value,
      default_unit=setting.value['unit'],
      pixel_unit=Gimp.Unit.pixel(),
      percent_unit=Gimp.Unit.percent(),
      percent_placeholder_names=setting.percent_placeholder_names,
      percent_placeholder_labels=[
        placeholders_.PLACEHOLDERS[name].display_name for name in setting.percent_placeholder_names
      ],
      percent_property_names=list(placeholders_.ATTRIBUTES),
      percent_property_labels=list(placeholders_.ATTRIBUTES.values()),
      percent_placeholder_attribute_map=setting.placeholder_attribute_map,
    )

    return dimension_box

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


class AngleBoxPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `gui.AngleBox` widgets.

  Value: A dictionary representing data obtained from a `gui.AngleBox`.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.AngleBox(
      default_value=setting.value['value'],
      default_unit=setting.value['unit'],
      units=dict(builtin_actions_.UNITS),
    )

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


class AnchorBoxPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `gui.AnchorBox` widgets.

  Value: A value representing an anchor point.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.AnchorBox(
      anchor_names_and_display_names=setting.items_display_names,
      default_anchor_name=setting.default_value,
    )

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


class CoordinatesBoxPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `gui.CoordinatesBox` widgets.

  Value: A dictionary representing data obtained from a `gui.CoordinatesBox`.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, label_x=None, label_y=None, **kwargs):
    return gui_widgets_.CoordinatesBox(
      default_x=setting.value['x'],
      default_y=setting.value['y'],
      min_x=setting.min_x,
      min_y=setting.min_y,
      max_x=setting.max_x,
      max_y=setting.max_y,
      label_x=label_x,
      label_y=label_y,
    )

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


class FileFormatOptionsPresenter(setting_.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Grid` widgets representing
  dictionaries of (string, value) pairs.

  Value: Dictionary of (string, value) pairs where the value is obtained from
    each widget.
  """

  def __init__(self, *args, show_display_name=False, **kwargs):
    super().__init__(*args, show_display_name=show_display_name, **kwargs)

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.FileFormatOptionsBox(**kwargs)

  def set_active_file_formats(self, file_formats):
    file_format_options = [
      self.setting.value.get(file_format, None) for file_format in file_formats]

    if self.setting.EXPANDED_KEY not in self.setting.value:
      self.setting.value[self.setting.EXPANDED_KEY] = {}

    self._widget.set_active_file_formats(
      file_formats, file_format_options, self.setting.value[self.setting.EXPANDED_KEY])

  def get_value(self):
    if self.setting.ACTIVE_FILE_FORMAT_KEY in self.setting.value:
      active_file_formats = self.setting.value[self.setting.ACTIVE_FILE_FORMAT_KEY]
      for active_file_format in active_file_formats:
        if active_file_format in self.setting.value:
          self.setting.value[active_file_format].apply_gui_values_to_settings()

    return self.setting.value

  def _set_value(self, value):
    if self.setting.EXPANDED_KEY not in value:
      value[self.setting.EXPANDED_KEY] = {}

    file_formats = value.get(self.setting.ACTIVE_FILE_FORMAT_KEY, None)

    if file_formats is not None:
      file_format_options = [value.get(file_format, None) for file_format in file_formats]
      self._widget.set_active_file_formats(
        file_formats, file_format_options, value[self.setting.EXPANDED_KEY])
    else:
      self._widget.set_active_file_formats([], [], value[self.setting.EXPANDED_KEY])
