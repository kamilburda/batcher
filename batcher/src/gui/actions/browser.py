"""Widget displaying a list of available actions (procedures/constraints).

The list includes GIMP PDB procedures.
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg
from pygimplib import pdb

from . import editor as action_editor_
from . import utils as action_utils_

from src import actions as actions_
from src import placeholders as placeholders_
from src.gui.entry import entries as entries_


class ActionBrowser(GObject.GObject):

  _DIALOG_SIZE = 675, 450
  _HPANED_POSITION = 325

  _CONTENTS_BORDER_WIDTH = 6
  _VBOX_BROWSER_SPACING = 6
  _HBOX_SEARCH_BAR_SPACING = 6

  _ARROW_ICON_PIXEL_SIZE = 12

  _ACTION_NAME_WIDTH_CHARS = 25

  _SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS = 100

  _COLUMNS = (
    _COLUMN_ACTION_NAME,
    _COLUMN_ACTION_MENU_NAME,
    _COLUMN_ACTION_DESCRIPTION,
    _COLUMN_ACTION_TYPE,
    _COLUMN_ACTION_DICT,
    _COLUMN_ACTION_EDITOR_WIDGET) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_STRING],
    [2, GObject.TYPE_STRING],
    [3, GObject.TYPE_STRING],
    [4, GObject.TYPE_PYOBJECT],
    [5, GObject.TYPE_PYOBJECT])

  __gsignals__ = {
    'action-selected': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'confirm-add-action': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
    'cancel-add-action': (GObject.SignalFlags.RUN_FIRST, None, ()),
  }

  def __init__(self, title=None, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._title = title

    self._parent_tree_iters = {}

    self._predefined_parent_tree_iter_names = [
      'plug_ins',
      'gimp_procedures',
      'file_load_procedures',
      'file_save_procedures',
      'other',
    ]
    self._predefined_parent_tree_iter_display_names = [
      _('Plug-ins'),
      _('GIMP Procedures'),
      _('File Load Procedures'),
      _('File Save Procedures'),
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

    # We pre-sort procedure names so that the column with these names will
    # appear sorted for entries without a menu name (corresponding to the column
    # used for sorting by default).
    pdb_procedures = [
      Gimp.get_pdb().lookup_procedure(name)
      for name in sorted(pdb.gimp_pdb_query('', '', '', '', '', '', ''))]

    action_dicts = [
      actions_.get_action_dict_for_pdb_procedure(procedure) for procedure in pdb_procedures]

    for procedure, action_dict in zip(pdb_procedures, action_dicts):
      if (action_dict['name'].startswith('file-')
          and (action_dict['name'].endswith('-load') or '-load-' in action_dict['name'])):
        action_type = 'file_load_procedures'
      elif (action_dict['name'].startswith('file-')
            and (action_dict['name'].endswith('-save') or '-save-' in action_dict['name'])):
        action_type = 'file_save_procedures'
      elif (action_dict['name'].startswith('plug-in-')
            or procedure.get_proc_type() in [
                Gimp.PDBProcType.PLUGIN, Gimp.PDBProcType.EXTENSION, Gimp.PDBProcType.TEMPORARY]):
        if self._has_plugin_procedure_image_or_drawable_arguments(action_dict):
          action_type = 'plug_ins'
        else:
          action_type = 'other'
      else:
        action_type = 'gimp_procedures'

      if action_dict['display_name'] != action_dict['name']:
        display_name = action_dict['display_name']
      else:
        display_name = ''

      # This prevents certain procedures from triggering undesired behavior
      #  (e.g. displaying a layer copy as a new image).
      action_dict['enabled'] = False

      self._tree_model.append(
        self._parent_tree_iters[action_type],
        [action_dict['name'],
         display_name,
         action_utils_.get_action_description(procedure, action_dict),
         action_type,
         action_dict,
         None])

    self._tree_view.expand_row(
      self._tree_model[self._predefined_parent_tree_iter_names.index('plug_ins')].path,
      False)
    self._tree_view.expand_row(
      self._tree_model[self._predefined_parent_tree_iter_names.index('gimp_procedures')].path,
      False)

    first_selectable_row = self._tree_model[0].iterchildren().next()
    if first_selectable_row is not None:
      self._currently_filling_contents = True

      self._tree_view.set_cursor(first_selectable_row.path)

      self._currently_filling_contents = False

  def _get_selected_action(self, model=None, selected_iter=None):
    if model is None and selected_iter is None:
      model, selected_iter = self._tree_view.get_selection().get_selected()

    if selected_iter is not None:
      row = Gtk.TreeModelRow(model, selected_iter)

      action_dict = row[self._COLUMN_ACTION_DICT[0]]
      action_editor_widget = row[self._COLUMN_ACTION_EDITOR_WIDGET[0]]

      selected_child_iter = model.convert_iter_to_child_iter(selected_iter)

      if action_dict is not None:
        if action_editor_widget is None:
          action_editor_widget = self._add_action_editor_widget_to_model(
            action_dict, model, selected_child_iter)

        return (
          action_dict,
          action_editor_widget.action,
          action_editor_widget,
          model,
          selected_child_iter,
        )
      else:
        return None, None, None, model, selected_child_iter
    else:
      return None, None, None, model, None

  def _has_plugin_procedure_image_or_drawable_arguments(self, action_dict):
    if not action_dict['arguments']:
      return False

    if len(action_dict['arguments']) == 1:
      return self._is_action_argument_image_drawable_or_drawables(action_dict['arguments'][0])

    if (self._is_action_argument_run_mode(action_dict['arguments'][0])
        and self._is_action_argument_image_drawable_or_drawables(action_dict['arguments'][1])):
      return True

    if self._is_action_argument_image_drawable_or_drawables(action_dict['arguments'][0]):
      return True

    return False

  @staticmethod
  def _is_action_argument_run_mode(action_argument):
    return (
      action_argument['type'] == pg.setting.EnumSetting
      and action_argument['enum_type'] == Gimp.RunMode.__gtype__)

  @staticmethod
  def _is_action_argument_image_drawable_or_drawables(action_argument):
    return (
      action_argument['type'] in [
        pg.setting.ImageSetting,
        pg.setting.LayerSetting,
        pg.setting.DrawableSetting,
        pg.setting.ItemSetting,
        placeholders_.PlaceholderImageSetting,
        placeholders_.PlaceholderLayerSetting,
        placeholders_.PlaceholderDrawableSetting,
        placeholders_.PlaceholderItemSetting,
        placeholders_.PlaceholderDrawableArraySetting,
        placeholders_.PlaceholderLayerArraySetting,
        placeholders_.PlaceholderItemArraySetting]
      or (action_argument['type'] == pg.setting.ArraySetting
          and action_argument['element_type'] in [
              pg.setting.ImageSetting,
              pg.setting.LayerSetting,
              pg.setting.DrawableSetting,
              pg.setting.ItemSetting])
    )

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
      role=pg.config.PLUGIN_NAME,
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
    column_name.set_sort_column_id(self._COLUMN_ACTION_NAME[0])

    cell_renderer_action_name = Gtk.CellRendererText(
      width_chars=self._ACTION_NAME_WIDTH_CHARS,
      ellipsize=Pango.EllipsizeMode.END,
    )
    column_name.pack_start(cell_renderer_action_name, False)
    column_name.set_attributes(
      cell_renderer_action_name,
      text=self._COLUMN_ACTION_NAME[0])

    self._tree_view.append_column(column_name)

    column_menu_name = Gtk.TreeViewColumn()
    column_menu_name.set_resizable(True)
    column_menu_name.set_title(_('Menu Name'))
    column_menu_name.set_sort_column_id(self._COLUMN_ACTION_MENU_NAME[0])

    cell_renderer_action_menu_name = Gtk.CellRendererText(
      width_chars=self._ACTION_NAME_WIDTH_CHARS,
      ellipsize=Pango.EllipsizeMode.END,
    )
    column_menu_name.pack_start(cell_renderer_action_menu_name, False)
    column_menu_name.set_attributes(
      cell_renderer_action_menu_name,
      text=self._COLUMN_ACTION_MENU_NAME[0])

    self._tree_view.append_column(column_menu_name)

    self._tree_model_filter = Gtk.TreeModelFilter(child_model=self._tree_model)
    self._tree_model_filter.set_visible_func(self._get_row_visibility_based_on_search_query)

    self._tree_model_sorted = Gtk.TreeModelSort.new_with_model(self._tree_model_filter)
    self._tree_model_sorted.set_sort_func(
      self._COLUMN_ACTION_NAME[0], self._sort_actions_by_name)
    self._tree_model_sorted.set_sort_func(
      self._COLUMN_ACTION_MENU_NAME[0], self._sort_actions_by_menu_name)
    self._tree_model_sorted.set_sort_column_id(
      self._COLUMN_ACTION_MENU_NAME[0], Gtk.SortType.ASCENDING)

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

    self._scrolled_window_action_list = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window_action_list.add(self._tree_view)

    self._vbox_browser = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._VBOX_BROWSER_SPACING,
    )
    self._vbox_browser.pack_start(self._hbox_search_bar, False, False, 0)
    self._vbox_browser.pack_start(self._scrolled_window_action_list, True, True, 0)

    self._scrolled_window_action_arguments = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )

    self._label_no_selection = Gtk.Label(
      label='<i>{}</i>'.format(_('Select a procedure')),
      xalign=0.5,
      yalign=0.5,
      use_markup=True,
    )
    self._label_no_selection.show()
    self._label_no_selection.set_no_show_all(True)

    self._hbox_action = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
    )
    self._hbox_action.pack_start(self._scrolled_window_action_arguments, True, True, 0)
    self._hbox_action.pack_start(self._label_no_selection, True, True, 0)

    self._hpaned = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
      border_width=self._CONTENTS_BORDER_WIDTH,
      position=self._HPANED_POSITION,
    )
    self._hpaned.pack1(self._vbox_browser, True, False)
    self._hpaned.pack2(self._hbox_action, True, True)

    self._dialog.vbox.pack_start(self._hpaned, True, True, 0)

    self._button_add = self._dialog.add_button(_('_Add'), Gtk.ResponseType.OK)
    self._button_close = self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._dialog.set_focus(self._entry_search)

    self._set_search_bar_icon_sensitivity()

  def _get_row_visibility_based_on_search_query(self, model, iter, _data):
    row = Gtk.TreeModelRow(model, iter)

    processed_search_query = self._process_text_for_search(self._entry_search.get_text())

    # Do not filter parents
    if model.iter_parent(iter) is None:
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

  def _sort_actions_by_name(self, model, first_iter, second_iter, _user_data):
    first_row = Gtk.TreeModelRow(model, first_iter)
    first_name = first_row[self._COLUMN_ACTION_NAME[0]]
    first_type = first_row[self._COLUMN_ACTION_TYPE[0]]

    second_row = Gtk.TreeModelRow(model, second_iter)
    second_name = second_row[self._COLUMN_ACTION_NAME[0]]
    second_type = second_row[self._COLUMN_ACTION_TYPE[0]]

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

  def _sort_actions_by_menu_name(self, model, first_iter, second_iter, _user_data):
    first_row = Gtk.TreeModelRow(model, first_iter)
    first_name = first_row[self._COLUMN_ACTION_MENU_NAME[0]]
    first_type = first_row[self._COLUMN_ACTION_TYPE[0]]

    second_row = Gtk.TreeModelRow(model, second_iter)
    second_name = second_row[self._COLUMN_ACTION_MENU_NAME[0]]
    second_type = second_row[self._COLUMN_ACTION_TYPE[0]]

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
    pg.invocation.timeout_add_strict(
      self._SEARCH_QUERY_CHANGED_TIMEOUT_MILLISECONDS,
      lambda: self._tree_model_filter.refilter(),  # Wrap `gi.FunctionInfo` as it is unhashable
    )

  def _set_search_bar_icon_sensitivity(self):
    self._entry_search.set_icon_sensitive(
      Gtk.EntryIconPosition.SECONDARY, self._entry_search.get_text())

  def _on_entry_search_icon_press(self, _entry, _icon_position, _event):
    self._entry_search.set_text('')

  def _on_button_search_settings_clicked(self, button):
    pg.gui.menu_popup_below_widget(self._menu_search_settings, button)

  def _on_tree_view_selection_changed(self, selection):
    model, selected_iter = selection.get_selected()

    if selected_iter is not None and model.iter_parent(selected_iter) is not None:
      _action_dict, action, action_editor_widget, _model, _iter = self._get_selected_action(
        model, selected_iter)

      if not self._currently_filling_contents:
        self.emit('action-selected', action)

      self._label_no_selection.hide()

      self._detach_action_editor_widget()

      self._attach_action_editor_widget(action_editor_widget)

      self._scrolled_window_action_arguments.show()
    else:
      self._label_no_selection.show()
      self._scrolled_window_action_arguments.hide()

      if not self._currently_filling_contents:
        self.emit('action-selected', None)

  def _on_dialog_show(self, _dialog):
    model, selected_iter = self._tree_view.get_selection().get_selected()

    if selected_iter is not None and model.iter_parent(selected_iter) is not None:
      _action_dict, action, action_editor_widget, _model, _iter = self._get_selected_action(
        model, selected_iter)

      self.emit('action-selected', action)
    else:
      self.emit('action-selected', None)

  def _on_dialog_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      action_dict, action, action_editor_widget, model, selected_child_iter = (
        self._get_selected_action())

      if action is not None:
        self._detach_action_editor_widget()
        self._remove_action_editor_widget_from_model(model, selected_child_iter)

        self.emit('confirm-add-action', action, action_editor_widget)

        new_action_editor_widget = self._add_action_editor_widget_to_model(
          action_dict, model, selected_child_iter)
        self._attach_action_editor_widget(new_action_editor_widget)

        dialog.hide()
    else:
      self.emit('cancel-add-action')
      dialog.hide()

  def _attach_action_editor_widget(self, action_editor_widget):
    action_editor_widget.widget.show_all()
    self._scrolled_window_action_arguments.add(action_editor_widget.widget)
    self._scrolled_window_action_arguments.get_child().set_shadow_type(Gtk.ShadowType.NONE)

  def _detach_action_editor_widget(self):
    for child in self._scrolled_window_action_arguments:
      if isinstance(child, Gtk.Viewport):
        child.remove(child.get_child())
      self._scrolled_window_action_arguments.remove(child)

  def _add_action_editor_widget_to_model(self, action_dict, model, selected_child_iter):
    action = actions_.create_action(action_dict)

    action.initialize_gui(only_null=True)

    action_editor_widget = action_editor_.ActionEditorWidget(
      action, self.widget, show_additional_settings=True)

    model.get_model().set_value(
      selected_child_iter,
      self._COLUMN_ACTION_EDITOR_WIDGET[0],
      action_editor_widget,
    )

    return action_editor_widget

  def _remove_action_editor_widget_from_model(self, model, selected_child_iter):
    model.get_model().set_value(
      selected_child_iter,
      self._COLUMN_ACTION_EDITOR_WIDGET[0],
      None,
    )


GObject.type_register(ActionBrowser)
