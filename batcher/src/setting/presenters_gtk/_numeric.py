import math

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import _base


__all__ = [
  'IntSpinButtonPresenter',
  'DoubleSpinButtonPresenter',
]


class IntSpinButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.

  Value: Integer value of the spin button.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, **kwargs):
    return _create_spin_button(setting, digits=0)

  def get_value(self):
    return self._widget.get_value_as_int()

  def _set_value(self, value):
    self._widget.set_value(value)


class DoubleSpinButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.

  Value: Floating point value of the spin button.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(self, setting, digits=None, step_increment=None, **kwargs):
    return _create_spin_button(setting, digits=digits, step_increment=step_increment)

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


def _create_spin_button(setting, digits=None, step_increment=None):
  if digits is None:
    digits = 2

  if hasattr(setting, 'min_value') and setting.min_value is not None:
    min_value = setting.min_value
  elif hasattr(setting, 'pdb_min_value') and setting.pdb_min_value is not None:
    min_value = setting.pdb_min_value
  else:
    min_value = GLib.MININT

  if hasattr(setting, 'max_value') and setting.max_value is not None:
    max_value = setting.max_value
  elif hasattr(setting, 'pdb_max_value') and setting.pdb_max_value is not None:
    max_value = setting.pdb_max_value
  else:
    max_value = GLib.MAXINT

  value_range = abs(max_value - min_value)

  if value_range <= GLib.MAXUINT16:
    spin_button_class = GimpUi.SpinScale
  else:
    spin_button_class = Gtk.SpinButton

  if step_increment is None:
    if digits > 0 and 0 < value_range <= 1:
      digits_in_value_range = -math.floor(math.log10(value_range))

      step_increment = 10 ** -(digits_in_value_range + 1)
    else:
      step_increment = 1

  page_increment = 10 * step_increment

  return spin_button_class(
    adjustment=Gtk.Adjustment(
      value=setting.value,
      lower=min_value,
      upper=max_value,
      step_increment=step_increment,
      page_increment=page_increment,
    ),
    digits=digits,
    numeric=True,
  )
