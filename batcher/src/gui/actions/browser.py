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

from src.gui.entry import entries as entries_


class ActionBrowser:

  _DIALOG_SIZE = 500, 400
  _HPANED_POSITION = 200

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

  _pdb_procedures = {}

  def __init__(self, builtin_actions=None, title=None):
    self._builtin_actions = builtin_actions
    self._title = title

    self._action_dict = None

    self._init_gui()

    self._entry_search.connect('changed', self._on_entry_search_changed)
    self._entry_search.connect('icon-press', self._on_entry_search_icon_press)

  @classmethod
  def _get_pdb_procedure_dict(cls):
    if not cls._pdb_procedures:
      cls._pdb_procedures = {
        'plug_ins': [],
        'gimp_procedures': [],
      }

      pdb_procedures = [
        Gimp.get_pdb().lookup_procedure(name)
        for name in pdb.gimp_pdb_query('', '', '', '', '', '', '')]

      for pdb_procedure in pdb_procedures:
        if pdb_procedure.get_proc_type() == Gimp.PDBProcType.INTERNAL:
          cls._pdb_procedures['gimp_procedures'].append(pdb_procedure)
        else:
          cls._pdb_procedures['plug_ins'].append(pdb_procedure)

    return cls._pdb_procedures

  @property
  def widget(self):
    return self._dialog

  def fill_contents_if_empty(self):
    if self._action_dict is not None:
      return

    self._action_dict = {'builtin_actions': []}

    if self._builtin_actions is not None:
      for action in self._builtin_actions:
        self._action_dict['builtin_actions'].append(action)

    self._action_dict.update(self._get_pdb_procedure_dict())

    self._fill_tree_view()

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

  def _fill_tree_view(self):
    pass

  def _on_entry_search_changed(self, _entry):
    self._set_search_bar_icon_sensitivity()

  def _set_search_bar_icon_sensitivity(self):
    self._entry_search.set_icon_sensitive(
      Gtk.EntryIconPosition.SECONDARY, self._entry_search.get_text())

  def _on_entry_search_icon_press(self, _entry, _icon_position, _event):
    self._entry_search.set_text('')
