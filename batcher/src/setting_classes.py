"""Additional setting and setting GUI classes specific to the plug-in."""

import collections
from collections.abc import Iterable
import os
from typing import Type

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg

from src import file_formats as file_formats_
from src import renamer as renamer_
from src.gui import file_format_options_box as file_format_options_box_
from src.gui.entry import entries as entries_
from src.path import validators as validators_


class ValidatableStringSetting(pg.setting.StringSetting):
  """Abstract class for string settings which are meant to be validated with one
  of the `path.validators.StringValidator` subclasses.

  To determine whether the string is valid, `is_valid()` from the corresponding
  subclass is called.

  Message IDs for invalid values:
    Message IDs defined in `path.validators.FileValidatorErrorStatuses`.
  """

  _ABSTRACT = True

  def __init__(
        self,
        name: str,
        string_validator_class: Type[validators_.StringValidator],
        **kwargs,
  ):
    """Initializes a `ValidatableStringSetting` instance.

    Args:
      string_validator_class:
        `path.validators.StringValidator` subclass used to validate the value
        assigned to this object.
    """
    self._string_validator = string_validator_class

    super().__init__(name, **kwargs)

  def _validate(self, string_):
    is_valid, status_messages = self._string_validator.is_valid(string_)

    if not is_valid:
      for status, status_message in status_messages:
        return status_message, status


