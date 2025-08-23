"""Main GUI dialog classes for each plug-in procedure."""

import os

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from config import CONFIG
from src import setting as setting_
from src.gui import message_box as message_box_
from src.gui import message_label as message_label_
from src.gui import messages as messages_
from src.gui.main import command_lists as command_lists_
from src.gui.main import batcher_manager as batcher_manager_
from src.gui.main import export_settings as export_settings_
from src.gui.main import previews as previews_
from src.gui.main import settings_manager as settings_manager_
from src.procedure_groups import *


class BatchProcessingGui:

  _DIALOG_CONTENTS_BORDER_WIDTH = 8
  _DIALOG_VBOX_SPACING = 5
  _VBOX_SETTINGS_SPACING = 10
  _EXPORT_SETTINGS_BOTTOM_MARGIN = 10

  _HBOX_MESSAGE_HORIZONTAL_SPACING = 8

  _DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS = 10000

  def __init__(
        self,
        item_tree,
        settings,
        mode,
        item_type,
        title=None,
        current_image=None,
        run_gui_func=None,
  ):
    if mode not in ['edit', 'export']:
      raise ValueError('mode must be either "edit" or "export"')

    self._item_tree = item_tree
    self._settings = settings
    self._mode = mode
    self._item_type = item_type
    self._title = title
    self._current_image = current_image

    self._batcher_manager = batcher_manager_.BatcherManager(self._item_tree, self._settings)

    self._init_gui()
    self._assign_gui_to_settings()
    self._connect_events()

    self._finish_init_and_show()

    if not run_gui_func:
      Gtk.main()
    else:
      run_gui_func(self, self._dialog, self._settings)

  @property
  def name_preview(self):
    return self._previews.name_preview

  @property
  def image_preview(self):
    return self._previews.image_preview

  @property
  def action_list(self):
    return self._command_lists.action_list

  @property
  def condition_list(self):
    return self._command_lists.condition_list

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(title=self._title, role=CONFIG.PLUGIN_NAME)
    if self._settings['gui/size/dialog_size'].value:
      self._dialog.set_default_size(*self._settings['gui/size/dialog_size'].value)
    self._dialog.set_default_response(Gtk.ResponseType.CANCEL)

    GimpUi.window_set_transient(self._dialog)

    messages_.set_gui_excepthook_parent(self._dialog)

    self._label_message = message_label_.MessageLabel()

    if self._item_type == 'image':
      previews_top_label = _('Input Images')
    elif self._item_type == 'layer':
      previews_top_label = _('Input Layers')
    else:
      previews_top_label = _('Input Items')

    self._previews = previews_.Previews(
      self._settings,
      self._mode,
      self._item_type,
      self._item_tree,
      previews_top_label,
      lock_previews=True,
      manage_items=CONFIG.PROCEDURE_GROUP == CONVERT_GROUP,
      display_message_func=self._display_inline_message,
      current_image=self._current_image,
      parent=self._dialog,
    )

    if self._mode == 'export':
      self._export_settings = export_settings_.ExportSettings(
        self._settings,
        current_image=self._current_image,
        name_preview=self._previews.name_preview,
        image_preview=self._previews.image_preview,
        parent=self._dialog,
      )
      self._export_settings.widget.set_margin_bottom(self._EXPORT_SETTINGS_BOTTOM_MARGIN)
    else:
      self._export_settings = None

    self._command_lists = command_lists_.CommandLists(
      self._settings,
      self._dialog,
    )

    self._button_run = self._dialog.add_button('', Gtk.ResponseType.OK)
    self._button_run.set_can_default(True)
    self._button_run.hide()
    if self._mode == 'export' and CONFIG.PROCEDURE_GROUP != CONVERT_GROUP:
      self._button_run.set_label(_('_Export'))
    else:
      self._button_run.set_label(_('_Run'))

    self._button_close = self._dialog.add_button('', Gtk.ResponseType.CANCEL)
    self._button_close.hide()
    if self._mode == 'export':
      self._set_close_button_label(self._settings['gui/auto_close'])
    else:
      self._button_close.set_label(_('_Close'))

    self._button_stop = Gtk.Button(label=_('_Stop'), use_underline=True)
    self._button_stop.set_no_show_all(True)

    self._settings_manager = settings_manager_.SettingsManager(
      self._settings,
      self._dialog,
      previews_controller=self._previews.controller,
      display_message_func=self._display_inline_message,
    )

    self._dialog.action_area.pack_end(self._button_stop, False, False, 0)
    self._dialog.action_area.pack_start(self._settings_manager.button, False, False, 0)
    self._dialog.action_area.set_child_secondary(self._settings_manager.button, True)

    self._button_help = self._get_help_button(self._button_run)

    self._dialog.action_area.pack_start(self._button_help, False, False, 0)
    self._dialog.action_area.set_child_secondary(self._button_help, True)

    self._progress_bar = Gtk.ProgressBar(
      ellipsize=Pango.EllipsizeMode.MIDDLE,
    )
    self._progress_bar.set_no_show_all(True)

    self._box_warning_messages = message_box_.SettingValueNotValidMessageBox(
      message_type=Gtk.MessageType.WARNING)

    self._hbox_messages = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_MESSAGE_HORIZONTAL_SPACING,
    )
    self._hbox_messages.pack_start(self._box_warning_messages, False, False, 0)
    self._hbox_messages.pack_start(self._label_message, True, True, 0)

    self._vbox_settings = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._VBOX_SETTINGS_SPACING,
    )
    if self._mode == 'export':
      self._vbox_settings.pack_start(self._export_settings.widget, False, False, 0)
    self._vbox_settings.pack_start(self._command_lists.vbox_actions, False, False, 0)
    self._vbox_settings.pack_start(self._command_lists.vbox_conditions, False, False, 0)

    self._vbox_settings_with_messages = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._VBOX_SETTINGS_SPACING,
    )
    self._vbox_settings_with_messages.pack_start(self._vbox_settings, True, True, 0)
    self._vbox_settings_with_messages.pack_start(self._hbox_messages, False, False, 0)

    self._hpaned_settings_and_previews = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
    )
    self._hpaned_settings_and_previews.pack1(self._vbox_settings_with_messages, True, False)
    self._hpaned_settings_and_previews.pack2(self._previews.vbox_previews, True, True)

    self._hbox_contents = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_contents.pack_start(self._hpaned_settings_and_previews, True, True, 0)

    self._dialog.vbox.set_spacing(self._DIALOG_VBOX_SPACING)
    self._dialog.vbox.set_border_width(self._DIALOG_CONTENTS_BORDER_WIDTH)
    self._dialog.vbox.pack_start(self._hbox_contents, True, True, 0)
    self._dialog.vbox.pack_end(self._progress_bar, False, False, 0)

  def _connect_events(self):
    self._button_run.connect('clicked', self._on_button_run_clicked)
    self._button_close.connect('clicked', self._on_button_close_clicked)
    self._button_stop.connect('clicked', self._on_button_stop_clicked)

    self._settings['gui/auto_close'].connect_event('value-changed', self._on_auto_close_changed)

    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)

    self._previews.connect_events(self._command_lists, self._hpaned_settings_and_previews)

  def _finish_init_and_show(self):
    self._previews.controller.initialize_inputs_in_name_preview()

    self._previews.unlock()

    self._dialog.vbox.show_all()

    if self._mode == 'export':
      self._dialog.set_focus(self._export_settings.file_extension_entry)
    else:
      self._dialog.set_focus(self._command_lists.action_list.button_add)

    self._button_run.grab_default()

    self._dialog.show()

    if self._mode == 'export':
      self._export_settings.file_extension_entry.set_position(-1)

  def _assign_gui_to_settings(self):
    if self._mode == 'edit':
      self._assign_gui_to_settings_for_edit_mode()
    elif self._mode == 'export':
      self._assign_gui_to_settings_for_export_mode()

  def _assign_gui_to_settings_for_edit_mode(self):
    self._assign_gui_to_settings_common()

  def _assign_gui_to_settings_for_export_mode(self):
    self._settings['main/export'].tags.add('ignore_initialize_gui')

    self._assign_gui_to_settings_common()

    self._settings['main/export'].tags.remove('ignore_initialize_gui')

    self._settings['main/export'].initialize_gui(only_null=True)

  def _assign_gui_to_settings_common(self):
    self._settings.initialize_gui(
      {
        'gui/size/dialog_position': dict(
          gui_type=setting_.SETTING_GUI_TYPES.window_position,
          widget=self._dialog),
        'gui/size/dialog_size': dict(
          gui_type=setting_.SETTING_GUI_TYPES.window_size,
          widget=self._dialog),
        'gui/size/paned_outside_previews_position': dict(
          gui_type=setting_.SETTING_GUI_TYPES.paned_position,
          widget=self._hpaned_settings_and_previews),
      },
      only_null=True,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  def _on_button_run_clicked(self, _button):
    self._set_up_gui_before_run()

    should_quit = self._batcher_manager.run_batcher(
      self._mode,
      self._item_type,
      self._command_lists,
      self._previews,
      self._settings_manager,
      self._dialog,
      self._progress_bar,
    )

    self._restore_gui_after_batch_run()

    if should_quit and self._settings['gui/auto_close'].value:
      Gtk.main_quit()

  def _set_up_gui_before_run(self):
    self._display_inline_message(None)

    self._command_lists.reset_command_tooltips_and_indicators()
    self._command_lists.close_command_edit_dialogs()

    self._previews.close_import_options_dialog()

    if self._export_settings is not None:
      self._export_settings.close_export_options_dialog()

    self._set_gui_enabled(False)

  def _restore_gui_after_batch_run(self):
    self._set_gui_enabled(True)

  def _set_gui_enabled(self, enabled):
    self._progress_bar.set_visible(not enabled)
    self._button_stop.set_visible(not enabled)
    self._button_close.set_visible(enabled)

    self._hbox_contents.set_sensitive(enabled)

    if self._export_settings is not None:
      self._export_settings.widget.set_sensitive(enabled)
    self._settings_manager.button.set_sensitive(enabled)
    self._button_help.set_sensitive(enabled)
    self._button_run.set_sensitive(enabled)

    self._dialog.set_focus(self._button_stop)

  def _on_dialog_key_press_event(self, dialog, event):
    if not dialog.get_mapped():
      return False

    if Gdk.keyval_name(event.keyval) == 'Escape':
      stopped = self._batcher_manager.stop_batcher()
      return stopped

    return False

  @staticmethod
  def _on_dialog_delete_event(_dialog, _event):
    Gtk.main_quit()

  @staticmethod
  def _on_button_close_clicked(_button):
    Gtk.main_quit()

  def _on_button_stop_clicked(self, _button):
    self._batcher_manager.stop_batcher()

  def _on_auto_close_changed(self, auto_close_setting):
    if self._mode == 'export':
      self._set_close_button_label(auto_close_setting)

  def _set_close_button_label(self, auto_close_setting):
    if auto_close_setting.value:
      self._button_close.set_label(_('_Cancel'))
    else:
      self._button_close.set_label(_('_Close'))

  def _display_inline_message(self, text, message_type=Gtk.MessageType.ERROR):
    self._label_message.set_text(text, message_type, self._DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS)

  @staticmethod
  def _get_help_button(reference_button):
    button_help = Gtk.LinkButton(
      uri=(
        CONFIG.LOCAL_DOCS_PATH if os.path.isfile(CONFIG.LOCAL_DOCS_PATH)
        else CONFIG.DOCS_URL),
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
      lambda button, *args: button.unset_state_flags(
        Gtk.StateFlags.VISITED | Gtk.StateFlags.LINK))

    return button_help


class BatchProcessingQuickGui:

  _BORDER_WIDTH = 8
  _DIALOG_VBOX_SPACING = 8

  _DEFAULT_DIALOG_WIDTH = 350

  def __init__(
        self,
        item_tree,
        settings,
        mode,
        item_type,
        title=None,
        current_image=None,
        run_gui_func=None,
  ):
    if mode not in ['edit', 'export']:
      raise ValueError('mode must be either "edit" or "export"')

    self._item_tree = item_tree
    self._settings = settings
    self._mode = mode
    self._item_type = item_type
    self._title = title
    self._current_image = current_image

    self._batcher_manager = batcher_manager_.BatcherManagerQuick(self._item_tree, self._settings)

    self._init_gui()

    self._dialog.show_all()

    if mode == 'export' and self._settings['gui/show_quick_settings'].value:
      self._button_run.connect('clicked', self._on_button_run_clicked)

      if not run_gui_func:
        Gtk.main()
      else:
        run_gui_func(self, self._dialog, self._settings)
    else:
      Gtk.main_iteration()

      self._run_batcher_quick()

  @property
  def dialog(self):
    return self._dialog

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(title=self._title, role=CONFIG.PLUGIN_NAME)
    self._dialog.set_border_width(self._BORDER_WIDTH)
    self._dialog.set_default_size(self._DEFAULT_DIALOG_WIDTH, -1)

    self._dialog.vbox.set_spacing(self._DIALOG_VBOX_SPACING)

    GimpUi.window_set_transient(self._dialog)

    messages_.set_gui_excepthook_parent(self._dialog)

    self._button_run = None
    self._export_settings = None
    self._check_button_show_this_dialog = None

    if self._mode == 'export' and self._settings['gui/show_quick_settings'].value:
      self._export_settings = export_settings_.ExportSettings(
        self._settings,
        current_image=self._current_image,
        parent=self._dialog,
      )
      self._dialog.vbox.pack_start(self._export_settings.widget, False, False, 0)

      self._check_button_show_this_dialog = Gtk.CheckButton(label=_('Show this dialog'))
      self._check_button_show_this_dialog.set_active(self._settings['gui/show_quick_settings'].value)

      self._dialog.vbox.pack_start(self._check_button_show_this_dialog, False, False, 0)

      if self._mode == 'export' and CONFIG.PROCEDURE_GROUP != CONVERT_GROUP:
        button_run_label = _('_Export')
      else:
        button_run_label = _('_Run')

      self._button_run = self._dialog.add_button(button_run_label, Gtk.ResponseType.OK)

      self._button_run.set_can_default(True)

    self._button_cancel = self._dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)

    self._progress_bar = Gtk.ProgressBar(
      ellipsize=Pango.EllipsizeMode.MIDDLE,
    )
    self._progress_bar.set_no_show_all(True)

    self._dialog.vbox.pack_end(self._progress_bar, True, True, 0)

    self._button_cancel.connect('clicked', self._on_button_cancel_clicked)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)

  def _on_button_run_clicked(self, _button):
    self._run_batcher_quick()

    self._settings['gui/show_quick_settings'].set_value(self._should_show_dialog_next_time())

    settings_to_save = [
      self._settings['gui'],
    ]

    if self._mode == 'export':
      settings_to_save.extend([
        self._settings['main/file_extension'],
        self._settings['main/output_directory'],
        self._settings['main/name_pattern'],
        self._settings['main/overwrite_mode'],
        self._settings['main/export'],
      ])

    # Save only select settings as e.g. conditions are modified by Export/Edit
    # Selected Layers. We cannot use 'ignore_save' on actions or conditions
    # as that would save empty groups, effectively erasing them.
    setting_.Persistor.save(settings_to_save)

    Gtk.main_quit()

  def _run_batcher_quick(self):
    if self._button_run is not None:
      self._button_run.set_sensitive(False)

    if self._export_settings is not None:
      self._export_settings.widget.set_sensitive(False)

    if self._check_button_show_this_dialog is not None:
      self._check_button_show_this_dialog.set_sensitive(False)

    self._progress_bar.show()

    self._batcher_manager.run_batcher(
      self._mode,
      self._item_type,
      self._item_tree,
      self._dialog,
      self._progress_bar,
    )

  def _should_show_dialog_next_time(self):
    return self._check_button_show_this_dialog.get_active()

  def _on_button_cancel_clicked(self, _button):
    self._batcher_manager.stop_batcher()

    Gtk.main_quit()

  def _on_dialog_delete_event(self, _dialog, _event):
    self._batcher_manager.stop_batcher()

    Gtk.main_quit()
