import contextlib
import functools
import os

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import actions as actions_
from src import renamer as renamer_
from src import update
from src import utils as utils_

from src.gui.entry import entries as entries_
from src.gui import messages as messages_


def display_reset_prompt(parent=None):
  dialog = Gtk.MessageDialog(
    parent=parent,
    message_type=Gtk.MessageType.WARNING,
    modal=True,
    destroy_with_parent=True,
    buttons=Gtk.ButtonsType.YES_NO,
  )

  dialog.set_transient_for(parent)
  dialog.set_markup(GLib.markup_escape_text(_('Are you sure you want to reset settings?')))
  dialog.set_focus(dialog.get_widget_for_response(Gtk.ResponseType.NO))

  dialog.show_all()
  response_id = dialog.run()
  dialog.destroy()

  return response_id


@contextlib.contextmanager
def handle_gui_in_export(run_mode, image, layer, output_filepath, window):
  should_manipulate_window = run_mode == Gimp.RunMode.INTERACTIVE

  if should_manipulate_window:
    window_position = window.get_position()
    window.hide()
  else:
    window_position = None

  while Gtk.events_pending():
    Gtk.main_iteration()

  try:
    yield
  finally:
    if window_position is not None:
      window.move(*window_position)
      window.show()

    while Gtk.events_pending():
      Gtk.main_iteration()


def stop_batcher(batcher):
  if batcher is not None:
    batcher.stop()
    return True
  else:
    return False


def set_settings(func):

  @functools.wraps(func)
  def func_wrapper(self, *args, **kwargs):
    self._settings['main'].apply_gui_values_to_settings()
    self._settings['gui'].apply_gui_values_to_settings()

    self._settings['main/output_directory'].gui.update_setting_value()

    # FIXME: These settings should be synced automatically
    self._settings['main/selected_layers'].value[self._image] = (
      self._name_preview.selected_items)
    self._settings['gui/name_preview_layers_collapsed_state'].value[self._image] = (
      self._name_preview.collapsed_items)
    self._settings['gui/image_preview_displayed_layers'].value[self._image] = (
      [self._image_preview.item.raw] if self._image_preview.item is not None else [])

    func(self, *args, **kwargs)

  return func_wrapper


