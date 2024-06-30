"""Main GUI dialog classes for each plug-in procedure."""

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg

from src.gui import message_box as message_box_
from src.gui import message_label as message_label_
from src.gui import messages as messages_

from src.gui.main import action_lists as action_lists_
from src.gui.main import batcher_manager as batcher_manager_
from src.gui.main import common
from src.gui.main import export_settings as export_settings_
from src.gui.main import previews as previews_
from src.gui.main import settings_manager as settings_manager_


class ExportLayersGui:

  _DIALOG_CONTENTS_BORDER_WIDTH = 8
  _DIALOG_VBOX_SPACING = 5
  _EXPORT_SETTINGS_AND_ACTIONS_SPACING = 10

  _HBOX_MESSAGE_HORIZONTAL_SPACING = 8

  _DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS = 10000

  def __init__(self, initial_layer_tree, settings, run_gui_func=None):
    self._initial_layer_tree = initial_layer_tree
    self._settings = settings

    self._image = self._initial_layer_tree.image

    self._batcher_manager = batcher_manager_.BatcherManager(self._settings)

    common.set_up_output_directory_settings(self._settings, self._image)

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
  def procedure_list(self):
    return self._action_lists.procedure_list

  @property
  def constraint_list(self):
    return self._action_lists.constraint_list

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(title=_('Export Layers'), role=pg.config.PLUGIN_NAME)
    if self._settings['gui/size/dialog_size'].value:
      self._dialog.set_default_size(*self._settings['gui/size/dialog_size'].value)
    self._dialog.set_default_response(Gtk.ResponseType.CANCEL)

    GimpUi.window_set_transient(self._dialog)

    messages_.set_gui_excepthook_parent(self._dialog)

    self._previews = previews_.Previews(
      self._settings,
      self._initial_layer_tree,
      lock_previews=True,
      display_message_func=self._display_inline_message,
    )

    self._export_settings = export_settings_.ExportSettings(
      self._settings,
      row_spacing=self._DIALOG_VBOX_SPACING,
      name_preview=self._previews.name_preview,
      display_message_func=self._display_inline_message,
    )

    self._action_lists = action_lists_.ActionLists(
      self._settings,
      self._dialog,
    )

    self._vbox_export_settings_and_actions = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._EXPORT_SETTINGS_AND_ACTIONS_SPACING,
    )
    self._vbox_export_settings_and_actions.pack_start(self._export_settings.widget, False, False, 0)
    self._vbox_export_settings_and_actions.pack_start(
      self._action_lists.vbox_procedures, False, False, 0)
    self._vbox_export_settings_and_actions.pack_start(
      self._action_lists.vbox_constraints, False, False, 0)

    self._hpaned_settings_and_previews = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
    )
    self._hpaned_settings_and_previews.pack1(self._vbox_export_settings_and_actions, True, False)
    self._hpaned_settings_and_previews.pack2(self._previews.vbox_previews, True, True)

    self._button_run = self._dialog.add_button(_('_Export'), Gtk.ResponseType.OK)
    self._button_run.set_can_default(True)
    self._button_run.hide()

    self._button_close = self._dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    self._button_close.hide()

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

    self._button_help = common.get_help_button(self._button_run)

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
    self._button_run.connect('clicked', self._on_button_run_clicked)
    self._button_close.connect('clicked', self._on_button_close_clicked)
    self._button_stop.connect('clicked', self._on_button_stop_clicked)

    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)
    self._dialog.connect('window-state-event', self._on_dialog_window_state_event)

    self._previews.connect_events(self._action_lists, self._hpaned_settings_and_previews)

  def _finish_init_and_show(self):
    self._previews.unlock()

    self._dialog.vbox.show_all()
    self._update_gui_for_edit_mode(update_name_preview=False)

    if not self._settings['main/edit_mode'].value:
      self._dialog.set_focus(self._export_settings.file_extension_entry)

    self._button_run.grab_default()

    self._dialog.show()

  def _assign_gui_to_settings(self):
    self._settings.initialize_gui(
      {
        'gui/size/dialog_position': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.window_position,
          widget=self._dialog),
        'gui/size/dialog_size': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.window_size,
          widget=self._dialog),
        'gui/size/paned_outside_previews_position': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
          widget=self._hpaned_settings_and_previews),
      },
      only_null=True,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  def _update_gui_for_edit_mode(self, update_name_preview=True):
    # FIXME: Remove this once the Edit Layers dialog is created
    if self._settings['main/edit_mode'].value:
      self._export_settings.widget.hide()

      self._button_run.set_label(_('Run'))
      self._button_close.set_label(_('Close'))
    else:
      self._export_settings.widget.show()

      self._button_run.set_label(_('Export'))
      self._button_close.set_label(_('Cancel'))

    if update_name_preview:
      self._previews.name_preview.update()

  def _on_dialog_window_state_event(self, _dialog, event):
    if event.new_window_state & Gdk.WindowState.FOCUSED:
      if not self._image.is_valid():
        Gtk.main_quit()
        return

  def _on_button_run_clicked(self, _button):
    self._set_up_gui_before_run()

    should_quit = self._batcher_manager.run_batcher(
      self._image,
      self._action_lists,
      self._previews,
      self._settings_manager,
      self._dialog,
      self._progress_bar,
    )

    self._restore_gui_after_batch_run()

    if should_quit:
      Gtk.main_quit()

  def _set_up_gui_before_run(self):
    self._display_inline_message(None)

    self._action_lists.reset_action_tooltips_and_indicators()
    self._action_lists.close_action_edit_dialogs()

    self._set_gui_enabled(False)

  def _restore_gui_after_batch_run(self):
    self._set_gui_enabled(True)

  def _set_gui_enabled(self, enabled):
    self._progress_bar.set_visible(not enabled)
    self._button_stop.set_visible(not enabled)
    self._button_close.set_visible(enabled)

    self._hbox_contents.set_sensitive(enabled)

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

  def _display_inline_message(self, text, message_type=Gtk.MessageType.ERROR):
    self._label_message.set_text(text, message_type, self._DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS)


class ExportLayersQuickGui:

  _BORDER_WIDTH = 8
  _HBOX_HORIZONTAL_SPACING = 8
  _DIALOG_WIDTH = 500

  def __init__(self, layer_tree, settings):
    self._layer_tree = layer_tree
    self._settings = settings

    self._image = self._layer_tree.image

    self._batcher_manager = batcher_manager_.BatcherManagerQuick(self._settings)

    self._init_gui()

    messages_.set_gui_excepthook_parent(self._dialog)

    Gtk.main_iteration()

    self.show()

    self._batcher_manager.run_batcher(
      self._image,
      self._layer_tree,
      self._dialog,
      self._progress_bar,
    )

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

  def show(self):
    self._dialog.vbox.show_all()
    self._dialog.action_area.hide()
    self._dialog.show()

  def hide(self):
    self._dialog.hide()

  def _on_button_stop_clicked(self, _button):
    self._batcher_manager.stop_batcher()

  def _on_dialog_delete_event(self, _dialog, _event):
    self._batcher_manager.stop_batcher()
