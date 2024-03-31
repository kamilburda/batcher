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

import pygimplib as pg
from pygimplib import pdb

from src import actions as actions_
from src.gui.entry import entries as entries_


class ActionBrowser:

  _DIALOG_SIZE = 550, 450
  _HPANED_POSITION = 230

  _CONTENTS_BORDER_WIDTH = 6
  _VBOX_BROWSER_SPACING = 6
  _HBOX_SEARCH_BAR_SPACING = 6

  _COLUMNS = (
    _COLUMN_ACTION_NAME,
    _COLUMN_ACTION_TYPE,
    _COLUMN_ACTION) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_STRING],
    [2, GObject.TYPE_PYOBJECT])

  def __init__(self, builtin_actions=None, builtin_actions_text=None, title=None):
    self._builtin_actions = builtin_actions
    self._builtin_actions_text = builtin_actions_text
    self._title = title

    self._parent_tree_iters = {}

    self._predefined_parent_tree_iter_names = [
      ('plug_ins', _('Plug-ins')),
      ('gimp_procedures', _('GIMP Procedures')),
      ('file_load_procedures', _('File Load Procedures')),
      ('file_save_procedures', _('File Save Procedures')),
    ]

    self._contents_filled = False

    self._init_gui()

    self._entry_search.connect('changed', self._on_entry_search_changed)
    self._entry_search.connect('icon-press', self._on_entry_search_icon_press)

  @property
  def widget(self):
    return self._dialog

  def fill_contents_if_empty(self):
    if self._contents_filled:
      return

    self._contents_filled = True

    if self._builtin_actions is not None:
      self._parent_tree_iters['builtin_actions'] = self._tree_model.append(
        None,
        [self._builtin_actions_text,
         'builtin_actions',
         None])

      for action_dict in self._builtin_actions.values():
        self._tree_model.append(
          self._parent_tree_iters['builtin_actions'],
          [action_dict['display_name'],
           'builtin_actions',
           action_dict])

    for name, display_name in self._predefined_parent_tree_iter_names:
      self._parent_tree_iters[name] = self._tree_model.append(
        None,
        [display_name,
         name,
         None])

    pdb_procedures = [
      Gimp.get_pdb().lookup_procedure(name)
      for name in pdb.gimp_pdb_query('', '', '', '', '', '', '')]

    procedure_dicts = [
      actions_.get_action_dict_for_pdb_procedure(procedure) for procedure in pdb_procedures]

    # Taken from: https://stackoverflow.com/q/3071415
    sorted_indexes = sorted(
      range(len(procedure_dicts)),
      key=lambda index_: procedure_dicts[index_]['display_name'].lower())

    for index in sorted_indexes:
      procedure = pdb_procedures[index]
      procedure_dict = procedure_dicts[index]

      if (procedure_dict['name'].startswith('file-')
            and procedure_dict['name'].endswith('-load')):
        action_type = 'file_load_procedures'
      elif (procedure_dict['name'].startswith('file-')
            and procedure_dict['name'].endswith('-save')):
        action_type = 'file_save_procedures'
      elif (procedure_dict['name'].startswith('plug-in-')
            or procedure.get_proc_type() in [
                Gimp.PDBProcType.PLUGIN, Gimp.PDBProcType.EXTENSION, Gimp.PDBProcType.TEMPORARY]):
        action_type = 'plug_ins'
      else:
        action_type = 'gimp_procedures'

      self._tree_model.append(
        self._parent_tree_iters[action_type],
        [procedure_dict['display_name'],
         action_type,
         procedure_dict])

  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
      role=pg.config.PLUGIN_NAME,
    )
    self._dialog.set_default_size(*self._DIALOG_SIZE)

    self._tree_model = Gtk.TreeStore(*[column[1] for column in self._COLUMNS])

    self._tree_view = Gtk.TreeView(
      model=self._tree_model,
      headers_visible=False,
      enable_search=False,
      enable_tree_lines=False,
    )
    self._tree_view.get_selection().set_mode(Gtk.SelectionMode.BROWSE)

    column = Gtk.TreeViewColumn()

    cell_renderer_item_name = Gtk.CellRendererText()
    column.pack_start(cell_renderer_item_name, False)
    column.set_attributes(
      cell_renderer_item_name,
      text=self._COLUMN_ACTION_NAME[0])

    self._tree_view.append_column(column)

    self._scrolled_window_action_list = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window_action_list.add(self._tree_view)

    self._entry_search = entries_.ExtendedEntry(
      expandable=False,
      placeholder_text=_('Search'),
    )
    self._entry_search.set_icon_from_icon_name(
      Gtk.EntryIconPosition.SECONDARY, GimpUi.ICON_EDIT_CLEAR)
    self._entry_search.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)

    self._hbox_search_bar = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_SEARCH_BAR_SPACING,
    )
    self._hbox_search_bar.pack_start(self._entry_search, True, True, 0)

    self._vbox_browser = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._VBOX_BROWSER_SPACING,
    )
    self._vbox_browser.pack_start(self._hbox_search_bar, False, False, 0)
    self._vbox_browser.pack_start(self._scrolled_window_action_list, True, True, 0)

    self._vbox_action = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
    )

    self._scrolled_window_action = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window_action.add(self._vbox_action)

    self._hpaned = Gtk.Paned(
      orientation=Gtk.Orientation.HORIZONTAL,
      wide_handle=True,
      border_width=self._CONTENTS_BORDER_WIDTH,
      position=self._HPANED_POSITION,
    )
    self._hpaned.pack1(self._vbox_browser, True, False)
    self._hpaned.pack2(self._scrolled_window_action, True, True)

    self._dialog.vbox.pack_start(self._hpaned, True, True, 0)

    self._button_add = self._dialog.add_button(_('_Add'), Gtk.ResponseType.OK)
    self._button_close = self._dialog.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self._dialog.set_focus(self._button_close)

    self._set_search_bar_icon_sensitivity()

  def _on_entry_search_changed(self, _entry):
    self._set_search_bar_icon_sensitivity()

  def _set_search_bar_icon_sensitivity(self):
    self._entry_search.set_icon_sensitive(
      Gtk.EntryIconPosition.SECONDARY, self._entry_search.get_text())

  def _on_entry_search_icon_press(self, _entry, _icon_position, _event):
    self._entry_search.set_text('')