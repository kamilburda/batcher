import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from . import _base


__all__ = [
  'GimpResourceChooserPresenter',
  'BrushChooserPresenter',
  'FontChooserPresenter',
  'GradientChooserPresenter',
  'PaletteChooserPresenter',
  'PatternChooserPresenter',
]


class GimpResourceChooserPresenter(_base.GtkPresenter):
  """Abstract `setting.Presenter` subclass for widgets allowing to select and
  modify a `Gimp.Resource` instance via a specialized button.
  """

  _ABSTRACT = True

  _VALUE_CHANGED_SIGNAL = 'resource-set'

  def get_value(self):
    return self._widget.get_resource()

  def _set_value(self, value):
    if value is not None:
      self._widget.set_resource(value)


class BrushChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.BrushChooser` widgets.

  Value: A `Gimp.Brush` instance.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.BrushChooser.new(None, None, setting.value)


class FontChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.FontChooser` widgets.

  Value: A `Gimp.Font` instance.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.FontChooser.new(None, None, setting.value)


class GradientChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.GradientChooser` widgets.

  Value: A `Gimp.Gradient` instance.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.GradientChooser.new(None, None, setting.value)


class PaletteChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.PaletteChooser` widgets.

  Value: A `Gimp.Palette` instance.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.PaletteChooser.new(None, None, setting.value)


class PatternChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.PatternChooser` widgets.

  Value: String representing a pattern.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.PatternChooser.new(None, None, setting.value)
