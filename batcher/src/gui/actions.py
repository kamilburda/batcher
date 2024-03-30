"""Widgets to interactively edit actions (procedures/constraints)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg
from pygimplib import pdb

from src import actions as actions_
from src.gui import editable_label as editable_label_
from src.gui import placeholders as gui_placeholders_
from src.gui import popup_hide_context as popup_hide_context_
from src.gui import messages as gui_messages_


class ActionBox(pg.gui.ItemBox):
  """A scrollable vertical box that allows the user to add, edit and remove
  actions interactively.

  An action represents a procedure or constraint that can be applied to a
  GIMP item (image, layer, ...). Actions can be created via the `src.actions`
  module.

  Actions are applied starting from the top (i.e. actions ordered higher take
  precedence).

  The box connects events to the passed actions that keeps the actions and
  the box in sync. For example, when adding an action via `src.actions.add()`,
  the item for the action is automatically added to the box. Conversely, when
  calling `add_item()` from this class, both the action and the item are
  added to the actions and the GUI, respectively.
  
  Signals:
  
  * ``'action-box-item-added'`` - An item (action) was added.
    
    Arguments:
    
    * The added item.

  * ``'action-box-item-added-interactive'`` - An item (action) was added
    interactively (via `add_item()`).

    Arguments:

    * The added item.
    
  * ``'action-box-item-reordered'`` - An item (action) was reordered via
    `reorder_item()`.
    
    Arguments:
    
    * The reordered item.
    * The new position of the reordered item (starting from 0).
    
  * ``'action-box-item-removed'`` - An item (action) was removed via
    `remove_item()`.
    
    Arguments:
    
    * The removed item.
  """
  
  __gsignals__ = {
    'action-box-item-added': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'action-box-item-added-interactive': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'action-box-item-reordered': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_INT)),
    'action-box-item-removed': (
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
        item_spacing: int = pg.gui.ItemBox.ITEM_SPACING,
        **kwargs):
    super().__init__(item_spacing=item_spacing, **kwargs)
    
    self._actions = actions
    self._builtin_actions = builtin_actions if builtin_actions is not None else {}
    self._add_action_text = add_action_text
    self._allow_custom_actions = allow_custom_actions
    self._add_custom_action_text = add_custom_action_text
    
    self._pdb_procedure_browser_dialog = None
    
    self._init_gui()
    
    self._after_add_action_event_id = self._actions.connect_event(
      'after-add-action',
      lambda _actions, action, orig_action_dict: self._add_item_from_action(action))
    
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

  def add_item(
        self,
        action_dict_or_pdb_proc_name: Union[Dict[str, Any], str],
  ) -> _ActionBoxItem:
    self._actions.set_event_enabled(self._after_add_action_event_id, False)
    action = actions_.add(self._actions, action_dict_or_pdb_proc_name)
    self._actions.set_event_enabled(self._after_add_action_event_id, True)
    
    item = self._add_item_from_action(action)

    self.emit('action-box-item-added-interactive', item)
    
    return item
  
  def reorder_item(self, item, new_position):
    processed_new_position = self._reorder_item(item, new_position)
    
    self._actions.set_event_enabled(self._after_reorder_action_event_id, False)
    actions_.reorder(self._actions, item.action.name, processed_new_position)
    self._actions.set_event_enabled(self._after_reorder_action_event_id, True)
    
    self.emit('action-box-item-reordered', item, new_position)
  
  def remove_item(self, item):
    self._remove_item(item)
    
    self._actions.set_event_enabled(self._before_remove_action_event_id, False)
    actions_.remove(self._actions, item.action.name)
    self._actions.set_event_enabled(self._before_remove_action_event_id, True)
    
    self.emit('action-box-item-removed', item)
  
  def _init_gui(self):
    self._button_add = Gtk.Button(relief=Gtk.ReliefStyle.NONE)

    if self._add_action_text is not None:
      button_hbox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=self._ADD_BUTTON_HBOX_SPACING,
      )
      button_hbox.pack_start(
        Gtk.Image.new_from_icon_name(GimpUi.ICON_LIST_ADD, Gtk.IconSize.MENU), False, False, 0)
      
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

    item = _ActionBoxItem(action)

    super().add_item(item)

    self.emit('action-box-item-added', item)

    return item
  
  def _reorder_action(self, action, new_position):
    item = next((item_ for item_ in self._items if item_.action.name == action.name), None)
    if item is not None:
      self._reorder_item(item, new_position)
    else:
      raise ValueError(f'action "{action.name}" does not match any item in "{self}"')
  
  def _reorder_item(self, item, new_position):
    return super().reorder_item(item, new_position)
  
  def _remove_action(self, action):
    item = next((item_ for item_ in self._items if item_.action.name == action.name), None)
    
    if item is not None:
      self._remove_item(item)
    else:
      raise ValueError(f'action "{action.get_path()}" does not match any item in "{self}"')
  
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
      parent_names = tuple(action_dict['menu_path'].split(pg.MENU_PATH_SEPARATOR))

      current_parent_menu = self._actions_menu
      for i in range(len(parent_names)):
        current_names = parent_names[:i + 1]

        if current_names not in self._builtin_actions_submenus:
          self._builtin_actions_submenus[current_names] = Gtk.MenuItem(
            label=current_names[-1], use_underline=False)
          self._builtin_actions_submenus[current_names].set_submenu(Gtk.Menu())

          current_parent_menu.append(self._builtin_actions_submenus[current_names])

        current_parent_menu = self._builtin_actions_submenus[current_names].get_submenu()

    menu_item = Gtk.MenuItem(label=action_dict['display_name'], use_underline=False)
    menu_item.connect('activate', self._on_actions_menu_item_activate, action_dict)

    current_parent_menu.append(menu_item)
  
  def _on_actions_menu_item_activate(self, menu_item, action_dict):
    self.add_item(action_dict)
  
  def _add_add_custom_action_to_menu_popup(self):
    menu_item = Gtk.MenuItem(label=self._add_custom_action_text, use_underline=False)
    menu_item.connect('activate', self._on_add_custom_action_menu_item_activate)
    self._actions_menu.append(menu_item)
  
  def _on_add_custom_action_menu_item_activate(self, menu_item):
    if self._pdb_procedure_browser_dialog:
      self._pdb_procedure_browser_dialog.show()
    else:
      self._pdb_procedure_browser_dialog = self._create_pdb_procedure_browser_dialog()
  
  def _create_pdb_procedure_browser_dialog(self):
    dialog = GimpUi.ProcBrowserDialog(
      title=_('Procedure Browser'),
      role=pg.config.PLUGIN_NAME,
    )

    dialog.add_buttons(
      Gtk.STOCK_ADD, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    
    dialog.set_default_response(Gtk.ResponseType.OK)
    
    dialog.connect('response', self._on_pdb_procedure_browser_dialog_response)
    
    dialog.show_all()
    
    return dialog
  
  def _on_pdb_procedure_browser_dialog_response(self, dialog, response_id):
    if response_id == Gtk.ResponseType.OK:
      procedure_name = dialog.get_selected()
      if procedure_name:
        self.add_item(actions_.get_action_dict_for_pdb_procedure(procedure_name))
    
    dialog.hide()

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


class _ActionBoxItem(pg.gui.ItemBoxItem):

  LABEL_ACTION_NAME_MAX_WIDTH_CHARS = 50

  _DRAG_ICON_WIDTH = 250
  _DRAG_ICON_BORDER_WIDTH = 4

  def __init__(self, action):
    self._action = action
    self._display_warning_message_event_id = None
    self._drag_icon_window = None

    self._button_action = self._action['enabled'].gui.widget

    self._action['enabled'].connect_event('value-changed', self._on_action_enabled_changed)

    super().__init__(self._button_action, button_display_mode='always')

    self._init_gui()

    self._button_edit.connect('clicked', self._on_button_edit_clicked)
    self._button_remove.connect('clicked', lambda *args: self.edit_dialog.destroy())

    if self._action['display_options_on_create'].value:
      self._action['display_options_on_create'].set_value(False)
      self.widget.connect('realize', lambda *args: self.edit_dialog.show_all())

    self._edit_dialog.connect('close', self._on_action_edit_dialog_close)
    self._edit_dialog.connect('response', self._on_action_edit_dialog_response)

  @property
  def action(self):
    return self._action

  @property
  def edit_dialog(self):
    return self._edit_dialog

  @property
  def drag_icon(self):
    return self._drag_icon_window

  def is_being_edited(self):
    return self.edit_dialog.get_mapped()

  def set_tooltip(self, text):
    self.widget.set_tooltip_text(text)

  def reset_tooltip(self):
    self._set_tooltip_if_label_does_not_fit_text(self._label_action_name)

  def has_warning(self):
    return self._button_warning.get_visible()

  def set_warning(self, show, main_message=None, failure_message=None, details=None, parent=None):
    if show:
      self.set_tooltip(failure_message)

      if self._display_warning_message_event_id is not None:
        self._button_warning.disconnect(self._display_warning_message_event_id)

      self._display_warning_message_event_id = self._button_warning.connect(
        'clicked',
        self._on_button_warning_clicked, main_message, failure_message, details, parent)

      self._button_warning.show()
    else:
      self._button_warning.hide()

      self.reset_tooltip()
      if self._display_warning_message_event_id is not None:
        self._button_warning.disconnect(self._display_warning_message_event_id)
        self._display_warning_message_event_id = None

  def create_drag_icon(self):
    if self._drag_icon_window is not None:
      # We do not destroy the widget on "drag-end" so that an animation
      # indicating failed dragging is played.
      self._drag_icon_window.destroy()
      self._drag_icon_window = None

    button = Gtk.CheckButton(label=self._action['display_name'].value)
    button.get_child().set_xalign(0.0)
    button.get_child().set_yalign(0.5)
    button.get_child().set_ellipsize(Pango.EllipsizeMode.END)
    button.get_child().set_can_focus(False)

    button.set_border_width(self._DRAG_ICON_BORDER_WIDTH)
    button.set_can_focus(False)

    button.set_active(self._action['enabled'].value)

    frame = Gtk.Frame(shadow_type=Gtk.ShadowType.OUT)
    frame.add(button)

    self._drag_icon_window = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      screen=self.widget.get_screen(),
      width_request=self._DRAG_ICON_WIDTH,
    )
    self._drag_icon_window.add(frame)
    self._drag_icon_window.show_all()

    return self._drag_icon_window

  def _init_gui(self):
    self._label_action_name = self._action['display_name'].gui.widget.get_child()
    self._label_action_name.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_action_name.set_max_width_chars(self.LABEL_ACTION_NAME_MAX_WIDTH_CHARS)
    self._label_action_name.connect('size-allocate', self._on_label_action_name_size_allocate)

    self._button_edit = self._setup_item_button(icon=GimpUi.ICON_EDIT, position=0)
    self._button_edit.set_tooltip_text(_('Edit'))

    self._edit_dialog = _ActionEditDialog(
      self._action,
      self.widget,
      title=self._action['display_name'].value,
      role=pg.config.PLUGIN_NAME,
    )
    self.widget.connect('realize', self._on_action_widget_realize)

    self._button_remove.set_tooltip_text(_('Remove'))

    self._button_warning = self._setup_item_indicator_button(
      icon=GimpUi.ICON_DIALOG_WARNING, position=0)
    self._button_warning.hide()

  def _on_label_action_name_size_allocate(self, label_action_name, _allocation):
    self._set_tooltip_if_label_does_not_fit_text(label_action_name)

  def _on_action_widget_realize(self, _dialog):
    self._edit_dialog.set_transient_for(pg.gui.get_toplevel_window(self.widget))
    self._edit_dialog.set_attached_to(pg.gui.get_toplevel_window(self.widget))

  def _set_tooltip_if_label_does_not_fit_text(self, label_action_name):
    if pg.gui.label_fits_text(label_action_name):
      self.widget.set_tooltip_text(None)
    else:
      self.widget.set_tooltip_text(label_action_name.get_text())

  def _on_label_action_name_changed(self, editable_label):
    self._action['display_name'].set_value(editable_label.label.get_text())
    editable_label.label.set_label(self._action['display_name'].value)

  def _on_button_edit_clicked(self, _button):
    if self.is_being_edited():
      self.edit_dialog.present()
    else:
      self.edit_dialog.show_all()

  @staticmethod
  def _on_button_warning_clicked(_button, main_message, short_message, full_message, parent):
    gui_messages_.display_failure_message(main_message, short_message, full_message, parent=parent)

  def _on_action_enabled_changed(self, _setting):
    self._action['arguments'].apply_gui_values_to_settings(force=True)

  def _on_action_edit_dialog_close(self, _dialog):
    self.edit_dialog.hide()

  def _on_action_edit_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.CLOSE:
      self.edit_dialog.hide()


class _ActionEditDialog(GimpUi.Dialog):

  _CONTENTS_BORDER_WIDTH = 6
  _CONTENTS_SPACING = 3

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  _MORE_OPTIONS_SPACING = 3
  _MORE_OPTIONS_LABEL_TOP_MARGIN = 6
  _MORE_OPTIONS_LABEL_BOTTOM_MARGIN = 3

  _ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS = 60
  _ACTION_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING = 3
  _ACTION_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS = 40

  def __init__(self, action, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.set_resizable(False)
    self.connect('delete-event', lambda *_args: self.hide_on_delete())

    if action['origin'].is_item('gimp_pdb') and action['function'].value:
      self._pdb_procedure = pdb[action['function'].value]
    else:
      self._pdb_procedure = None

    self._init_gui(action)

  def _init_gui(self, action):
    self._set_up_editable_name(action)

    self._set_up_action_info(action, self)

    self._grid_action_arguments = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )

    self._vbox_more_options = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._MORE_OPTIONS_SPACING,
      margin_top=self._MORE_OPTIONS_LABEL_BOTTOM_MARGIN,
    )
    self._vbox_more_options.pack_start(
      action['more_options/enabled_for_previews'].gui.widget, False, False, 0)
    if 'also_apply_to_parent_folders' in action['more_options']:
      self._vbox_more_options.pack_start(
        action['more_options/also_apply_to_parent_folders'].gui.widget, False, False, 0)

    action['more_options_expanded'].gui.widget.add(self._vbox_more_options)
    action['more_options_expanded'].gui.widget.set_margin_top(self._MORE_OPTIONS_LABEL_TOP_MARGIN)

    self._vbox = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      border_width=self._CONTENTS_BORDER_WIDTH,
      spacing=self._CONTENTS_SPACING,
    )

    self._vbox.pack_start(self._label_editable_action_name, False, False, 0)
    if self._action_info_hbox is not None:
      self._vbox.pack_start(self._action_info_hbox, False, False, 0)
    self._vbox.pack_start(self._grid_action_arguments, True, True, 0)
    self._vbox.pack_start(action['more_options_expanded'].gui.widget, False, False, 0)

    self.vbox.pack_start(self._vbox, False, False, 0)

    self._button_reset_response_id = 1
    self._button_reset = self.add_button(_('Reset'), self._button_reset_response_id)
    self._button_reset.connect('clicked', self._on_button_reset_clicked, action)

    self._button_close = self.add_button(_('Close'), Gtk.ResponseType.CLOSE)

    self._set_arguments(action, self._pdb_procedure)

    self.set_focus(self._button_close)

  def _set_up_editable_name(self, action):
    self._label_editable_action_name = editable_label_.EditableLabel()

    self._label_editable_action_name.label.set_use_markup(True)
    self._label_editable_action_name.label.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_editable_action_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(action['display_name'].value)))
    self._label_editable_action_name.label.set_max_width_chars(
      _ActionBoxItem.LABEL_ACTION_NAME_MAX_WIDTH_CHARS)

    self._label_editable_action_name.button_edit.set_tooltip_text(_('Edit Name'))

    self._label_editable_action_name.connect(
      'changed', self._on_label_editable_action_name_changed, action)

  def _on_label_editable_action_name_changed(self, editable_label, action):
    action['display_name'].set_value(editable_label.label.get_text())

    self._set_editable_label_text(editable_label.label.get_text())

  def _set_editable_label_text(self, text):
    self._label_editable_action_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(text)))

  def _set_up_action_info(self, action, parent):
    self._action_info = None
    self._label_short_description = None
    self._info_popup = None
    self._info_popup_text = None
    self._button_info = None
    self._action_info_hbox = None

    if self._pdb_procedure is not None:
      short_description = self._pdb_procedure.proc.get_blurb()
    else:
      short_description = ''

    self._action_info = _get_action_info(action, self._pdb_procedure)

    if self._action_info is None:
      return

    self._label_short_description = Gtk.Label(
      label=short_description,
      use_markup=False,
      selectable=True,
      wrap=True,
      max_width_chars=self._ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS,
    )

    self._info_popup, self._info_popup_text = _create_action_info_popup(self._action_info, parent)

    self._button_info = Gtk.Button(
      image=Gtk.Image.new_from_icon_name(GimpUi.ICON_DIALOG_INFORMATION, Gtk.IconSize.BUTTON),
      relief=Gtk.ReliefStyle.NONE,
    )
    self._button_info.set_tooltip_text(_('Show More Information'))

    self._button_info.connect('clicked', self._on_button_info_clicked)
    self._button_info.connect('focus-out-event', self._on_button_info_focus_out_event)

    self._action_info_hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._ACTION_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING,
    )
    self._action_info_hbox.pack_start(self._label_short_description, False, False, 0)
    self._action_info_hbox.pack_start(self._button_info, False, False, 0)

  def _on_button_info_clicked(self, _button):
    self._info_popup.show()
    self._info_popup_text.select_region(0, 0)  # Prevents selecting the entire text
    self._update_info_popup_position()

  def _on_button_info_focus_out_event(self, _button, _event):
    self._info_popup.hide()

  def _update_info_popup_position(self):
    if self._button_info is not None:
      position = pg.gui.utils.get_position_below_widget(self._button_info)
      if position is not None:
        self._info_popup.move(*position)

  def _set_arguments(self, action, pdb_procedure):
    if pdb_procedure is not None:
      pdb_argument_names_and_blurbs = {
        arg.name: arg.blurb for arg in pdb_procedure.proc.get_arguments()}
    else:
      pdb_argument_names_and_blurbs = None

    row_index = 0

    for setting in action['arguments']:
      if not setting.gui.get_visible():
        continue

      if pdb_procedure is not None:
        argument_description = pdb_argument_names_and_blurbs[setting.name]
      else:
        argument_description = setting.display_name

      label = Gtk.Label(
        label=argument_description,
        xalign=0.0,
        yalign=0.5,
        max_width_chars=self._ACTION_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS,
        wrap=True,
      )

      self._grid_action_arguments.attach(label, 0, row_index, 1, 1)

      widget_to_attach = setting.gui.widget

      if isinstance(setting.gui, pg.setting.SETTING_GUI_TYPES.null):
        widget_to_attach = gui_placeholders_.create_placeholder_widget()
      else:
        if (isinstance(setting, pg.setting.ArraySetting)
            and not setting.element_type.get_allowed_gui_types()):
          widget_to_attach = gui_placeholders_.create_placeholder_widget()

      self._grid_action_arguments.attach(widget_to_attach, 1, row_index, 1, 1)

      row_index += 1

  def _on_button_reset_clicked(self, _button, action):
    action['arguments'].reset()
    action['more_options'].reset()

    action['display_name'].reset()
    self._set_editable_label_text(action['display_name'].value)


def _get_action_info(action, pdb_procedure):
  if pdb_procedure is not None:
    action_info = ''
    action_main_info = []

    help_text = pdb_procedure.proc.get_help()
    if help_text:
      action_main_info.append(help_text)

    action_info += '\n\n'.join(action_main_info)

    action_author_info = []
    authors = pdb_procedure.proc.get_authors()
    if authors:
      action_author_info.append(authors)

    date_text = pdb_procedure.proc.get_date()
    if date_text:
      action_author_info.append(date_text)

    copyright_text = pdb_procedure.proc.get_copyright()
    if copyright_text:
      if not authors.startswith(copyright_text):
        action_author_info.append(f'\u00a9 {copyright_text}')
      else:
        if authors:
          action_author_info[0] = f'\u00a9 {action_author_info[0]}'

    if action_author_info:
      action_info += '\n\n' + ', '.join(action_author_info)

    return action_info
  else:
    if action['description'].value:
      return action['description'].value
    else:
      return None


def _create_action_info_popup(action_info, widget, max_width_chars=100, border_width=3):
  info_popup = Gtk.Window(
    type=Gtk.WindowType.POPUP,
    type_hint=Gdk.WindowTypeHint.TOOLTIP,
    resizable=False,
  )
  info_popup.set_attached_to(widget)

  widget.connect(
    'realize',
    lambda *args: info_popup.set_transient_for(pg.gui.utils.get_toplevel_window(widget)))

  info_popup_text = Gtk.Label(
    label=action_info,
    use_markup=False,
    selectable=True,
    wrap=True,
    max_width_chars=max_width_chars,
  )

  info_popup_hbox = Gtk.Box(
    orientation=Gtk.Orientation.HORIZONTAL,
    homogeneous=False,
    border_width=border_width,
  )
  info_popup_hbox.pack_start(info_popup_text, True, True, 0)

  info_popup_hide_context = popup_hide_context_.PopupHideContext(
    info_popup,
    widget,
    widgets_to_exclude_from_triggering_hiding=[
      info_popup,
      widget,
    ],
  )
  info_popup_hide_context.enable()

  info_popup_scrolled_window = Gtk.ScrolledWindow(
    hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    shadow_type=Gtk.ShadowType.ETCHED_IN,
    propagate_natural_width=True,
    propagate_natural_height=True,
  )
  info_popup_scrolled_window.add(info_popup_hbox)
  info_popup_scrolled_window.show_all()

  info_popup.add(info_popup_scrolled_window)

  return info_popup, info_popup_text
