from __future__ import annotations

from . import _base

__all__ = [
  'ContainerSetting',
  'ListSetting',
  'TupleSetting',
  'SetSetting',
  'DictSetting',
]


class ContainerSetting(_base.Setting):
  """Abstract class for settings representing container types.

  Container settings can hold items of arbitrary type, but cannot be
  registered to the GIMP PDB and do not have a GUI widget. Use `ArraySetting`
  if you need to pass the items to a GIMP PDB procedure and allow adjusting
  the item values via GUI.

  If you intend to save container settings to a setting source, make sure each
  item is of one of the types specified in the description of
  `Setting.to_dict()`. Otherwise, saving may fail.

  Optionally, when assigning, the value can be nullable (``None``) instead of
  always a container.
  """

  _ABSTRACT = True

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = []

  def __init__(self, name: str, nullable: bool = False, **kwargs):
    """Initializes a `ContainerSetting` instance.

    Args:
      nullable:
        See the `nullable` property.
    """
    super().__init__(name, **kwargs)

    self._nullable = nullable

  @property
  def nullable(self) -> bool:
    """If ``True``, ``None`` is treated as a valid value when calling
    `set_value()`.
    """
    return self._nullable

  def _validate(self, value):
    if value is None and not self._nullable:
      return (
        'cannot assign a null value (None) if the setting is not nullable',
        'value_is_none',
        False,
      )


class ListSetting(ContainerSetting):
  """Class for settings representing lists (mutable sequences of elements)."""

  _DEFAULT_DEFAULT_VALUE = lambda self: []

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, list) and raw_value is not None:
      return list(raw_value)
    else:
      return raw_value


class TupleSetting(ContainerSetting):
  """Class for settings representing tuples (immutable sequences of elements).
  """

  _DEFAULT_DEFAULT_VALUE = lambda self: ()

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, tuple) and raw_value is not None:
      return tuple(raw_value)
    else:
      return raw_value

  def _value_to_raw(self, value):
    return list(value)


class SetSetting(ContainerSetting):
  """Class for settings representing sets (mutable unordered collections of
  elements).
  """

  _DEFAULT_DEFAULT_VALUE = lambda self: set()

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, set) and raw_value is not None:
      return set(raw_value)
    else:
      return raw_value

  def _value_to_raw(self, value):
    return list(value)


class DictSetting(ContainerSetting):
  """Class for settings representing dictionaries (collections of key-value
  pairs).
  """

  _ALIASES = ['dictionary', 'map']

  _DEFAULT_DEFAULT_VALUE = lambda self: {}

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, dict) and raw_value is not None:
      return dict(raw_value)
    else:
      return raw_value
