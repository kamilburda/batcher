from src.gui import widgets as gui_widgets_

from src import utils_pdb

from . import _base

__all__ = []

if utils_pdb.get_gimp_version() >= (3, 2):
  __all__.extend([
    'CurveEditorPresenter',
  ])


if utils_pdb.get_gimp_version() >= (3, 2):
  class CurveEditorPresenter(_base.GtkPresenter):
    """`setting.Presenter` subclass for `gui.CurveEditor` widgets.

    Value: `Gimp.Curve` instance.
    """

    _VALUE_CHANGED_SIGNAL = 'curve-changed'

    def _create_widget(self, setting, **kwargs):
      return gui_widgets_.CurveEditor(setting.value)

    def get_value(self):
      return self._widget.get_curve()

    def _set_value(self, value):
      self._widget.set_curve(value)
