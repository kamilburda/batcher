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

  def _create_widget(
        self,
        setting,
        step_increment=None,
        page_increment=None,
        soft_minimum=None,
        soft_maximum=None,
        **kwargs,
  ):
    return _create_spin_button(
      setting,
      digits=0,
      step_increment=step_increment,
      page_increment=page_increment,
      soft_minimum=soft_minimum,
      soft_maximum=soft_maximum,
      gamma=None,
    )

  def get_value(self):
    return self._widget.get_value_as_int()

  def _set_value(self, value):
    self._widget.set_value(value)


class DoubleSpinButtonPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.

  Value: Floating point value of the spin button.
  """

  _VALUE_CHANGED_SIGNAL = 'value-changed'

  def _create_widget(
        self,
        setting,
        digits=None,
        step_increment=None,
        page_increment=None,
        soft_minimum=None,
        soft_maximum=None,
        gamma=None,
        **kwargs,
  ):
    return _create_spin_button(
      setting,
      digits=digits,
      step_increment=step_increment,
      page_increment=page_increment,
      soft_minimum=soft_minimum,
      soft_maximum=soft_maximum,
      gamma=gamma,
    )

  def get_value(self):
    return self._widget.get_value()

  def _set_value(self, value):
    self._widget.set_value(value)


def _create_spin_button(
      setting,
      digits=None,
      step_increment=None,
      page_increment=None,
      soft_minimum=None,
      soft_maximum=None,
      gamma=None,
):
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

  if soft_minimum is not None and soft_minimum < min_value:
    soft_minimum = min_value

  if soft_maximum is not None and soft_maximum > max_value:
    soft_maximum = max_value

  if soft_minimum is not None and soft_maximum is not None:
    value_range = abs(soft_maximum - soft_minimum)
  else:
    value_range = abs(max_value - min_value)

  if value_range <= GLib.MAXUINT16:
    spin_button_class = GimpUi.SpinScale
  else:
    spin_button_class = Gtk.SpinButton

  if step_increment is None:
    if digits > 0 and 0 < value_range <= 1:
      digits_in_value_range = -math.floor(math.log10(value_range))

      step_increment = 10 ** -(digits_in_value_range + 2)
    elif digits > 0 and 1 < value_range <= 10:
      step_increment = 0.1
    else:
      step_increment = 1

  if page_increment is None:
    page_increment = 10 * step_increment

  spin_button = spin_button_class(
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

  if isinstance(spin_button, GimpUi.SpinScale):
    if gamma is not None:
      spin_button.set_gamma(gamma)

    if soft_minimum is not None and soft_maximum is not None:
      spin_button.set_scale_limits(soft_minimum, soft_maximum)

  return spin_button
