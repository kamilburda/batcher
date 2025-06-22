from __future__ import annotations

import inspect
from typing import Callable, Optional

from . import _base


class GenericSetting(_base.Setting):
  """Class for settings storing arbitrary data.

  Since there are limitations on the types of values that can be saved to a
  setting source (see the description for `Setting` for the supported types),
  it is strongly recommended that you provide ``value_set`` and
  ``value_save`` parameters to `GenericSetting.__init__()`. The functions
  must ensure the setting value will be loaded and saved properly. If
  ``value_save`` is ``None``, the value is converted to a string via `repr()`
  as fallback. Such a string will very likely not be usable in your
  application when loading the setting.
  """

  def __init__(
        self,
        name: str,
        value_set: Optional[Callable] = None,
        value_save: Optional[Callable] = None,
        **kwargs,
  ):
    """Initializes a `GenericSetting` instance.

    Args:
      value_set:
        Function invoked at the beginning of `set_value()`. The function
        allows converting values of other types or formats, particularly when
        loading value for this setting from a source that allows storing only
        several value types. The function accepts one or two positional
        parameters - the input value and this setting instance (the latter
        can be omitted if not needed).
      value_save:
        Function invoked at the beginning of `to_dict()`. The function should
        ensure that the setting value is converted to a type supported by
        setting sources. The function accepts one or two positional
        parameters - the current setting value and this setting instance (the
        latter can be omitted if not needed).
    """
    self._before_value_set = value_set
    self._before_value_save = value_save

    self._validate_function(self._before_value_set, 'value_set')
    self._validate_function(self._before_value_save, 'value_save')

    super().__init__(name, **kwargs)

  def to_dict(self):
    settings_dict = super().to_dict()

    settings_dict.pop('value_set', None)
    settings_dict.pop('value_save', None)

    return settings_dict

  def _raw_to_value(self, raw_value):
    value = raw_value

    if self._before_value_set is not None:
      if len(inspect.getfullargspec(self._before_value_set).args) == 1:
        value = self._before_value_set(raw_value)
      else:
        value = self._before_value_set(raw_value, self)

    return value

  def _value_to_raw(self, value):
    raw_value = value

    if self._before_value_save is not None:
      if len(inspect.getfullargspec(self._before_value_save).args) == 1:
        raw_value = self._before_value_save(value)
      else:
        raw_value = self._before_value_save(value, self)
    else:
      raw_value = repr(value)

    return raw_value

  @staticmethod
  def _validate_function(func, name):
    if func is None:
      return

    if not callable(func):
      raise TypeError(f'{name} must be callable')

    if len(inspect.getfullargspec(func).args) not in [1, 2]:
      raise TypeError(f'{name} function must have 1 or 2 positional parameters')
