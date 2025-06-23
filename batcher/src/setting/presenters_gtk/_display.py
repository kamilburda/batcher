import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import _base


__all__ = [
  'DisplaySpinButtonPresenter',
]


class DisplaySpinButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.

  Value: `Gimp.Display` instance, represented by its integer ID in the spin
  button.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, **kwargs):
    return Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=setting.value.get_id() if setting.value is not None else 0,
        lower=0,
        upper=GLib.MAXINT,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
    )

  def get_value(self):
    return Gimp.Display.get_by_id(self._widget.get_value_as_int())

  def _set_value(self, value):
    if value is not None:
      self._widget.set_value(value.get_id())
