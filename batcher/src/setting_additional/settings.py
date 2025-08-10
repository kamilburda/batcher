"""Additional setting and setting GUI classes specific to the plug-in."""

import abc
import collections
from collections.abc import Iterable
import os
from typing import Callable, Dict, List, Type, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GLib

from src import file_formats as file_formats_
from src import itemtree
from src import placeholders as placeholders_
from src import setting as setting_
from src import utils
from src import utils_pdb
from src.path import validators as validators_


__all__ = [
  'ValidatableStringSetting',
  'FileExtensionSetting',
  'NamePatternSetting',
  'DimensionSetting',
  'AngleSetting',
  'AnchorSetting',
  'CoordinatesSetting',
  'ItemTreeItemsSetting',
  'GimpItemTreeItemsSetting',
  'GimpImageTreeItemsSetting',
  'ImageFileTreeItemsSetting',
  'ImagesAndDirectoriesSetting',
  'FileFormatOptionsSetting',
  'TaggedItemsSetting',
]


class ValidatableStringSetting(setting_.StringSetting):
  """Abstract class for string settings which are meant to be validated with one
  of the `path.validators.StringValidator` subclasses.

  To determine whether the string is valid, `is_valid()` from the corresponding
  subclass is called.

  If you pass ``nullable=True``, ``None`` or an empty string will be
  considered a valid value.

  Message IDs for invalid values:
    Message IDs defined in `path.validators.FileValidatorErrorStatuses`.
  """

  _ABSTRACT = True

  def __init__(
        self,
        name: str,
        string_validator_class: Type[validators_.StringValidator],
        nullable: bool = False,
        **kwargs,
  ):
    """Initializes a `ValidatableStringSetting` instance.

    Args:
      string_validator_class:
        `path.validators.StringValidator` subclass used to validate the value
        assigned to this object.
      nullable:
        See the `nullable` property.
    """
    self._string_validator = string_validator_class
    self._nullable = nullable

    super().__init__(name, **kwargs)

  @property
  def nullable(self) -> bool:
    """If ``True``, ``None`` is treated as a valid value when calling
    `set_value()`.
    """
    return self._nullable

  def _validate(self, string_):
    if self._nullable and not string_:
      return

    is_valid, status_messages = self._string_validator.is_valid(string_)

    if not is_valid:
      for status, status_message in status_messages:
        return status_message, status


class FileExtensionSetting(ValidatableStringSetting):
  """Class for settings storing file extensions as strings.

  The `path.validators.FileExtensionValidator` subclass is used to determine
  whether the file extension is valid.
  """

  _ALLOWED_GUI_TYPES = [
    setting_.SETTING_GUI_TYPES.entry,
    setting_.SETTING_GUI_TYPES.file_extension_entry,
  ]

  def __init__(self, name, adjust_value=False, **kwargs):
    """Additional parameters:

    adjust_value:
      if ``True``, process the new value when `set_value()` is
      called. This involves removing leading '.' characters.
    """
    super().__init__(name, validators_.FileExtensionValidator, **kwargs)

    if adjust_value:
      self._assign_value = self._adjust_value

  def _adjust_value(self, value):
    self._value = value.lstrip('.')


class NamePatternSetting(setting_.StringSetting):

  _ALLOWED_GUI_TYPES = [
    setting_.SETTING_GUI_TYPES.name_pattern_entry,
    setting_.SETTING_GUI_TYPES.extended_entry,
    setting_.SETTING_GUI_TYPES.entry,
  ]

  def _assign_value(self, value):
    if not value:
      self._value = self._default_value
    else:
      self._value = value


