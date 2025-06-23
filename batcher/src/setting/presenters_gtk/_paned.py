from . import _base


__all__ = [
  'PanedPositionPresenter',
]


class PanedPositionPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Paned` widgets.

  Value: Position of the divider between the two panes.
  """

  def get_value(self):
    return self._widget.get_position()

  def _set_value(self, value):
    self._widget.set_position(value)
