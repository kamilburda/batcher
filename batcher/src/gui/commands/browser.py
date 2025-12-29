"""Widget displaying a list of available commands (actions/conditions).

The list includes GIMP PDB procedures.
"""

from typing import Dict, Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GdkPixbuf
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from . import editor as command_editor_

from src import commands as commands_
from src import placeholders as placeholders_
from src import pypdb
from src import setting as setting_
from src import utils
from src.gui import utils as gui_utils_
from src.gui.entry import entries as entries_
from src.pypdb import pdb


class _CommandCategory:

  def __init__(
        self,
        name='',
        display_name='',
        number=0,
        expanded=True,
        tree_iter=None,
  ):
    self.name = name
    self.display_name = display_name
    self.number = number
    self.expanded = expanded
    self.tree_iter = tree_iter

    self.command_rows = []


class _CommandBrowserItemTypes:

  ITEM_TYPES = (
    COMMAND,
    PARENT,
  ) = (0, 1)


class _CommandRow:

  def __init__(
        self,
        type_: _CommandBrowserItemTypes = _CommandBrowserItemTypes.COMMAND,
        category: Optional[_CommandCategory] = None,
        internal_name: str = '',
        name: str = '',
        description: str = '',
        command_dict: Optional[Dict] = None,
        command_editor_widget: Optional[command_editor_.CommandEditorWidget] = None,
        visible_via_search: bool = True,
        visible: bool = True,
        tree_iter: Optional[Gtk.TreeIter] = None,
  ):
    self.type_ = type_
    self.category = category
    self.internal_name = internal_name
    self.name = name
    self.description = description
    self.command_dict = command_dict
    self.command_editor_widget = command_editor_widget
    self.visible_via_search = visible_via_search
    self.visible = visible
    self.tree_iter = tree_iter


