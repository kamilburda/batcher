import os
import pathlib

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import overwrite

from src.gui import messages as messages_
from src.gui import utils as gui_utils_
from src.gui.preview import controller as previews_controller_
from src.gui.preview import base as preview_base_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_


class Previews:

  _PREVIEWS_GLOBAL_KEY = 'previews_global'
  _PREVIEWS_SENSITIVE_KEY = 'previews_sensitive'
  _VPANED_PREVIEW_SENSITIVE_KEY = 'vpaned_preview_sensitive'

  _DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS = 500

  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0

  _FILE_COUNT_FIRST_THRESHOLD = 1000
  _FILE_COUNT_SECOND_THRESHOLD = 10000

  _PREVIEWS_LEFT_MARGIN = 4
  _LABEL_TOP_BOTTOM_MARGIN = 4

  _NAME_PREVIEW_BUTTONS_SPACING = 4
  _BUTTONS_GRID_ROW_SPACING = 3
  _BUTTONS_GRID_COLUMN_SPACING = 3
  _NAME_PREVIEW_BUTTONS_BOTTOM_MARGIN = 4

  def __init__(
        self,
        settings,
        batcher_mode,
        item_type,
        item_tree,
        top_label,
        lock_previews=True,
        manage_items=False,
        display_message_func=None,
        current_image=None,
  ):
    self._settings = settings
    self._batcher_mode = batcher_mode
    self._item_type = item_type
    self._item_tree = item_tree
    self._top_label = top_label
    self._manage_items = manage_items
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._current_image = current_image

    overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
      overwrite.OverwriteModes.RENAME_NEW)

    self._batcher_for_name_preview = gui_utils_.get_batcher_class(self._item_type)(
      item_tree=self._item_tree,
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=self._batcher_mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
      overwrite_chooser=overwrite_chooser)

    self._name_preview = preview_name_.NamePreview(
      self._batcher_for_name_preview,
      self._settings,
      set(self._settings['gui/name_preview_items_collapsed_state'].active_items),
      list(self._settings['gui/selected_items'].active_items),
      initial_cursor_item=(
        next(
          iter(key for key in self._settings['gui/image_preview_displayed_items'].active_items),
          None,
        )
        if self._settings['gui/image_preview_displayed_items'].active_items else None),
    )

    self._batcher_for_image_preview = gui_utils_.get_batcher_class(self._item_type)(
      # This is an empty tree that will be replaced during the preview anyway.
      item_tree=type(self._item_tree)(),
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=self._batcher_mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
      overwrite_chooser=overwrite_chooser)

    self._image_preview = preview_image_.ImagePreview(
      self._batcher_for_image_preview, self._settings)

    self._previews_controller = previews_controller_.PreviewsController(
      self._name_preview, self._image_preview, self._settings, current_image=self._current_image)

    self._paned_outside_previews_previous_position = (
      self._settings['gui/size/paned_outside_previews_position'].value)

    self._paned_between_previews_previous_position = (
      self._settings['gui/size/paned_between_previews_position'].value)

    if lock_previews:
      self.lock()

    self._init_gui()

    self._init_setting_gui()

  @property
  def name_preview(self):
    return self._name_preview

  @property
  def image_preview(self):
    return self._image_preview

  @property
  def controller(self):
    return self._previews_controller

  @property
  def vbox_previews(self):
    return self._vbox_previews

  def lock(self, key=_PREVIEWS_GLOBAL_KEY):
    self._previews_controller.lock_previews(key)

  def unlock(
        self,
        key=_PREVIEWS_GLOBAL_KEY,
        update=True,
        name_preview_update_args=None,
        name_preview_update_kwargs=None,
        image_preview_update_args=None,
        image_preview_update_kwargs=None,
  ):
    self._previews_controller.unlock_previews(
      key,
      update=update,
      name_preview_update_args=name_preview_update_args,
      name_preview_update_kwargs=name_preview_update_kwargs,
      image_preview_update_args=image_preview_update_args,
      image_preview_update_kwargs=image_preview_update_kwargs,
    )

  def _init_setting_gui(self):
    self._settings['gui/image_preview_automatic_update'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.check_menu_item,
      widget=self._image_preview.menu_item_update_automatically,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/size/paned_between_previews_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
      widget=self._vpaned_previews,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  def _init_gui(self):
    self._label_top = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      margin_bottom=self._LABEL_TOP_BOTTOM_MARGIN,
    )
    self._label_top.set_markup('<b>{}</b>'.format(self._top_label))

    if self._manage_items:
      self._set_up_managing_items()
      upper_widget = self._vbox_name_preview_and_buttons
    else:
      upper_widget = self._name_preview

    self._vpaned_previews = Gtk.Paned(
      orientation=Gtk.Orientation.VERTICAL,
      wide_handle=True,
    )
    self._vpaned_previews.pack1(upper_widget, True, True)
    self._vpaned_previews.pack2(self._image_preview, True, True)

    self._vbox_previews = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      margin_start=self._PREVIEWS_LEFT_MARGIN,
    )
    self._vbox_previews.pack_start(self._label_top, False, False, 0)
    self._vbox_previews.pack_start(self._vpaned_previews, True, True, 0)

  def _set_up_managing_items(self):
    self._button_add_files = Gtk.Button(
      label=_('Add _Files...'), use_underline=True, hexpand=True)
    self._button_add_folders = Gtk.Button(
      label=_('Add Fol_ders...'), use_underline=True, hexpand=True)
    self._button_remove_items = Gtk.Button(
      label=_('R_emove'), use_underline=True, hexpand=True)
    self._button_remove_all_items = Gtk.Button(
      label=_('Re_move All'), use_underline=True, hexpand=True)

    self._grid_buttons = Gtk.Grid(
      row_spacing=self._BUTTONS_GRID_ROW_SPACING,
      column_spacing=self._BUTTONS_GRID_COLUMN_SPACING,
      column_homogeneous=True,
      hexpand=True,
    )
    self._grid_buttons.attach(self._button_add_files, 0, 0, 1, 1)
    self._grid_buttons.attach(self._button_add_folders, 1, 0, 1, 1)
    self._grid_buttons.attach(self._button_remove_items, 0, 1, 1, 1)
    self._grid_buttons.attach(self._button_remove_all_items, 1, 1, 1, 1)

    self._vbox_name_preview_and_buttons = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._NAME_PREVIEW_BUTTONS_SPACING,
      margin_bottom=self._NAME_PREVIEW_BUTTONS_BOTTOM_MARGIN,
    )
    self._vbox_name_preview_and_buttons.pack_start(self._name_preview, True, True, 0)
    self._vbox_name_preview_and_buttons.pack_start(self._grid_buttons, False, False, 0)

    self._button_add_files.connect(
      'clicked', self._on_button_add_files_clicked, _('Add Files'))
    self._button_add_folders.connect(
      'clicked', self._on_button_add_folders_clicked, _('Add Folders'))
    self._button_remove_items.connect(
      'clicked', self._on_button_remove_items_clicked)
    self._button_remove_all_items.connect(
      'clicked', self._on_button_remove_all_items_clicked)

    self.name_preview.tree_view.connect(
      'key-press-event', self._on_name_preview_key_press_event)
    self.name_preview.tree_view.connect(
      'key-release-event', self._on_name_preview_key_release_event)

  def _on_button_add_files_clicked(self, _button, title):
    filepaths = self._get_paths(Gtk.FileChooserAction.OPEN, title)
    if filepaths:
      self._add_items_to_name_preview(filepaths)

  def _on_button_add_folders_clicked(self, _button, title):
    dirpaths = self._get_paths(Gtk.FileChooserAction.SELECT_FOLDER, title)
    if dirpaths:
      self._add_items_to_name_preview(dirpaths)

  def _on_button_remove_items_clicked(self, _button):
    self._name_preview.remove_selected_items()

  def _on_button_remove_all_items_clicked(self, _button):
    self._name_preview.remove_all_items()

  def _on_name_preview_key_press_event(self, _tree_view, event):
    key_name = Gdk.keyval_name(event.keyval)

    if key_name == 'v' and (event.state & Gdk.ModifierType.CONTROL_MASK):  # ctrl + V
      clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

      paths = gui_utils_.get_paths_from_clipboard(clipboard)
      if paths:
        self._add_items_to_name_preview(paths)

  def _on_name_preview_key_release_event(self, _tree_view, event):
    key_name = Gdk.keyval_name(event.keyval)

    if key_name == 'Delete':
      modifiers_not_allowed_for_delete = (
        Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK)

      if not (event.state & modifiers_not_allowed_for_delete):
        self._name_preview.remove_selected_items()

  def _add_items_to_name_preview(self, paths):
    can_add = self._check_files_and_warn_if_needed(paths)
    if can_add:
      self._name_preview.add_items(paths)

  def _check_files_and_warn_if_needed(self, paths):
    warned_on_count_first_threshold = False
    warned_on_count_second_threshold = False
    can_continue = True

    def _warn_on_adding_top_level_folder(dirpath_):
      nonlocal can_continue

      if len(pathlib.Path(dirpath_).parts) <= 2:
        can_continue = self._warn_on_adding_items(
          _('You are about to add a top-level folder named "{}".'
            ' Are you sure you want to continue?').format(dirpath))

    def _warn_on_exceeding_file_count_thresholds(path_count_):
      nonlocal warned_on_count_first_threshold
      nonlocal warned_on_count_second_threshold
      nonlocal can_continue

      if not warned_on_count_first_threshold and path_count_ > self._FILE_COUNT_FIRST_THRESHOLD:
        warned_on_count_first_threshold = True

        can_continue = self._warn_on_adding_items(
          _('You are about to add more than {} files. Are you sure you want to continue?').format(
            self._FILE_COUNT_FIRST_THRESHOLD))

        if not can_continue:
          return

      if not warned_on_count_second_threshold and path_count_ > self._FILE_COUNT_SECOND_THRESHOLD:
        warned_on_count_second_threshold = True

        can_continue = self._warn_on_adding_items(
          _(('<b>WARNING:</b> You are about to add more than {} files.'
             ' To be on the safe side, check if you added the files or folders you really wanted.'
             ' Do you want to continue?')).format(
            self._FILE_COUNT_SECOND_THRESHOLD))

        if not can_continue:
          return

    filepaths = []
    dirpaths = []
    for path in paths:
      if os.path.isdir(path):
        dirpaths.append(path)
      else:
        filepaths.append(path)

    path_count = len(filepaths)

    _warn_on_exceeding_file_count_thresholds(path_count)

    if warned_on_count_first_threshold and not can_continue:
      return False

    if warned_on_count_second_threshold:
      return can_continue

    for dirpath in dirpaths:
      _warn_on_adding_top_level_folder(dirpath)

      if not can_continue:
        return False

      for _root_dirpath, _dirnames, filenames in os.walk(dirpath):
        path_count += len(filenames)

        _warn_on_exceeding_file_count_thresholds(path_count)

        if warned_on_count_first_threshold and not can_continue:
          return False

        if warned_on_count_second_threshold:
          return can_continue

    return True

  def _warn_on_adding_items(self, message_markup):
    response_id = messages_.display_alert_message(
      parent=pg.gui.get_toplevel_window(self._vbox_previews),
      message_type=Gtk.MessageType.WARNING,
      modal=True,
      destroy_with_parent=True,
      message_markup=message_markup,
      message_secondary_markup='',
      details=None,
      display_details_initially=False,
      button_texts_and_responses=[(_('Yes'), Gtk.ResponseType.YES), (_('No'), Gtk.ResponseType.NO)],
      response_id_of_button_to_focus=Gtk.ResponseType.NO,
    )

    return response_id == Gtk.ResponseType.YES

  def _get_paths(self, file_chooser_action, title):
    file_dialog = Gtk.FileChooserDialog(
      title=title,
      action=file_chooser_action,
      select_multiple=True,
      modal=True,
      parent=pg.gui.get_toplevel_window(self._vbox_previews),
      transient_for=pg.gui.get_toplevel_window(self._vbox_previews),
    )

    file_dialog.add_buttons(
      _('_Add'), Gtk.ResponseType.OK,
      _('_Cancel'), Gtk.ResponseType.CANCEL)

    paths = []

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.OK:
      paths = file_dialog.get_filenames()

    file_dialog.destroy()

    return paths

  def connect_events(self, action_lists, paned_outside_previews):
    self._vpaned_previews.connect(
      'notify::position',
      self._on_paned_between_previews_notify_position)

    paned_outside_previews.connect(
      'notify::position',
      self._on_paned_outside_previews_notify_position)

    self._image_preview.connect('preview-updated', self._on_image_preview_updated, action_lists)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated, action_lists)

    self._previews_controller.connect_setting_changes_to_previews()

  def _on_paned_outside_previews_notify_position(self, paned, _property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property('max-position')

    if (current_position == max_position
        and self._paned_outside_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
      self._disable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
    elif (current_position != max_position
          and self._paned_outside_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
      self._enable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
    elif current_position != self._paned_outside_previews_previous_position:
      if self._image_preview.is_larger_than_image():
        pg.invocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        pg.invocation.timeout_remove(self._image_preview.update)
        self._image_preview.resize()

    self._paned_outside_previews_previous_position = current_position

  def _on_paned_between_previews_notify_position(self, paned, _property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property('max-position')
    min_position = paned.get_property('min-position')

    if (current_position == max_position
        and self._paned_between_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position != max_position
          and self._paned_between_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position == min_position
          and self._paned_between_previews_previous_position != min_position):
      self._disable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position != min_position
          and self._paned_between_previews_previous_position == min_position):
      self._enable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif current_position != self._paned_between_previews_previous_position:
      if self._image_preview.is_larger_than_image():
        pg.invocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        pg.invocation.timeout_remove(self._image_preview.update)
        self._image_preview.resize()

    self._paned_between_previews_previous_position = current_position

  def _enable_preview_on_paned_drag(
        self,
        preview: preview_base_.Preview,
        preview_sensitive_setting: pg.setting.Setting,
        update_lock_key: str,
  ):
    preview.lock_update(False, update_lock_key)
    preview.add_function_at_update(preview.set_sensitive, True)
    # In case the image preview gets resized, the update would be canceled,
    # hence update always.
    GLib.timeout_add(self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS, preview.update)
    preview_sensitive_setting.set_value(True)

  def _disable_preview_on_paned_drag(
        self,
        preview: preview_base_.Preview,
        preview_sensitive_setting: pg.setting.Setting,
        update_lock_key: str,
  ):
    preview.lock_update(True, update_lock_key)
    preview.set_sensitive(False)
    preview_sensitive_setting.set_value(False)

  def _on_image_preview_updated(self, _preview, _error, update_duration_seconds, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(self._batcher_for_image_preview)

    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)

      self._display_message_func(
        _('The preview no longer updates automatically as rendering takes too long.'),
        Gtk.MessageType.INFO)

  def _on_name_preview_updated(self, _preview, _error, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(
      self._batcher_for_name_preview, clear_previous=False)
