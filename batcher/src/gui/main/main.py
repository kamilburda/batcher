"""Main GUI dialog classes for each plug-in procedure."""

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg

from src import core
from src import exceptions
from src import overwrite
from src import utils as utils_

from src.gui import message_box as message_box_
from src.gui import message_label as message_label_
from src.gui import messages as messages_
from src.gui import overwrite_chooser as overwrite_chooser_
from src.gui import progress_updater as progress_updater_
from src.gui.preview import controller as previews_controller_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_

from src.gui.main import common


class ExportLayersGui:

  _DIALOG_CONTENTS_BORDER_WIDTH = 8
  _DIALOG_VBOX_SPACING = 5
  _EXPORT_SETTINGS_AND_ACTIONS_SPACING = 10

  _PREVIEWS_LEFT_MARGIN = 4
  _PREVIEW_LABEL_BOTTOM_MARGIN = 4
  _HBOX_MESSAGE_HORIZONTAL_SPACING = 8

  _DELAY_CLEAR_LABEL_MESSAGE_MILLISECONDS = 10000

  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0

  _PREVIEWS_INITIAL_UPDATE_KEY = 'initial_update'

  def __init__(self, initial_layer_tree, settings, run_gui_func=None):
    self._initial_layer_tree = initial_layer_tree
    self._settings = settings

    self._image = self._initial_layer_tree.image
    self._batcher = None
    self._batcher_for_previews = core.Batcher(
      Gimp.RunMode.NONINTERACTIVE,
      self._image,
      self._settings['main/procedures'],
      self._settings['main/constraints'],
      overwrite_chooser=overwrite.NoninteractiveOverwriteChooser(
        self._settings['main/overwrite_mode'].items['replace']),
      item_tree=self._initial_layer_tree)

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
    return self._name_preview

  @property
  def image_preview(self):
    return self._image_preview

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

    self._export_settings = common.ExportSettings(
      self._settings,
      row_spacing=self._DIALOG_VBOX_SPACING,
      name_preview=self._name_preview,
      display_message_func=self._display_inline_message,
    )

    self._action_lists = common.ActionLists(
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
    self._hpaned_settings_and_previews.pack2(self._vbox_previews, True, True)

    self._button_run = self._dialog.add_button(_('_Export'), Gtk.ResponseType.OK)
    self._button_run.set_can_default(True)
    self._button_run.hide()

    self._button_close = self._dialog.add_button(_('_Cancel'), Gtk.ResponseType.CANCEL)
    self._button_close.hide()

    self._button_stop = Gtk.Button(label=_('_Stop'), use_underline=True)
    self._button_stop.set_no_show_all(True)

    self._settings_manager = common.SettingsManager(
      self._settings,
      self._dialog,
      previews_controller=self._previews_controller,
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
    self._button_run.connect('clicked', self._on_button_run_clicked, 'processing')
    self._button_close.connect('clicked', self._on_button_close_clicked)
    self._button_stop.connect('clicked', self._on_button_stop_clicked)

    self._dialog.connect('key-press-event', self._on_dialog_key_press_event)
    self._dialog.connect('delete-event', self._on_dialog_delete_event)
    self._dialog.connect('window-state-event', self._on_dialog_window_state_event)

    self._hpaned_settings_and_previews.connect(
      'notify::position',
      self._previews_controller.on_paned_outside_previews_notify_position)
    self._vpaned_previews.connect(
      'notify::position',
      self._previews_controller.on_paned_between_previews_notify_position)

    self._previews_controller.connect_setting_changes_to_previews(
      self._action_lists.procedure_list,
      self._action_lists.constraint_list,
    )
    self._previews_controller.connect_name_preview_events()

    self._image_preview.connect('preview-updated', self._on_image_preview_updated)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated)

  def _finish_init_and_show(self):
    self._previews_controller.unlock_and_update_previews(self._PREVIEWS_INITIAL_UPDATE_KEY)

    self._dialog.vbox.show_all()
    self._update_gui_for_edit_mode(update_name_preview=False)

    if not self._settings['main/edit_mode'].value:
      self._dialog.set_focus(self._export_settings.file_extension_entry)

    self._button_run.grab_default()

    self._dialog.show()

  def _assign_gui_to_settings(self):
    self._settings.initialize_gui(
      {
        'gui/image_preview_automatic_update': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.check_menu_item,
          widget=self._image_preview.menu_item_update_automatically),
        'gui/size/dialog_position': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.window_position,
          widget=self._dialog),
        'gui/size/dialog_size': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.window_size,
          widget=self._dialog),
        'gui/size/paned_outside_previews_position': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
          widget=self._hpaned_settings_and_previews),
        'gui/size/paned_between_previews_position': dict(
          gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
          widget=self._vpaned_previews),
      },
      only_null=True,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

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
    self._previews_controller.lock_previews(self._PREVIEWS_INITIAL_UPDATE_KEY)

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
      self._name_preview.update()

  def _on_dialog_window_state_event(self, _dialog, event):
    if event.new_window_state & Gdk.WindowState.FOCUSED:
      if not self._image.is_valid():
        Gtk.main_quit()
        return

  def _on_image_preview_updated(self, _preview, _error, update_duration_seconds):
    self._action_lists.display_warnings_and_tooltips_for_actions(self._batcher_for_previews)

    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)

      self._display_inline_message(
        _('Disabling automatic preview update. The preview takes too long to update.'),
        Gtk.MessageType.INFO)

  def _on_name_preview_updated(self, _preview, _error):
    self._action_lists.display_warnings_and_tooltips_for_actions(
      self._batcher_for_previews, clear_previous=False)

  def _on_button_run_clicked(self, _button, lock_update_key):
    self._settings.apply_gui_values_to_settings()

    self._set_up_gui_before_run()
    self._batcher, overwrite_chooser, progress_updater = self._set_up_batcher()

    should_quit = True
    self._name_preview.lock_update(True, lock_update_key)
    self._image_preview.lock_update(True, lock_update_key)

    try:
      self._batcher.run(**utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
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

      self._action_lists.set_warning_on_actions(self._batcher)

      self._batcher = None

    if overwrite_chooser.overwrite_mode in self._settings['main/overwrite_mode'].items.values():
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)

    self._settings_manager.save_settings()

    if should_quit:
      Gtk.main_quit()
    else:
      self._restore_gui_after_batch_run()
      progress_updater.reset()

  def _set_up_gui_before_run(self):
    self._display_inline_message(None)

    self._action_lists.reset_action_tooltips_and_indicators()
    self._action_lists.close_action_edit_dialogs()

    self._set_gui_enabled(False)

  def _restore_gui_after_batch_run(self):
    self._set_gui_enabled(True)

  def _set_up_batcher(self):
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
      export_context_manager=common.handle_gui_in_export,
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

    self._settings_manager.button.set_sensitive(enabled)
    self._button_help.set_sensitive(enabled)
    self._button_run.set_sensitive(enabled)

    self._dialog.set_focus(self._button_stop)

  def _on_dialog_key_press_event(self, dialog, event):
    if not dialog.get_mapped():
      return False

    if Gdk.keyval_name(event.keyval) == 'Escape':
      stopped = common.stop_batcher(self._batcher)
      return stopped

    return False

  @staticmethod
  def _on_dialog_delete_event(_dialog, _event):
    Gtk.main_quit()

  @staticmethod
  def _on_button_close_clicked(_button):
    Gtk.main_quit()

  def _on_button_stop_clicked(self, _button):
    common.stop_batcher(self._batcher)

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
    self._batcher = None

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
      export_context_manager=common.handle_gui_in_export,
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

  def _on_button_stop_clicked(self, _button):
    common.stop_batcher(self._batcher)

  def _on_dialog_delete_event(self, _dialog, _event):
    common.stop_batcher(self._batcher)