class FolderChooserButtonPresenter(pg.setting.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.FileChooserButton` widgets used as
  folder choosers.

  Value: Current folder.
  """

  _VALUE_CHANGED_SIGNAL = 'file-set'

  def _create_widget(self, setting, width_chars=30, **kwargs):
    button = Gtk.FileChooserButton(
      title=setting.display_name,
      action=Gtk.FileChooserAction.SELECT_FOLDER,
    )

    if setting.value is not None:
      button.set_filename(setting.value)

    self._set_width_chars(button, width_chars)

    return button

  def get_value(self):
    folder = self._widget.get_filename()

    if folder is not None:
      return folder
    else:
      return pg.utils.get_pictures_directory()

  def _set_value(self, dirpath):
    self._widget.set_filename(dirpath if dirpath is not None else '')

  @staticmethod
  def _set_width_chars(button, width_chars):
    combo_box = next(iter(child for child in button if isinstance(child, Gtk.ComboBox)), None)

    if combo_box is not None:
      cell_renderer = next(
        iter(cr for cr in combo_box.get_cells() if isinstance(cr, Gtk.CellRendererText)), None)

      if cell_renderer is not None:
        # This should force each row to not take extra vertical space after
        # reducing the number of characters to render.
        cell_renderer.set_property(
          'height', cell_renderer.get_preferred_height(combo_box).natural_size)

        cell_renderer.set_property('max-width-chars', width_chars)
        cell_renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        cell_renderer.set_property('wrap-width', -1)


class DirpathSetting(ValidatableStringSetting):
  """Class for settings storing directory paths as strings.

  The `path.validatorsDirpathValidator` subclass is used to determine whether
  the directory path is valid.

  If ``None`` or an empty string is assigned to this seting, the default value
  (see below) is assigned instead.

  Default value: `Pictures` directory in the user's home directory.
  """

  _ALLOWED_GUI_TYPES = [FolderChooserButtonPresenter]

  _DEFAULT_DEFAULT_VALUE = pg.utils.get_pictures_directory()

  def __init__(self, name, **kwargs):
    super().__init__(name, validators_.DirpathValidator, **kwargs)

  def _raw_to_value(self, raw_value):
    if raw_value:
      return raw_value
    else:
      return self._DEFAULT_DEFAULT_VALUE


class ExtendedEntryPresenter(pg.setting.GtkPresenter):
  """`setting.Presenter` subclass for `gui.ExtendedEntry` widgets.

  Value: Text in the entry.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def get_value(self):
    text = self._widget.get_text()
    return text if text is not None else ''

  def _set_value(self, value):
    self._widget.assign_text(value if value is not None else '', enable_undo=True)


class FileExtensionEntryPresenter(ExtendedEntryPresenter):
  """`setting.Presenter` subclass for `gui.entries.FileExtensionEntry` widgets.

  Value: Text in the entry.
  """

  def _create_widget(self, setting, **kwargs):
    return entries_.FileExtensionEntry()


class FileExtensionSetting(ValidatableStringSetting):
  """Class for settings storing file extensions as strings.

  The `path.validatorsFileExtensionValidator` subclass is used to determine
  whether the file extension is valid.
  """

  _ALLOWED_GUI_TYPES = [
    pg.SETTING_GUI_TYPES.entry,
    FileExtensionEntryPresenter,
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


class NamePatternEntryPresenter(ExtendedEntryPresenter):
  """`pygimplib.setting.Presenter` subclass for
  `gui.entries.NamePatternEntry` widgets.

  Value: Text in the entry.
  """

  def _create_widget(self, setting, **kwargs):
    return entries_.NamePatternEntry(renamer_.get_field_descriptions(renamer_.FIELDS))


class NamePatternSetting(pg.setting.StringSetting):

  _ALLOWED_GUI_TYPES = [
    NamePatternEntryPresenter,
    pg.SETTING_GUI_TYPES.extended_entry,
    pg.SETTING_GUI_TYPES.entry,
  ]

  def _assign_value(self, value):
    if not value:
      self._value = self._default_value
    else:
      self._value = value


class ImagesAndGimpItemsSetting(pg.setting.Setting):
  """Class for settings representing a mapping of
  ``(GIMP image, GIMP items)`` pairs.
  
  The mapping is implemented as `collections.defaultdict(set)`.
  
  A GIMP item can be represented as a `Gimp.Item` instance or a ``(Gimp.Item,
  FOLDER_KEY)`` tuple, where ``FOLDER_KEY`` is a string literal defined in
  `pygimplib.itemtree`.
  
  When storing this setting to a source, images are stored as file paths and
  items are stored as ``(item class name, item path)`` or ``(item class name,
  item path, FOLDER_KEY)`` tuples. ``Item class name`` and ``item path`` are
  described in `pygimplib.pdbutils.get_item_from_image_and_item_path()`.
  
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
          if Gimp.Image.id_is_valid(key):
            image = Gimp.Image.get_by_id(key)
          else:
            image = None
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
                if Gimp.Item.id_is_valid(item[0]):
                  processed_items.add((item[0], item[1]))
              else:  # (item, item type)
                if item[0].is_valid():
                  processed_items.add((item[0].get_id(), item[1]))
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
                  processed_items.add(item_object.get_id())
                else:
                  processed_items.add((item_object.get_id(), item_type))
          elif isinstance(item, int):
            if Gimp.Item.id_is_valid(item):
              processed_items.add(item)
          else:
            if item is not None:
              processed_items.add(item.get_id())
        
        value[image] = processed_items
    else:
      value = raw_value
    
    return value
  
  def _value_to_raw(self, value):
    raw_value = {}

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

          item_id = item[0]
          item_type = item[1]
        else:
          item_id = item
          item_type = None

        if not Gimp.Item.id_is_valid(item_id):
          continue

        item_as_path = pg.pdbutils.get_item_as_path(
          Gimp.Item.get_by_id(item_id), include_image=False)

        if item_as_path is not None:
          if item_type is None:
            raw_value[image_filepath].append(item_as_path)
          else:
            raw_value[image_filepath].append(item_as_path + [item_type])

    return raw_value
  
  def _validate(self, value):
    if not isinstance(value, dict):
      return 'value must be a dictionary', 'value_must_be_dict'


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
    current_images = Gimp.get_images()
    self._filter_images_no_longer_opened(current_images)
    self._add_new_opened_images(current_images)
  
  def update_dirpath(self, image, dirpath):
    """Assigns a new directory path to the specified image."""
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


class FileFormatOptionsPresenter(pg.setting.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Grid` widgets representing
  dictionaries of (string, value) pairs.

  Value: Dictionary of (string, value) pairs where the value is obtained from
    each widget.
  """

  def _create_widget(self, setting, **kwargs):
    file_format_options_box = file_format_options_box_.FileFormatOptionsBox(
      initial_header_title=setting.display_name,
      **kwargs,
    )

    return file_format_options_box

  def set_active_file_format(self, file_format):
    self._widget.set_active_file_format(file_format, self.setting.value.get(file_format, None))

  def get_value(self):
    if FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY in self.setting.value:
      active_file_format = self.setting.value[FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY]
      if active_file_format in self.setting.value:
        self.setting.value[active_file_format].apply_gui_values_to_settings()

    return self.setting.value

  def _set_value(self, value):
    active_file_format_key = FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY

    self._widget.set_active_file_format(
      value[active_file_format_key], value.get(value[active_file_format_key], None))


class FileFormatOptionsSetting(pg.setting.DictSetting):
  """Class for settings storing file format-specific options.

  The options are stored in a dictionary as pairs of (file extension,
  settings representing options). The `ACTIVE_FILE_FORMAT_KEY` key,
  if exists, indicates the currently active file format (the format whose
  options are displayed when running the plug-in interactively).
  """

  # Ideally, we would use `None` to represent the active file format to avoid
  # the slightest possibility of a string being used as a file extension.
  # However, JSON only allows strings as keys, so this will have to do.
  ACTIVE_FILE_FORMAT_KEY = '_active'

  _ALLOWED_GUI_TYPES = [FileFormatOptionsPresenter]

  _DEFAULT_DEFAULT_VALUE = lambda self: {self.ACTIVE_FILE_FORMAT_KEY: self._initial_file_format}

  def __init__(self, name: str, import_or_export: str, initial_file_format: str, **kwargs):
    self._import_or_export = import_or_export
    self._initial_file_format = initial_file_format

    super().__init__(name, **kwargs)

  @property
  def import_or_export(self):
    return self._import_or_export

  def set_active_file_format(self, file_format: str):
    processed_file_format = file_formats_.FILE_FORMAT_ALIASES.get(file_format, file_format)

    self._value[self.ACTIVE_FILE_FORMAT_KEY] = processed_file_format

    file_formats_.fill_file_format_options(
      self._value, self._value[self.ACTIVE_FILE_FORMAT_KEY], self._import_or_export)

    if hasattr(self.gui, 'set_active_file_format'):
      self.gui.set_active_file_format(processed_file_format)

  def _raw_to_value(self, raw_value):
    value = {}

    for key, group_or_active_file_format in raw_value.items():
      if key != self.ACTIVE_FILE_FORMAT_KEY:
        if isinstance(group_or_active_file_format, pg.setting.Group):
          # We need to create new settings to avoid the same setting to be
          # a part of multiple instances of `FileFormatOptionsSetting`.
          value[key] = file_formats_.create_file_format_options_settings(
            self._file_format_options_to_dict(group_or_active_file_format))
        else:
          value[key] = file_formats_.create_file_format_options_settings(
            group_or_active_file_format)
      else:
        value[key] = group_or_active_file_format

    return value

  def _value_to_raw(self, value):
    raw_value = {}

    for key, group_or_active_file_format in value.items():
      if key != self.ACTIVE_FILE_FORMAT_KEY:
        raw_value[key] = self._file_format_options_to_dict(group_or_active_file_format)
      else:
        raw_value[key] = group_or_active_file_format

    return raw_value

  def _validate(self, value):
    if self.ACTIVE_FILE_FORMAT_KEY not in value:
      return (
        f'the value must contain {self.ACTIVE_FILE_FORMAT_KEY} as the dictionary key',
        'value_does_not_contain_active_file_format_key',
        False,
      )

  def _assign_value(self, value):
    if self.ACTIVE_FILE_FORMAT_KEY in self._value:
      orig_active_file_format = self._value[self.ACTIVE_FILE_FORMAT_KEY]
    else:
      orig_active_file_format = None

    super()._assign_value(value)

    if (orig_active_file_format is not None
        and self.ACTIVE_FILE_FORMAT_KEY in value
        and value[self.ACTIVE_FILE_FORMAT_KEY] != orig_active_file_format):
      self.set_active_file_format(value[self.ACTIVE_FILE_FORMAT_KEY])

  @staticmethod
  def _file_format_options_to_dict(file_format_options):
    return [setting.to_dict() for setting in file_format_options]


class TaggedItemsSetting(pg.setting.ListSetting):
  """Class for settings storing a list of items with color tags.

  This class disallows saving setting values by always returning an empty list.
  """

  def _value_to_raw(self, value):
    return []
