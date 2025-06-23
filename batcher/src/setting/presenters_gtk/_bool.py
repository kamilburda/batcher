import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import _base


__all__ = [
  'CheckButtonPresenter',
  'CheckMenuItemPresenter',
  'ExpanderPresenter',
]


class CheckButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckButton` widgets.

  Value: Checked state of the check button (checked/unchecked).
  """

  _VALUE_CHANGED_SIGNAL = 'clicked'

  def __init__(
        self,
        *args,
        show_display_name=False,
        width_chars_when_attached_to_grid=25,
        **kwargs,
  ):
    super().__init__(*args, show_display_name=show_display_name, **kwargs)

    self._width_chars_when_attached_to_grid = width_chars_when_attached_to_grid

    self.setting.connect_event('gui-attached-to-grid', self._on_attached_to_grid)

  def _create_widget(self, setting, width_chars=20, max_width_chars=40, **kwargs):
    check_button = Gtk.CheckButton(
      label=setting.display_name,
      use_underline=False,
    )

    check_button.get_child().set_width_chars(width_chars)
    check_button.get_child().set_max_width_chars(max_width_chars)
    check_button.get_child().set_use_markup(False)
    check_button.get_child().set_line_wrap(True)

    return check_button

  def get_value(self):
    return self._widget.get_active()

  def _set_value(self, value):
    self._widget.set_active(value)

  def _on_attached_to_grid(self, _setting):
    if not self.show_display_name:
      self._widget.get_child().set_width_chars(self._width_chars_when_attached_to_grid)


class CheckMenuItemPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckMenuItem` widgets.

  Value: Checked state of the menu item (checked/unchecked).
  """

  _VALUE_CHANGED_SIGNAL = 'toggled'

  def _create_widget(self, setting, **kwargs):
    return Gtk.CheckMenuItem(label=setting.display_name)

  def get_value(self):
    return self._widget.get_active()

  def _set_value(self, value):
    self._widget.set_active(value)


class ExpanderPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Expander` widgets.

  Value: ``True`` if the expander is expanded, ``False`` if collapsed.
  """

  _VALUE_CHANGED_SIGNAL = 'notify::expanded'

  def _create_widget(self, setting, **kwargs):
    return Gtk.Expander(label=setting.display_name, use_underline=True)

  def get_value(self):
    return self._widget.get_expanded()

  def _set_value(self, value):
    self._widget.set_expanded(value)