class DimensionSetting(setting_.NumericSetting):
  """Class for settings representing a dimension (e.g. width of an image).

  In this setting, a dimension is a dictionary consisting of a value, a unit
  (e.g. pixels or a percentage) and additional data required to further specify
  a particular unit (e.g. an object (image, layer, ...) and a dimension (width,
  X-offset, ...) to take a percentage from).

  Default value: A dictionary representing 0 pixels.
  """

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = [setting_.SETTING_GUI_TYPES.dimension_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: {
    'pixel_value': 100.0,
    'percent_value': 100.0,
    'other_value': 1.0,
    'unit': Gimp.Unit.pixel(),
    'percent_object': 'current_image',
    'percent_property': {
      ('current_image',): 'width',
      ('current_layer', 'background_layer', 'foreground_layer'): 'width',
    },
  }

  _PERCENT_PROPERTY_PLACEHOLDER_SEPARATOR = ','

  def __init__(self, name, percent_placeholder_names: Iterable[str], **kwargs):
    """Additional parameters:

    percent_placeholder_names:
      List of strings representing placeholders available for the percentage
      unit.
    """
    self._percent_placeholder_names = percent_placeholder_names
    self._built_in_units = setting_.UnitSetting.get_built_in_units()

    self._placeholder_attribute_map = utils.semi_deep_copy(placeholders_.PLACEHOLDER_ATTRIBUTE_MAP)

    super().__init__(name, **kwargs)

  @property
  def percent_placeholder_names(self):
    return self._percent_placeholder_names

  @property
  def placeholder_attribute_map(self):
    return self._placeholder_attribute_map

  def _copy_value(self, value):
    if isinstance(value, Iterable) and not isinstance(value, str):
      return utils.semi_deep_copy(value)
    else:
      return value

  def _validate(self, value):
    if 'pixel_value' in value:
      result_pixel_value = super()._validate(value['pixel_value'])
      if result_pixel_value is not None:
        return result_pixel_value

    if 'percent_value' in value:
      result_percent_value = super()._validate(value['percent_value'])
      if result_percent_value is not None:
        return result_percent_value

    if 'other_value' in value:
      result_other_value = super()._validate(value['other_value'])
      if result_other_value is not None:
        return result_other_value

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, dict):
      return raw_value

    if 'unit' in raw_value:
      raw_value['unit'] = setting_.UnitSetting.raw_data_to_unit(raw_value['unit'])
    else:
      raw_value['unit'] = self._default_value['unit']

    if 'percent_property' in raw_value:
      new_percent_property_dict = {}

      for key, value in raw_value['percent_property'].items():
        if isinstance(key, str):
          new_percent_property_dict[
            tuple(key.split(self._PERCENT_PROPERTY_PLACEHOLDER_SEPARATOR))] = value
        else:
          new_percent_property_dict[key] = value

      raw_value['percent_property'] = new_percent_property_dict

    return raw_value

  def _value_to_raw(self, value):
    processed_value = utils.semi_deep_copy(value)
    if 'unit' in processed_value:
      processed_value['unit'] = setting_.UnitSetting.unit_to_raw_data(
        processed_value['unit'], self._built_in_units)

    if 'percent_property' in processed_value:
      new_percent_property_dict = {}
      for key, value in processed_value['percent_property'].items():
        if isinstance(key, str):
          new_percent_property_dict[key] = value
        else:
          new_percent_property_dict[
            self._PERCENT_PROPERTY_PLACEHOLDER_SEPARATOR.join(key)] = value

      processed_value['percent_property'] = new_percent_property_dict

    return processed_value


