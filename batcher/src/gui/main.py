"""Main module for the plug-in GUI."""

import contextlib
import functools
import os

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg

from src import actions
from src import core
from src import builtin_constraints
from src import builtin_procedures
from src import exceptions
from src import overwrite
from src import renamer as renamer_
from src import update
from src import utils as utils_

from src.gui import actions as actions_
from src.gui import message_box as message_box_
from src.gui import message_label as message_label_
from src.gui import messages as messages_
from src.gui import overwrite_chooser as overwrite_chooser_
from src.gui import progress_updater as progress_updater_
from src.gui.entry import entries as entries_
from src.gui.preview import controller as previews_controller_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_


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


def _set_settings(func):
  """Decorator for `Group.apply_gui_values_to_settings()` that prevents the
  decorated function from being invoked if there are invalid setting values.

  When assigning an invalid value, a warning message is displayed.
  
  This decorator is meant to be used in the `ExportLayersDialog` class.
  """
  
  @functools.wraps(func)
  def func_wrapper(self, *args, **kwargs):
    self._settings['main'].apply_gui_values_to_settings()
    self._settings['gui'].apply_gui_values_to_settings()

    self._settings['main/output_directory'].gui.update_setting_value()

    self._settings['main/selected_layers'].value[self._image] = (
      self._name_preview.selected_items)
    self._settings['gui/name_preview_layers_collapsed_state'].value[self._image] = (
      self._name_preview.collapsed_items)
    self._settings['gui/image_preview_displayed_layers'].value[self._image] = (
      [self._image_preview.item.raw] if self._image_preview.item is not None else [])

    func(self, *args, **kwargs)
  
  return func_wrapper


