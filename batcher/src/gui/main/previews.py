import os
import pathlib
import pickle

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

from src import itemtree
from src import overwrite
from src import setting as setting_
from src import utils
from src.gui import messages as messages_
from src.gui import utils as gui_utils_
from src.gui.preview import controller as previews_controller_
from src.gui.preview import base as preview_base_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_
from src.gui.widgets import drag_and_drop_context as drag_and_drop_context_
from src.path import fileext

from . import _utils as gui_main_utils_


class Previews:

  _PREVIEWS_GLOBAL_KEY = 'previews_global'
  _PREVIEWS_SENSITIVE_KEY = 'previews_sensitive'
  _VPANED_PREVIEW_SENSITIVE_KEY = 'vpaned_preview_sensitive'

  _DELAY_PREVIEW_UPDATE_MILLISECONDS = 100
  _DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS = 500

  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0

  _FILE_COUNT_FIRST_THRESHOLD = 1000
  _FILE_COUNT_SECOND_THRESHOLD = 10000

  _PREVIEWS_LEFT_MARGIN = 6
  _LABEL_TOP_BUTTONS_SPACING = 8
  _IMPORT_OPTIONS_ICON_LABEL_SPACING = 6
  _NAME_PREVIEW_BUTTONS_SPACING = 3
  _NAME_PREVIEW_PLACEHOLDER_LABEL_PAD = 8
  _NAME_PREVIEW_DRAG_ICON_OFFSET = -8

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
        parent=None,
  ):
    self._settings = settings
    self._batcher_mode = batcher_mode
    self._item_type = item_type
    self._item_tree = item_tree
    self._top_label = top_label
    self._manage_items = manage_items
    self._display_message_func = (
      display_message_func if display_message_func is not None else utils.empty_func)

    self._current_image = current_image
    self._parent = parent

    overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
      overwrite.OverwriteModes.RENAME_NEW)

    self._batcher_for_name_preview = gui_main_utils_.get_batcher_class(self._item_type)(
      item_tree=self._item_tree,
      actions=self._settings['main/actions'],
      conditions=self._settings['main/conditions'],
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

    self._batcher_for_image_preview = gui_main_utils_.get_batcher_class(self._item_type)(
      # This is an empty tree that will be replaced during the preview anyway.
      item_tree=type(self._item_tree)(),
      actions=self._settings['main/actions'],
      conditions=self._settings['main/conditions'],
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

  def close_import_options_dialog(self):
    if self._import_options_dialog is not None:
      self._import_options_dialog.widget.hide()

  def _init_setting_gui(self):
    self._settings['gui/image_preview_automatic_update'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.check_menu_item,
      widget=self._image_preview.menu_item_update_automatically,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/size/paned_between_previews_position'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.paned_position,
      widget=self._vpaned_previews,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  def _init_gui(self):
    self._label_top = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._label_top.set_markup('<b>{}</b>'.format(self._top_label))

    self._button_input_options = Gtk.Button(
      relief=Gtk.ReliefStyle.NONE,
      tooltip_text=_('Options'),
    )
    self._button_input_options.set_image(
      Gtk.Image.new_from_icon_name('pan-down', Gtk.IconSize.BUTTON))

    self._menu_input_options = Gtk.Menu()

    self._settings['gui/show_original_item_names'].set_gui()
    self._menu_input_options.append(self._settings['gui/show_original_item_names'].gui.widget)

    self._hbox_input_options = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._NAME_PREVIEW_BUTTONS_SPACING,
    )

    self._hbox_input_options.pack_end(self._button_input_options, False, False, 0)

    self._hbox_top = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._LABEL_TOP_BUTTONS_SPACING,
    )
    self._hbox_top.pack_start(self._label_top, False, False, 0)
    self._hbox_top.pack_start(self._hbox_input_options, False, False, 0)

    self._import_options_dialog = None

    self._name_preview_drag_and_drop_context = drag_and_drop_context_.DragAndDropContext()
    self._name_preview_drag_dest_row = None
    self._name_preview_row_drop_position = None

    if self._manage_items:
      self._set_up_managing_items()
      upper_widget = self._name_preview_overlay
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
    self._vbox_previews.pack_start(self._hbox_top, False, False, 0)
    self._vbox_previews.pack_start(self._vpaned_previews, True, True, 0)

    self._button_input_options.connect('clicked', self._on_button_input_options_clicked)

  def _set_up_managing_items(self):
    self._name_preview_placeholder_label = Gtk.Label(
      label='<i>{}</i>'.format(
        _('Drop or paste files and folders here, or use the button above to add them')),
      use_markup=True,
      xalign=0.5,
      yalign=0.5,
      width_chars=30,
      max_width_chars=40,
      justify=Gtk.Justification.CENTER,
      wrap=True,
      wrap_mode=Pango.WrapMode.WORD,
      margin_top=self._NAME_PREVIEW_PLACEHOLDER_LABEL_PAD,
      margin_bottom=self._NAME_PREVIEW_PLACEHOLDER_LABEL_PAD,
      margin_start=self._NAME_PREVIEW_PLACEHOLDER_LABEL_PAD,
      margin_end=self._NAME_PREVIEW_PLACEHOLDER_LABEL_PAD,
    )

    self._name_preview_overlay = Gtk.Overlay(
      hexpand=True,
      vexpand=True,
    )
    self._name_preview_overlay.add_overlay(self._name_preview_placeholder_label)
    self._name_preview_overlay.set_overlay_pass_through(self._name_preview_placeholder_label, True)
    self._name_preview_overlay.add(self._name_preview)

    self._menu_item_add_files = Gtk.MenuItem(label=_('Add Files...'), use_underline=False)
    self._menu_item_add_folders = Gtk.MenuItem(label=_('Add Folders...'), use_underline=False)

    self._menu_add = Gtk.Menu()
    self._menu_add.append(self._menu_item_add_files)
    self._menu_add.append(self._menu_item_add_folders)
    self._menu_add.show_all()

    self._button_add = Gtk.Button(
      relief=Gtk.ReliefStyle.NONE,
      tooltip_text=_('Add'),
    )
    self._button_add.set_image(
      Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.BUTTON))

    self._menu_item_remove_selected = Gtk.MenuItem(label=_('Remove Selected'), use_underline=False)
    self._menu_item_remove_all = Gtk.MenuItem(label=_('Remove All'), use_underline=False)

    self._menu_remove = Gtk.Menu()
    self._menu_remove.append(self._menu_item_remove_selected)
    self._menu_remove.append(self._menu_item_remove_all)
    self._menu_remove.show_all()

    self._button_remove = Gtk.Button(
      relief=Gtk.ReliefStyle.NONE,
      tooltip_text=_('Remove'),
    )
    self._button_remove.set_image(
      Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_REMOVE, Gtk.IconSize.BUTTON))

    self._hbox_input_options.pack_start(self._button_add, False, False, 0)
    self._hbox_input_options.pack_start(self._button_remove, False, False, 0)

    self._menu_item_import_options = Gtk.MenuItem()
    self._hbox_menu_item_import_options = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._IMPORT_OPTIONS_ICON_LABEL_SPACING,
    )
    self._hbox_menu_item_import_options.add(
      Gtk.Image.new_from_icon_name('applications-system', Gtk.IconSize.MENU)
    )
    self._hbox_menu_item_import_options.add(
      Gtk.Label(
        label=_('Import Options...'),
        use_underline=False,
      ),
    )
    self._menu_item_import_options.add(self._hbox_menu_item_import_options)
    self._menu_item_import_options.show_all()

    self._menu_input_options.insert(self._menu_item_import_options, 0)
    self._menu_input_options.show_all()

    self._show_hide_name_preview_placeholder_label()

    self._button_add.connect('clicked', self._on_button_add_clicked)
    self._menu_item_add_files.connect(
      'activate', self._on_menu_item_add_files_activate, _('Add Files'))
    self._menu_item_add_folders.connect(
      'activate', self._on_menu_item_add_folders_activate, _('Add Folders'))
    self._button_remove.connect('clicked', self._on_button_remove_clicked)
    self._menu_item_remove_selected.connect(
      'activate', self._on_menu_item_remove_selected_clicked)
    self._menu_item_remove_all.connect(
      'activate', self._on_menu_item_remove_all_clicked)
    self._menu_item_import_options.connect('activate', self._on_menu_item_import_options_clicked)

    self._name_preview.tree_view.connect(
      'key-press-event', self._on_name_preview_key_press_event)
    self._name_preview.tree_view.connect(
      'key-release-event', self._on_name_preview_key_release_event)

    self._name_preview_drag_and_drop_context.setup_drag(
      self._name_preview.tree_view,
      self._name_preview_get_drag_data,
      self._name_preview_drag_data_received,
      get_drag_icon_func=self._name_preview_get_drag_icon,
      # We must remove the default drag highlight as otherwise the empty space
      # would be highlighted while drag-and-dropping.
      dest_defaults=Gtk.DestDefaults.ALL & ~Gtk.DestDefaults.HIGHLIGHT,
      target_flags=Gtk.TargetFlags.SAME_WIDGET,
      additional_dest_targets=[
        Gtk.TargetEntry.new(target_name, 0, 0)
        for target_name in gui_utils_.get_external_drag_data_sources()
      ],
    )

    self._name_preview.tree_view.connect('drag-end', self._on_name_preview_drag_end)
    self._name_preview.tree_view.connect('drag-motion', self._on_name_preview_drag_motion)
    self._name_preview.tree_view.connect('draw', self._on_name_preview_draw)

    # We also need to set up the drag destination for external data sources
    # for the overlay, presumably because the overlay, if displayed, prevents
    # the underlying widget from receiving drag data.
    self._name_preview_overlay.connect(
      'drag-data-received', self._on_name_preview_overlay_drag_data_received)
    self._name_preview_overlay.drag_dest_set(
      Gtk.DestDefaults.ALL,
      [
        Gtk.TargetEntry.new(target_name, 0, 0)
        for target_name in gui_utils_.get_external_drag_data_sources()
      ],
      Gdk.DragAction.MOVE)

    self._connect_import_setting_events()

  def _name_preview_get_drag_data(self):
    return pickle.dumps(self._name_preview.selected_items)

  def _name_preview_drag_data_received(self, selection_data):
    if selection_data.get_target().name() in gui_utils_.get_external_drag_data_sources():
      self._add_paths_from_drag_data_to_name_preview_if_any(selection_data)
    else:
      if self._name_preview_drag_dest_row is None:
        return

      reference_item = self._name_preview.get_item_from_path(self._name_preview_drag_dest_row)

      if reference_item is None:
        return

      insertion_mode = 'after'

      if self._name_preview_row_drop_position is not None:
        if (self._name_preview_row_drop_position in [
              Gtk.TreeViewDropPosition.BEFORE, Gtk.TreeViewDropPosition.INTO_OR_BEFORE]):
          insertion_mode = 'before'
        elif self._name_preview_row_drop_position == Gtk.TreeViewDropPosition.INTO_OR_AFTER:
          insertion_mode = 'after'
        elif self._name_preview_row_drop_position == Gtk.TreeViewDropPosition.AFTER:
          if self._name_preview.batcher.item_tree.next(reference_item) is not None:
            insertion_mode = 'after'
          else:
            insertion_mode = 'last_top_level'

      selected_item_keys = pickle.loads(selection_data.get_data())
      self._name_preview.reorder_items(selected_item_keys, reference_item, insertion_mode)

  def _name_preview_get_drag_icon(self, _widget, drag_context):
    if self._name_preview.selected_items:
      # TODO: Replace with a proper widget
      #  * For multiple selected items, display all rows
      icon = Gtk.Image.new_from_icon_name('applications-system', Gtk.IconSize.BUTTON)
      icon.show_all()

      Gtk.drag_set_icon_widget(
        drag_context,
        icon,
        self._NAME_PREVIEW_DRAG_ICON_OFFSET,
        self._NAME_PREVIEW_DRAG_ICON_OFFSET,
      )

  def _on_name_preview_draw(self, _tree_view, cairo_context):
    if self._name_preview_drag_dest_row:
      Gtk.TreeView.do_draw(self._name_preview.tree_view, cairo_context)

      reference_item = self._name_preview.get_item_from_path(self._name_preview_drag_dest_row)

      if reference_item is None or reference_item.key in self._name_preview.selected_items:
        return True

      reference_item_parents_keys = [item.key for item in reference_item.parents]
      if any(item_key in reference_item_parents_keys
             for item_key in self._name_preview.selected_items):
        return True

      name_preview_style_context = self._name_preview.tree_view.get_style_context()
      drag_highlight_color = name_preview_style_context.get_color(Gtk.StateFlags.DROP_ACTIVE)

      rectangle = self._name_preview.tree_view.get_background_area(
        self._name_preview_drag_dest_row, self._name_preview.get_tree_view_column())

      line_width = 0.5
      # This makes the drag highlight line crispier.
      line_offset = 0.5 * line_width

      line_start_x = rectangle.x + line_offset
      line_end_x = line_start_x + rectangle.width
      line_y = rectangle.y + line_offset

      cairo_context.set_source_rgba(
        drag_highlight_color.red,
        drag_highlight_color.green,
        drag_highlight_color.blue,
        drag_highlight_color.alpha,
      )
      cairo_context.set_line_width(line_width)

      is_drop_into_or_after = (
        self._name_preview_row_drop_position == Gtk.TreeViewDropPosition.INTO_OR_AFTER)
      is_drop_after = self._name_preview_row_drop_position == Gtk.TreeViewDropPosition.AFTER

      if is_drop_into_or_after or is_drop_after:
        line_y += rectangle.height - 1

      is_reference_item_last = self._name_preview.batcher.item_tree.next(reference_item) is None
      if is_reference_item_last and is_drop_after:
        line_y += 1

      cairo_context.move_to(line_start_x, line_y)
      cairo_context.line_to(line_end_x, line_y)
      cairo_context.stroke()

      if reference_item.type == itemtree.TYPE_FOLDER and (is_drop_into_or_after or is_drop_after):
        upper_line_y = line_y - (rectangle.height - 1)

        cairo_context.move_to(line_start_x, upper_line_y)
        cairo_context.line_to(line_end_x, upper_line_y)
        cairo_context.stroke()

      return True
    else:
      return False

  def _on_name_preview_drag_motion(self, _widget, _context, x, y, _timestamp):
    result = self._name_preview.tree_view.get_dest_row_at_pos(x, y)

    if result is not None:
      self._name_preview_drag_dest_row = result[0]
      self._name_preview_row_drop_position = result[1]

      self._name_preview.tree_view.queue_draw()

  def _on_name_preview_drag_end(self, _tree_view, _drag_context):
    self._name_preview_drag_dest_row = None
    self._name_preview_row_drop_position = None

    self._name_preview.tree_view.queue_draw()

  def _on_name_preview_overlay_drag_data_received(
        self,
        _widget,
        _drag_context,
        _drop_x,
        _drop_y,
        selection_data,
        _info,
        _timestamp,
  ):
    self._add_paths_from_drag_data_to_name_preview_if_any(selection_data)

  def _add_paths_from_drag_data_to_name_preview_if_any(self, selection_data):
    paths = gui_utils_.get_paths_from_drag_data(selection_data)
    if paths:
      self._add_items_to_name_preview(paths)

  def _connect_import_setting_events(self):
    for setting in self._settings['main/import']:
      setting.connect_event('value-changed', self._update_previews_on_import_options_change)

  def _update_previews_on_import_options_change(self, _setting):
    if self._name_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._name_preview.update)

    if self._image_preview is not None:
      utils.timeout_add_strict(
        self._DELAY_PREVIEW_UPDATE_MILLISECONDS,
        self._image_preview.update)

  def _on_button_add_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_add, button)

  def _on_menu_item_add_files_activate(self, _menu_item, title):
    filepaths = self._get_paths(Gtk.FileChooserAction.OPEN, title)
    if filepaths:
      self._add_items_to_name_preview(filepaths)

  def _on_menu_item_add_folders_activate(self, _menu_item, title):
    dirpaths = self._get_paths(Gtk.FileChooserAction.SELECT_FOLDER, title)
    if dirpaths:
      self._add_items_to_name_preview(dirpaths)

  def _on_button_remove_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_remove, button)

  def _on_menu_item_remove_selected_clicked(self, _menu_item):
    self._name_preview.remove_selected_items()

  def _on_menu_item_remove_all_clicked(self, _menu_item):
    self._name_preview.remove_all_items()

  def _on_menu_item_import_options_clicked(self, _menu_item):
    if self._import_options_dialog is None:
      self._import_options_dialog = gui_main_utils_.ImportExportOptionsDialog(
        self._settings['main/import'],
        title=_('Import Options'),
        parent=self._parent,
      )

      self._import_options_dialog.widget.show()
    else:
      self._import_options_dialog.widget.show()
      self._import_options_dialog.widget.present()

  def _on_button_input_options_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_input_options, button)

  def _on_name_preview_key_press_event(self, _tree_view, event):
    key_name = Gdk.keyval_name(event.keyval)

    if key_name == 'v' and (event.state & Gdk.ModifierType.CONTROL_MASK):  # ctrl + V
      clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

      paths = gui_utils_.get_paths_from_clipboard(clipboard)
      if paths:
        self._add_items_to_name_preview(paths)
    elif key_name == 'c' and (event.state & Gdk.ModifierType.CONTROL_MASK):  # ctrl + C
      clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

      item_tree = self._name_preview.batcher.item_tree
      clipboard.set_text(
        os.linesep.join([
          item_tree[item_key].id for item_key in self._name_preview.selected_items
          if item_key in item_tree]),
        -1,
      )

      self._display_message_func(
        _('Copied the selected images and folders as text.'),
        Gtk.MessageType.INFO)

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
            ' Are you sure you want to continue?').format(dirpath_))

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
          _('<b>WARNING:</b> You are about to add more than {} files.'
            ' To be on the safe side, check if you added the files or folders you really wanted.'
            ' Do you want to continue?').format(
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
      parent=gui_utils_.get_toplevel_window(self._vbox_previews),
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
    file_dialog = Gtk.FileChooserNative(
      title=title,
      action=file_chooser_action,
      select_multiple=True,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self._vbox_previews),
    )

    paths = []

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.ACCEPT:
      paths = file_dialog.get_filenames()

    file_dialog.destroy()

    return paths

  def connect_events(self, command_lists, paned_outside_previews):
    self._vpaned_previews.connect(
      'notify::position',
      self._on_paned_between_previews_notify_position)

    paned_outside_previews.connect(
      'notify::position',
      self._on_paned_outside_previews_notify_position)

    self._image_preview.connect('preview-updated', self._on_image_preview_updated, command_lists)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated, command_lists)

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
        utils.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        utils.timeout_remove(self._image_preview.update)
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
        utils.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        utils.timeout_remove(self._image_preview.update)
        self._image_preview.resize()

    self._paned_between_previews_previous_position = current_position

  def _enable_preview_on_paned_drag(
        self,
        preview: preview_base_.Preview,
        preview_sensitive_setting: setting_.Setting,
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
        preview_sensitive_setting: setting_.Setting,
        update_lock_key: str,
  ):
    preview.lock_update(True, update_lock_key)
    preview.set_sensitive(False)
    preview_sensitive_setting.set_value(False)

  def _on_image_preview_updated(self, _preview, _error, update_duration_seconds, command_lists):
    command_lists.display_warnings_and_tooltips_for_commands_and_deactivate_failing_commands(
      self._batcher_for_image_preview)

    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)

      self._display_message_func(
        _('The preview no longer updates automatically as rendering takes too long.'),
        Gtk.MessageType.INFO)

  def _on_name_preview_updated(self, _preview, _error, command_lists):
    if self._manage_items:
      self._show_hide_name_preview_placeholder_label()
      self._update_file_format_import_options()

    command_lists.display_warnings_and_tooltips_for_commands_and_deactivate_failing_commands(
      self._batcher_for_name_preview, clear_previous=False)

  def _show_hide_name_preview_placeholder_label(self):
    if len(self._name_preview.tree_view.get_model()) <= 0:
      self._name_preview_placeholder_label.show()
    else:
      self._name_preview_placeholder_label.hide()

  def _update_file_format_import_options(self):
    file_extensions = set(
      fileext.get_file_extension(item.orig_name).lower()
      for item in self._name_preview.batcher.item_tree.iter(with_folders=False)
    )

    # Ignore files with no extension
    file_extensions.discard('')
    file_extensions = sorted(file_extensions)

    self._settings['main/import/file_format_import_options'].set_active_file_formats(
      file_extensions)
