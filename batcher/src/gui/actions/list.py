"""List of actions (procedures/constraints) that can be edited interactively."""

from typing import Any, Dict, Optional, Union

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from . import browser as action_browser_
from . import item as action_item_

from src import actions as actions_


class ActionList(pg.gui.ItemBox):
  """A scrollable vertical list that allows the user to add, edit and remove
  actions interactively.

  An action represents a procedure or constraint that can be applied to a
  GIMP item (image, layer, ...). Actions can be created via the `src.actions`
  module.

  Actions are applied starting from the top (i.e. actions ordered higher take
  precedence).

  The list connects events to the passed actions that keeps the actions and
  the list in sync. For example, when adding an action via `src.actions.add()`,
  the item for the action is automatically added to the list. Conversely, when
  calling `add_item()` from this class, both the action and the item are
  added to the actions and the GUI, respectively.

  Signals:

  * ``'action-list-item-added'`` - An item (action) was added.

    Arguments:

    * The added item.

  * ``'action-list-item-added-interactive'`` - An item (action) was added
    interactively (via `add_item()`).

    Arguments:

    * The added item.

  * ``'action-list-item-reordered'`` - An item (action) was reordered via
    `reorder_item()`.

    Arguments:

    * The reordered item.
    * The new position of the reordered item (starting from 0).

  * ``'action-list-item-removed'`` - An item (action) was removed via
    `remove_item()`.

    Arguments:

    * The removed item.
  """

  __gsignals__ = {
    'action-list-item-added': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'action-list-item-added-interactive': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'action-list-item-reordered': (
      GObject.SignalFlags.RUN_FIRST, None,
      (GObject.TYPE_PYOBJECT, GObject.TYPE_INT)),
    'action-list-item-removed': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
  }

  _ADD_BUTTON_HBOX_SPACING = 6

  _DRAG_ICON_OFFSET = -8

  def __init__(
        self,
        actions: pg.setting.Group,
        builtin_actions: Optional[Dict[str, Any]] = None,
        add_action_text: Optional[str] = None,
        allow_custom_actions: bool = True,
        add_custom_action_text: Optional[str] = None,
        action_browser_text: Optional[str] = None,
        item_spacing: int = pg.gui.ItemBox.ITEM_SPACING,
        **kwargs):
    super().__init__(item_spacing=item_spacing, **kwargs)

    self._actions = actions
    self._builtin_actions = builtin_actions if builtin_actions is not None else {}
    self._add_action_text = add_action_text
    self._allow_custom_actions = allow_custom_actions
    self._add_custom_action_text = add_custom_action_text
    self._action_browser_text = action_browser_text

    if self._allow_custom_actions:
      self._browser = action_browser_.ActionBrowser(title=self._action_browser_text)
    else:
      self._browser = None

    self._init_gui()

    if self._browser is not None:
      self._browser.widget.connect('realize', self._on_action_browser_realize)
      self._browser.widget.connect('response', self._on_action_browser_response)

    self._after_add_action_event_id = self._actions.connect_event(
      'after-add-action',
      lambda _actions, action, orig_action_dict: self._add_item_from_action(
        action))

    self._after_reorder_action_event_id = self._actions.connect_event(
      'after-reorder-action',
      lambda _actions, action, current_position, new_position: (
        self._reorder_action(action, new_position)))

    self._before_remove_action_event_id = self._actions.connect_event(
      'before-remove-action',
      lambda _actions, action: self._remove_action(action))

    self._before_clear_actions_event_id = self._actions.connect_event(
      'before-clear-actions', lambda _actions: self._clear())

  @property
  def actions(self):
    return self._actions

  @property
  def browser(self):
    return self._browser

  def add_item(
        self,
        action_dict_or_pdb_proc_name: Union[Dict[str, Any], str],
  ) -> action_item_.ActionItem:
    self._actions.set_event_enabled(self._after_add_action_event_id, False)
    action = actions_.add(self._actions, action_dict_or_pdb_proc_name)
    self._actions.set_event_enabled(self._after_add_action_event_id, True)

    item = self._add_item_from_action(action)

    self.emit('action-list-item-added-interactive', item)

    return item

  def reorder_item(self, item, new_position):
    processed_new_position = self._reorder_item(item, new_position)

    self._actions.set_event_enabled(self._after_reorder_action_event_id, False)
    actions_.reorder(self._actions, item.action.name, processed_new_position)
    self._actions.set_event_enabled(self._after_reorder_action_event_id, True)

    self.emit('action-list-item-reordered', item, new_position)

  def remove_item(self, item):
    self._remove_item(item)

    self._actions.set_event_enabled(self._before_remove_action_event_id, False)
    actions_.remove(self._actions, item.action.name)
    self._actions.set_event_enabled(self._before_remove_action_event_id, True)

    self.emit('action-list-item-removed', item)

  def _on_action_browser_realize(self, dialog):
    dialog.set_transient_for(pg.gui.get_toplevel_window(self))
    dialog.set_attached_to(pg.gui.get_toplevel_window(self))

  def _on_action_browser_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      procedure_dict = self._browser.get_selected_procedure()

      if procedure_dict is not None:
        self.add_item(procedure_dict)

    dialog.hide()

  def _init_gui(self):
    self._button_add = Gtk.Button(relief=Gtk.ReliefStyle.NONE)

    if self._add_action_text is not None:
      button_hbox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=self._ADD_BUTTON_HBOX_SPACING,
      )
      button_hbox.pack_start(
        Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.MENU),
        False, False, 0)

      label_add = Gtk.Label(
        label=self._add_action_text,
        use_underline=True,
      )
      button_hbox.pack_start(label_add, False, False, 0)

      self._button_add.add(button_hbox)
    else:
      self._button_add.set_image(
        Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.BUTTON))

    self._button_add.connect('clicked', self._on_button_add_clicked)

    self._vbox.pack_start(self._button_add, False, False, 0)

    self._actions_menu = Gtk.Menu()
    # key: tuple of menu path components; value: `Gtk.MenuItem`
    self._builtin_actions_submenus = {}
    self._init_actions_menu_popup()

  def _add_item_from_action(self, action):
    action.initialize_gui()

    item = action_item_.ActionItem(action)

    super().add_item(item)

    self.emit('action-list-item-added', item)

    return item

  def _reorder_action(self, action, new_position):
    item = next(
      (item_ for item_ in self._items if item_.action.name == action.name),
      None)
    if item is not None:
      self._reorder_item(item, new_position)
    else:
      raise ValueError(
        f'action "{action.name}" does not match any item in "{self}"')

  def _reorder_item(self, item, new_position):
    return super().reorder_item(item, new_position)

  def _remove_action(self, action):
    item = next(
      (item_ for item_ in self._items if item_.action.name == action.name),
      None)

    if item is not None:
      self._remove_item(item)
    else:
      raise ValueError(
        f'action "{action.get_path()}" does not match any item in "{self}"')

  def _remove_item(self, item):
    if self._get_item_position(item) == len(self._items) - 1:
      self._button_add.grab_focus()

    super().remove_item(item)

  def _clear(self):
    for _unused in range(len(self._items)):
      self._remove_item(self._items[0])

  def _init_actions_menu_popup(self):
    for action_dict in self._builtin_actions.values():
      self._add_action_to_menu_popup(action_dict)

    if self._allow_custom_actions:
      self._actions_menu.append(Gtk.SeparatorMenuItem())
      self._add_add_custom_action_to_menu_popup()

    self._actions_menu.show_all()

  def _on_button_add_clicked(self, button):
    self._actions_menu.popup_at_pointer(None)

  def _add_action_to_menu_popup(self, action_dict):
    if action_dict.get('menu_path') is None:
      current_parent_menu = self._actions_menu
    else:
      parent_names = tuple(
        action_dict['menu_path'].split(pg.MENU_PATH_SEPARATOR))

      current_parent_menu = self._actions_menu
      for i in range(len(parent_names)):
        current_names = parent_names[:i + 1]

        if current_names not in self._builtin_actions_submenus:
          self._builtin_actions_submenus[current_names] = Gtk.MenuItem(
            label=current_names[-1], use_underline=False)
          self._builtin_actions_submenus[current_names].set_submenu(Gtk.Menu())

          current_parent_menu.append(
            self._builtin_actions_submenus[current_names])

        current_parent_menu = self._builtin_actions_submenus[
          current_names].get_submenu()

    menu_item = Gtk.MenuItem(label=action_dict['display_name'],
                             use_underline=False)
    menu_item.connect('activate', self._on_actions_menu_item_activate,
                      action_dict)

    current_parent_menu.append(menu_item)

  def _on_actions_menu_item_activate(self, menu_item, action_dict):
    self.add_item(action_dict)

  def _add_add_custom_action_to_menu_popup(self):
    menu_item = Gtk.MenuItem(label=self._add_custom_action_text,
                             use_underline=False)
    menu_item.connect('activate', self._on_add_custom_action_menu_item_activate)
    self._actions_menu.append(menu_item)

  def _on_add_custom_action_menu_item_activate(self, menu_item):
    self._browser.fill_contents_if_empty()
    self._browser.widget.show_all()

  def _setup_drag(self, item):
    self._drag_and_drop_context.setup_drag(
      item.item_widget,
      self._get_drag_data,
      self._on_drag_data_received,
      [item],
      [item],
      self._get_drag_icon,
      [item],
    )

  def _get_drag_icon(self, _widget, drag_context, item):
    Gtk.drag_set_icon_widget(
      drag_context,
      item.create_drag_icon(),
      self._DRAG_ICON_OFFSET,
      self._DRAG_ICON_OFFSET,
    )