def _setup_images_and_directories_and_initial_directory(
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


def _setup_output_directory_changed(settings, current_image):
  def on_output_directory_changed(output_directory, images_and_directories, current_image_):
    images_and_directories.update_dirpath(current_image_, output_directory.value)
  
  settings['main/output_directory'].connect_event(
    'value-changed',
    on_output_directory_changed,
    settings['gui/images_and_directories'],
    current_image)


class ExportLayersDialog:

  _DIALOG_CONTENTS_BORDER_WIDTH = 8
  _DIALOG_VBOX_SPACING = 5
  _EXPORT_SETTINGS_AND_ACTIONS_SPACING = 10
  _CONSTRAINTS_TOP_MARGIN = 5

  _GRID_EXPORT_SETTINGS_COLUMN_SPACING = 10
  _ACTION_LABEL_BOX_SPACING = 5
  _PREVIEWS_LEFT_MARGIN = 4
  _PREVIEW_LABEL_BOTTOM_MARGIN = 4
  _HBOX_EXPORT_NAME_ENTRIES_SPACING = 3
  _HBOX_MESSAGE_HORIZONTAL_SPACING = 8

  _BUTTON_SETTINGS_SPACING = 2
  _IMPORT_SETTINGS_CUSTOM_WIDGETS_BORDER_WIDTH = 3
  
  _FILE_EXTENSION_ENTRY_MIN_WIDTH_CHARS = 4
  _FILE_EXTENSION_ENTRY_MAX_WIDTH_CHARS = 10
  _FILENAME_PATTERN_ENTRY_MIN_WIDTH_CHARS = 12
  _FILENAME_PATTERN_ENTRY_MAX_WIDTH_CHARS = 40
  
  _DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS = 100
  _DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS = 10000
  
  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0
  
  def __init__(self, initial_layer_tree, settings, run_gui_func=None):
    self._initial_layer_tree = initial_layer_tree
    self._settings = settings
    
    self._image = self._initial_layer_tree.image
    self._message_setting = None
    self._batcher = None
    self._batcher_for_previews = core.Batcher(
      Gimp.RunMode.NONINTERACTIVE,
      self._image,
      self._settings['main/procedures'],
      self._settings['main/constraints'],
      overwrite_chooser=overwrite.NoninteractiveOverwriteChooser(
        self._settings['main/overwrite_mode'].items['replace']),
      item_tree=self._initial_layer_tree)
    
    self._init_settings()
    
    self._init_gui()
    self._assign_gui_to_settings()
    self._connect_events()
    
    self._init_actions()
    
    self._finish_init_and_show()
    
    if not run_gui_func:
      Gtk.main()
    else:
      run_gui_func(self, self._dialog, self._settings)
  
  @property
  def name_preview(self):
    return self._name_preview
  
  @property
  def image_preview(self):
    return self._image_preview
  
  def _init_settings(self):
    self._settings['main/procedures'].tags.add('ignore_load')
    self._settings['main/constraints'].tags.add('ignore_load')
    
    load_result = self._settings.load()
    if pg.setting.Persistor.FAIL in load_result.statuses_per_source.values():
      messages_.display_message(
        utils_.format_message_from_persistor_statuses(
          load_result.statuses_per_source, separator='\n\n'),
        Gtk.MessageType.WARNING)
    
    _setup_images_and_directories_and_initial_directory(
      self._settings, self._settings['main/output_directory'], self._image)
    _setup_output_directory_changed(self._settings, self._image)
  
  def _init_actions(self):
    self._settings['main/procedures'].tags.discard('ignore_load')
    result = self._settings['main/procedures'].load()
    
    if self._settings['main/procedures'] in result.settings_not_loaded:
      actions.clear(self._settings['main/procedures'], add_initial_actions=True)

    self._settings['main/constraints'].tags.discard('ignore_load')
    result = self._settings['main/constraints'].load()
    
    if self._settings['main/constraints'] in result.settings_not_loaded:
      actions.clear(self._settings['main/constraints'], add_initial_actions=True)
  
  def _init_gui(self):
    self._dialog = GimpUi.Dialog(title=_('Export Layers'), role=pg.config.PLUGIN_NAME)
    if self._settings['gui/size/dialog_size'].value:
      self._dialog.set_default_size(*self._settings['gui/size/dialog_size'].value)
    self._dialog.set_default_response(Gtk.ResponseType.CANCEL)

    GimpUi.window_set_transient(self._dialog)

    messages_.set_gui_excepthook_parent(self._dialog)

    self._init_gui_previews()

    self._preview_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      margin_bottom=self._PREVIEW_LABEL_BOTTOM_MARGIN,
    )
    self._preview_label.set_markup('<b>{}</b>'.format(_('Preview')))

    self._vpaned_previews = Gtk.Paned(
      orientation=Gtk.Orientation.VERTICAL,
      wide_handle=True,
    )
    self._vpaned_previews.pack1(self._name_preview, True, True)
    self._vpaned_previews.pack2(self._image_preview, True, True)

    self._vbox_previews = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      margin_start=self._PREVIEWS_LEFT_MARGIN,
    )
    self._vbox_previews.pack_start(self._preview_label, False, False, 0)
    self._vbox_previews.pack_start(self._vpaned_previews, True, True, 0)

    self._folder_chooser_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._folder_chooser_label.set_markup('<b>{}</b>'.format(_('Save in folder:')))

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
    self._export_filename_label.set_markup('<b>{}:</b>'.format(GLib.markup_escape_text(_('Save as'))))
    
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
      row_spacing=self._DIALOG_VBOX_SPACING,
      column_spacing=self._GRID_EXPORT_SETTINGS_COLUMN_SPACING,
    )
    self._grid_export_settings.attach(self._folder_chooser_label, 0, 0, 1, 1)
    self._grid_export_settings.attach(self._folder_chooser, 1, 0, 1, 1)
    self._grid_export_settings.attach(self._export_filename_label, 0, 1, 1, 1)
    self._grid_export_settings.attach(self._hbox_export_filename_entries, 1, 1, 1, 1)

    self._label_procedures = Gtk.Label(
      label='<b>{}</b>'.format(_('Procedures')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._box_procedures = actions_.ActionBox(
      self._settings['main/procedures'],
      builtin_procedures.BUILTIN_PROCEDURES,
      _('Add P_rocedure...'),
      add_custom_action_text=_('Add Custom Procedure...'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._vbox_procedures = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
    )
    self._vbox_procedures.pack_start(self._label_procedures, False, False, 0)
    self._vbox_procedures.pack_start(self._box_procedures, True, True, 0)

    self._label_constraints = Gtk.Label(
      label='<b>{}</b>'.format(_('Constraints')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._box_constraints = actions_.ActionBox(
      self._settings['main/constraints'],
      builtin_constraints.BUILTIN_CONSTRAINTS,
      _('Add C_onstraint...'),
      allow_custom_actions=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._vbox_constraints = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
      margin_top=self._CONSTRAINTS_TOP_MARGIN,
    )
    self._vbox_constraints.pack_start(self._label_constraints, False, False, 0)
    self._vbox_constraints.pack_start(self._box_constraints, True, True, 0)

    self._vbox_export_settings_and_actions = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._EXPORT_SETTINGS_AND_ACTIONS_SPACING,
    )
    self._vbox_export_settings_and_actions.pack_start(self._grid_export_settings, False, False, 0)
    self._vbox_export_settings_and_actions.pack_start(self._vbox_procedures, False, False, 0)
    self._vbox_export_settings_and_actions.pack_start(self._vbox_constraints, False, False, 0)
    
    self._hpaned_settings_and_previews = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
    )
    self._hpaned_settings_and_previews.pack1(self._vbox_export_settings_and_actions, True, False)
    self._hpaned_settings_and_previews.pack2(self._vbox_previews, True, True)
    
    self._button_run = self._dialog.add_button(_('_Export'), Gtk.ResponseType.OK)
    self._button_run.set_can_default(True)
    self._button_run.hide()
    
    self._button_close = self._dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    self._button_close.hide()

    self._button_stop = Gtk.Button(label=_('_Stop'), use_underline=True)
    self._button_stop.set_no_show_all(True)
    
    self._label_button_settings = Gtk.Label(
      label=_('_Settings'),
      use_underline=True,
    )

    self._arrow_button_settings = Gtk.Arrow(
      arrow_type=Gtk.ArrowType.DOWN,
      shadow_type=Gtk.ShadowType.IN,
    )

    self._hbox_button_settings_components = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._BUTTON_SETTINGS_SPACING,
    )
    self._hbox_button_settings_components.pack_start(self._label_button_settings, False, False, 0)
    self._hbox_button_settings_components.pack_start(self._arrow_button_settings, False, False, 0)

    self._hbox_button_settings = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_button_settings.set_center_widget(self._hbox_button_settings_components)

    self._button_settings = Gtk.Button()
    self._button_settings.add(self._hbox_button_settings)

    self._menu_item_edit_mode = Gtk.CheckMenuItem(label=_('Edit Layers'))
    self._menu_item_save_settings = Gtk.MenuItem(label=_('Save Settings'))
    self._menu_item_reset_settings = Gtk.MenuItem(label=_('Reset settings'))
    self._menu_item_import_settings = Gtk.MenuItem(label=_('Import Settings...'))
    self._menu_item_export_settings = Gtk.MenuItem(label=_('Export Settings...'))

    self._menu_settings = Gtk.Menu()
    self._menu_settings.append(self._menu_item_edit_mode)
    self._menu_settings.append(self._menu_item_save_settings)
    self._menu_settings.append(self._menu_item_reset_settings)
    self._menu_settings.append(self._menu_item_import_settings)
    self._menu_settings.append(self._menu_item_export_settings)
    self._menu_settings.show_all()

    self._dialog.action_area.pack_end(self._button_stop, False, False, 0)
    self._dialog.action_area.pack_start(self._button_settings, False, False, 0)
    self._dialog.action_area.set_child_secondary(self._button_settings, True)

    self._button_help = self._get_help_button(self._button_run)

    self._dialog.action_area.pack_start(self._button_help, False, False, 0)
    self._dialog.action_area.set_child_secondary(self._button_help, True)

    self._progress_bar = Gtk.ProgressBar(
      ellipsize=Pango.EllipsizeMode.MIDDLE,
    )
    self._progress_bar.set_no_show_all(True)

    self._label_message = message_label_.MessageLabel()

    self._box_warning_messages = message_box_.SettingValueNotValidMessageBox(
      message_type=Gtk.MessageType.WARNING)

    self._hbox_messages = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_MESSAGE_HORIZONTAL_SPACING,
    )
    self._hbox_messages.pack_start(self._box_warning_messages, False, False, 0)
    self._hbox_messages.pack_start(self._label_message, True, True, 0)
    
    self._hbox_contents = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_contents.pack_start(self._hpaned_settings_and_previews, True, True, 0)
    
    self._dialog.vbox.set_spacing(self._DIALOG_VBOX_SPACING)
    self._dialog.vbox.set_border_width(self._DIALOG_CONTENTS_BORDER_WIDTH)
    self._dialog.vbox.pack_start(self._hbox_contents, True, True, 0)
    self._dialog.vbox.pack_end(self._progress_bar, False, False, 0)
    self._dialog.vbox.pack_end(self._hbox_messages, False, False, 0)
  
  def _connect_events(self):
    self._box_procedures.connect(
      'action-box-item-added', self._on_box_procedures_item_added)
    
    self._button_run.connect('clicked', self._on_button_run_clicked, 'processing')
    self._button_close.connect('clicked', self._on_button_close_clicked)
    self._button_stop.connect('clicked', self._on_button_stop_clicked)
    
    self._button_settings.connect('clicked', self._on_button_settings_clicked)
    self._menu_item_edit_mode.connect('toggled', self._on_menu_item_edit_mode_toggled)
    self._menu_item_save_settings.connect('activate', self._on_save_settings_activate)
    self._menu_item_reset_settings.connect('activate', self._on_reset_settings_activate)
    self._menu_item_import_settings.connect('activate', self._on_import_settings_activate)
    self._menu_item_export_settings.connect('activate', self._on_export_settings_activate)
    
    self._file_extension_entry.connect(
      'changed',
      self._on_text_entry_changed,
      self._settings['main/file_extension'],
      'invalid_file_extension')

    self._file_extension_entry.connect(
      'focus-out-event',
      self._on_file_extension_entry_focus_out_event,
      self._settings['main/file_extension'])

    self._filename_pattern_entry.connect(
      'changed',
      self._on_text_entry_changed,
      self._settings['main/layer_filename_pattern'],
      'invalid_layer_filename_pattern')
    
    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)
    self._dialog.connect('notify::is-active', self._on_dialog_notify_is_active)
    
    self._hpaned_settings_and_previews.connect(
      'notify::position',
      self._previews_controller.on_paned_outside_previews_notify_position)
    self._vpaned_previews.connect(
      'notify::position',
      self._previews_controller.on_paned_between_previews_notify_position)
    
    self._previews_controller.connect_setting_changes_to_previews()
    self._previews_controller.connect_name_preview_events()
    
    self._image_preview.connect('preview-updated', self._on_image_preview_updated)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated)

  @staticmethod
  def _get_help_button(reference_button):
    button_help = Gtk.LinkButton(
      uri=(
        pg.config.LOCAL_DOCS_PATH if os.path.isfile(pg.config.LOCAL_DOCS_PATH)
        else pg.config.DOCS_URL),
      label=_('_Help'),
      use_underline=True,
    )
    # Make the button appear like a regular button
    button_help_style_context = button_help.get_style_context()

    for style_class in button_help_style_context.list_classes():
      button_help_style_context.remove_class(style_class)

    for style_class in reference_button.get_style_context().list_classes():
      button_help_style_context.add_class(style_class)

    button_help.unset_state_flags(Gtk.StateFlags.LINK)

    # Make sure the button retains the style of a regular button when clicked.
    button_help.connect(
      'clicked',
      lambda button, *args: button.unset_state_flags(Gtk.StateFlags.VISITED | Gtk.StateFlags.LINK))

    return button_help

  def _finish_init_and_show(self):
    while Gtk.events_pending():
      Gtk.main_iteration()
    
    self._dialog.vbox.show_all()
    self._update_gui_for_edit_mode(update_name_preview=False)
    
    if not self._settings['main/edit_mode'].value:
      self._dialog.set_focus(self._file_extension_entry)
    
    self._button_run.grab_default()
    # Place the cursor at the end of the text entry.
    self._file_extension_entry.set_position(-1)
    
    self._dialog.show()
  
  def _assign_gui_to_settings(self):
    self._settings.initialize_gui({
      'main/output_directory': [
        pg.setting.SETTING_GUI_TYPES.folder_chooser_button, self._folder_chooser],
      'main/file_extension': [
        pg.setting.SETTING_GUI_TYPES.extended_entry, self._file_extension_entry],
      'main/layer_filename_pattern': [
        pg.setting.SETTING_GUI_TYPES.extended_entry, self._filename_pattern_entry],
      'main/edit_mode': [
        pg.setting.SETTING_GUI_TYPES.check_menu_item, self._menu_item_edit_mode],
      'gui/image_preview_automatic_update': [
        pg.setting.SETTING_GUI_TYPES.check_menu_item,
        self._image_preview.menu_item_update_automatically],
      'gui/size/dialog_position': [
        pg.setting.SETTING_GUI_TYPES.window_position, self._dialog],
      'gui/size/dialog_size': [
        pg.setting.SETTING_GUI_TYPES.window_size, self._dialog],
      'gui/size/paned_outside_previews_position': [
        pg.setting.SETTING_GUI_TYPES.paned_position, self._hpaned_settings_and_previews],
      'gui/size/paned_between_previews_position': [
        pg.setting.SETTING_GUI_TYPES.paned_position, self._vpaned_previews],
    })
  
  def _init_gui_previews(self):
    self._name_preview = preview_name_.NamePreview(
      self._batcher_for_previews,
      self._settings,
      self._initial_layer_tree,
      self._settings['gui/name_preview_layers_collapsed_state'].value[self._image],
      self._settings['main/selected_layers'].value[self._image],
      'selected_in_preview')
    
    self._image_preview = preview_image_.ImagePreview(self._batcher_for_previews, self._settings)
    
    self._previews_controller = previews_controller_.PreviewsController(
      self._name_preview, self._image_preview, self._settings, self._image)
  
  def _import_settings(self, filepath, file_format, load_size_settings=True):
    source = pg.setting.sources.JsonFileSource(pg.config.SOURCE_NAME, filepath)
    
    actions.clear(self._settings['main/procedures'], add_initial_actions=False)
    actions.clear(self._settings['main/constraints'], add_initial_actions=False)
    
    settings_to_ignore_for_reset = []
    for setting in self._settings.walk(lambda s: 'ignore_reset' not in s.tags):
      if setting.get_path('root').startswith('gui/size'):
        setting.tags.add('ignore_reset')
        settings_to_ignore_for_reset.append(setting)
    
    self._reset_settings()
    
    for setting in settings_to_ignore_for_reset:
      setting.tags.discard('ignore_reset')
    
    status, message = update.update(
      self._settings, handle_invalid='terminate', sources={'persistent': source})
    if status == update.TERMINATE:
      messages_.display_import_export_settings_failure_message(
        _(('Failed to import settings from file "{}".'
           ' Settings must be reset completely.').format(filepath)),
        details=message,
        parent=self._dialog)
      
      self._reset_settings()
      actions.clear(self._settings['main/procedures'])
      actions.clear(self._settings['main/constraints'])
      return False
    
    size_settings_to_ignore_for_load = []
    if not load_size_settings:
      for setting in self._settings['gui'].walk(lambda s: 'ignore_load' not in s.tags):
        if setting.get_path('root').startswith('gui/size'):
          setting.tags.add('ignore_load')
          size_settings_to_ignore_for_load.append(setting)
    
    load_result = self._settings.load({'persistent': source})
    
    for setting in size_settings_to_ignore_for_load:
      setting.tags.discard('ignore_load')
    
    if any(status in load_result.statuses_per_source.values()
           for status in [pg.setting.Persistor.SOURCE_NOT_FOUND, pg.setting.Persistor.FAIL]):
      messages_.display_import_export_settings_failure_message(
        _('Failed to import settings from file "{}"'.format(filepath)),
        details=utils_.format_message_from_persistor_statuses(
          load_result.statuses_per_source, separator='\n\n'),
        parent=self._dialog)
      return False
    else:
      return True
  
  def _save_settings(self, filepath=None, file_format='json'):
    if filepath is None:
      save_result = self._settings.save()
    else:
      source = pg.setting.sources.JsonFileSource(pg.config.SOURCE_NAME, filepath)
      save_result = self._settings.save({'persistent': source})
    
    if pg.setting.Persistor.FAIL in save_result.statuses_per_source.values():
      messages_.display_import_export_settings_failure_message(
        _('Failed to export settings to file "{}"'.format(filepath)),
        details=utils_.format_message_from_persistor_statuses(
          save_result.statuses_per_source, separator='\n\n'),
        parent=self._dialog)
      return False
    else:
      return True
  
  @_set_settings
  def _save_settings_to_default_location(self):
    save_successful = self._save_settings()
    if save_successful:
      self._display_inline_message(_('Settings successfully saved.'), Gtk.MessageType.INFO)
  
  def _reset_settings(self):
    self._settings.reset()
  
  def _get_setting_filepath(self, action, add_file_extension_if_missing=True):
    if action == 'import':
      dialog_action = Gtk.FileChooserAction.OPEN
      button_ok = Gtk.STOCK_OPEN
      title = _('Import Settings')
    elif action == 'export':
      dialog_action = Gtk.FileChooserAction.SAVE
      button_ok = Gtk.STOCK_SAVE
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
      Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

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
  
  def _on_text_entry_changed(self, entry, setting, name_preview_lock_update_key=None):
    validation_result = setting.validate(setting.gui.get_value())

    if validation_result is None:
      setting.gui.update_setting_value()

      self._name_preview.lock_update(False, name_preview_lock_update_key)

      if self._message_setting == setting:
        self._display_inline_message(None)

      self._name_preview.add_function_at_update(
        self._name_preview.set_sensitive, True)

      pg.invocation.timeout_add_strict(
        self._DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS,
        self._name_preview.update)
    else:
      pg.invocation.timeout_add_strict(
        self._DELAY_NAME_PREVIEW_UPDATE_TEXT_ENTRIES_MILLISECONDS,
        self._name_preview.set_sensitive, False)

      self._display_inline_message(validation_result.message, Gtk.MessageType.ERROR, setting)

      self._name_preview.lock_update(True, name_preview_lock_update_key)

  @staticmethod
  def _on_file_extension_entry_focus_out_event(entry, event, setting):
    setting.apply_to_gui()
  
  def _on_box_procedures_item_added(self, box_procedures, item):
    if any(item.action['orig_name'].value == name
           for name in ['insert_background', 'insert_foreground']):
      actions.reorder(self._settings['main/procedures'], item.action.name, 0)
  
  def _on_menu_item_edit_mode_toggled(self, menu_item):
    self._update_gui_for_edit_mode()
  
  def _update_gui_for_edit_mode(self, update_name_preview=True):
    if self._menu_item_edit_mode.get_active():
      self._grid_export_settings.hide()
      
      self._button_run.set_label(_('Run'))
      self._button_close.set_label(_('Close'))
    else:
      self._grid_export_settings.show()
      
      self._button_run.set_label(_('Export'))
      self._button_close.set_label(_('Cancel'))
    
    if update_name_preview:
      self._name_preview.update()
  
  def _on_dialog_notify_is_active(self, dialog, property_spec):
    if not self._image.is_valid():
      Gtk.main_quit()
      return
    
    if self._initial_layer_tree is not None:
      self._initial_layer_tree = None
      return
  
  def _on_image_preview_updated(self, preview, error, update_duration_seconds):
    self._display_warnings_and_tooltips_for_actions()
    
    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)
      
      self._display_inline_message(
        '{}\n\n{}'.format(
          _('Disabling automatic preview update.'),
          _('The preview takes too long to update.'
            ' You may turn automatic updates back on from the menu above the previewed image.')),
        Gtk.MessageType.INFO)
  
  def _on_name_preview_updated(self, preview, error):
    self._display_warnings_and_tooltips_for_actions(clear_previous=False)
  
  def _display_warnings_and_tooltips_for_actions(self, clear_previous=True):
    self._set_warning_on_actions(self._batcher_for_previews, clear_previous=clear_previous)
    
    self._set_action_skipped_tooltips(
      self._box_procedures,
      self._batcher_for_previews.skipped_procedures,
      _('This procedure is skipped. Reason: {}'),
      clear_previous=clear_previous)
    
    self._set_action_skipped_tooltips(
      self._box_constraints,
      self._batcher_for_previews.skipped_constraints,
      _('This constraint is skipped. Reason: {}'),
      clear_previous=clear_previous)
  
  def _on_dialog_key_press_event(self, dialog, event):
    if not dialog.get_mapped():
      return False

    if Gdk.keyval_name(event.keyval) == 'Escape':
      stopped = stop_batcher(self._batcher)
      return stopped
    
    # Ctrl + S is pressed
    if ((event.state & Gtk.accelerator_get_default_mod_mask()) == Gdk.ModifierType.CONTROL_MASK
        and Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)) == 's'):
      self._save_settings_to_default_location()
      return True
    
    return False
  
  def _on_button_settings_clicked(self, button):
    pg.gui.menu_popup_below_widget(self._menu_settings, button)
  
  def _on_save_settings_activate(self, menu_item):
    self._save_settings_to_default_location()
  
  def _on_import_settings_activate(self, menu_item):
    filepath, file_format, load_size_settings = self._get_setting_filepath(action='import')
    
    if filepath is not None:
      import_successful = self._import_settings(filepath, file_format, load_size_settings)
      # Also override default setting sources so that the imported settings actually persist.
      self._save_settings()
      
      if import_successful:
        self._display_inline_message(_('Settings successfully imported.'), Gtk.MessageType.INFO)
  
  @_set_settings
  def _on_export_settings_activate(self, menu_item):
    filepath, file_format, _unused = self._get_setting_filepath(action='export')
    
    if filepath is not None:
      export_successful = self._save_settings(filepath, file_format)
      if export_successful:
        self._display_inline_message(_('Settings successfully exported.'), Gtk.MessageType.INFO)
  
  def _on_reset_settings_activate(self, menu_item):
    response_id = display_reset_prompt(parent=self._dialog)
    
    if response_id == Gtk.ResponseType.YES:
      actions.clear(self._settings['main/procedures'])
      actions.clear(self._settings['main/constraints'])
      
      self._reset_settings()
      self._save_settings()
      
      utils_.clear_setting_sources(self._settings)
      
      self._display_inline_message(_('Settings reset.'), Gtk.MessageType.INFO)
  
  @_set_settings
  def _on_button_run_clicked(self, button, lock_update_key):
    self._setup_gui_before_batch_run()
    self._batcher, overwrite_chooser, progress_updater = self._setup_batcher()
    
    should_quit = True
    self._name_preview.lock_update(True, lock_update_key)
    self._image_preview.lock_update(True, lock_update_key)
    
    try:
      self._batcher.run(**utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError as e:
      should_quit = False
    except exceptions.ActionError as e:
      messages_.display_failure_message(
        messages_.get_failing_action_message(e),
        failure_message=str(e),
        details=e.traceback,
        parent=self._dialog)
      should_quit = False
    except exceptions.BatcherError as e:
      messages_.display_processing_failure_message(e, parent=self._dialog)
      should_quit = False
    except Exception:
      if self._image.is_valid():
        raise
      else:
        messages_.display_invalid_image_failure_message(parent=self._dialog)
    else:
      if self._settings['main/edit_mode'].value or not self._batcher.exported_raw_items:
        should_quit = False
      
      if not self._settings['main/edit_mode'].value and not self._batcher.exported_raw_items:
        messages_.display_message(
          _('No layers were exported.'), Gtk.MessageType.INFO, parent=self._dialog)
    finally:
      self._name_preview.lock_update(False, lock_update_key)
      self._image_preview.lock_update(False, lock_update_key)
      
      if self._settings['main/edit_mode'].value:
        self._image_preview.update()
        self._name_preview.update(reset_items=True)
      
      self._set_warning_on_actions(self._batcher)
      
      self._batcher = None
    
    if overwrite_chooser.overwrite_mode in self._settings['main/overwrite_mode'].items.values():
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)
    
    self._settings['main'].save()
    self._settings['gui'].save()
    
    if should_quit:
      Gtk.main_quit()
    else:
      self._restore_gui_after_batch_run()
      progress_updater.reset()
  
  def _setup_gui_before_batch_run(self):
    self._display_inline_message(None)
    self._reset_action_tooltips_and_indicators()
    self._close_action_edit_dialogs()
    self._set_gui_enabled(False)
  
  def _restore_gui_after_batch_run(self):
    self._set_gui_enabled(True)
  
  def _setup_batcher(self):
    overwrite_chooser = overwrite_chooser_.GtkDialogOverwriteChooser(
      self._get_overwrite_dialog_items(),
      default_value=self._settings['main/overwrite_mode'].items['replace'],
      default_response=overwrite.OverwriteModes.CANCEL,
      parent=self._dialog)
    
    progress_updater = progress_updater_.GtkProgressUpdater(self._progress_bar)
    
    batcher = core.Batcher(
      Gimp.RunMode.INTERACTIVE,
      self._image,
      self._settings['main/procedures'],
      self._settings['main/constraints'],
      overwrite_chooser=overwrite_chooser,
      progress_updater=progress_updater,
      export_context_manager=handle_gui_in_export,
      export_context_manager_args=[self._dialog])
    
    return batcher, overwrite_chooser, progress_updater
  
  def _get_overwrite_dialog_items(self):
    return dict(zip(
      self._settings['main/overwrite_mode'].items.values(),
      self._settings['main/overwrite_mode'].items_display_names.values()))
  
  def _set_gui_enabled(self, enabled):
    self._progress_bar.set_visible(not enabled)
    self._button_stop.set_visible(not enabled)
    self._button_close.set_visible(enabled)

    self._hbox_contents.set_sensitive(enabled)
    
    self._button_settings.set_sensitive(enabled)
    self._button_help.set_sensitive(enabled)
    self._button_run.set_sensitive(enabled)

    if enabled:
      self._dialog.set_focus(self._file_extension_entry)
      self._file_extension_entry.set_position(-1)
    else:
      self._dialog.set_focus(self._button_stop)
  
  @staticmethod
  def _on_dialog_delete_event(dialog, event):
    Gtk.main_quit()
  
  @staticmethod
  def _on_button_close_clicked(button):
    Gtk.main_quit()
  
  def _on_button_stop_clicked(self, button):
    stop_batcher(self._batcher)
  
  @staticmethod
  def _set_action_skipped_tooltips(action_box, skipped_actions, message, clear_previous=True):
    for box_item in action_box.items:
      if not box_item.has_warning():
        if box_item.action.name in skipped_actions:
          skipped_message = skipped_actions[box_item.action.name][0][1]
          box_item.set_tooltip(message.format(skipped_message))
        else:
          if clear_previous:
            box_item.reset_tooltip()
  
  def _set_warning_on_actions(self, batcher, clear_previous=True):
    action_boxes = [self._box_procedures, self._box_constraints]
    failed_actions_dict = [batcher.failed_procedures, batcher.failed_constraints]
    
    for action_box, failed_actions in zip(action_boxes, failed_actions_dict):
      for box_item in action_box.items:
        if box_item.action.name in failed_actions:
          box_item.set_warning(
            True,
            messages_.get_failing_action_message(
              (box_item.action, failed_actions[box_item.action.name][0][0])),
            failed_actions[box_item.action.name][0][1],
            failed_actions[box_item.action.name][0][2],
            parent=self._dialog)
        else:
          if clear_previous:
            box_item.set_warning(False)
  
  def _reset_action_tooltips_and_indicators(self):
    for action_box in [self._box_procedures, self._box_constraints]:
      for box_item in action_box.items:
        box_item.reset_tooltip()
        box_item.set_warning(False)

  def _close_action_edit_dialogs(self):
    for action_box in [self._box_procedures, self._box_constraints]:
      for box_item in action_box.items:
        box_item.action_edit_dialog.hide()

  def _display_inline_message(self, text, message_type=Gtk.MessageType.ERROR, setting=None):
    self._message_setting = setting

    self._label_message.set_text(text, message_type, self._DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS)