class CommandBrowser(GObject.GObject):

  _DIALOG_SIZE = 840, 450
  _HPANED_POSITION = 275

  _ICON_XPAD = 2

  _CONTENTS_BORDER_WIDTH = 6
  _VBOX_BROWSER_SPACING = 6
  _HBOX_SEARCH_BAR_SPACING = 6

  _COMMAND_NAME_WIDTH_CHARS = 25

  _SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS = 100

  _COLUMNS = (
    _COLUMN_COMMAND_NAME,
    _COLUMN_COMMAND_VISIBLE,
    _COLUMN_ICON_PARENT,
    _COLUMN_COMMAND_ROW,
  ) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_PYOBJECT],
  )

  __gsignals__ = {
    'command-selected': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'confirm-add-command': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
    'cancel-add-command': (GObject.SignalFlags.RUN_FIRST, None, ()),
  }

  def __init__(self, title=None, parent=None, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._title = title
    self._parent = parent

    self._command_categories = {
      'filters': _CommandCategory('filters', _('Filters, Layer Effects'), 0, True),
      'plug_ins': _CommandCategory('plug_ins', _('Plug-ins'), 1, True),
      'gimp_procedures': _CommandCategory('gimp_procedures', _('GIMP Procedures'), 2, False),
      'other': _CommandCategory('other', _('Other'), 3, False),
    }

    self._command_rows = []
    self._command_rows_and_indexes = {}

    self._contents_filled = False

    self._last_search_text = ''

    self._init_gui()

    self._dialog.connect('realize', self._on_dialog_realize)

    self._entry_search.connect('changed', self._on_entry_search_changed)
    self._entry_search.connect('icon-press', self._on_entry_search_icon_press)

    self._button_search_settings.connect('clicked', self._on_button_search_settings_clicked)

    for menu_item in self._menu_search_settings.get_children():
      if isinstance(menu_item, Gtk.CheckMenuItem):
        menu_item.connect('toggled', self._update_visibility_and_category_expanded_state)

    self._tree_model_sorted.connect('sort-column-changed', self._on_tree_model_sort_column_changed)
    self._tree_view_selection_changed_event_handler_id = self._tree_view.get_selection().connect(
      'changed', self._on_tree_view_selection_changed)
    self._tree_view.connect('button-press-event', self._on_tree_view_button_press_event)
    self._tree_view.connect('key-press-event', self._on_tree_view_key_press_event)

    self._dialog.connect('show', self._on_dialog_show)
    self._dialog.connect('response', self._on_dialog_response)

  @property
  def widget(self):
    return self._dialog

  @property
  def paned(self):
    return self._hpaned

  def select_command_by_internal_name(self, internal_name):
    def _is_command_with_internal_name(command_row):
      return (
        command_row.type_ == _CommandBrowserItemTypes.COMMAND
        and command_row.visible
        and command_row.internal_name == internal_name
      )

    self._select_first_matching_command(_is_command_with_internal_name)

  def fill_contents_if_empty(self):
    if self._contents_filled:
      return

    GObject.signal_handler_block(
      self._tree_view.get_selection(),
      self._tree_view_selection_changed_event_handler_id,
    )

    self._contents_filled = True

    def is_file_load_procedure(name_):
      return (name_.startswith('file-')
              and (name_.endswith('-load') or name_.endswith('-load-thumb')))

    def is_file_export_procedure(name_):
      return (name_.startswith('file-')
              and (name_.endswith('-export')
                   or name_.endswith('-export-internal')
                   or name_.endswith('-export-multi')))

    def is_gegl_operation_internal(name_):
      operation_categories = Gegl.Operation.get_key(name_, 'categories')

      if operation_categories:
        return any(
          operation_category in ['input', 'output', 'programming']
          for operation_category in operation_categories.split(':'))
      else:
        return False

    def is_gegl_operation_hidden(name_):
      operation_categories = Gegl.Operation.get_key(name_, 'categories')

      if operation_categories:
        return 'hidden' in operation_categories.split(':')
      else:
        return False

    def is_procedure_gimp_plugin(procedure_):
      return (
        isinstance(procedure_, pypdb.GimpPDBProcedure)
        and procedure_.proc.get_proc_type() in [
          Gimp.PDBProcType.PLUGIN, Gimp.PDBProcType.PERSISTENT, Gimp.PDBProcType.TEMPORARY]
      )

    for category_name, category in self._command_categories.items():
      command_row = _CommandRow(
        type_=_CommandBrowserItemTypes.PARENT,
        category=self._command_categories[category_name],
        internal_name=category_name,
        name=category.display_name,
      )

      category.tree_iter = self._tree_model.append([
          command_row.name,
          command_row.visible,
          self._get_icons_based_on_expanded_state(category)[0],
          command_row,
      ])

      command_row.tree_iter = category.tree_iter

      self._command_rows.append(command_row)

    pdb_procedures = [
      pdb[name]
      for name in pdb.list_all_gegl_operations()
      if not is_gegl_operation_internal(name)
    ]

    pdb_procedures.extend(
      pdb[name]
      for name in pdb.list_all_gimp_pdb_procedures()
      if not is_file_load_procedure(name) and not is_file_export_procedure(name)
    )

    command_dicts = [
      commands_.get_command_dict_from_pdb_procedure(procedure) for procedure in pdb_procedures]

    for procedure, command_dict in zip(pdb_procedures, command_dicts):
      # We are sanitizing the command name as it can contain characters not
      # allowed in `setting.Setting`. We therefore prefer 'function'
      # if it is a string as that is kept unprocessed.
      if isinstance(command_dict['function'], str):
        procedure_name = command_dict['function']
      else:
        procedure_name = command_dict['name']

      if isinstance(procedure, pypdb.GeglProcedure):
        if not is_gegl_operation_hidden(procedure_name):
          category_name = 'filters'
        else:
          category_name = 'other'
      elif procedure_name.startswith('file-'):
        category_name = 'other'
      elif procedure_name.startswith('plug-in-') or is_procedure_gimp_plugin(procedure):
        if self._has_plugin_procedure_image_or_drawable_arguments(command_dict):
          category_name = 'plug_ins'
        else:
          category_name = 'other'
      else:
        category_name = 'gimp_procedures'

      if command_dict['display_name'] != procedure_name:
        display_name = command_dict['display_name']
      else:
        display_name = None

      # This prevents certain procedures from triggering undesired behavior
      #  (e.g. displaying a layer copy as a new image).
      command_dict['enabled'] = False

      category = self._command_categories[category_name]

      command_row = _CommandRow(
        type_=_CommandBrowserItemTypes.COMMAND,
        category=category,
        internal_name=procedure_name,
        name=display_name if display_name is not None else procedure_name,
        description=command_dict.get('description', ''),
        command_dict=command_dict,
        command_editor_widget=None,
      )

      tree_iter = self._tree_model.append([
          command_row.name,
          command_row.visible,
          None,
          command_row,
      ])

      command_row.tree_iter = tree_iter

      self._command_rows.append(command_row)
      category.command_rows.append(command_row)

    self._sort_command_rows()

    GObject.signal_handler_unblock(
      self._tree_view.get_selection(),
      self._tree_view_selection_changed_event_handler_id,
    )

    self._select_first_visible_command()

  def _select_first_visible_command(self):
    def _is_visible_command(command_row):
      return command_row.type_ == _CommandBrowserItemTypes.COMMAND and command_row.visible

    self._select_first_matching_command(_is_visible_command)

  def _select_first_matching_command(self, predicate):
    tree_iter = next(
      iter(
        command_row.tree_iter for command_row in self._command_rows
        if predicate(command_row)
      ),
      None,
    )

    if tree_iter is None:
      return

    path = self._tree_model.get_path(tree_iter)

    filter_path = self._tree_model_filter.convert_child_path_to_path(path)
    if filter_path is None:
      return

    sorted_path = self._tree_model_sorted.convert_child_path_to_path(filter_path)
    if sorted_path is None:
      return

    self._tree_view.get_selection().select_path(sorted_path)
    self._tree_view.scroll_to_cell(sorted_path, None, True, 0.5, 0.0)

  def _get_selected_command(self, tree_model=None, selected_iter=None):
    if tree_model is None and selected_iter is None:
      tree_model, selected_iter = self._tree_view.get_selection().get_selected()

    if selected_iter is not None:
      command_row = tree_model[selected_iter][self._COLUMN_COMMAND_ROW[0]]

      selected_child_iter = tree_model.convert_iter_to_child_iter(selected_iter)

      if command_row.command_dict is not None:
        if command_row.command_editor_widget is None:
          command_row.command_editor_widget = self._add_command_editor_widget(
            command_row.command_dict, tree_model, selected_child_iter)

        return (
          command_row.command_dict,
          command_row.command_editor_widget.command,
          command_row.command_editor_widget,
          tree_model,
          selected_child_iter,
        )
      else:
        return None, None, None, tree_model, selected_child_iter
    else:
      return None, None, None, tree_model, None

  def _has_plugin_procedure_image_or_drawable_arguments(self, command_dict):
    if not command_dict['arguments']:
      return False

    if len(command_dict['arguments']) == 1:
      return self._is_command_argument_image_drawable_or_drawables(command_dict['arguments'][0])

    if (self._is_command_argument_run_mode(command_dict['arguments'][0])
        and self._is_command_argument_image_drawable_or_drawables(command_dict['arguments'][1])):
      return True

    if self._is_command_argument_image_drawable_or_drawables(command_dict['arguments'][0]):
      return True

    return False

  @staticmethod
  def _is_command_argument_run_mode(command_argument):
    return (
      command_argument['type'] == setting_.EnumSetting
      and command_argument['name'] == 'run-mode')

  @staticmethod
  def _is_command_argument_image_drawable_or_drawables(command_argument):
    return (
      command_argument['type'] in [
        setting_.ImageSetting,
        setting_.LayerSetting,
        setting_.DrawableSetting,
        setting_.ItemSetting,
        placeholders_.PlaceholderImageSetting,
        placeholders_.PlaceholderLayerSetting,
        placeholders_.PlaceholderDrawableSetting,
        placeholders_.PlaceholderItemSetting,
        placeholders_.PlaceholderDrawableArraySetting,
        placeholders_.PlaceholderLayerArraySetting,
        placeholders_.PlaceholderItemArraySetting]
      or (command_argument['type'] == setting_.ArraySetting
          and command_argument['element_type'] in [
              setting_.ImageSetting,
              setting_.LayerSetting,
              setting_.DrawableSetting,
              setting_.ItemSetting])
    )

  def get_collapsed_state_of_categories(self):
    return {category.name: category.expanded for category in self._command_categories.values()}

  def set_collapsed_state_of_categories(self, value):
    for category_name, expanded in value.items():
      category = self._command_categories[category_name]

      # If the tree iter is `None`, it means the browser is not filled yet.
      # The expanded/collapsed state will properly be updated in the GUI once
      # filled.
      if category.tree_iter is not None:
        _current_icon, new_icon = self._get_icons_based_on_expanded_state(category)
        self._tree_model.set_value(category.tree_iter, self._COLUMN_ICON_PARENT[0], new_icon)

      category.expanded = expanded

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
      attached_to=self._parent,
    )
    self._dialog.set_default_size(*self._DIALOG_SIZE)

    self._tree_model = Gtk.ListStore(*[column[1] for column in self._COLUMNS])

    self._tree_view = Gtk.TreeView(
      headers_visible=True,
      enable_search=False,
      enable_tree_lines=False,
    )
    self._tree_view.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

    self._column_name = Gtk.TreeViewColumn()
    self._column_name.set_resizable(True)
    self._column_name.set_title(_('Name'))

    self._icon_arrow_down = gui_utils_.get_icon_pixbuf(
      'pan-down', self._tree_view, Gtk.IconSize.MENU)
    self._icon_arrow_end = gui_utils_.get_icon_pixbuf(
      'pan-end', self._tree_view, Gtk.IconSize.MENU)

    cell_renderer_icon_parent = Gtk.CellRendererPixbuf(
      xpad=self._ICON_XPAD,
    )
    self._column_name.pack_start(cell_renderer_icon_parent, False)
    self._column_name.set_attributes(
      cell_renderer_icon_parent,
      pixbuf=self._COLUMN_ICON_PARENT[0],
    )

    cell_renderer_command_name = Gtk.CellRendererText(
      width_chars=self._COMMAND_NAME_WIDTH_CHARS,
      ellipsize=Pango.EllipsizeMode.END,
    )
    self._column_name.pack_start(cell_renderer_command_name, False)
    self._column_name.set_attributes(
      cell_renderer_command_name,
      text=self._COLUMN_COMMAND_NAME[0],
    )
    self._column_name.set_sort_column_id(self._COLUMN_COMMAND_NAME[0])

    self._tree_view.append_column(self._column_name)

    self._tree_model_filter = Gtk.TreeModelFilter(child_model=self._tree_model)
    self._tree_model_filter.set_visible_column(self._COLUMN_COMMAND_VISIBLE[0])

    self._tree_model_sorted = Gtk.TreeModelSort.new_with_model(self._tree_model_filter)
    self._tree_model_sorted.set_sort_func(
      self._COLUMN_COMMAND_NAME[0], self._sort_commands_by_name)
    self._tree_model_sorted.set_sort_column_id(
      self._COLUMN_COMMAND_NAME[0], Gtk.SortType.ASCENDING)

    self._tree_view.set_model(self._tree_model_sorted)

    self._entry_search = entries_.ExtendedEntry(
      placeholder_text=_('Search'),
    )
    self._entry_search.set_icon_from_icon_name(
      Gtk.EntryIconPosition.SECONDARY, GimpUi.ICON_EDIT_CLEAR)
    self._entry_search.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)

    self._button_search_settings = Gtk.Button(
      image=Gtk.Image.new_from_icon_name('pan-down', Gtk.IconSize.BUTTON),
      relief=Gtk.ReliefStyle.NONE,
    )

    self._menu_item_by_name = Gtk.CheckMenuItem(
      label=_('by name'),
      active=True,
    )
    self._menu_item_by_internal_name = Gtk.CheckMenuItem(
      label=_('by internal name'),
      active=True,
    )
    self._menu_item_by_description = Gtk.CheckMenuItem(
      label=_('by description'),
      active=True,
    )

    self._menu_search_settings = Gtk.Menu()
    self._menu_search_settings.append(self._menu_item_by_name)
    self._menu_search_settings.append(self._menu_item_by_internal_name)
    self._menu_search_settings.append(self._menu_item_by_description)
    self._menu_search_settings.show_all()

    self._hbox_search_bar = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_SEARCH_BAR_SPACING,
    )
    self._hbox_search_bar.pack_start(self._entry_search, True, True, 0)
    self._hbox_search_bar.pack_start(self._button_search_settings, False, False, 0)

    self._scrolled_window_command_list = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window_command_list.add(self._tree_view)

    self._vbox_browser = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._VBOX_BROWSER_SPACING,
    )
    self._vbox_browser.pack_start(self._hbox_search_bar, False, False, 0)
    self._vbox_browser.pack_start(self._scrolled_window_command_list, True, True, 0)

    self._scrolled_window_command_arguments = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window_command_arguments_viewport = Gtk.Viewport(shadow_type=Gtk.ShadowType.NONE)
    self._scrolled_window_command_arguments.add(self._scrolled_window_command_arguments_viewport)

    self._scrolled_window_command_arguments.show_all()
    self._scrolled_window_command_arguments.set_no_show_all(True)
    self._scrolled_window_command_arguments.hide()

    self._label_no_selection = Gtk.Label(
      label='<i>{}</i>'.format(_('Select an action')),
      xalign=0.5,
      yalign=0.5,
      use_markup=True,
    )
    self._label_no_selection.show()
    self._label_no_selection.set_no_show_all(True)

    self._hbox_command = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_command.pack_start(self._scrolled_window_command_arguments, True, True, 0)
    self._hbox_command.pack_start(self._label_no_selection, True, True, 0)

    self._hpaned = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
      border_width=self._CONTENTS_BORDER_WIDTH,
      position=self._HPANED_POSITION,
    )
    self._hpaned.pack1(self._vbox_browser, True, False)
    self._hpaned.pack2(self._hbox_command, True, True)

    self._dialog.vbox.pack_start(self._hpaned, True, True, 0)

    self._button_add = self._dialog.add_button(_('_Add'), Gtk.ResponseType.OK)
    self._button_close = self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._dialog.set_focus(self._entry_search)

    self._set_search_bar_icon_sensitivity()

  def _sort_commands_by_name(self, tree_model, first_iter, second_iter, _user_data):
    sort_type = self._get_sort_type()

    first_category_number, first_name = self._get_sort_column_key(
      tree_model[first_iter][self._COLUMN_COMMAND_ROW[0]], sort_type)
    second_category_number, second_name = self._get_sort_column_key(
      tree_model[second_iter][self._COLUMN_COMMAND_ROW[0]], sort_type)

    if (first_category_number, first_name) > (second_category_number, second_name):
      return 1
    elif (first_category_number, first_name) == (second_category_number, second_name):
      return 0
    else:
      return -1

  def _get_sort_column_key(self, command_row, sort_type):
    if command_row.type_ == _CommandBrowserItemTypes.COMMAND:
      name = command_row.name.lower()
    else:
      name = ''

    category_number = command_row.category.number

    if sort_type == Gtk.SortType.DESCENDING:
      category_number = len(self._command_categories) - category_number - 1
      if command_row.type_ == _CommandBrowserItemTypes.PARENT:
        # Make sure parents precede items in the same category.
        category_number += 1

    return category_number, name

  def _get_sort_type(self):
    return self._tree_model_sorted.get_sort_column_id()[1]

  def _sort_command_rows(self):
    self._command_rows.sort(
      key=self._get_sort_column_key_from_internal_name,
      reverse=self._get_sort_type() == Gtk.SortType.DESCENDING,
    )

    self._command_rows_and_indexes = {
      command_row: index for index, command_row in enumerate(self._command_rows)}

  def _get_sort_column_key_from_internal_name(self, command_row):
    return self._get_sort_column_key(command_row, self._get_sort_type())

  def _on_dialog_realize(self, dialog):
    dialog.set_transient_for(gui_utils_.get_toplevel_window(self._parent))

  def _on_entry_search_changed(self, entry):
    entry_text = entry.get_text()

    if entry_text == self._last_search_text:
      return

    self._last_search_text = entry_text

    self._set_search_bar_icon_sensitivity()

    self._update_search_results()

  def _set_search_bar_icon_sensitivity(self):
    self._entry_search.set_icon_sensitive(
      Gtk.EntryIconPosition.SECONDARY, self._entry_search.get_text())

  def _update_search_results(self, *_args):
    utils.timeout_add_strict(
      self._SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS,
      self._update_visibility_and_category_expanded_state,
    )

  def _update_visibility_and_category_expanded_state(self, *_args, origin='search'):
    GObject.signal_handler_block(
      self._tree_view.get_selection(),
      self._tree_view_selection_changed_event_handler_id,
    )

    search_queries = self._get_search_queries()

    tree_model, selected_iter = self._tree_view.get_selection().get_selected()
    selected_command_row = None

    if origin == 'search':
      if selected_iter is not None:
        selected_command_row = tree_model[selected_iter][self._COLUMN_COMMAND_ROW[0]]
        selected_visible_via_search = self._get_row_visibility_based_on_search(
          search_queries, selected_command_row)

        should_select_different_command = (
          not (selected_visible_via_search and selected_command_row.category.expanded))
      else:
        should_select_different_command = True
    else:
      should_select_different_command = False

    row_to_select = None

    if selected_command_row is not None:
      start_index = self._command_rows_and_indexes[selected_command_row]

      for command_row in self._command_rows[start_index:]:
        row_to_select = self._update_row_and_category_properties(
          command_row,
          origin,
          search_queries,
          should_select_different_command,
          row_to_select,
        )
    else:
      start_index = None

    for command_row in self._command_rows[:start_index]:
      row_to_select = self._update_row_and_category_properties(
        command_row,
        origin,
        search_queries,
        should_select_different_command,
        row_to_select,
      )

    for category in self._command_categories.values():
      num_command_rows_visible_via_search_per_category = [
        command_row.visible_via_search for command_row in category.command_rows].count(True)
      category.visible = num_command_rows_visible_via_search_per_category > 0
      self._tree_model.set_value(
        category.tree_iter, self._COLUMN_COMMAND_VISIBLE[0], category.visible)

    if should_select_different_command and row_to_select is not None:
      self._select_command(row_to_select, origin)

    GObject.signal_handler_unblock(
      self._tree_view.get_selection(),
      self._tree_view_selection_changed_event_handler_id,
    )

    # We manually emit the handler here as it was suppressed up to this point.
    # The handler is emitted regardless of whether the selection needs to be
    # changed or not.
    self._tree_view.get_selection().emit('changed')

  def _update_row_and_category_properties(
        self,
        command_row,
        origin,
        search_queries,
        should_select_different_command,
        row_to_select,
  ):
    row = self._tree_model[command_row.tree_iter]

    if command_row.type_ == _CommandBrowserItemTypes.PARENT:
      return row_to_select

    if origin == 'search':
      visible_via_search = self._get_row_visibility_based_on_search(search_queries, command_row)
      command_row.visible_via_search = visible_via_search
    else:
      visible_via_search = command_row.visible_via_search

    if visible_via_search:
      if should_select_different_command and row_to_select is None:
        if origin == 'search':
          row_to_select = row

          if not command_row.category.expanded:
            _current_icon, new_icon = self._get_icons_based_on_expanded_state(command_row.category)
            self._tree_model.set_value(
              command_row.category.tree_iter, self._COLUMN_ICON_PARENT[0], new_icon)

            command_row.category.expanded = True
        else:
          if command_row.category.expanded:
            row_to_select = row

    command_row.visible = visible_via_search and command_row.category.expanded

    row[self._COLUMN_COMMAND_VISIBLE[0]] = command_row.visible

    return row_to_select

  def _get_row_visibility_based_on_search(self, search_queries, command_row):
    if not search_queries:
      return True

    enabled_search_criteria = []
    if self._menu_item_by_name.get_active():
      enabled_search_criteria.append(self._process_text_for_search(command_row.name))
    if self._menu_item_by_internal_name.get_active():
      enabled_search_criteria.append(self._process_text_for_search(command_row.internal_name))
    if self._menu_item_by_description.get_active():
      enabled_search_criteria.append(self._process_text_for_search(command_row.description))

    if enabled_search_criteria:
      visible = False
      for search_query in search_queries:
        visible = visible or any(search_query in text for text in enabled_search_criteria)

      return visible
    else:
      return True

  def _get_search_queries(self):
    query_str = self._process_text_for_search(self._entry_search.get_text())

    return query_str.split()

  @staticmethod
  def _process_text_for_search(text):
    return text.replace('_', '-').lower()

  def _select_command(self, row_to_select, origin):
    converted_filter_path = self._tree_model_filter.convert_child_path_to_path(row_to_select.path)
    if converted_filter_path is None:
      return

    converted_path = self._tree_model_sorted.convert_child_path_to_path(converted_filter_path)
    if converted_path is None:
      return

    if origin == 'search':
      self._tree_view.set_cursor(converted_path)
    else:
      self._tree_view.get_selection().select_path(converted_path)

  def _on_entry_search_icon_press(self, _entry, _icon_position, _event):
    self._entry_search.set_text('')

  def _on_button_search_settings_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_search_settings, button)

  def _on_tree_model_sort_column_changed(self, _tree_model):
    self._sort_command_rows()

  def _on_tree_view_selection_changed(self, selection):
    model, selected_iter = selection.get_selected()

    if selected_iter is not None:
      _command_dict, command, command_editor_widget, _model, _iter = (
        self._get_selected_command(model, selected_iter))

      self.emit('command-selected', command)

      self._detach_command_editor_widget()

      if command_editor_widget is not None:
        self._label_no_selection.hide()
        self._attach_command_editor_widget(command_editor_widget)
        self._scrolled_window_command_arguments.show()
        self._button_add.set_sensitive(True)
      else:
        self._scrolled_window_command_arguments.hide()
        self._label_no_selection.show()
        self._button_add.set_sensitive(False)
    else:
      self._scrolled_window_command_arguments.hide()
      self._label_no_selection.show()
      self._button_add.set_sensitive(False)

      self.emit('command-selected', None)

  def _on_tree_view_button_press_event(self, _tree_view, event):
    if event.type != Gdk.EventType.BUTTON_PRESS:
      return False

    result = self._tree_view.get_path_at_pos(int(event.x), int(event.y))

    if not result:
      return False

    path, column, x, y = result

    command_row = self._tree_model_sorted[path][self._COLUMN_COMMAND_ROW[0]]

    if command_row.type_ == _CommandBrowserItemTypes.COMMAND:
      return False

    if column != self._column_name:
      return False

    current_icon, new_icon = self._get_icons_based_on_expanded_state(command_row.category)

    if x >= (current_icon.get_width() + self._ICON_XPAD * 2):
      return False

    self._expand_collapse_commands_under_category(
      self._tree_model, command_row.category.tree_iter, command_row.category, new_icon)

    return True

  def _on_tree_view_key_press_event(self, _tree_view, event):
    if event.type != Gdk.EventType.KEY_PRESS:
      return False

    if event.keyval not in [Gdk.KEY_space, Gdk.KEY_Return]:
      return False

    tree_model, tree_iter = self._tree_view.get_selection().get_selected()

    if tree_iter is None:
      return False

    command_row = tree_model[tree_iter][self._COLUMN_COMMAND_ROW[0]]

    if command_row.type_ == _CommandBrowserItemTypes.COMMAND:
      return False

    _current_icon, new_icon = self._get_icons_based_on_expanded_state(command_row.category)

    converted_iter = tree_model.convert_iter_to_child_iter(tree_iter)

    self._expand_collapse_commands_under_category(
      tree_model.get_model(), converted_iter, command_row.category, new_icon)

    return True

  def _get_icons_based_on_expanded_state(self, category):
    if category.expanded:
      return self._icon_arrow_down, self._icon_arrow_end
    else:
      return self._icon_arrow_end, self._icon_arrow_down

  def _expand_collapse_commands_under_category(self, tree_model, tree_iter, category, new_icon):
    tree_model.set_value(tree_iter, self._COLUMN_ICON_PARENT[0], new_icon)

    category.expanded = not category.expanded

    self._update_visibility_and_category_expanded_state(origin='expand_category')

  def _on_dialog_show(self, _dialog):
    self._tree_view.get_selection().emit('changed')

  def _on_dialog_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      command_dict, command, command_editor_widget, model, selected_child_iter = (
        self._get_selected_command())

      if command is not None:
        self._detach_command_editor_widget()
        self._remove_command_editor_widget(model, selected_child_iter)

        self.emit('confirm-add-command', command, command_editor_widget)

        new_command_editor_widget = self._add_command_editor_widget(
          command_dict, model, selected_child_iter)
        self._attach_command_editor_widget(new_command_editor_widget)

        dialog.hide()
    else:
      self.emit('cancel-add-command')
      dialog.hide()

  def _attach_command_editor_widget(self, command_editor_widget):
    command_editor_widget.widget.show_all()
    self._scrolled_window_command_arguments_viewport.add(command_editor_widget.widget)

  def _detach_command_editor_widget(self):
    viewport_child = self._scrolled_window_command_arguments_viewport.get_child()

    if viewport_child is not None:
      self._scrolled_window_command_arguments_viewport.remove(viewport_child)

  def _add_command_editor_widget(self, command_dict, tree_model, selected_child_iter):
    command = commands_.create_command(command_dict)

    command.initialize_gui(only_null=True)

    command_row = tree_model.get_model()[selected_child_iter][self._COLUMN_COMMAND_ROW[0]]

    command_row.command_editor_widget = command_editor_.CommandEditorWidget(
      command, self.widget, show_additional_settings=True)

    return command_row.command_editor_widget

  def _remove_command_editor_widget(self, tree_model, selected_child_iter):
    command_row = tree_model.get_model()[selected_child_iter][self._COLUMN_COMMAND_ROW[0]]

    command_row.command_editor_widget = None


GObject.type_register(CommandBrowser)
