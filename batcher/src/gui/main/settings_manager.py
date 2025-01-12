import os
from typing import Optional

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import actions as actions_
from src import update
from src import utils as utils_

from src.gui import messages as messages_


class SettingsManager:

  _BUTTON_SETTINGS_SPACING = 3
  _ARROW_ICON_PIXEL_SIZE = 12

  _LOAD_SETTINGS_FROM_FILE_CUSTOM_WIDGETS_BORDER_WIDTH = 3

  _PREVIEWS_LOAD_SETTINGS_KEY = 'load_settings'

  def __init__(
        self,
        settings,
        dialog,
        previews_controller=None,
        display_message_func=None,
  ):
    self._settings = settings
    self._dialog = dialog
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
    self._menu_item_load_settings_from_file = Gtk.MenuItem(label=_('Load Settings from File...'))
    self._menu_item_save_settings_to_file = Gtk.MenuItem(label=_('Save Settings to File...'))
    self._menu_item_reset_settings = Gtk.MenuItem(label=_('Reset Settings'))

    self._menu_settings = Gtk.Menu()
    self._settings['gui/auto_close'].set_gui()
    self._menu_settings.append(self._settings['gui/auto_close'].gui.widget)
    if 'keep_inputs' in self._settings['gui']:
      self._settings['gui/keep_inputs'].set_gui()
      self._menu_settings.append(self._settings['gui/keep_inputs'].gui.widget)
    self._menu_settings.append(self._menu_item_save_settings)
    self._menu_settings.append(self._menu_item_load_settings_from_file)
    self._menu_settings.append(self._menu_item_save_settings_to_file)
    self._menu_settings.append(self._menu_item_reset_settings)
    self._menu_settings.show_all()

    self._button_settings.connect('clicked', self._on_button_settings_clicked)

    self._menu_item_save_settings.connect('activate', self._on_save_settings_activate)
    self._menu_item_load_settings_from_file.connect(
      'activate', self._on_load_settings_from_file_activate)
    self._menu_item_save_settings_to_file.connect(
      'activate', self._on_save_settings_to_file_activate)
    self._menu_item_reset_settings.connect('activate', self._on_reset_settings_activate)

    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)

  @property
  def button(self):
    return self._button_settings

  def save_settings(self, filepath=None):
    if filepath is None:
      save_result = self._settings.save()
    else:
      source = pg.setting.sources.JsonFileSource(pg.config.PROCEDURE_GROUP, filepath)
      save_result = self._settings.save({'persistent': source})

    if pg.setting.Persistor.FAIL in save_result.statuses_per_source.values():
      if filepath is None:
        main_message = _('Failed to save settings.')
      else:
        main_message = _('Failed to save settings to file "{}".'.format(filepath))

      display_load_save_settings_failure_message(
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

  def _on_load_settings_from_file_activate(self, _menu_item):
    filepath, file_format, load_size_settings = self._get_setting_file_and_options(action='load')

    if filepath is not None:
      load_successful = self._load_settings_from_file(filepath, file_format, load_size_settings)
      # Also override default setting sources so that the loaded settings actually persist.
      self.save_settings()

      if load_successful:
        self._display_message_func(_('Settings successfully loaded.'), Gtk.MessageType.INFO)

  def _on_save_settings_to_file_activate(self, _menu_item):
    filepath, _file_format, _load_size_settings = self._get_setting_file_and_options(action='save')

    if filepath is not None:
      self._settings.apply_gui_values_to_settings()

      save_successful = self.save_settings(filepath)
      if save_successful:
        self._display_message_func(
          _('Settings successfully saved to "{}".').format(os.path.basename(filepath)),
          Gtk.MessageType.INFO)

  def _on_reset_settings_activate(self, _menu_item):
    response_id = self._display_reset_prompt()

    if response_id == Gtk.ResponseType.YES:
      actions_.clear(self._settings['main/procedures'])
      actions_.clear(self._settings['main/constraints'])

      self.reset_settings()

      pg.setting.Persistor.clear()

      self.save_settings()

      self._display_message_func(_('Settings reset.'), Gtk.MessageType.INFO)

  def _display_reset_prompt(self):
    dialog = Gtk.MessageDialog(
      parent=self._dialog,
      message_type=Gtk.MessageType.WARNING,
      modal=True,
      destroy_with_parent=True,
      buttons=Gtk.ButtonsType.YES_NO,
    )

    dialog.set_transient_for(self._dialog)
    dialog.set_markup(GLib.markup_escape_text(_('Are you sure you want to reset settings?')))
    dialog.set_focus(dialog.get_widget_for_response(Gtk.ResponseType.NO))

    dialog.show_all()
    response_id = dialog.run()
    dialog.destroy()

    return response_id

  def _on_dialog_key_press_event(self, dialog, event):
    if not dialog.get_mapped():
      return False

    # Ctrl + S is pressed
    if ((event.state & Gtk.accelerator_get_default_mod_mask()) == Gdk.ModifierType.CONTROL_MASK
        and Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval)) == 's'):
      self._save_settings_to_default_location()
      return True

    return False

  def _save_settings_to_default_location(self):
    self._settings.apply_gui_values_to_settings()

    save_successful = self.save_settings()
    if save_successful:
      self._display_message_func(_('Settings successfully saved.'), Gtk.MessageType.INFO)

  def _load_settings_from_file(self, filepath, _file_format, load_size_settings=True):
    source = pg.setting.sources.JsonFileSource(pg.config.PROCEDURE_GROUP, filepath)

    actions_.clear(self._settings['main/procedures'], add_initial_actions=False)
    actions_.clear(self._settings['main/constraints'], add_initial_actions=False)

    settings_to_ignore_for_reset = []
    for setting in self._settings.walk(lambda s: 'ignore_reset' not in s.tags):
      if setting.get_path('root').startswith('gui/size/'):
        setting.tags.add('ignore_reset')
        settings_to_ignore_for_reset.append(setting)

    self.reset_settings()

    for setting in settings_to_ignore_for_reset:
      setting.tags.discard('ignore_reset')

    if self._previews_controller is not None:
      self._previews_controller.lock_previews(self._PREVIEWS_LOAD_SETTINGS_KEY)

    size_settings_to_ignore_for_load = []
    if not load_size_settings:
      for setting in self._settings['gui'].walk(lambda s: 'ignore_load' not in s.tags):
        if setting.get_path('root').startswith('gui/size/'):
          setting.tags.add('ignore_load')
          size_settings_to_ignore_for_load.append(setting)

    status, message = update.load_and_update(
      self._settings,
      sources={'persistent': source},
      update_sources=False,
      procedure_group=pg.config.PROCEDURE_GROUP,
    )

    for setting in size_settings_to_ignore_for_load:
      setting.tags.discard('ignore_load')

    if status == update.TERMINATE:
      display_load_save_settings_failure_message(
        _(('Failed to load settings from file "{}".'
           ' Settings must be reset completely.')).format(filepath),
        details=message,
        parent=self._dialog)

      self.reset_settings()
      actions_.clear(self._settings['main/procedures'])
      actions_.clear(self._settings['main/constraints'])

    if self._previews_controller is not None:
      self._previews_controller.unlock_previews(self._PREVIEWS_LOAD_SETTINGS_KEY)

    return status != update.TERMINATE

  def _get_setting_file_and_options(self, action, add_file_extension_if_missing=True):
    if action == 'load':
      dialog_action = Gtk.FileChooserAction.OPEN
      button_ok = _('_Open')
      title = _('Load Settings from File')
    elif action == 'save':
      dialog_action = Gtk.FileChooserAction.SAVE
      button_ok = _('_Save')
      title = _('Save Settings to File')
    else:
      raise ValueError('invalid action; valid values: "load", "save"')

    file_dialog = Gtk.FileChooserDialog(
      title=title,
      parent=self._dialog,
      action=dialog_action,
      do_overwrite_confirmation=True,
    )

    file_dialog.add_buttons(
      button_ok, Gtk.ResponseType.OK,
      _('_Cancel'), Gtk.ResponseType.CANCEL)

    if action == 'load':
      check_button_load_size_settings = Gtk.CheckButton(
        label=_('Load size-related settings'),
        border_width=self._LOAD_SETTINGS_FROM_FILE_CUSTOM_WIDGETS_BORDER_WIDTH,
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


def display_load_save_settings_failure_message(
      main_message: str,
      details: str,
      parent: Optional[Gtk.Window] = None,
):
  messages_.display_failure_message(
    main_message,
    failure_message='',
    details=details,
    parent=parent,
    report_description=_(
      'If you believe this is an error in the plug-in, you can help fix it'
      ' by sending a report with the file and the text in the details to one of the sites below'))
