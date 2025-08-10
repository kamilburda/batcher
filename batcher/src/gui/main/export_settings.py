import os

import gi
from gi.repository import Gio
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config import CONFIG
from src import renamer as renamer_
from src import setting as setting_
from src import utils
from src.gui.entry import entries as entries_

from . import _utils as gui_main_utils_


class ExportSettings:

  _GRID_ROW_SPACING = 7
  _GRID_COLUMN_SPACING = 7
  _EXPORT_OPTIONS_SPACING = 3

  _NAME_PATTERN_ENTRY_MIN_WIDTH_CHARS = 15
  _NAME_PATTERN_ENTRY_MAX_WIDTH_CHARS = 15

  _FILE_EXTENSION_ENTRY_WIDTH_CHARS = 5
  _FILE_EXTENSION_ENTRY_MAX_WIDTH_CHARS = 5

  _DELAY_PREVIEW_UPDATE_MILLISECONDS = 100

  def __init__(
        self,
        settings,
        current_image=None,
        name_preview=None,
        image_preview=None,
        parent=None,
  ):
    self._settings = settings
    self._current_image = current_image
    self._name_preview = name_preview
    self._image_preview = image_preview
    self._parent = parent

    self._init_gui()

    self._init_setting_gui()

    if self._current_image is not None:
      _set_up_output_directory_settings(self._settings, self._current_image)

  def close_export_options_dialog(self):
    if self._export_options_dialog is not None:
      self._export_options_dialog.widget.hide()

  def _init_gui(self):
    self._folder_chooser_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._folder_chooser_label.set_markup(
      '<b>{}</b>'.format(_('Folder:')))

    self._settings['main/output_directory'].set_gui()
    self._settings['main/output_directory'].gui.widget.set_hexpand(True)

    self._label_filename = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._label_filename.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(_('Filename:'))))

    self._name_pattern_entry = entries_.NamePatternEntry(
      renamer_.get_field_descriptions(),
      default_item=self._settings['main/name_pattern'].default_value,
      width_chars=self._NAME_PATTERN_ENTRY_MIN_WIDTH_CHARS,
      max_width_chars=self._NAME_PATTERN_ENTRY_MAX_WIDTH_CHARS,
    )
    self._name_pattern_entry.set_activates_default(True)

    self._file_extension_entry = entries_.FileExtensionEntry(
      width_chars=self._FILE_EXTENSION_ENTRY_WIDTH_CHARS,
      max_width_chars=self._FILE_EXTENSION_ENTRY_MAX_WIDTH_CHARS,
      activates_default=True,
    )

    self._export_options_button = Gtk.Button(
      image=Gtk.Image.new_from_icon_name('applications-system', Gtk.IconSize.BUTTON),
      tooltip_text=_('Export Options'),
    )

    self._hbox_filename = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._EXPORT_OPTIONS_SPACING,
    )
    self._hbox_filename.pack_start(self._name_pattern_entry, True, True, 0)
    self._hbox_filename.pack_start(self._file_extension_entry, False, False, 0)
    self._hbox_filename.pack_start(self._export_options_button, False, False, 0)

    self._grid = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )
    self._grid.attach(self._folder_chooser_label, 0, 0, 1, 1)
    self._grid.attach(self._settings['main/output_directory'].gui.widget, 1, 0, 1, 1)
    self._grid.attach(self._label_filename, 0, 1, 1, 1)
    self._grid.attach(self._hbox_filename, 1, 1, 1, 1)

    self._export_options_dialog = None

  def _init_setting_gui(self):
    self._settings['main/name_pattern'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.extended_entry,
      widget=self._name_pattern_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['main/file_extension'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.extended_entry,
      widget=self._file_extension_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

    self._set_up_name_pattern()
    self._set_up_file_extension()

    self._export_options_button.connect('clicked', self._on_export_options_button_clicked)

    self._connect_setting_events()

  @property
  def widget(self):
    return self._grid

  @property
  def folder_chooser(self):
    return self._settings['main/output_directory'].gui.widget

  @property
  def file_extension_entry(self):
    return self._file_extension_entry

  @property
  def name_pattern_entry(self):
    return self._name_pattern_entry

  def _connect_setting_events(self):
    for setting in self._settings['main/export']:
      setting.connect_event('value-changed', self._update_previews_on_export_options_change)

    self._settings['main/output_directory'].connect_event(
      'value-changed', self._update_previews_on_export_options_change)

  def _set_up_name_pattern(self):
    self._settings['main/name_pattern'].connect_event(
      'value-changed', self._on_name_pattern_changed)

  def _on_name_pattern_changed(self, _setting):
    if self._name_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

  def _set_up_file_extension(self):
    CONFIG.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE.add(
      self._settings['main/file_extension'])

    self._file_extension_entry.connect(
      'changed',
      self._on_file_extension_entry_changed,
      self._settings['main/file_extension'])

    self._file_extension_entry.connect(
      'focus-out-event',
      self._on_file_extension_entry_focus_out_event,
      self._settings['main/file_extension'])

  def _on_file_extension_entry_changed(self, _entry, setting):
    apply_file_extension_gui_to_setting_if_valid(setting)

    if self._name_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

  @staticmethod
  def _on_file_extension_entry_focus_out_event(_entry, _event, setting):
    revert_file_extension_gui_to_last_valid_value(setting)

  def _on_export_options_button_clicked(self, _button):
    if self._export_options_dialog is None:
      self._export_options_dialog = gui_main_utils_.ImportExportOptionsDialog(
        self._settings['main/export'],
        title=_('Export Options'),
        parent=self._parent,
      )

      self._export_options_dialog.widget.show()
    else:
      self._export_options_dialog.widget.show()
      self._export_options_dialog.widget.present()

  def _update_previews_on_export_options_change(self, _setting):
    if self._name_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

    if self._image_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._image_preview.update)


def apply_file_extension_gui_to_setting_if_valid(setting):
  validation_result = setting.validate(setting.gui.get_value())

  if validation_result is None:
    setting.gui.update_setting_value()


def revert_file_extension_gui_to_last_valid_value(setting):
  validation_result_gui_value = setting.validate(setting.gui.get_value())

  if validation_result_gui_value is not None:
    # We presume the last setting value is valid. This might not be the case
    # if the last value itself is not valid, which can happen when saving
    # the setting with an invalid value. In that case, we revert to the
    # setting's default value, which presumably is valid.
    validation_result_setting_value = setting.validate(setting.value)
    if validation_result_setting_value is None:
      setting.apply_to_gui()
    else:
      setting.reset()


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
    setting.set_value(Gio.file_new_for_path(current_image_dirpath))
    return True

  if current_image.get_file() is not None and current_image.get_file().get_path() is not None:
    setting.set_value(Gio.file_new_for_path(os.path.dirname(current_image.get_file().get_path())))
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
