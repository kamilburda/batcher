"""List of commands (actions/conditions) that can be edited interactively."""

from typing import Any, Dict, Optional, Union

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import browser as command_browser_
from . import item as command_item_

from src import constants
from src import commands as commands_
from src import setting as setting_
from src.gui import utils as gui_utils_
from src.gui import widgets as gui_widgets_


class CommandList(gui_widgets_.ItemBox):
  """A scrollable vertical list that allows the user to add, edit and remove
  commands interactively.

  A command represents an action or a condition that can be applied to a
  GIMP item (image, layer, ...). Commands can be created via the `src.commands`
  module.

  Commands are applied starting from the top (i.e. commands ordered higher take
  precedence).

  The list connects events to the passed commands that keeps the commands and
  the list in sync. For example, when adding a command via `src.commands.add()`,
  the item for the command is automatically added to the list. Conversely, when
  calling `add_item()` from this class, both the command and the item are
  added to the commands and the GUI, respectively.

  Signals:

  * ``'command-list-item-added'`` - An item (command) was added.

    Arguments:

    * The added item.

  * ``'command-list-item-added-interactive'`` - An item (command) was added
    interactively (via `add_item()`).

    Arguments:

    * The added item.

  * ``'command-list-item-reordered'`` - An item (command) was reordered via
    `reorder_item()`.

    Arguments:

    * The reordered item.
    * The new position of the reordered item (starting from 0).

  * ``'command-list-item-removed'`` - An item (command) was removed via
    `remove_item()`.

    Arguments:

    * The removed item.
  """

  __gsignals__ = {
    'command-list-item-added': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'command-list-item-added-interactive': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'command-list-item-reordered': (
      GObject.SignalFlags.RUN_FIRST, None,
      (GObject.TYPE_PYOBJECT, GObject.TYPE_INT)),
    'command-list-item-removed': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
  }

  _ADD_BUTTON_HBOX_SPACING = 6

  _DRAG_ICON_OFFSET = -8

  def __init__(
        self,
        commands: setting_.Group,
        builtin_commands: Optional[Dict[str, Any]] = None,
        add_command_text: Optional[str] = None,
        allow_custom_commands: bool = True,
        add_custom_command_text: Optional[str] = None,
        command_browser_text: Optional[str] = None,
        item_spacing: int = gui_widgets_.ItemBox.ITEM_SPACING,
        **kwargs):
    super().__init__(item_spacing=item_spacing, **kwargs)

    self._commands = commands
    self._builtin_commands = builtin_commands if builtin_commands is not None else {}
    self._add_command_text = add_command_text
    self._allow_custom_commands = allow_custom_commands
    self._add_custom_command_text = add_custom_command_text
    self._command_browser_text = command_browser_text

    if self._allow_custom_commands:
      self._browser = command_browser_.CommandBrowser(title=self._command_browser_text)
    else:
      self._browser = None

    self._current_temporary_command = None
    self._current_temporary_command_item = None

    self._init_gui()

    if self._browser is not None:
      self._browser.widget.connect('realize', self._on_command_browser_realize)
      self._browser.connect('command-selected', self._on_command_browser_command_selected)
      self._browser.connect('confirm-add-command', self._on_command_browser_confirm_add_command)
      self._browser.connect('cancel-add-command', self._on_command_browser_cancel_add_command)

    self._after_add_command_event_id = self._commands.connect_event(
      'after-add-command',
      lambda _commands, command_, orig_command_dict: self._add_item_from_command(command_))

    # Add already existing commands
    for command in self._commands:
      self._add_item_from_command(command)

    self._after_reorder_command_event_id = self._commands.connect_event(
      'after-reorder-command',
      lambda _commands, command_, current_position, new_position: (
        self._reorder_command(command_, new_position)))

    self._before_remove_command_event_id = self._commands.connect_event(
      'before-remove-command',
      lambda _commands, command_: self._remove_command(command_))

    self._before_clear_commands_event_id = self._commands.connect_event(
      'before-clear-commands', self._on_before_clear_commands)

  @property
  def commands(self):
    return self._commands

  @property
  def browser(self):
    return self._browser

  @property
  def button_add(self):
    return self._button_add

  def add_item(
        self,
        command_dict_or_pdb_proc_name_or_command: Union[Dict[str, Any], str, setting_.Group],
        attach_editor_widget=True,
  ) -> command_item_.CommandItem:
    self._commands.set_event_enabled(self._after_add_command_event_id, False)
    command = commands_.add(self._commands, command_dict_or_pdb_proc_name_or_command)
    self._commands.set_event_enabled(self._after_add_command_event_id, True)

    item = self._add_item_from_command(command, attach_editor_widget=attach_editor_widget)

    self.emit('command-list-item-added-interactive', item)

    return item

  def reorder_item(self, item, new_position):
    processed_new_position = self._reorder_item(item, new_position)

    self._commands.set_event_enabled(self._after_reorder_command_event_id, False)
    commands_.reorder(self._commands, item.command.name, processed_new_position)
    self._commands.set_event_enabled(self._after_reorder_command_event_id, True)

    self.emit('command-list-item-reordered', item, new_position)

  def remove_item(self, item):
    self._remove_item(item)

    self._commands.set_event_enabled(self._before_remove_command_event_id, False)
    commands_.remove(self._commands, item.command.name)
    self._commands.set_event_enabled(self._before_remove_command_event_id, True)

    self.emit('command-list-item-removed', item)

  def _on_command_browser_realize(self, dialog):
    dialog.set_attached_to(gui_utils_.get_toplevel_window(self))

  def _on_command_browser_command_selected(self, _browser, command):
    if command is not None:
      if self._current_temporary_command != command:
        if self._current_temporary_command_item:
          self.remove_item(self._current_temporary_command_item)

        command.tags.add('ignore_save')

        self._current_temporary_command = command
        
        self._current_temporary_command_item = self.add_item(command, attach_editor_widget=False)
        self._current_temporary_command_item.widget.set_sensitive(False)
    else:
      if self._current_temporary_command_item:
        self.remove_item(self._current_temporary_command_item)

      self._current_temporary_command = None
      self._current_temporary_command_item = None

  def _on_command_browser_confirm_add_command(self, _browser, command, command_editor_widget):
    if self._current_temporary_command_item:
      self._current_temporary_command_item.editor.attach_editor_widget(command_editor_widget)
      self._current_temporary_command_item.widget.set_sensitive(True)

      command_editor_widget.show_additional_settings = False

      command['enabled'].set_value(True)
      command.tags.remove('ignore_save')

      self._current_temporary_command = None
      self._current_temporary_command_item = None

  def _on_command_browser_cancel_add_command(self, _browser):
    if self._current_temporary_command_item:
      self.remove_item(self._current_temporary_command_item)

      self._current_temporary_command = None
      self._current_temporary_command_item = None

  def _on_before_clear_commands(self, _commands):
    self._clear()

    self._current_temporary_command = None
    self._current_temporary_command_item = None

  def _init_gui(self):
    self._button_add = Gtk.Button(relief=Gtk.ReliefStyle.NONE)

    if self._add_command_text is not None:
      button_hbox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=self._ADD_BUTTON_HBOX_SPACING,
      )
      button_hbox.pack_start(
        Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.MENU),
        False, False, 0)

      label_add = Gtk.Label(
        label=self._add_command_text,
        use_underline=True,
      )
      button_hbox.pack_start(label_add, False, False, 0)

      self._button_add.add(button_hbox)
    else:
      self._button_add.set_image(
        Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.BUTTON))

    self._button_add.connect('clicked', self._on_button_add_clicked)

    self._vbox.pack_start(self._button_add, False, False, 0)

    self._commands_menu = Gtk.Menu()
    # key: tuple of menu path components; value: `Gtk.MenuItem`
    self._builtin_commands_submenus = {}
    self._init_commands_menu_popup()

  def _add_item_from_command(self, command, attach_editor_widget=True):
    command.initialize_gui(only_null=True)

    item = command_item_.CommandItem(command, attach_editor_widget=attach_editor_widget)

    super().add_item(item)

    self.emit('command-list-item-added', item)

    return item

  def _reorder_command(self, command, new_position):
    item = next(
      (item_ for item_ in self._items if item_.command.name == command.name),
      None)
    if item is not None:
      self._reorder_item(item, new_position)
    else:
      raise ValueError(
        f'command "{command.name}" does not match any item in "{self}"')

  def _reorder_item(self, item, new_position):
    return super().reorder_item(item, new_position)

  def _remove_command(self, command):
    item = next(
      (item_ for item_ in self._items if item_.command.name == command.name),
      None)

    if item is not None:
      self._remove_item(item)
    else:
      raise ValueError(
        f'command "{command.get_path()}" does not match any item in "{self}"')

  def _remove_item(self, item):
    if self._get_item_position(item) == len(self._items) - 1:
      self._button_add.grab_focus()

    item.prepare_command_for_detachment()

    super().remove_item(item)

  def _clear(self):
    for _unused in range(len(self._items)):
      self._remove_item(self._items[0])

  def _init_commands_menu_popup(self):
    for command_dict in self._builtin_commands.values():
      self._add_command_to_menu_popup(command_dict)

    if self._allow_custom_commands:
      self._commands_menu.append(Gtk.SeparatorMenuItem())
      self._add_add_custom_command_to_menu_popup()

    self._commands_menu.show_all()

  def _on_button_add_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._commands_menu, button)

  def _add_command_to_menu_popup(self, command_dict):
    if command_dict.get('menu_path') is None:
      current_parent_menu = self._commands_menu
    else:
      parent_names = tuple(command_dict['menu_path'].split(constants.MENU_PATH_SEPARATOR))

      current_parent_menu = self._commands_menu
      for i in range(len(parent_names)):
        current_names = parent_names[:i + 1]

        if current_names not in self._builtin_commands_submenus:
          self._builtin_commands_submenus[current_names] = Gtk.MenuItem(
            label=current_names[-1], use_underline=False)
          self._builtin_commands_submenus[current_names].set_submenu(Gtk.Menu())

          current_parent_menu.append(self._builtin_commands_submenus[current_names])

        current_parent_menu = self._builtin_commands_submenus[current_names].get_submenu()

    menu_item = Gtk.MenuItem(label=command_dict['display_name'], use_underline=False)
    menu_item.connect('activate', self._on_commands_menu_item_activate, command_dict)

    current_parent_menu.append(menu_item)

  def _on_commands_menu_item_activate(self, _menu_item, command_dict):
    self.add_item(command_dict)

  def _add_add_custom_command_to_menu_popup(self):
    menu_item = Gtk.MenuItem(label=self._add_custom_command_text, use_underline=False)
    menu_item.connect('activate', self._on_add_custom_command_menu_item_activate)
    self._commands_menu.append(menu_item)

  def _on_add_custom_command_menu_item_activate(self, _menu_item):
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

  def _remove_drag(self, item):
    self._drag_and_drop_context.remove_drag(item.item_widget)

  def _get_drag_icon(self, _widget, drag_context, item):
    Gtk.drag_set_icon_widget(
      drag_context,
      item.create_drag_icon(),
      self._DRAG_ICON_OFFSET,
      self._DRAG_ICON_OFFSET,
    )
