from . import _base


__all__ = [
  'WindowPositionPresenter',
  'WindowSizePresenter',
]


class WindowPositionPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Window` widgets to get/set position.

  Value: Current position of the window as a tuple of 2 integers.
  """

  def get_value(self):
    return self._widget.get_position()

  def _set_value(self, value):
    """Sets a new position of the window (i.e. moves the window).

    The window is not moved if ``value`` is ``None`` or empty.
    """
    if value:
      self._widget.move(*value)


class WindowSizePresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Window` widgets to get/set size.

  Value: Current size of the window as a tuple of 2 integers.
  """

  def get_value(self):
    return self._widget.get_size()

  def _set_value(self, value):
    """Sets a new size of the window.

    The window is not resized if ``value`` is ``None`` or empty.
    """
    if value:
      self._widget.resize(*value)
