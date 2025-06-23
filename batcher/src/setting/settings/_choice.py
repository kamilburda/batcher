
from __future__ import annotations

from typing import Dict, List, Optional, Union, Tuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import pypdb
from src.pypdb import pdb

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'ChoiceSetting',
]


class ChoiceSetting(_base.Setting):
  """Class for settings with a limited number of values, accessed by their
  associated names.

  Allowed GIMP PDB types:
  * `GObject.TYPE_STRING`

  Default value: Name of the first item passed to the ``items`` parameter in
  `ChoiceSetting.__init__()`.

  To access an item value:

    setting.items[item name]

  To access an item display name:

    setting.items_display_names[item name]

  Raises:
    ValueError:
      The same numeric value was assigned to multiple items, or an uneven
      number of elements was passed to the ``items`` parameter in `__init__()`.
    KeyError:
      Invalid key for the `items` or `items_display_names` property.

  Message IDs for invalid values:
    * ``'invalid_value'``: The value assigned is not one of the items in this
      setting if the ``items`` parameter passed to `__init__()` was not empty.
    * ``'invalid_default_value'``: Item name is not valid (not found in the
      ``items`` parameter in `__init__()`) if the ``items`` parameter passed to
      `__init__()` was not empty.
  """

  _ALLOWED_PDB_TYPES = [GObject.TYPE_STRING]

  _REGISTRABLE_TYPE_NAME = 'choice'

  _ALLOWED_GUI_TYPES = [
    _SETTING_GUI_TYPES.combo_box,
    _SETTING_GUI_TYPES.radio_button_box,
    _SETTING_GUI_TYPES.prop_choice_combo_box,
  ]

  _DEFAULT_DEFAULT_VALUE = lambda self: next(iter(self._items), '')

  def __init__(
        self,
        name: str,
        items: Optional[
          Union[
            List[Tuple[str, str]],
            List[Tuple[str, str, int]],
            List[Tuple[str, str, int, str]],
            Gimp.Choice]
        ] = None,
        procedure: Optional[Union[pypdb.PDBProcedure, str]] = None,
        **kwargs,
  ):
    """Initializes a `ChoiceSetting` instance.

    Args:
      items:
        A list of (item name, item display name) tuples, (item name,
        item display name, item value) tuples or a `Gimp.Choice` instance
        filled with possible choices. For 2-element tuples, item values are
        assigned automatically, starting with 0. Use 3-element tuples to
        assign explicit item values. Values must be unique and specified in
        each tuple. Use only 2- or only 3-element tuples, they cannot be
        combined. If ``items`` is ``None`` or an empty list, any string can
        be assigned to this setting.
      procedure:
        A `pypdb.PDBProcedure` instance, or name thereof, whose PDB parameter
        having the name ``name`` contains possible choices. This is ignored if
        ``items`` is a non-empty list.
    """
    self._items, self._items_by_value, self._items_display_names, self._items_help, self._choice = (
      self._create_item_attributes(items))

    self._procedure = self._process_procedure(procedure, items)
    self._procedure_config = self._create_procedure_config(self._procedure)

    super().__init__(name, **kwargs)

  @property
  def items(self) -> Dict[str, int]:
    """A dictionary of (item name, item value) pairs."""
    return self._items

  @property
  def items_by_value(self) -> Dict[int, str]:
    """A dictionary of (item value, item name) pairs."""
    return self._items_by_value

  @property
  def items_display_names(self) -> Dict[str, str]:
    """A dictionary of (item name, item display name) pairs.

    Item display names can be used e.g. as combo box items in the GUI.
    """
    return self._items_display_names

  @property
  def items_help(self) -> Dict[str, str]:
    """A dictionary of (item name, item help) pairs.

    Item help describes the item in more detail.
    """
    return self._items_help

  @property
  def procedure(self) -> Union[pypdb.PDBProcedure, None]:
    """A `pypdb.PDBProcedure` instance allowing to obtain the `Gimp.Choice`
    instance for this setting.
    """
    return self._procedure

  @property
  def procedure_config(self) -> Union[Gimp.ConfigInterface, None]:
    """A procedure config allowing to obtain the `Gimp.Choice` instance for this
    setting.
    """
    return self._procedure_config

  def to_dict(self):
    settings_dict = super().to_dict()

    if 'items' in settings_dict:
      if settings_dict['items'] is None:
        settings_dict['items'] = []
      elif isinstance(settings_dict['items'], Gimp.Choice):
        settings_dict['items'] = [
          [
            name,
            self._choice.get_label(name) if self._choice.get_label(name) is not None else '',
            self._choice.get_id(name),
            self._choice.get_help(name) if self._choice.get_help(name) is not None else '',
          ]
          for name in self._choice.list_nicks()
        ]
      else:
        settings_dict['items'] = [list(elements) for elements in settings_dict['items']]

    if 'procedure' in settings_dict:
      if settings_dict['procedure'] is not None and self._procedure is not None:
        settings_dict['procedure'] = self._procedure.name

    return settings_dict

  def get_name(self) -> str:
    """Returns the item name corresponding to the current setting value.

    This is a more convenient and less verbose alternative to

      setting.items_by_value(setting.value)
    """
    return self._items_by_value[self.value]

  def get_item_display_names_and_values(self) -> List[Tuple[str, int]]:
    """Returns a list of (item display name, item value) tuples."""
    display_names_and_values = []
    for item_name, item_value in zip(self._items_display_names.values(), self._items.values()):
      display_names_and_values.append((item_name, item_value))
    return display_names_and_values

  def _resolve_default_value(self, default_value):
    if isinstance(default_value, type(_base.Setting.DEFAULT_VALUE)):
      # We assume that at least one item exists (this is handled before this
      # method) and thus the default value is valid.
      return super()._resolve_default_value(default_value)
    else:
      if self._items:
        if default_value in self._items:
          return default_value
        else:
          self._handle_failed_validation(
            f'invalid default value "{default_value}"; must be one of {list(self._items)}',
            'invalid_default_value',
            prepend_value=False,
          )
      else:
        return default_value

  def _validate(self, item_name):
    if self._items and item_name not in self._items:
      return f'invalid item name; valid values: {list(self._items)}', 'invalid_value'

  @staticmethod
  def _process_procedure(procedure, raw_items) -> Union[pypdb.PDBProcedure, str, None]:
    if procedure is None or raw_items:
      return None
    elif isinstance(procedure, pypdb.PDBProcedure):
      return procedure
    elif isinstance(procedure, str):
      if procedure in pdb:
        return pdb[procedure]
      else:
        return None
    else:
      raise TypeError('procedure must be None, a string or a pypdb.PDBProcedure instance')

  @staticmethod
  def _create_procedure_config(procedure):
    if procedure is not None:
      return procedure.create_config()
    else:
      return None

  @staticmethod
  def _create_item_attributes(input_items):
    items = {}
    items_by_value = {}
    items_display_names = {}
    items_help = {}

    if not input_items:
      return items, items_by_value, items_display_names, items_help, Gimp.Choice.new()

    if isinstance(input_items, Gimp.Choice):
      for name in input_items.list_nicks():
        value = input_items.get_id(name)
        items[name] = value
        items_by_value[value] = name

        item_label = input_items.get_label(name)
        items_display_names[name] = item_label if item_label is not None else ''

        item_help = input_items.get_help(name)
        items_help[name] = item_help if item_help is not None else ''

      return items, items_by_value, items_display_names, items_help, input_items

    if all(len(elem) == 2 for elem in input_items):
      for i, (item_name, item_display_name) in enumerate(input_items):
        if item_name in items:
          raise ValueError('cannot use the same name for multiple items - they must be unique')

        items[item_name] = i
        items_by_value[i] = item_name
        items_display_names[item_name] = item_display_name
        items_help[item_name] = ''
    elif all(len(elem) in [3, 4] for elem in input_items):
      for item in input_items:
        if len(item) == 3:
          item_name, item_display_name, item_value = item
          item_help = ''
        else:
          item_name, item_display_name, item_value, item_help = item

        if item_name in items:
          raise ValueError('cannot use the same name for multiple items - they must be unique')

        if item_value in items_by_value:
          raise ValueError('cannot set the same value for multiple items - they must be unique')

        items[item_name] = item_value
        items_by_value[item_value] = item_name
        items_display_names[item_name] = item_display_name
        items_help[item_name] = item_help
    else:
      raise ValueError(
        'wrong number of tuple elements in items - must be only 2- or only 3-element tuples')

    choice = Gimp.Choice.new()
    for item in zip(items.items(), items_display_names.values(), items_help.values()):
      (name, value), display_name, help_ = item
      choice.add(name, value, display_name, help_)

    return items, items_by_value, items_display_names, items_help, choice

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._choice,
      self._default_value,
      GObject.ParamFlags.READWRITE,
    ]