class AngleSetting(setting_.DictSetting):
  """Class for settings representing an angle.

  In this setting, a dimension is a dictionary consisting of a value and a unit
  (degrees or radians).

  Default value: A dictionary representing 0 degrees.
  """

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = [setting_.SETTING_GUI_TYPES.angle_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: {
    'value': 0.0,
    'unit': 'degree',
  }

  def _copy_value(self, value):
    if isinstance(value, Iterable) and not isinstance(value, str):
      return utils.semi_deep_copy(value)
    else:
      return value


class AnchorSetting(setting_.ChoiceSetting):
  """Class for settings representing an anchor point.

  Default value: ''
  """

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = [setting_.SETTING_GUI_TYPES.anchor_box]

  _DEFAULT_DEFAULT_VALUE = ''


class CoordinatesSetting(setting_.DictSetting):
  """Class for settings representing values along the X- and Y-axis (e.g.
  position or resolution).

  The values are stored in a dictionary.

  Default value: A dictionary containing default values along the X- and Y-axis.
  """

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = [setting_.SETTING_GUI_TYPES.coordinates_box]

  _DEFAULT_DEFAULT_VALUE = lambda self: {
    'x': 0.0,
    'y': 0.0,
  }

  def __init__(
        self,
        name,
        min_x: float = -GLib.MAXDOUBLE,
        min_y: float = -GLib.MAXDOUBLE,
        max_x: float = GLib.MAXDOUBLE,
        max_y: float = GLib.MAXDOUBLE,
        **kwargs,
  ):
    super().__init__(name, **kwargs)

    self._min_x = min_x
    self._min_y = min_y
    self._max_x = max_x
    self._max_y = max_y

  @property
  def min_x(self) -> float:
    """The minimum value along the X-axis."""
    return self._min_x

  @property
  def min_y(self) -> float:
    """The minimum value along the Y-axis."""
    return self._min_y

  @property
  def max_x(self) -> float:
    """The maximum value along the X-axis."""
    return self._max_x

  @property
  def max_y(self) -> float:
    """The maximum value along the Y-axis."""
    return self._max_y

  def _copy_value(self, value):
    if isinstance(value, Iterable) and not isinstance(value, str):
      return utils.semi_deep_copy(value)
    else:
      return value


class ItemTreeItemsSetting(setting_.Setting):
  """Abstract class for settings representing `itemtree.Item` instances,
  specifically a list of values of the `itemtree.Item.key` property.

  The persistent format of settings of this class depends on the subclass of
  `ItemTreeItemsSetting`. For more information, see the documentation for the
  subclasses.

  Default value: `[]`
  """

  _ABSTRACT = True

  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = []

  _DEFAULT_DEFAULT_VALUE = lambda self: []

  def __init__(self, name, **kwargs):
    super().__init__(name, **kwargs)

    self._initial_active_items = {}
    self._active_items = {}
    self._inactive_items = []

    self.connect_event('before-reset', self._on_before_reset)

  @property
  def active_items(self) -> Dict:
    """Subset of items whose corresponding `Gimp.Image`s are loaded.

    It is an ordered mapping of ``item key: image``. ``image`` is an existing
    `Gimp.Image` instance for the `GimpItemTreeItemsSetting` subclass,
    or ``None`` for all other subclasses of `ItemTreeItemsSetting`. In the
    latter case, `active_items` contains all items as the `value` property in
    the same order.
    """
    return self._active_items

  @property
  def inactive_items(self) -> List:
    """Subset of items that are not loaded.

    Items not loaded represent items whose corresponding `Gimp.Image`s are not
    loaded, but exist in the file system.

    These items are not a part of the `active_items` property, but are included
    in the `value` property and are stored persistently when the setting is
    saved.
    """
    return self._inactive_items

  def set_active_items(self, item_keys: Iterable):
    """Sets a new subset of items in the `active_subset` property and adds new
    items to the `value` property.

    The ``'value-changed'`` event is invoked once all items are set.
    """
    self._active_items = {}

    self._do_set_active_items(item_keys)

    self.invoke_event('value-changed')

  @abc.abstractmethod
  def _do_set_active_items(self, item_keys: Iterable):
    pass

  def _raw_to_value(self, raw_value):
    if not isinstance(raw_value, (list, tuple)):
      return raw_value

    self._initial_active_items = {}
    self._active_items = {}
    self._inactive_items = []

    value = self._fill_value_active_inactive_items(raw_value)

    self._initial_active_items = dict(self._active_items)

    return value

  @abc.abstractmethod
  def _fill_value_active_inactive_items(self, raw_value):
    pass

  def _value_to_raw(self, value):
    raw_value = []

    for item_key in self._active_items:
      item_as_raw = self._active_item_to_raw(item_key)
      if item_as_raw is not None:
        raw_value.append(item_as_raw)

    for item_data in self._inactive_items:
      raw_value.append(utils.semi_deep_copy(item_data))

    return raw_value

  @abc.abstractmethod
  def _active_item_to_raw(self, item_key):
    pass

  def _validate(self, value):
    if not isinstance(value, (list, tuple)):
      return 'value must be a list or a tuple', 'value_must_be_list_or_tuple'

  def _on_before_reset(self, _setting):
    self._initial_active_items = {}
    self._active_items = {}
    self._inactive_items = []


class GimpItemTreeItemsSetting(ItemTreeItemsSetting):
  """Class for settings representing `itemtree.GimpItem` instances.

  The persistent format for each item for settings of this subclass is the
  following:
  ``[class name, item path components, folder key, image file path]``.

  The ``class name`` corresponds to one of the GIMP item classes,
  e.g. ``'Layer'`` or ``'Channel'``. ``item path components`` is a list of
  path components from the topmost parent to the item itself. ``folder key``
  is either ``''`` or `itemtree.FOLDER_KEY`, signifying that an item is
  either a regular item or a folder, respectively. ``image file path`` is a
  file path to the image containing the corresponding item.
  """

  def _do_set_active_items(self, item_keys: Iterable):
    for item_key in item_keys:
      if isinstance(item_key, int):
        item_id = item_key
        processed_item_key = item_key
      else:
        item_id = item_key[0]
        processed_item_key = tuple(item_key)

      if processed_item_key in self._initial_active_items:
        self._active_items[processed_item_key] = self._initial_active_items[processed_item_key]
      else:
        if Gimp.Item.id_is_valid(item_id):
          self._value.append(processed_item_key)

          image = Gimp.Item.get_by_id(item_id).get_image()
          self._active_items[processed_item_key] = image
          self._initial_active_items[processed_item_key] = image

  def _fill_value_active_inactive_items(self, raw_value):
    value = []

    opened_images = {
      image.get_file().get_path(): image
      for image in Gimp.get_images()
      if image.get_file() is not None and image.get_file().get_path() is not None}

    for item_data in raw_value:
      if isinstance(item_data, int):
        if Gimp.Item.id_is_valid(item_data):
          value.append(item_data)

          image = Gimp.Item.get_by_id(item_data).get_image()
          self._active_items[item_data] = image
      elif isinstance(item_data, (list, tuple)):
        if len(item_data) == 2:  # (item ID, folder key)
          if isinstance(item_data[0], int) and isinstance(item_data[1], str):
            item_id, folder_key = item_data
            if Gimp.Item.id_is_valid(item_id):
              value.append((item_id, folder_key))

              image = Gimp.Item.get_by_id(item_id).get_image()
              self._active_items[(item_id, folder_key)] = image
          else:
            raise TypeError('items with two elements must be (item ID, folder key)')
        elif len(item_data) == 4:  # (item class name, item path, folder key, image path)
          if item_data[3] in opened_images:
            image = opened_images[item_data[3]]

            item_object = utils_pdb.get_item_from_image_and_item_path(
              item_data[0], item_data[1], image)
            if item_object is not None:
              if item_data[2] == itemtree.FOLDER_KEY:
                item_key = (item_object.get_id(), itemtree.FOLDER_KEY)
              else:
                item_key = item_object.get_id()

              value.append(item_key)

              self._active_items[item_key] = image
          else:
            if os.path.isfile(item_data[3]):
              value.append(item_data)
              self._inactive_items.append(item_data)
        else:
          raise ValueError(f'unsupported format for GIMP items: {item_data}')
      else:
        raise TypeError(f'unsupported type for GIMP items: {item_data}')

    return value

  def _active_item_to_raw(self, item_key):
    if isinstance(item_key, int):  # item ID
      item_id = item_key
      folder_key = ''
    else:  # (item ID, folder key)
      item_id = item_key[0]
      folder_key = itemtree.FOLDER_KEY

    if not Gimp.Item.id_is_valid(item_id):
      return None

    item_as_path = utils_pdb.get_item_as_path(Gimp.Item.get_by_id(item_id))
    if item_as_path is not None:
      item_class_name, item_path_components, image_filepath = item_as_path
      return [item_class_name, item_path_components, folder_key, image_filepath]

    return None


class GimpImageTreeItemsSetting(ItemTreeItemsSetting):
  """Class for settings representing `itemtree.GimpImageItem` instances.

  The persistent format for each item for settings of this subclass is simply
  ``image file path``, representing a file path to the image.
  """

  def _do_set_active_items(self, item_keys: Iterable[int]):
    for item_id in item_keys:
      if item_id in self._initial_active_items:
        self._active_items[item_id] = self._initial_active_items[item_id]
      else:
        if Gimp.Image.id_is_valid(item_id):
          self._value.append(item_id)
          self._active_items[item_id] = None
          self._initial_active_items[item_id] = None

  def _fill_value_active_inactive_items(self, raw_value):
    value = []

    opened_images = {
      image.get_file().get_path(): image
      for image in Gimp.get_images()
      if image.get_file() is not None and image.get_file().get_path() is not None}

    for item_data in raw_value:
      if isinstance(item_data, int):
        if Gimp.Image.id_is_valid(item_data):
          value.append(item_data)
          self._active_items[item_data] = None
      elif isinstance(item_data, str):
        if item_data in opened_images:
          image = opened_images[item_data]
          image_id = image.get_id()

          value.append(image_id)
          self._active_items[image_id] = None
        else:
          if os.path.isfile(item_data):
            value.append(item_data)
            self._inactive_items.append(item_data)
      else:
        raise TypeError(f'unsupported type for GIMP images: {item_data}')

    return value

  def _active_item_to_raw(self, item_key):
    if not Gimp.Image.id_is_valid(item_key):
      return None

    image = Gimp.Image.get_by_id(item_key)
    if image is None or not image.is_valid():
      return None

    image_file = image.get_file()
    if image_file is None:
      return None

    image_filepath = image_file.get_path()
    if image_filepath is None:
      return None

    return image_filepath


class ImageFileTreeItemsSetting(ItemTreeItemsSetting):
  """Class for settings representing `itemtree.ImageFileItem` instances.

  The persistent format for each item for settings of this subclass is
  ``[file path, folder key]``. ``folder key`` is either ``''`` or
  `itemtree.FOLDER_KEY`, signifying that an item is either a regular file or
  a folder, respectively.

  The `inactive_items` property is always empty for this subclass.
  """

  def _do_set_active_items(self, item_keys: Iterable):
    for item_key in item_keys:
      if isinstance(item_key, str):
        processed_item_key = item_key
      else:
        processed_item_key = tuple(item_key)

      if processed_item_key in self._initial_active_items:
        self._active_items[processed_item_key] = self._initial_active_items[processed_item_key]
      else:
        self._value.append(processed_item_key)
        self._active_items[processed_item_key] = None
        self._initial_active_items[processed_item_key] = None

  def _fill_value_active_inactive_items(self, raw_value):
    value = []

    for item_data in raw_value:
      value.append(item_data)
      self._active_items[item_data] = None

    return value

  def _active_item_to_raw(self, item_key):
    return item_key


class ImagesAndDirectoriesSetting(setting_.Setting):
  """Class for settings the list of currently opened images and their import
  directory paths.
  
  The setting value is a dictionary of ``(Gimp.Image, import directory path)``
  pairs. The import directory path is ``None`` if the image does not have any.
  
  Default value: `collections.defaultdict(lambda: None)`
  """
  
  _DEFAULT_DEFAULT_VALUE = lambda self: collections.defaultdict(utils.return_none_func)
  
  @property
  def value(self):
    """The setting value.

    A copy is returned to prevent modifying the dictionary indirectly by
    assigning  to individual items.
    """
    return dict(self._value)
  
  def update_images_and_dirpaths(self):
    """Removes all (image, import directory path) pairs for images no longer
    opened in GIMP. Adds (image, import directory path) pairs for new images
    opened in GIMP.
    """
    current_images = Gimp.get_images()
    self._filter_images_no_longer_opened(current_images)
    self._add_new_opened_images(current_images)
  
  def update_dirpath(self, image, directory: Union[str, Gio.File]):
    """Assigns a new directory path to the specified image."""
    if isinstance(directory, Gio.File):
      self._value[image] = directory.get_path()
    else:
      self._value[image] = directory

  def _filter_images_no_longer_opened(self, current_images):
    self._value = {image: self._value[image] for image in self._value if image in current_images}
  
  def _add_new_opened_images(self, current_images):
    for image in current_images:
      if image not in self._value:
        self._value[image] = self._get_image_import_dirpath(image)
  
  @staticmethod
  def _get_image_import_dirpath(image):
    if image.get_file() is not None and image.get_file().get_path() is not None:
      return os.path.dirname(image.get_file().get_path())
    else:
      return None

  def _raw_to_value(self, raw_value):
    value = raw_value

    if isinstance(value, dict):
      value = collections.defaultdict(utils.return_none_func)

      for image_key, dirpath in raw_value.items():
        if isinstance(image_key, int):
          image = Gimp.Image.get_by_id(image_key)
        elif isinstance(image_key, str):
          image = utils_pdb.find_image_by_filepath(image_key)
        else:
          image = image_key

        if image is not None and image.is_valid():
          value[image] = dirpath

    return value

  def _value_to_raw(self, value):
    raw_value = {}

    for image, dirpath in value.items():
      if (image is None
          or not image.is_valid()
          or image.get_file() is None or image.get_file().get_path() is None):
        continue

      raw_value[image.get_file().get_path()] = dirpath

    return raw_value

  def _validate(self, value):
    if not isinstance(value, dict):
      return 'value must be a dictionary', 'value_must_be_dict'


class FileFormatOptionsSetting(setting_.DictSetting):
  """Class for settings storing file format-specific options.

  The options are stored in a dictionary as pairs of (file extension,
  settings representing options).

  The `ACTIVE_FILE_FORMAT_KEY` key, if exists, indicates the currently active
  file format (the format whose options are displayed when running the
  plug-in interactively).
  """

  # HACK: Use a leading '_' to avoid clashing with file extensions.
  ACTIVE_FILE_FORMAT_KEY = '_active'

  _ALLOWED_GUI_TYPES = [setting_.SETTING_GUI_TYPES.file_format_options]

  _DEFAULT_DEFAULT_VALUE = lambda self: {}

  def __init__(
        self,
        name: str,
        import_or_export: str,
        **kwargs,
  ):
    self._import_or_export = import_or_export
    self._connected_events = []

    super().__init__(name, **kwargs)

  @property
  def import_or_export(self):
    return self._import_or_export

  def connect_event(
        self,
        event_type: str,
        event_handler: Callable,
        *event_handler_args,
        **event_handler_kwargs,
  ):
    if event_type == 'value-changed':
      for key, group_or_active_file_format in self._value.items():
        if key == self.ACTIVE_FILE_FORMAT_KEY:
          continue

        for setting in group_or_active_file_format:
          setting.connect_event(
            event_type, event_handler, *event_handler_args, **event_handler_kwargs)

      self._connected_events.append(
        (event_type, event_handler, event_handler_args, event_handler_kwargs))

    return super().connect_event(
      event_type, event_handler, *event_handler_args, **event_handler_kwargs)

  def set_active_file_formats(self, file_formats: List[str]):
    processed_file_formats = [
      file_formats_.FILE_FORMAT_ALIASES.get(file_format, file_format)
      for file_format in file_formats
    ]

    self._value[self.ACTIVE_FILE_FORMAT_KEY] = processed_file_formats

    for file_format in self._value[self.ACTIVE_FILE_FORMAT_KEY]:
      file_formats_.fill_file_format_options(self._value, file_format, self._import_or_export)
      self._connect_events_for_new_file_format_options(self._value, file_format)

    if hasattr(self.gui, 'set_active_file_formats'):
      self.gui.set_active_file_formats(processed_file_formats)

  def _raw_to_value(self, raw_value):
    value = {}

    for key, group_or_active_file_format in raw_value.items():
      if key == self.ACTIVE_FILE_FORMAT_KEY:
        value[key] = group_or_active_file_format
      else:
        processed_file_format = file_formats_.FILE_FORMAT_ALIASES.get(key, key)
        if file_formats_.file_format_procedure_exists(processed_file_format, self.import_or_export):
          if isinstance(group_or_active_file_format, setting_.Group):
            # We need to create new settings to avoid the same setting to be
            # a part of multiple instances of `FileFormatOptionsSetting`.
            value[key] = file_formats_.create_file_format_options_settings(
              self._file_format_options_to_dict(group_or_active_file_format))
          else:
            value[key] = file_formats_.create_file_format_options_settings(
              group_or_active_file_format)

          self._connect_events_for_new_file_format_options(value, processed_file_format)

    return value

  def _value_to_raw(self, value):
    raw_value = {}

    for key, group_or_active_file_format in value.items():
      if key == self.ACTIVE_FILE_FORMAT_KEY:
        raw_value[key] = group_or_active_file_format
      else:
        raw_value[key] = self._file_format_options_to_dict(group_or_active_file_format)

    return raw_value

  def _assign_value(self, value):
    if self.ACTIVE_FILE_FORMAT_KEY in self._value:
      orig_active_file_format = self._value[self.ACTIVE_FILE_FORMAT_KEY]
    else:
      orig_active_file_format = None

    super()._assign_value(value)

    if (orig_active_file_format is not None
        and self.ACTIVE_FILE_FORMAT_KEY in value
        and value[self.ACTIVE_FILE_FORMAT_KEY] != orig_active_file_format):
      self.set_active_file_formats(value[self.ACTIVE_FILE_FORMAT_KEY])

  def _connect_events_for_new_file_format_options(self, value, file_format):
    processed_file_format = file_formats_.FILE_FORMAT_ALIASES.get(file_format, file_format)

    if processed_file_format is None or processed_file_format not in value:
      return

    for setting in value[processed_file_format]:
      for event_type, event_handler, args, kwargs in self._connected_events:
        if not setting.has_event(
          event_type=event_type,
          event_handler=event_handler,
          event_handler_args=args,
          event_handler_kwargs=kwargs,
        ):
          setting.connect_event(event_type, event_handler, *args, **kwargs)

  @staticmethod
  def _file_format_options_to_dict(file_format_options):
    return [setting.to_dict() for setting in file_format_options]


class TaggedItemsSetting(setting_.ListSetting):
  """Class for settings storing a list of items with color tags.

  This class disallows saving setting values by always returning an empty list.
  """

  def _value_to_raw(self, value):
    return []
