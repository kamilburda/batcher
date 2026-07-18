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
        factor=1,
        **kwargs,
  ):
    self._factor = int(factor)

    return _create_spin_button(
      setting,
      digits=0,
      step_increment=step_increment,
      page_increment=page_increment,
      soft_minimum=soft_minimum,
      soft_maximum=soft_maximum,
      gamma=None,
      factor=self._factor,
    )

  def get_value(self):
    return self._widget.get_value_as_int() // self._factor

  def _set_value(self, value):
    self._widget.set_value(value * self._factor)


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
        factor=1.0,
        **kwargs,
  ):
    self._factor = factor

    return _create_spin_button(
      setting,
      digits=digits,
      step_increment=step_increment,
      page_increment=page_increment,
      soft_minimum=soft_minimum,
      soft_maximum=soft_maximum,
      gamma=gamma,
      factor=self._factor,
    )

  def get_value(self):
    return self._widget.get_value() / self._factor

  def _set_value(self, value):
    self._widget.set_value(value * self._factor)


def _create_spin_button(
      setting,
      digits=None,
      step_increment=None,
      page_increment=None,
      soft_minimum=None,
      soft_maximum=None,
      gamma=None,
      factor=1.0,
):
  if digits is None:
    digits = 2

  if hasattr(setting, 'min_value') and setting.min_value is not None:
    min_value = setting.min_value
  elif hasattr(setting, 'pdb_min_value') and setting.pdb_min_value is not None:
    min_value = setting.pdb_min_value
  else:
    min_value = GLib.MININT

  min_value_scaled = max(min_value * factor, GLib.MININT)

  if hasattr(setting, 'max_value') and setting.max_value is not None:
    max_value = setting.max_value
  elif hasattr(setting, 'pdb_max_value') and setting.pdb_max_value is not None:
    max_value = setting.pdb_max_value
  else:
    max_value = GLib.MAXINT

  max_value_scaled = min(max_value * factor, GLib.MAXINT)

  if soft_minimum is not None and soft_minimum < min_value:
    soft_minimum = min_value
    soft_minimum_scaled = max(soft_minimum * factor, GLib.MININT)
  else:
    soft_minimum_scaled = None

  if soft_maximum is not None and soft_maximum > max_value:
    soft_maximum = max_value
    soft_maximum_scaled = min(soft_maximum * factor, GLib.MAXINT)
  else:
    soft_maximum_scaled = None

  if soft_minimum_scaled is not None and soft_maximum_scaled is not None:
    value_range = abs(soft_minimum_scaled - soft_maximum_scaled)
  else:
    value_range = abs(max_value_scaled - min_value_scaled)

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
      lower=min_value_scaled,
      upper=max_value_scaled,
      step_increment=step_increment,
      page_increment=page_increment,
    ),
    digits=digits,
    numeric=True,
  )

  if isinstance(spin_button, GimpUi.SpinScale):
    if gamma is not None:
      spin_button.set_gamma(gamma)

    if soft_minimum_scaled is not None and soft_maximum_scaled is not None:
      spin_button.set_scale_limits(soft_minimum_scaled, soft_maximum_scaled)

  return spin_button
