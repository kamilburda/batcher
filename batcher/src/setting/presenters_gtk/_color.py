import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from . import _base


__all__ = [
  'ColorButtonPresenter',
]


class ColorButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `GimpUi.ColorButton` widgets.

  Value: `Gegl.Color` instance representing color in RGBA.
  """

  _VALUE_CHANGED_SIGNAL = 'color-changed'

  def _create_widget(self, setting, width=100, height=20):
    return GimpUi.ColorButton.new(
      setting.display_name,
      width,
      height,
      self.setting.get_value_as_color(setting.value),
      GimpUi.ColorAreaType.SMALL_CHECKS,
    )

  def get_value(self):
    return self._widget.get_color()

  def _set_value(self, value):
    self._widget.set_color(self.setting.get_value_as_color(value))