def set_up_output_directory_settings(settings, current_image):
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
        row_spacing=_ROW_SPACING,
        column_spacing=_COLUMN_SPACING,
        name_preview=None,
        display_message_func=None,
  ):
    self._settings = settings
    self._row_spacing = row_spacing
    self._column_spacing = column_spacing
    self._name_preview = name_preview
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._message_setting = None

    self._init_gui()

    self._init_setting_gui()

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
      default_item=self._settings['main/layer_filename_pattern'].default_value)
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
        self._settings['main/layer_filename_pattern'],
        'invalid_layer_filename_pattern')

  def _init_setting_gui(self):
    self._settings['main/output_directory'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.folder_chooser_button,
      widget=self._folder_chooser,
    )
    self._settings['main/file_extension'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._file_extension_entry,
    )
    self._settings['main/layer_filename_pattern'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.extended_entry,
      widget=self._filename_pattern_entry,
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


class SettingsManager:

  _BUTTON_SETTINGS_SPACING = 3
  _ARROW_ICON_PIXEL_SIZE = 12

  _IMPORT_SETTINGS_CUSTOM_WIDGETS_BORDER_WIDTH = 3

  _PREVIEWS_IMPORT_SETTINGS_KEY = 'import_settings'

  def __init__(
        self,
        settings,
        dialog,
        # FIXME: Remove `image`, `name_preview` and `image_preview`,
        #  which are only used for manually syncing settings.
        image,
        name_preview,
        image_preview,
        previews_controller=None,
        display_message_func=None,
  ):
    self._settings = settings
    self._dialog = dialog
    self._image = image
    self._name_preview = name_preview
    self._image_preview = image_preview
    self._previews_controller = previews_controller
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._init_gui()

  def _init_gui(self):
    self._label_button_settings = Gtk.Label(
      label=_('_Settings'),
      use_underline=True,
    )

    self._image_arrow_settings = Gtk.Image.new_from_icon_name('go-down', Gtk.IconSize.BUTTON)
    self._image_arrow_settings.set_pixel_size(self._ARROW_ICON_PIXEL_SIZE)

    self._hbox_button_settings_components = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._BUTTON_SETTINGS_SPACING,
    )
    self._hbox_button_settings_components.pack_start(self._label_button_settings, False, False, 0)
    self._hbox_button_settings_components.pack_start(self._image_arrow_settings, False, False, 0)

    self._hbox_button_settings = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_button_settings.set_center_widget(self._hbox_button_settings_components)

    self._button_settings = Gtk.Button()
    self._button_settings.add(self._hbox_button_settings)

    self._menu_item_save_settings = Gtk.MenuItem(label=_('Save Settings'))
    self._menu_item_reset_settings = Gtk.MenuItem(label=_('Reset settings'))
    self._menu_item_import_settings = Gtk.MenuItem(label=_('Import Settings...'))
    self._menu_item_export_settings = Gtk.MenuItem(label=_('Export Settings...'))

    self._menu_settings = Gtk.Menu()
    self._menu_settings.append(self._menu_item_save_settings)
    self._menu_settings.append(self._menu_item_reset_settings)
    self._menu_settings.append(self._menu_item_import_settings)
    self._menu_settings.append(self._menu_item_export_settings)
    self._menu_settings.show_all()

    self._button_settings.connect('clicked', self._on_button_settings_clicked)

    self._menu_item_save_settings.connect('activate', self._on_save_settings_activate)
    self._menu_item_reset_settings.connect('activate', self._on_reset_settings_activate)
    self._menu_item_import_settings.connect('activate', self._on_import_settings_activate)
    self._menu_item_export_settings.connect('activate', self._on_export_settings_activate)

    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)

  @property
  def button(self):
    return self._button_settings

  def save_settings(self, filepath=None):
    if filepath is None:
      save_result = self._settings.save()
    else:
      source = pg.setting.sources.JsonFileSource(pg.config.SOURCE_NAME, filepath)
      save_result = self._settings.save({'persistent': source})

    if pg.setting.Persistor.FAIL in save_result.statuses_per_source.values():
      if filepath is None:
        main_message = _('Failed to save settings.')
      else:
        main_message = _('Failed to export settings to file "{}".'.format(filepath))

      messages_.display_import_export_settings_failure_message(
        main_message,
        details=utils_.format_message_from_persistor_statuses(save_result, separator='\n\n'),
        parent=self._dialog)
      return False
    else:
      return True

  def reset_settings(self):
    self._settings.reset()

  def _on_button_settings_clicked(self, button):
    pg.gui.menu_popup_below_widget(self._menu_settings, button)

  def _on_save_settings_activate(self, _menu_item):
    self._save_settings_to_default_location()

  def _on_reset_settings_activate(self, _menu_item):
    response_id = display_reset_prompt(parent=self._dialog)

    if response_id == Gtk.ResponseType.YES:
      actions_.clear(self._settings['main/procedures'])
      actions_.clear(self._settings['main/constraints'])

      self.reset_settings()

      pg.setting.Persistor.clear()

      self.save_settings()

      self._display_message_func(_('Settings reset.'), Gtk.MessageType.INFO)

  def _on_import_settings_activate(self, menu_item):
    filepath, file_format, load_size_settings = self._get_setting_filepath(action='import')

    if filepath is not None:
      import_successful = self._import_settings(filepath, file_format, load_size_settings)
      # Also override default setting sources so that the imported settings actually persist.
      self.save_settings()

      if import_successful:
        self._display_message_func(_('Settings successfully imported.'), Gtk.MessageType.INFO)

  @set_settings
  def _on_export_settings_activate(self, menu_item):
    filepath, _file_format, _load_size_settings = self._get_setting_filepath(action='export')

    if filepath is not None:
      export_successful = self.save_settings(filepath)
      if export_successful:
        self._display_message_func(_('Settings successfully exported.'), Gtk.MessageType.INFO)

  def _on_dialog_key_press_event(self, dialog, event):
    if not dialog.get_mapped():
      return False

    # Ctrl + S is pressed
    if ((event.state & Gtk.accelerator_get_default_mod_mask()) == Gdk.ModifierType.CONTROL_MASK
        and Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)) == 's'):
      self._save_settings_to_default_location()
      return True

    return False

  @set_settings
  def _save_settings_to_default_location(self):
    save_successful = self.save_settings()
    if save_successful:
      self._display_message_func(_('Settings successfully saved.'), Gtk.MessageType.INFO)

  def _import_settings(self, filepath, file_format, load_size_settings=True):
    source = pg.setting.sources.JsonFileSource(pg.config.SOURCE_NAME, filepath)

    actions_.clear(self._settings['main/procedures'], add_initial_actions=False)
    actions_.clear(self._settings['main/constraints'], add_initial_actions=False)

    settings_to_ignore_for_reset = []
    for setting in self._settings.walk(lambda s: 'ignore_reset' not in s.tags):
      if setting.get_path('root').startswith('gui/size'):
        setting.tags.add('ignore_reset')
        settings_to_ignore_for_reset.append(setting)

    self.reset_settings()

    for setting in settings_to_ignore_for_reset:
      setting.tags.discard('ignore_reset')

    if self._previews_controller is not None:
      self._previews_controller.lock_previews(self._PREVIEWS_IMPORT_SETTINGS_KEY)

    size_settings_to_ignore_for_load = []
    if not load_size_settings:
      for setting in self._settings['gui'].walk(lambda s: 'ignore_load' not in s.tags):
        if setting.get_path('root').startswith('gui/size'):
          setting.tags.add('ignore_load')
          size_settings_to_ignore_for_load.append(setting)

    status, message = update.load_and_update(
      self._settings,
      sources={'persistent': source},
      update_sources=False,
    )

    for setting in size_settings_to_ignore_for_load:
      setting.tags.discard('ignore_load')

    if self._previews_controller is not None:
      self._previews_controller.unlock_and_update_previews(self._PREVIEWS_IMPORT_SETTINGS_KEY)

    if status == update.TERMINATE:
      messages_.display_import_export_settings_failure_message(
        _(('Failed to import settings from file "{}".'
           ' Settings must be reset completely.')).format(filepath),
        details=message,
        parent=self._dialog)

      self.reset_settings()
      actions_.clear(self._settings['main/procedures'])
      actions_.clear(self._settings['main/constraints'])
      return False

    return True

  def _get_setting_filepath(self, action, add_file_extension_if_missing=True):
    if action == 'import':
      dialog_action = Gtk.FileChooserAction.OPEN
      button_ok = _('_Open')
      title = _('Import Settings')
    elif action == 'export':
      dialog_action = Gtk.FileChooserAction.SAVE
      button_ok = _('_Save')
      title = _('Export Settings')
    else:
      raise ValueError('invalid action; valid values: "import", "export"')

    file_dialog = Gtk.FileChooserDialog(
      title=title,
      parent=self._dialog,
      action=dialog_action,
      do_overwrite_confirmation=True,
    )

    file_dialog.add_buttons(
      button_ok, Gtk.ResponseType.OK,
      _('_Cancel'), Gtk.ResponseType.CANCEL)

    if action == 'import':
      check_button_load_size_settings = Gtk.CheckButton(
        label=_('Import size-related settings'),
        border_width=self._IMPORT_SETTINGS_CUSTOM_WIDGETS_BORDER_WIDTH,
      )
      file_dialog.vbox.pack_start(check_button_load_size_settings, False, False, 0)
    else:
      check_button_load_size_settings = None

    json_file_ext = '.json'

    filter_json = Gtk.FileFilter()
    filter_json.set_name(_('JSON file ({})').format(json_file_ext))
    filter_json.add_mime_type('application/json')
    file_dialog.add_filter(filter_json)

    default_file_ext = json_file_ext
    default_file_format = json_file_ext[1:]

    filter_any = Gtk.FileFilter()
    filter_any.set_name(_('Any file'))
    filter_any.add_pattern('*')
    file_dialog.add_filter(filter_any)

    file_dialog.show_all()

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.OK:
      filepath = file_dialog.get_filename() if file_dialog.get_filename() is not None else ''

      file_ext = os.path.splitext(filepath)[1]
      if add_file_extension_if_missing and not file_ext:
        filepath += default_file_ext

      file_ext = os.path.splitext(filepath)[1]
      if file_ext:
        file_format = file_ext[1:]
      else:
        file_format = default_file_format
    else:
      filepath = None
      file_format = None

    if check_button_load_size_settings:
      load_size_settings = check_button_load_size_settings.get_active()
    else:
      load_size_settings = False

    file_dialog.destroy()

    return filepath, file_format, load_size_settings
