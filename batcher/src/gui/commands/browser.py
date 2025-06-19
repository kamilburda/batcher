"""Widget displaying a list of available commands (actions/conditions).

The list includes GIMP PDB procedures.
"""

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
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


class CommandBrowser(GObject.GObject):

  _DIALOG_SIZE = 675, 450
  _HPANED_POSITION = 325

  _CONTENTS_BORDER_WIDTH = 6
  _VBOX_BROWSER_SPACING = 6
  _HBOX_SEARCH_BAR_SPACING = 6

  _ARROW_ICON_PIXEL_SIZE = 12

  _COMMAND_NAME_WIDTH_CHARS = 25

  _SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS = 100

  _COLUMNS = (
    _COLUMN_COMMAND_NAME,
    _COLUMN_COMMAND_MENU_NAME,
    _COLUMN_COMMAND_DESCRIPTION,
    _COLUMN_COMMAND_TYPE,
    _COLUMN_COMMAND_DICT,
    _COLUMN_COMMAND_EDITOR_WIDGET) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_STRING],
    [2, GObject.TYPE_STRING],
    [3, GObject.TYPE_STRING],
    [4, GObject.TYPE_PYOBJECT],
    [5, GObject.TYPE_PYOBJECT])

  __gsignals__ = {
    'command-selected': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'confirm-add-command': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
    'cancel-add-command': (GObject.SignalFlags.RUN_FIRST, None, ()),
  }

  def __init__(self, title=None, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._title = title

    self._parent_tree_iters = {}

    self._predefined_parent_tree_iter_names = [
      'filters',
      'plug_ins',
      'gimp_procedures',
      'other',
    ]
    self._predefined_parent_tree_iter_display_names = [
      _('Filters, Effects'),
      _('Plug-ins'),
      _('GIMP Procedures'),
      _('Other'),
    ]

    self._contents_filled = False
    self._currently_filling_contents = False

    self._init_gui()

    self._entry_search.connect('changed', self._on_entry_search_changed)
    self._entry_search.connect('icon-press', self._on_entry_search_icon_press)

    self._button_search_settings.connect('clicked', self._on_button_search_settings_clicked)

    for menu_item in self._menu_search_settings.get_children():
      if isinstance(menu_item, Gtk.CheckMenuItem):
        menu_item.connect('toggled', self._update_search_results)

    self._tree_view.get_selection().connect('changed', self._on_tree_view_selection_changed)

    self._dialog.connect('show', self._on_dialog_show)
    self._dialog.connect('response', self._on_dialog_response)

  @property
  def widget(self):
    return self._dialog

  @property
  def paned(self):
    return self._hpaned

  def select_command(self, name):
    parents = [self._tree_model_sorted]

    while parents:
      parent = parents.pop(0)

      for row in parent:
        if row[0] == name:
          converted_path = self._tree_model_filter.convert_child_path_to_path(row.path)
          self._tree_view.get_selection().select_iter(row.iter)
          self._tree_view.scroll_to_cell(converted_path, None, True, 0.5, 0.0)
          return

        parents.append(row.iterchildren())

  def fill_contents_if_empty(self):
    if self._contents_filled:
      return

    self._contents_filled = True

    for name, display_name in zip(
          self._predefined_parent_tree_iter_names, self._predefined_parent_tree_iter_display_names):
      self._parent_tree_iters[name] = self._tree_model.append(
        None,
        [display_name,
         '',
         '',
         name,
         None,
         None])

    def is_file_load_procedure(name_):
      return (name_.startswith('file-')
              and (name_.endswith('-load') or name_.endswith('-load-thumb')))

    def is_file_export_procedure(name_):
      return (name_.startswith('file-')
              and (name_.endswith('-export')
                   or name_.endswith('-export-internal')
                   or name_.endswith('-export-multi')))

    def is_gegl_operation_internal(name_):
      categories = Gegl.Operation.get_key(name_, 'categories')

      if categories:
        return any(
          category in ['input', 'output', 'programming']
          for category in categories.split(':'))
      else:
        return False

    def is_gegl_operation_hidden(name_):
      categories = Gegl.Operation.get_key(name_, 'categories')

      if categories:
        return 'hidden' in categories.split(':')
      else:
        return False

    def is_procedure_gimp_plugin(procedure_):
      return (
        isinstance(procedure_, pypdb.GimpPDBProcedure)
        and procedure_.proc.get_proc_type() in [
          Gimp.PDBProcType.PLUGIN, Gimp.PDBProcType.PERSISTENT, Gimp.PDBProcType.TEMPORARY]
      )

    # We pre-sort procedure names so that the column with these names will
    # appear sorted for entries without a menu name (corresponding to the column
    # used for sorting by default).
    pdb_procedures = [
      pdb[name]
      for name in sorted(pdb.list_all_gegl_operations())
      if not is_gegl_operation_internal(name)
    ]

    pdb_procedures.extend(
      pdb[name]
      for name in sorted(pdb.list_all_gimp_pdb_procedures())
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
          command_type = 'filters'
        else:
          command_type = 'other'
      elif procedure_name.startswith('file-'):
        command_type = 'other'
      elif procedure_name.startswith('plug-in-') or is_procedure_gimp_plugin(procedure):
        if self._has_plugin_procedure_image_or_drawable_arguments(command_dict):
          command_type = 'plug_ins'
        else:
          command_type = 'other'
      else:
        command_type = 'gimp_procedures'

      if command_dict['display_name'] != procedure_name:
        display_name = command_dict['display_name']
      else:
        display_name = ''

      # This prevents certain procedures from triggering undesired behavior
      #  (e.g. displaying a layer copy as a new image).
      command_dict['enabled'] = False

      self._tree_model.append(
        self._parent_tree_iters[command_type],
        [procedure_name,
         display_name,
         command_dict.get('description', ''),
         command_type,
         command_dict,
         None])

    self._tree_view.expand_row(
      self._tree_model[self._predefined_parent_tree_iter_names.index('filters')].path,
      False)

    first_selectable_path = self._tree_model[0].path
    first_selectable_path.down()

    self._currently_filling_contents = True

    self._tree_view.set_cursor(first_selectable_path)

    self._currently_filling_contents = False

  def _get_selected_command(self, model=None, selected_iter=None):
    if model is None and selected_iter is None:
      model, selected_iter = self._tree_view.get_selection().get_selected()

    if selected_iter is not None:
      row = Gtk.TreeModelRow(model, selected_iter)

      command_dict = row[self._COLUMN_COMMAND_DICT[0]]
      command_editor_widget = row[self._COLUMN_COMMAND_EDITOR_WIDGET[0]]

      selected_child_iter = model.convert_iter_to_child_iter(selected_iter)

      if command_dict is not None:
        if command_editor_widget is None:
          command_editor_widget = self._add_command_editor_widget_to_model(
            command_dict, model, selected_child_iter)

        return (
          command_dict,
          command_editor_widget.command,
          command_editor_widget,
          model,
          selected_child_iter,
        )
      else:
        return None, None, None, model, selected_child_iter
    else:
      return None, None, None, model, None

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

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
    )
    self._dialog.set_default_size(*self._DIALOG_SIZE)

    self._tree_model = Gtk.TreeStore(*[column[1] for column in self._COLUMNS])

    self._tree_view = Gtk.TreeView(
      headers_visible=True,
      enable_search=False,
      enable_tree_lines=False,
    )
    self._tree_view.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

    column_name = Gtk.TreeViewColumn()
    column_name.set_resizable(True)
    column_name.set_title(_('Name'))
    column_name.set_sort_column_id(self._COLUMN_COMMAND_NAME[0])

    cell_renderer_command_name = Gtk.CellRendererText(
      width_chars=self._COMMAND_NAME_WIDTH_CHARS,
      ellipsize=Pango.EllipsizeMode.END,
    )
    column_name.pack_start(cell_renderer_command_name, False)
    column_name.set_attributes(
      cell_renderer_command_name,
      text=self._COLUMN_COMMAND_NAME[0])

    self._tree_view.append_column(column_name)

    column_menu_name = Gtk.TreeViewColumn()
    column_menu_name.set_resizable(True)
    column_menu_name.set_title(_('Menu Name'))
    column_menu_name.set_sort_column_id(self._COLUMN_COMMAND_MENU_NAME[0])

    cell_renderer_command_menu_name = Gtk.CellRendererText(
      width_chars=self._COMMAND_NAME_WIDTH_CHARS,
      ellipsize=Pango.EllipsizeMode.END,
    )
    column_menu_name.pack_start(cell_renderer_command_menu_name, False)
    column_menu_name.set_attributes(
      cell_renderer_command_menu_name,
      text=self._COLUMN_COMMAND_MENU_NAME[0])

    self._tree_view.append_column(column_menu_name)

    self._tree_model_filter = Gtk.TreeModelFilter(child_model=self._tree_model)
    self._tree_model_filter.set_visible_func(self._get_row_visibility_based_on_search_query)

    self._tree_model_sorted = Gtk.TreeModelSort.new_with_model(self._tree_model_filter)
    self._tree_model_sorted.set_sort_func(
      self._COLUMN_COMMAND_NAME[0], self._sort_commands_by_name)
    self._tree_model_sorted.set_sort_func(
      self._COLUMN_COMMAND_MENU_NAME[0], self._sort_commands_by_menu_name)
    self._tree_model_sorted.set_sort_column_id(
      self._COLUMN_COMMAND_MENU_NAME[0], Gtk.SortType.ASCENDING)

    self._tree_view.set_model(self._tree_model_sorted)

    self._entry_search = entries_.ExtendedEntry(
      expandable=False,
      placeholder_text=_('Search'),
    )
    self._entry_search.set_icon_from_icon_name(
      Gtk.EntryIconPosition.SECONDARY, GimpUi.ICON_EDIT_CLEAR)
    self._entry_search.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)

    self._image_drop_down = Gtk.Image.new_from_icon_name('go-down', Gtk.IconSize.BUTTON)
    self._image_drop_down.set_pixel_size(self._ARROW_ICON_PIXEL_SIZE)

    self._button_search_settings = Gtk.Button(
      image=self._image_drop_down,
      relief=Gtk.ReliefStyle.NONE,
    )

    self._menu_item_by_name = Gtk.CheckMenuItem(
      label=_('by name'),
      active=True,
    )
    self._menu_item_by_menu_name = Gtk.CheckMenuItem(
      label=_('by menu name'),
      active=True,
    )
    self._menu_item_by_description = Gtk.CheckMenuItem(
      label=_('by description'),
      active=True,
    )

    self._menu_search_settings = Gtk.Menu()
    self._menu_search_settings.append(self._menu_item_by_name)
    self._menu_search_settings.append(self._menu_item_by_menu_name)
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

  def _get_row_visibility_based_on_search_query(self, model, iter_, _data):
    row = Gtk.TreeModelRow(model, iter_)

    processed_search_query = self._process_text_for_search(self._entry_search.get_text())

    # Do not filter parents
    if model.iter_parent(iter_) is None:
      return True

    enabled_search_criteria = []
    if self._menu_item_by_name.get_active():
      enabled_search_criteria.append(self._process_text_for_search(row[0]))
    if self._menu_item_by_menu_name.get_active():
      enabled_search_criteria.append(self._process_text_for_search(row[1]))
    if self._menu_item_by_description.get_active():
      enabled_search_criteria.append(self._process_text_for_search(row[2]))

    return any(processed_search_query in text for text in enabled_search_criteria)

  @staticmethod
  def _process_text_for_search(text):
    return text.replace('_', '-').lower()

  def _sort_commands_by_name(self, model, first_iter, second_iter, _user_data):
    first_row = Gtk.TreeModelRow(model, first_iter)
    first_name = first_row[self._COLUMN_COMMAND_NAME[0]]
    first_type = first_row[self._COLUMN_COMMAND_TYPE[0]]

    second_row = Gtk.TreeModelRow(model, second_iter)
    second_name = second_row[self._COLUMN_COMMAND_NAME[0]]
    second_type = second_row[self._COLUMN_COMMAND_TYPE[0]]

    if first_type == second_type:
      if first_name < second_name:
        return -1
      elif first_name == second_name:
        return 0
      else:
        return 1
    else:
      # Keep order of parents intact
      return 0

  def _sort_commands_by_menu_name(self, model, first_iter, second_iter, _user_data):
    first_row = Gtk.TreeModelRow(model, first_iter)
    first_name = first_row[self._COLUMN_COMMAND_MENU_NAME[0]]
    first_type = first_row[self._COLUMN_COMMAND_TYPE[0]]

    second_row = Gtk.TreeModelRow(model, second_iter)
    second_name = second_row[self._COLUMN_COMMAND_MENU_NAME[0]]
    second_type = second_row[self._COLUMN_COMMAND_TYPE[0]]

    if first_type == second_type:
      # Treat empty menu name as lower in order
      if first_name != '' and second_name != '':
        if first_name < second_name:
          return -1
        elif first_name == second_name:
          return 0
        else:
          return 1
      elif first_name == '' and second_name == '':
        return 0
      elif first_name == '' and second_name != '':
        return 1
      elif first_name != '' and second_name == '':
        return -1
    else:
      # Keep order of parents intact
      return 0

  def _on_entry_search_changed(self, _entry):
    self._set_search_bar_icon_sensitivity()

    self._update_search_results()

  def _update_search_results(self, *args):
    utils.timeout_add_strict(
      self._SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS,
      lambda: self._tree_model_filter.refilter(),  # Wrap `gi.FunctionInfo` as it is unhashable
    )

  def _set_search_bar_icon_sensitivity(self):
    self._entry_search.set_icon_sensitive(
      Gtk.EntryIconPosition.SECONDARY, self._entry_search.get_text())

  def _on_entry_search_icon_press(self, _entry, _icon_position, _event):
    self._entry_search.set_text('')

  def _on_button_search_settings_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_search_settings, button)

  def _on_tree_view_selection_changed(self, selection):
    model, selected_iter = selection.get_selected()

    if selected_iter is not None and model.iter_parent(selected_iter) is not None:
      _command_dict, command, command_editor_widget, _model, _iter = self._get_selected_command(
        model, selected_iter)

      if not self._currently_filling_contents:
        self.emit('command-selected', command)

      self._label_no_selection.hide()

      self._detach_command_editor_widget()

      self._attach_command_editor_widget(command_editor_widget)

      self._scrolled_window_command_arguments.show()
    else:
      self._label_no_selection.show()
      self._scrolled_window_command_arguments.hide()

      if not self._currently_filling_contents:
        self.emit('command-selected', None)

  def _on_dialog_show(self, _dialog):
    model, selected_iter = self._tree_view.get_selection().get_selected()

    if selected_iter is not None and model.iter_parent(selected_iter) is not None:
      _command_dict, command, command_editor_widget, _model, _iter = self._get_selected_command(
        model, selected_iter)

      self.emit('command-selected', command)
    else:
      self.emit('command-selected', None)

  def _on_dialog_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      command_dict, command, command_editor_widget, model, selected_child_iter = (
        self._get_selected_command())

      if command is not None:
        self._detach_command_editor_widget()
        self._remove_command_editor_widget_from_model(model, selected_child_iter)

        self.emit('confirm-add-command', command, command_editor_widget)

        new_command_editor_widget = self._add_command_editor_widget_to_model(
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

  def _add_command_editor_widget_to_model(self, command_dict, model, selected_child_iter):
    command = commands_.create_command(command_dict)

    command.initialize_gui(only_null=True)

    command_editor_widget = command_editor_.CommandEditorWidget(
      command, self.widget, show_additional_settings=True)

    model.get_model().set_value(
      selected_child_iter,
      self._COLUMN_COMMAND_EDITOR_WIDGET[0],
      command_editor_widget,
    )

    return command_editor_widget

  def _remove_command_editor_widget_from_model(self, model, selected_child_iter):
    model.get_model().set_value(
      selected_child_iter,
      self._COLUMN_COMMAND_EDITOR_WIDGET[0],
      None,
    )


GObject.type_register(CommandBrowser)
