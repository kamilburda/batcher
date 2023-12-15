"""Custom setting classes specific to the plug-in."""

import collections
from collections.abc import Iterable
import os

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

import pygimplib as pg

from src import renamer as renamer_


class FilenamePatternEntryPresenter(pg.setting.presenters_gtk.ExtendedEntryPresenter):
  """`pygimplib.setting.Presenter` subclass for
  `pygimplib.gui.FilenamePatternEntry` widgets.

  Value: Text in the entry.
  """

  def _create_widget(self, setting, **kwargs):
    return pg.gui.FilenamePatternEntry(renamer_.get_field_descriptions(renamer_.FIELDS))


class FilenamePatternSetting(pg.setting.StringSetting):

  _ALLOWED_GUI_TYPES = [
    FilenamePatternEntryPresenter,
    pg.SETTING_GUI_TYPES.extended_entry,
    pg.SETTING_GUI_TYPES.entry,
  ]

  def _assign_value(self, value):
    if not value:
      self._value = self._default_value
    else:
      self._value = value


class GimpColorTagWithoutNoneComboBoxPresenter(pg.setting.presenters_gtk.EnumComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.EnumComboBox` widgets representing
  GIMP color tags.

  This presenter omits the `Gimp.ColorTag.NONE` option, which can be convenient
  when only an existing color tag must be selected.

  Value: GIMP color tag selected in the enum combo box.
  """

  def _create_widget(self, setting, **kwargs):
    combo_box = GimpUi.EnumComboBox.new_with_model(GimpUi.EnumStore.new(Gimp.ColorTag))

    del combo_box.get_model()[int(Gimp.ColorTag.NONE)]

    # If the default value is not valid, `set_active` returns `False`,
    # but otherwise does not result in errors.
    combo_box.set_active(int(setting.default_value))

    return combo_box


class ColorTagSetting(pg.setting.EnumSetting):
  """Class for settings representing GIMP color tags (`Gimp.ColorTag` enums).

  Allowed GIMP PDB types:
  * `Gimp.ColorTag`

  Default value: `Gimp.ColorTag.BLUE`
  """

  _ALLOWED_GUI_TYPES = [
    GimpColorTagWithoutNoneComboBoxPresenter,
    pg.SETTING_GUI_TYPES.enum_combo_box,
  ]

  _DEFAULT_DEFAULT_VALUE = Gimp.ColorTag.BLUE

  def __init__(self, name, **kwargs):
    # Ignore any `enum_type` in kwargs, which happens when saving and then
    # loading this setting since `enum_type` is always persisted.
    # We cannot pass multiple keyword arguments with the same name as this
    # results in an error.
    kwargs.pop('enum_type', None)

    super().__init__(name, enum_type=Gimp.ColorTag, **kwargs)


class ImagesAndGimpItemsSetting(pg.setting.Setting):
  """Class for settings representing a mapping of
  ``(GIMP image, GIMP items)`` pairs.
  
  The mapping is implemented as `collections.defaultdict(set)`.
  
  A GIMP item can be represented as a `Gimp.Item` instance or a ``(Gimp.Item,
  FOLDER_KEY)`` tuple, where ``FOLDER_KEY`` is a string literal defined in
  `pygimplib.itemtree`.
  
  When storing this setting to a persistent source, images are stored as file
  paths and items are stored as ``(item class name, item path)`` or ``(item
  class name, item path, FOLDER_KEY)`` tuples. ``Item class name`` and ``item
  path`` are described in
  `pygimplib.pdbutils.get_item_from_image_and_item_path()`.
  
  Default value: `collections.defaultdict(set)`
  """
  
  _ALLOWED_PDB_TYPES = []

  _ALLOWED_GUI_TYPES = []

  _DEFAULT_DEFAULT_VALUE = lambda self: collections.defaultdict(set)
  
  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, dict):
      value = collections.defaultdict(set)
      
      for key, items in raw_value.items():
        if isinstance(key, str):
          image = pg.pdbutils.find_image_by_filepath(key)
        elif isinstance(key, int):
          image = Gimp.Image.get_by_id(key)
        else:
          image = key
        
        if image is None:
          continue
        
        if not isinstance(items, Iterable) or isinstance(items, str):
          raise TypeError(f'expected a list-like, found {items}')
        
        processed_items = set()
        
        for item in items:
          if isinstance(item, (list, tuple)):
            if len(item) not in [2, 3]:
              raise ValueError(
                'list-likes representing items must contain exactly 2 or 3 elements'
                f' (has {len(item)})')

            if len(item) == 2 and not isinstance(item[0], str):
              if isinstance(item[0], int):  # (item ID, item type)
                item_object = Gimp.Item.get_by_id(item[0])
                if item_object is not None:
                  processed_items.add((item_object, item[1]))
              else:  # (item, item type)
                if item[0].is_valid():
                  processed_items.add(tuple(item))
            else:
              if len(item) == 3:
                item_type = item[2]
                item_class_name_and_path = item[:2]
              else:
                item_type = None
                item_class_name_and_path = item

              item_object = pg.pdbutils.get_item_from_image_and_item_path(
                image, *item_class_name_and_path)

              if item_object is not None:
                if item_type is None:
                  processed_items.add(item_object)
                else:
                  processed_items.add((item_object, item_type))
          elif isinstance(item, int):
            item_object = Gimp.Item.get_by_id(item)
            if item_object is not None:
              processed_items.add(item_object)
          else:
            if item is not None:
              processed_items.add(item)
        
        value[image] = processed_items
    else:
      value = raw_value
    
    return value
  
  def _value_to_raw(self, value, source_type):
    raw_value = {}
    
    if source_type == 'session':
      for image, items in value.items():
        raw_value[image.get_id()] = list(
          [item[0].get_id(), item[1]] if isinstance(item, (list, tuple)) else item.get_id()
          for item in items)
    else:
      for image, items in value.items():
        if (image is None
            or not image.is_valid()
            or image.get_file() is None or image.get_file().get_path() is None):
          continue
        
        image_filepath = image.get_file().get_path()

        raw_value[image_filepath] = []
        
        for item in items:
          if isinstance(item, (list, tuple)):
            if len(item) != 2:
              raise ValueError(
                'list-likes representing items must contain exactly 2 elements'
                f' (has {len(item)})')
            
            item_object = item[0]
            item_type = item[1]
          else:
            item_object = item
            item_type = None
          
          if item_object is None or not item_object.is_valid():
            continue
          
          item_as_path = pg.pdbutils.get_item_as_path(item_object, include_image=False)
          
          if item_as_path is not None:
            if item_type is None:
              raw_value[image_filepath].append(item_as_path)
            else:
              raw_value[image_filepath].append(item_as_path + [item_type])
    
    return raw_value
  
  def _init_error_messages(self):
    self.error_messages['value_must_be_dict'] = _('Value must be a dictionary.')
  
  def _validate(self, value):
    if not isinstance(value, dict):
      raise pg.setting.SettingValueError(
        pg.setting.value_to_str_prefix(value) + self.error_messages['value_must_be_dict'])


class ImagesAndDirectoriesSetting(pg.setting.Setting):
  """Class for settings the list of currently opened images and their import
  directory paths.
  
  The setting value is a dictionary of ``(Gimp.Image, import directory path)``
  pairs. The import directory path is ``None`` if the image does not have any.
  
  Default value: `collections.defaultdict(lambda: None)`
  """
  
  _DEFAULT_DEFAULT_VALUE = lambda self: collections.defaultdict(pg.utils.return_none_func)
  
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
    current_images = Gimp.list_images()
    self._filter_images_no_longer_opened(current_images)
    self._add_new_opened_images(current_images)
  
  def update_dirpath(self, image, dirpath):
    """Assigns a new directory path to the specified image.
    
    If the image does not exist in the setting, `KeyError` is raised.
    """
    self._value[image] = dirpath
  
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
      value = collections.defaultdict(pg.utils.return_none_func)

      for image_key, dirpath in raw_value.items():
        if isinstance(image_key, int):
          image = Gimp.Image.get_by_id(image_key)
        elif isinstance(image_key, str):
          image = pg.pdbutils.find_image_by_filepath(image_key)
        else:
          image = image_key

        if image is not None and image.is_valid():
          value[image] = dirpath

    return value

  def _value_to_raw(self, value, source_type):
    raw_value = {}

    if source_type == 'session':
      for image, dirpath in value.items():
        if image is not None and image.is_valid():
          raw_value[image.get_id()] = dirpath
    else:
      for image, dirpath in value.items():
        if (image is None
            or not image.is_valid()
            or image.get_file() is None or image.get_file().get_path() is None):
          continue

        raw_value[image.get_file().get_path()] = dirpath

    return raw_value

  def _init_error_messages(self):
    self.error_messages['value_must_be_dict'] = _('Value must be a dictionary.')

  def _validate(self, value):
    if not isinstance(value, dict):
      raise pg.setting.SettingValueError(
        pg.setting.value_to_str_prefix(value) + self.error_messages['value_must_be_dict'])
