from __future__ import annotations

from collections.abc import Iterable
from typing import Dict, List, Optional, Union, Tuple, Type

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import utils

from .. import meta as meta_
from .. import presenter as presenter_
from . import _base
from . import _numeric as _numeric_
from . import _string as _string_


_SETTING_TYPES = meta_.SETTING_TYPES
_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'ArraySetting',
]


class ArraySetting(_base.Setting):
  """Class for settings storing arrays of the specified type.

  Array settings can be registered to the GIMP PDB and have their own readily
  available GUI for adding, modifying and removing elements.

  Values of array settings are tuples whose elements are of the specified
  setting type.

  Any setting type can be passed on initialization of the array setting.
  However, only specific array types can be registered to the GIMP PDB or have
  their own GUI. For registrable array types, see the allowed GIMP PDB types
  below.

  If the ``element_type`` specified during instantiation has a matching GObject
  type (e.g. `Gimp.DoubleArray` for float arrays), then the array setting can
  be registered to the GIMP PDB. To disable registration, pass ``pdb_type=None``
  in `Setting.__init__()` as one normally would. The PDB type of individual
  elements cannot be customized as it appears that the GIMP API provides a fixed
  element type for each array type (e.g. `GObject.TYPE_DOUBLE` for
  `Gimp.DoubleArray`).

  Validation of setting values is performed for each element individually.

  If the input value to `set_value()` is not an iterable, it is wrapped in a
  tuple. Thus, if validation fails, ``'invalid_value'`` message ID is never
  returned.

  Array settings are useful for manipulating PDB array parameters or for
  storing a collection of values of the same type. For more fine-grained control
  (collection of values of different type, different GUI, etc.), use
  `setting.Group` instead.

  The following additional event types are invoked in `ArraySetting` instances:

  * ``'before-add-element'``: Invoked when calling `add_element()` immediately
    before adding an array element.

  * ``'after-add-element'``: Invoked when calling `add_element()` immediately
    after adding an array element.

  * ``'before-reorder-element'``: Invoked when calling `reorder_element()`
    immediately before reordering an array element.

  * ``'after-reorder-element'``: Invoked when calling `reorder_element()`
    immediately after reordering an array element.

  * ``'before-delete-element'``: Invoked when calling `remove_element()` or
    `__delitem__()` immediately before removing an array element.

  * ``'after-delete-element'``: Invoked when calling `remove_element()` or
    `__delitem__()` immediately after removing an array element.

  Allowed GIMP PDB types:
  * `Gimp.Int32Array`
  * `Gimp.DoubleArray`
  * `GObject.TYPE_STRV` (string array)
  * object arrays, i.e. arrays containing GIMP objects (e.g. images, layers,
    channels, ...).

  Default value: `()`

  Message IDs for invalid values:
  * ``'negative_min_size'``: `min_size` is negative.
  * ``'min_size_greater_than_max_size'``: `min_size` is greater than `max_size`.
  * ``'min_size_greater_than_value_length'``: `min_size` is greater than the
    length of the value.
  * ``'max_size_less_than_value_length'``: `max_size` is less than the length of
    the value.
  * ``'delete_below_min_size'``: deleting an element causes the array to have
    fewer than `min_size` elements.
  * ``'add_above_max_size'``: adding an element causes the array to have more
    than `max_size` elements.
  """

  ELEMENT_DEFAULT_VALUE = type('DefaultElementValue', (), {})()

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.array_box]

  _DEFAULT_DEFAULT_VALUE = ()

  _NATIVE_ARRAY_PDB_TYPES: Dict[Type[_base.Setting], Tuple[GObject.GType, GObject.GType]]
  _NATIVE_ARRAY_PDB_TYPES = {
    _numeric_.IntSetting: (Gimp.Int32Array, GObject.TYPE_INT, 'int32_array'),
    _numeric_.DoubleSetting: (Gimp.DoubleArray, GObject.TYPE_DOUBLE, 'double_array'),
    _string_.StringSetting: (GObject.TYPE_STRV, GObject.TYPE_STRING, 'string_array'),
  }

  def __init__(
        self,
        name: str,
        element_type: Union[str, Type[_base.Setting]],
        min_size: Optional[int] = 0,
        max_size: Optional[int] = None,
        **kwargs,
  ):
    """Initializes an `ArraySetting` instance.

    All parameters prefixed with ``'element_'`` (see ``**kwargs below``) will
    be created in the array setting as read-only properties.
    ``element_default_value`` will always be created.

    Args:
      name:
        See ``name`` in `Setting.__init__()`.
      element_type:
        A `Setting` subclass or the name of a `Setting` subclass determining
        the type of each array element.

        Passing `ArraySetting` is also possible, allowing to create
        multidimensional arrays. Note that in that case, required parameters
        for elements of each subsequent dimension must be specified and must
        have an extra ``'element_'`` prefix. For example, for the second
        dimension of a 2D array, `element_element_type` must also be specified.
      min_size:
        Minimum array size. If ``None``, the minimum size will be 0.
      max_size:
        Maximum array size. If ``None``, there is no upper limit on the array
        size.
      **kwargs:
        Additional keyword arguments for `Setting.__init__()`, plus all
        parameters that would be passed to the `Setting` class defined by
        ``element_type``. The arguments for the latter must be prefixed with
        ``element_`` - for example, for arrays containing integers (i.e.
        ``element_type`` is ``'int'``), you can optionally pass
        ``element_min_value=<value>`` to set the minimum value for all integer
        array elements.
        If ``element_pdb_type`` is specified, it will be ignored as each array
        type has one allowed PDB type for individual elements (e.g.
        `GObject.TYPE_DOUBLE` for `Gimp.DoubleArray`).
    """
    self._element_type = meta_.process_setting_type(element_type)
    self._min_size = min_size if min_size is not None else 0
    self._max_size = max_size

    self._element_kwargs = {
      key[len('element_'):]: value for key, value in kwargs.items()
      if key.startswith('element_')}

    if 'pdb_type' in self._element_kwargs:
      # Enforce a pre-set value for `element_pdb_type` as it appears that the
      # GIMP API allows only one type per array type.
      self._element_kwargs['pdb_type'] = self._get_default_element_pdb_type()

    self._reference_element = self._create_reference_element()

    if 'default_value' not in self._element_kwargs:
      self._element_kwargs['default_value'] = self._reference_element.default_value
    else:
      # noinspection PyProtectedMember
      self._element_kwargs['default_value'] = self._reference_element._raw_to_value(
        self._element_kwargs['default_value'])

    for key, value in self._element_kwargs.items():
      utils.create_read_only_property(self, f'element_{key}', value)

    self._elements = []

    array_kwargs = {key: value for key, value in kwargs.items() if not key.startswith('element_')}

    super().__init__(name, **array_kwargs)

  @property
  def value(self):
    """The array (setting value) as a tuple."""
    # This ensures that this property is always up-to-date no matter what events
    # are connected to individual elements.
    self._value = self._array_as_tuple()
    return self._value

  @property
  def value_for_pdb(self):
    """The array (setting value) in a format appropriate to be used as a PDB
    procedure argument.

    Certain array types as GIMP PDB procedure parameters (such as
    `Gimp.DoubleArray`) cannot accept a Python list/tuple and must be
    converted to the appropriate GObject-compatible type. The `value`
    property ensures that the array is converted to a GObject-compatible type.

    To access the array as a Python-like structure, use the `value` property
    returning the array values as a tuple. If you need to work directly with
    array elements as `Setting` instances, use `get_elements()`.
    """
    # This ensures that this property is always up-to-date no matter what events
    # are connected to individual elements.
    self._value = self._array_as_tuple()
    return array_as_pdb_compatible_type(self._value, self.element_type)

  @property
  def element_type(self) -> Type[_base.Setting]:
    """Setting type of array elements."""
    return self._element_type

  @property
  def min_size(self) -> int:
    """The minimum array size."""
    return self._min_size

  @property
  def max_size(self) -> Union[int, None]:
    """The maximum array size.

    If ``None``, the array size is unlimited.
    """
    return self._max_size

  def get_pdb_param(self) -> Union[List, None]:
    if self.can_be_used_in_pdb():
      if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
        return [
          self._NATIVE_ARRAY_PDB_TYPES[self.element_type][2],
          self._pdb_name,
          self._display_name,
          self._description,
          GObject.ParamFlags.READWRITE,
        ]
      elif self._reference_element.can_be_used_in_pdb():
        return [
          'core_object_array',
          self._pdb_name,
          self._display_name,
          self._description,
          self._reference_element.pdb_type,
          GObject.ParamFlags.READWRITE,
        ]
      else:
        return None
    else:
      return None

  def get_allowed_gui_types(self) -> List[Type[presenter_.Presenter]]:
    """Returns the list of allowed GUI types for this setting type.

    If the element type has no allowed GUI types, this setting type will not
    have any allowed GUI types either.
    """
    if self._reference_element.get_allowed_gui_types():
      return super().get_allowed_gui_types()
    else:
      return []

  def to_dict(self) -> Dict:
    settings_dict = super().to_dict()

    for key, val in settings_dict.items():
      if key == 'element_default_value':
        # noinspection PyProtectedMember
        settings_dict[key] = self._reference_element._value_to_raw(val)
      elif key == 'element_type':
        settings_dict[key] = _SETTING_TYPES[type(self._reference_element)]

    return settings_dict

  def __getitem__(
        self, index_or_slice: Union[int, slice],
  ) -> Union[_base.Setting, List[_base.Setting]]:
    """Returns an array element at the specified index, or a list of elements
    if given a slice.
    """
    return self._elements[index_or_slice]

  def __delitem__(self, index: int):
    """Removes an array element at the specified index."""
    if len(self._elements) == self._min_size:
      self._handle_failed_validation(
        f'cannot delete any more elements - at least {self._min_size} elements must be present',
        'delete_below_min_size',
        prepend_value=False,
      )

    self.invoke_event('before-delete-element', index)

    del self._elements[index]

    self.invoke_event('after-delete-element')

  def __len__(self) -> int:
    """Returns the number of elements of the array."""
    return len(self._elements)

  def add_element(
        self, index: Optional[int] = None, value=ELEMENT_DEFAULT_VALUE) -> _base.Setting:
    """Adds a new element with the specified value at the specified index
    (starting from 0).

    If ``index`` is ``None``, the value is appended at the end of the array.

    If ``value`` is `ELEMENT_DEFAULT_VALUE`, the default value of the
    underlying `element_type` is used.
    """
    if len(self._elements) == self._max_size:
      self._handle_failed_validation(
        f'cannot add any more elements - at most {self._max_size} elements are allowed',
        'add_above_max_size',
        prepend_value=False,
      )

    if isinstance(value, type(self.ELEMENT_DEFAULT_VALUE)):
      value = self._reference_element.default_value

    self.invoke_event('before-add-element', index, value)

    element = self._create_element(value)

    if index is None:
      self._elements.append(element)
      insertion_index = -1
    else:
      self._elements.insert(index, element)
      insertion_index = index if index >= 0 else index - 1

    self.invoke_event('after-add-element', insertion_index, value)

    return element

  def reorder_element(self, index: int, new_index: int):
    """Changes the order of an array element at ``index`` to a new position
    specified by ``new_index``.

    Both indexes start from 0.
    """
    self.invoke_event('before-reorder-element', index)

    element = self._elements.pop(index)

    if new_index < 0:
      new_index = max(len(self._elements) + new_index + 1, 0)

    self._elements.insert(new_index, element)

    self.invoke_event('after-reorder-element', index, new_index)

  def remove_element(self, index: int):
    """Removes an element at the specified index.

    This method is an alias to `__delitem__`.
    """
    self.__delitem__(index)

  def get_elements(self) -> List[_base.Setting]:
    """Returns a list of array elements as `Setting` instances."""
    return list(self._elements)

  def _raw_to_value(self, raw_value_array):
    if isinstance(raw_value_array, Iterable) and not isinstance(raw_value_array, str):
      # noinspection PyProtectedMember
      return tuple(
        self._reference_element._raw_to_value(raw_value)
        for raw_value in raw_value_array)
    else:
      # Convert to a safe value so that subsequent post-processing does not fail.
      return (raw_value_array,)

  def _value_to_raw(self, value_array):
    # noinspection PyProtectedMember
    return [
      self._reference_element._value_to_raw(value)
      for value in value_array]

  def _validate(self, value_array):
    if not hasattr(value_array, '__len__'):
      value_array = list(value_array)

    if self._min_size < 0:
      self._handle_failed_validation(
        f'minimum size ({self._min_size}) cannot be negative',
        'negative_min_size',
        prepend_value=False,
      )
    elif self._max_size is not None and self._min_size > self._max_size:
      self._handle_failed_validation(
        f'minimum size ({self._min_size}) cannot be greater than maximum size ({self._max_size})',
        'min_size_greater_than_max_size',
        prepend_value=False,
      )
    elif self._min_size > len(value_array):
      self._handle_failed_validation(
        (f'minimum size ({self._min_size}) cannot be greater'
         f' than the length of the value ({len(value_array)})'),
        'min_size_greater_than_value_length',
        prepend_value=False,
      )
    elif self._max_size is not None and self._max_size < len(value_array):
      self._handle_failed_validation(
        (f'maximum size ({self._max_size}) cannot be less'
         f' than the length of the value ({len(value_array)})'),
        'max_size_less_than_value_length',
        prepend_value=False,
      )

    for value in value_array:
      # noinspection PyProtectedMember
      self._reference_element._validate(value)
    self._reference_element.reset()

  def _assign_value(self, value_array):
    self._elements.clear()

    for value in value_array:
      element = self._create_element(value)
      self._elements.append(element)

    self._value = self._array_as_tuple()

  def _apply_gui_value_to_setting(self, value):
    # No assignment takes place to prevent breaking the sync between the array
    # and the GUI.
    self.invoke_event('value-changed')

  def _copy_value(self, value):
    self._elements = [self._create_element(element_value) for element_value in value]
    return self._array_as_tuple()

  def _get_default_pdb_type(self):
    if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
      return self._NATIVE_ARRAY_PDB_TYPES[self.element_type][0]
    elif self._reference_element.can_be_used_in_pdb():
      return GObject.GType.from_name('GimpCoreObjectArray')
    else:
      return None

  def _get_default_element_pdb_type(self):
    if self.element_type in self._NATIVE_ARRAY_PDB_TYPES:
      return self._NATIVE_ARRAY_PDB_TYPES[self.element_type][1]
    elif self._reference_element.can_be_used_in_pdb():
      return self._reference_element.pdb_type
    else:
      return None

  def _create_reference_element(self):
    """Creates a reference element to access and validate the element default
    value.
    """
    # Rely on the underlying element setting type to perform validation of the
    # default value.
    return self._element_type(name='element', **dict(self._element_kwargs, gui_type=None))

  def _create_element(self, value):
    kwargs = dict(
      dict(
        name='element',
        display_name='',
        pdb_type=None),
      **self._element_kwargs)

    setting = self._element_type(**kwargs)
    setting.set_value(value)

    return setting

  def _array_as_tuple(self):
    return tuple(setting.value for setting in self._elements)


def array_as_pdb_compatible_type(
      values: Tuple[Any, ...],
      element_setting_type: Optional[Type[_base.Setting]] = None,
) -> Union[Tuple[Any, ...], Gimp.Int32Array, Gimp.DoubleArray]:
  """Returns an array suitable to be passed to a GIMP PDB procedure."""
  if element_setting_type == _numeric_.IntSetting:
    array = GObject.Value(Gimp.Int32Array)
    Gimp.value_set_int32_array(array, values)
    return array.get_boxed()
  elif element_setting_type == _numeric_.DoubleSetting:
    array = GObject.Value(Gimp.DoubleArray)
    Gimp.value_set_double_array(array, values)
    return array.get_boxed()
  else:
    return values
