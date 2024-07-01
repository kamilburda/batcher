import os

import gi

from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import renamer as renamer_

from src.gui.entry import entries as entries_


class ExportSettings:

  _ROW_SPACING = 5
  _COLUMN_SPACING = 10

  _HBOX_EXPORT_NAME_ENTRIES_SPACING = 3

  _FILE_EXTENSION_ENTRY_MIN_WIDTH_CHARS = 4
  _FILE_EXTENSION_ENTRY_MAX_WIDTH_CHARS = 10
  _FILENAME_PATTERN_ENTRY_MIN_WIDTH_CHARS = 12
  _FILENAME_PATTERN_ENTRY_MAX_WIDTH_CHARS = 40

  _DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS = 100

  def __init__(
        self,
        settings,
        image,
        row_spacing=_ROW_SPACING,
        column_spacing=_COLUMN_SPACING,
        name_preview=None,
        display_message_func=None,
  ):
    self._settings = settings
    self._image = image
    self._row_spacing = row_spacing
    self._column_spacing = column_spacing
    self._name_preview = name_preview
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._message_setting = None

    self._init_gui()

    self._init_setting_gui()

    _set_up_output_directory_settings(self._settings, self._image)

  def _init_gui(self):
    self._folder_chooser_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._folder_chooser_label.set_markup(
      '<b>{}</b>'.format(_('Save in folder:')))

    self._folder_chooser = Gtk.FileChooserButton(
      action=Gtk.FileChooserAction.SELECT_FOLDER,
    )

    self._file_extension_entry = entries_.FileExtensionEntry(
      minimum_width_chars=self._FILE_EXTENSION_ENTRY_MIN_WIDTH_CHARS,
      maximum_width_chars=self._FILE_EXTENSION_ENTRY_MAX_WIDTH_CHARS,
      activates_default=True,
    )

    self._export_filename_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._export_filename_label.set_markup(
      '<b>{}:</b>'.format(GLib.markup_escape_text(_('Save as'))))

    self._dot_label = Gtk.Label(
      label='.',
      xalign=0.0,
      yalign=1.0,
    )

    self._filename_pattern_entry = entries_.FilenamePatternEntry(
      renamer_.get_field_descriptions(renamer_.FIELDS),
      minimum_width_chars=self._FILENAME_PATTERN_ENTRY_MIN_WIDTH_CHARS,
      maximum_width_chars=self._FILENAME_PATTERN_ENTRY_MAX_WIDTH_CHARS,
      default_item=self._settings['main/filename_pattern'].default_value)
    self._filename_pattern_entry.set_activates_default(True)

    self._hbox_export_filename_entries = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_EXPORT_NAME_ENTRIES_SPACING,
    )
    self._hbox_export_filename_entries.pack_start(self._filename_pattern_entry, False, False, 0)
    self._hbox_export_filename_entries.pack_start(self._dot_label, False, False, 0)
    self._hbox_export_filename_entries.pack_start(self._file_extension_entry, False, False, 0)

    self._grid_export_settings = Gtk.Grid(
      row_spacing=self._row_spacing,
      column_spacing=self._column_spacing,
    )
    self._grid_export_settings.attach(self._folder_chooser_label, 0, 0, 1, 1)
    self._grid_export_settings.attach(self._folder_chooser, 1, 0, 1, 1)
    self._grid_export_settings.attach(self._export_filename_label, 0, 1, 1, 1)
    self._grid_export_settings.attach(self._hbox_export_filename_entries, 1, 1, 1, 1)

    self._file_extension_entry.connect(
      'focus-out-event',
      self._on_file_extension_entry_focus_out_event,
      self._settings['main/file_extension'])

    if self._name_preview is not None:
      self._file_extension_entry.connect(
        'changed',
        self._on_text_entry_changed,
        self._settings['main/file_extension'],
        'invalid_file_extension')

    if self._name_preview is not None:
      self._filename_pattern_entry.connect(
        'changed',
        self._on_text_entry_changed,
        self._settings['main/filename_pattern'],
        'invalid_filename_pattern')

  def _init_setting_gui(self):
    self._settings['main/output_directory'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.folder_chooser_button,
      widget=self._folder_chooser,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['main/file_extension'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._file_extension_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['main/filename_pattern'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._filename_pattern_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  @property
  def widget(self):
    return self._grid_export_settings

  @property
  def file_extension_entry(self):
    return self._file_extension_entry

  @property
  def filename_pattern_entry(self):
    return self._filename_pattern_entry

  @staticmethod
  def _on_file_extension_entry_focus_out_event(_entry, _event, setting):
    setting.apply_to_gui()

  def _on_text_entry_changed(self, _entry, setting, name_preview_lock_update_key=None):
    validation_result = setting.validate(setting.gui.get_value())

    if validation_result is None:
      setting.gui.update_setting_value()

      self._name_preview.lock_update(False, name_preview_lock_update_key)

      if self._message_setting == setting:
        self._display_message_func(None)

      self._name_preview.add_function_at_update(
        self._name_preview.set_sensitive, True)

      pg.invocation.timeout_add_strict(
        self._DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS,
        self._name_preview.update)
    else:
      pg.invocation.timeout_add_strict(
        self._DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS,
        self._name_preview.set_sensitive, False)

      self._display_message_func(validation_result.message, Gtk.MessageType.ERROR)

      self._message_setting = setting

      self._name_preview.lock_update(True, name_preview_lock_update_key)


def _set_up_output_directory_settings(settings, current_image):
  _set_up_images_and_directories_and_initial_output_directory(
    settings, settings['main/output_directory'], current_image)
  _set_up_output_directory_changed(settings, current_image)


def _set_up_images_and_directories_and_initial_output_directory(
      settings, output_directory_setting, current_image):
  """Sets up the initial directory path for the current image.

  The path is set according to the following priority list:

    1. Last export directory path of the current image
    2. Import directory path of the current image
    3. Last export directory path of any image (i.e. the current value of
       ``'main/output_directory'``)
    4. The default directory path (default value) for
       ``'main/output_directory'``

  Notes:

    Directory 3. is set upon loading ``'main/output_directory'``.
    Directory 4. is set upon the instantiation of ``'main/output_directory'``.
  """
  settings['gui/images_and_directories'].update_images_and_dirpaths()

  _update_directory(
    output_directory_setting,
    current_image,
    settings['gui/images_and_directories'].value[current_image])


def _update_directory(setting, current_image, current_image_dirpath):
  """Sets the directory path to the ``setting``.

  The path is set according to the following priority list:

  1. ``current_image_dirpath`` if not ``None``
  2. ``current_image`` - import path of the current image if not ``None``

  If update was performed, ``True`` is returned, ``False`` otherwise.
  """
  if current_image_dirpath is not None:
    setting.set_value(current_image_dirpath)
    return True

  if current_image.get_file() is not None and current_image.get_file().get_path() is not None:
    setting.set_value(os.path.dirname(current_image.get_file().get_path()))
    return True

  return False


def _set_up_output_directory_changed(settings, current_image):
  def on_output_directory_changed(output_directory, images_and_directories, current_image_):
    images_and_directories.update_dirpath(current_image_, output_directory.value)

  settings['main/output_directory'].connect_event(
    'value-changed',
    on_output_directory_changed,
    settings['gui/images_and_directories'],
    current_image)