class ExportLayersNowDialog:
  
  _BORDER_WIDTH = 8
  _HBOX_HORIZONTAL_SPACING = 8
  _DIALOG_WIDTH = 500
  
  def __init__(self, layer_tree, settings):
    self._layer_tree = layer_tree
    self._settings = settings
    
    self._image = self._layer_tree.image
    self._batcher = None
    
    self._settings.load()
    
    self._init_gui()
    
    messages_.set_gui_excepthook_parent(self._dialog)
    
    Gtk.main_iteration()
    self.show()
    self.run_batcher()
  
  def _init_gui(self):
    self._dialog = GimpUi.Dialog(title=_('Export Layers'), role=None)
    self._dialog.set_border_width(self._BORDER_WIDTH)
    self._dialog.set_default_size(self._DIALOG_WIDTH, -1)

    GimpUi.window_set_transient(self._dialog)
    
    self._button_stop = Gtk.Button(label=_('_Stop'), use_underline=True)
    
    self._buttonbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
    self._buttonbox.pack_start(self._button_stop, False, False, 0)
    
    self._progress_bar = Gtk.ProgressBar(
      ellipsize=Pango.EllipsizeMode.MIDDLE,
    )
    
    self._hbox_action_area = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_HORIZONTAL_SPACING,
    )
    self._hbox_action_area.pack_start(self._progress_bar, True, True, 0)
    self._hbox_action_area.pack_end(self._buttonbox, False, False, 0)
    
    self._dialog.vbox.pack_end(self._hbox_action_area, False, False, 0)
    
    self._button_stop.connect('clicked', self._on_button_stop_clicked)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)
  
  def run_batcher(self):
    progress_updater = progress_updater_.GtkProgressUpdater(self._progress_bar)
    
    self._batcher = core.Batcher(
      Gimp.RunMode.WITH_LAST_VALS,
      self._image,
      self._settings['main/procedures'],
      self._settings['main/constraints'],
      overwrite_chooser=overwrite.NoninteractiveOverwriteChooser(
        self._settings['main/overwrite_mode'].value),
      progress_updater=progress_updater,
      export_context_manager=handle_gui_in_export,
      export_context_manager_args=[self._dialog])
    try:
      self._batcher.run(
        item_tree=self._layer_tree,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.BatcherError as e:
      messages_.display_processing_failure_message(e, parent=self._dialog)
    except Exception:
      if self._image.is_valid():
        raise
      else:
        messages_.display_invalid_image_failure_message(parent=self._dialog)
    else:
      if not self._settings['main/edit_mode'].value and not self._batcher.exported_raw_items:
        messages_.display_message(
          _('No layers were exported.'), Gtk.MessageType.INFO, parent=self._dialog)
  
  def show(self):
    self._dialog.vbox.show_all()
    self._dialog.action_area.hide()
    self._dialog.show()
  
  def hide(self):
    self._dialog.hide()
  
  def _on_button_stop_clicked(self, button):
    stop_batcher(self._batcher)
  
  def _on_dialog_delete_event(self, dialog, event):
    stop_batcher(self._batcher)
