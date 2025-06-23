from src.gui import widgets as gui_widgets_

from . import _base


__all__ = [
  'ParasiteBoxPresenter',
]


class ParasiteBoxPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `gui.ParasiteBox` widgets.

  Value: `Gimp.Parasite` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'parasite-changed'

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.ParasiteBox(setting.value, setting.DEFAULT_PARASITE_NAME)

  def get_value(self):
    return self._widget.get_parasite()

  def _set_value(self, value):
    self._widget.set_parasite(value)
