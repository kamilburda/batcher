import os

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import Gio
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import renamer as renamer_

from src.gui import utils as gui_utils_
from src.gui.entry import entries as entries_


class ExportSettings:

  _SPACING_BETWEEN_COMPONENTS = 7
  _SPACING_WITHIN_COMPONENTS = 7
  _HBOX_EXPORT_NAME_ENTRIES_SPACING = 3

  _FILE_EXTENSION_ENTRY_MIN_WIDTH_CHARS = 5
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

  def _init_gui(self):
    self._folder_chooser_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._folder_chooser_label.set_markup(
      '<b>{}</b>'.format(_('Folder:')))

    self._settings['main/output_directory'].set_gui()

    self._hbox_folder_chooser = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._SPACING_WITHIN_COMPONENTS,
    )
    self._hbox_folder_chooser.pack_start(self._folder_chooser_label, False, False, 0)
    self._hbox_folder_chooser.pack_start(
      self._settings['main/output_directory'].gui.widget, True, True, 0)

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
      '<b>{}</b>'.format(GLib.markup_escape_text(_('Name:'))))

    self._dot_label = Gtk.Label(
      label='.',
      xalign=0.0,
      yalign=1.0,
    )

    self._name_pattern_entry = entries_.NamePatternEntry(
      renamer_.get_field_descriptions(),
      expandable=False,
      default_item=self._settings['main/name_pattern'].default_value)
    self._name_pattern_entry.set_activates_default(True)

    self._hbox_export_filename_entries = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_EXPORT_NAME_ENTRIES_SPACING,
    )
    self._hbox_export_filename_entries.pack_start(self._name_pattern_entry, True, True, 0)
    self._hbox_export_filename_entries.pack_start(self._dot_label, False, False, 0)
    self._hbox_export_filename_entries.pack_start(self._file_extension_entry, False, False, 0)

    self._hbox_export_filename_entries_with_label = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._SPACING_WITHIN_COMPONENTS,
    )
    (self._hbox_export_filename_entries_with_label.pack_start
     (self._export_filename_label, False, False, 0))
    self._hbox_export_filename_entries_with_label.pack_start(
      self._hbox_export_filename_entries, True, True, 0)

    self._export_options_button = Gtk.Button(
      label=_('O_ptions...'),
      use_underline=True,
    )

    self._hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._SPACING_BETWEEN_COMPONENTS,
    )
    self._hbox.pack_start(self._hbox_folder_chooser, True, True, 0)
    self._hbox.pack_start(self._hbox_export_filename_entries_with_label, True, True, 0)
    self._hbox.pack_start(self._export_options_button, False, False, 0)

    self._export_options_dialog = None

  def _init_setting_gui(self):
    self._settings['main/name_pattern'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._name_pattern_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['main/file_extension'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._file_extension_entry,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

    self._set_up_name_pattern()
    self._set_up_file_extension()

    self._export_options_button.connect('clicked', self._on_export_options_button_clicked)

    for setting in self._settings['main/export']:
      setting.connect_event('value-changed', self._update_previews_on_export_options_change)
    self._settings['main/output_directory'].connect_event(
      'value-changed', self._update_previews_on_export_options_change)

  @property
  def widget(self):
    return self._hbox

  @property
  def folder_chooser(self):
    return self._settings['main/output_directory'].gui.widget

  @property
  def file_extension_entry(self):
    return self._file_extension_entry

  @property
  def name_pattern_entry(self):
    return self._name_pattern_entry

  def _set_up_name_pattern(self):
    self._settings['main/name_pattern'].connect_event(
      'value-changed', self._on_name_pattern_changed)

  def _on_name_pattern_changed(self, _setting):
    if self._name_preview is not None:
      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

  def _set_up_file_extension(self):
    pg.config.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE.add(
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
      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

  @staticmethod
  def _on_file_extension_entry_focus_out_event(_entry, _event, setting):
    revert_file_extension_gui_to_last_valid_value(setting)

  def _on_export_options_button_clicked(self, _button):
    if self._export_options_dialog is None:
      self._export_options_dialog = ExportOptionsDialog(self._settings, parent=self._parent)

      self._export_options_dialog.widget.show()
    else:
      self._export_options_dialog.widget.show()
      self._export_options_dialog.widget.present()

  def _update_previews_on_export_options_change(self, _setting):
    if self._name_preview is not None:
      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

    if self._image_preview is not None:
      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._image_preview.update)


class ExportOptionsDialog:

  _MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR = 650

  _CONTENTS_BORDER_WIDTH = 6

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  def __init__(self, settings, parent=None):
    self._settings = settings
    self._parent = parent

    self._init_gui()

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=_('Export Options'),
      parent=self._parent,
      resizable=False,
    )

    self._button_reset_response_id = 1
    self._button_reset = self._dialog.add_button(_('_Reset'), self._button_reset_response_id)

    self._button_reset.connect('clicked', self._on_export_options_dialog_button_reset_clicked)

    self._dialog.connect('delete-event', lambda *_args: self._dialog.hide_on_delete())
    self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._grid_export_options = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )
    self._grid_export_options.show()

    self._settings['main/export'].initialize_gui(only_null=True)

    for row_index, setting in enumerate(self._settings['main/export']):
      gui_utils_.attach_label_to_grid(
        self._grid_export_options, setting, row_index, set_name_as_tooltip=False)
      gui_utils_.attach_widget_to_grid(
        self._grid_export_options, setting, row_index, set_name_as_tooltip=False)

    self._scrolled_window_viewport = Gtk.Viewport(shadow_type=Gtk.ShadowType.NONE)
    self._scrolled_window_viewport.add(self._grid_export_options)
    self._scrolled_window_viewport.show()

    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
      max_content_height=self._MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR,
    )
    self._scrolled_window.add(self._scrolled_window_viewport)
    self._scrolled_window.show()

    self._dialog.vbox.pack_start(self._scrolled_window, False, False, 0)
    self._dialog.vbox.set_border_width(self._CONTENTS_BORDER_WIDTH)

    self._dialog.connect('realize', self._on_export_options_dialog_realize)
    self._dialog.connect('close', self._on_export_options_dialog_close)
    self._dialog.connect('response', self._on_export_options_dialog_response)

  @property
  def widget(self):
    return self._dialog

  def _on_export_options_dialog_close(self, _dialog):
    self._dialog.hide()

  def _on_export_options_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.CLOSE:
      self._dialog.hide()

  def _on_export_options_dialog_realize(self, _dialog):
    if self._parent is not None:
      self._dialog.set_transient_for(pg.gui.get_toplevel_window(self._parent))
      self._dialog.set_attached_to(pg.gui.get_toplevel_window(self._parent))

  def _on_export_options_dialog_button_reset_clicked(self, _button):
    self._settings['main/export'].reset()


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
