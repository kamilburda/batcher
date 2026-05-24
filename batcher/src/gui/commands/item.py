"""Widget representing a single command (action/condition) in the GUI."""

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from . import editor as command_editor_

from src import commands as commands_
from src.gui import messages as gui_messages_
from src.gui import utils as gui_utils_
from src.gui import widgets as gui_widgets_


class CommandItem(gui_widgets_.ItemBoxItem):

  _LABEL_COMMAND_NAME_MAX_WIDTH_CHARS = 50

  _DRAG_ICON_WIDTH = 250
  _DRAG_ICON_BORDER_WIDTH = 4

  _MENU_OPTIONS_ICON_LABEL_SPACING = 6
  _MENU_OPTIONS_HORIZONTAL_MARGIN = 9

  def __init__(self, command, attach_editor_widget=True):
    self._command = command
    self._attach_editor_widget = attach_editor_widget

    self._display_warning_message_event_id = None
    self._display_info_message_event_id = None
    self._drag_icon_window = None

    self._button_command = self._command['enabled'].gui.widget

    self._on_command_enabled_changed_event_id = (
      self._command['enabled'].connect_event('value-changed', self._on_command_enabled_changed))

    super().__init__(self._button_command, button_display_mode='always')

    self._init_gui()

    self._entry_for_editing_command_name.connect(
      'focus-out-event', self._on_entry_for_editing_command_name_focus_out_event)
    self._entry_for_editing_command_name.connect(
      'key-press-event', self._on_entry_for_editing_command_name_key_press_event)

    self._button_edit.connect('clicked', self._on_button_edit_clicked)
    self._button_options.connect('clicked', self._on_button_options_clicked)

    if self._command['display_options_on_create'].value:
      self._command['display_options_on_create'].set_value(False)
      self.widget.connect('realize', lambda *args: self.editor.show_all())

    self.editor.connect('close', self._on_command_edit_dialog_close)
    self.editor.connect('response', self._on_command_edit_dialog_response)

  @property
  def command(self):
    return self._command

  @property
  def editor(self):
    return self._editor

  @property
  def drag_icon(self):
    return self._drag_icon_window

  @property
  def button_edit(self) -> Gtk.Button:
    return self._button_edit

  @property
  def button_options(self) -> Gtk.Button:
    return self._button_options

  @property
  def menu_options(self) -> Gtk.Menu:
    return self._menu_options

  @property
  def rename_menu_item(self) -> Gtk.MenuItem:
    return self._rename_menu_item

  @property
  def move_up_menu_item(self) -> Gtk.MenuItem:
    return self._move_up_menu_item

  @property
  def move_down_menu_item(self) -> Gtk.MenuItem:
    return self._move_down_menu_item

  @property
  def duplicate_menu_item(self) -> Gtk.MenuItem:
    return self._duplicate_menu_item

  @property
  def remove_menu_item(self) -> Gtk.MenuItem:
    return self._remove_menu_item

  def toggle_edit_name(self):
    self._entry_for_editing_command_name.set_text(self._command['display_name'].value)
    self._entry_for_editing_command_name.show()
    self._entry_for_editing_command_name.grab_focus()
    self._entry_for_editing_command_name.set_position(-1)
    self._item_widget.hide()

  def _toggle_off_edit_name(self):
    self._entry_for_editing_command_name.hide()
    self._item_widget.show()

  def is_being_edited(self):
    return self.editor.get_mapped()

  def set_tooltip(self, additional_text=None):
    if self._command['description'].value:
      tooltip_text = self._command['description'].value
    else:
      tooltip_text = ''

    if additional_text:
      if tooltip_text:
        tooltip_text = f'{tooltip_text}\n\n{additional_text}'
      else:
        tooltip_text = additional_text

    self.item_widget.set_tooltip_text(tooltip_text)

  def reset_tooltip(self):
    self.set_tooltip()

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

  def set_info(self, show, message=None):
    if show:
      self.set_tooltip(message)

      if self._display_info_message_event_id is not None:
        self._button_info.disconnect(self._display_info_message_event_id)

      self._display_info_message_event_id = self._button_info.connect(
        'clicked', self._on_button_info_clicked, message)

      self._button_info.show()
    else:
      self._button_info.hide()

      self.reset_tooltip()

      if self._display_info_message_event_id is not None:
        self._button_info.disconnect(self._display_info_message_event_id)
        self._display_info_message_event_id = None

  def create_drag_icon(self):
    if self._drag_icon_window is not None:
      # We do not destroy the widget on "drag-end" so that an animation
      # indicating failed dragging is played.
      self._drag_icon_window.destroy()
      self._drag_icon_window = None

    button = Gtk.CheckButton(label=self._command['display_name'].value)
    button.get_child().set_xalign(0.0)
    button.get_child().set_yalign(0.5)
    button.get_child().set_ellipsize(Pango.EllipsizeMode.END)
    button.get_child().set_can_focus(False)

    button.set_border_width(self._DRAG_ICON_BORDER_WIDTH)
    button.set_can_focus(False)

    button.set_active(self._command['enabled'].value)

    frame = Gtk.Frame(shadow_type=Gtk.ShadowType.OUT)
    frame.add(button)

    self._drag_icon_window = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      screen=self.widget.get_screen(),
      width_request=self._DRAG_ICON_WIDTH,
      attached_to=self.widget,
      transient_for=gui_utils_.get_toplevel_window(self.widget),
    )
    self._drag_icon_window.add(frame)
    self._drag_icon_window.show_all()

    return self._drag_icon_window

  def prepare_command_for_detachment(self):
    self._command['enabled'].remove_event(self._on_command_enabled_changed_event_id)

  def _init_gui(self):
    self._label_command_name = self._command['display_name'].gui.widget.get_child()
    self._label_command_name.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_command_name.set_max_width_chars(self._LABEL_COMMAND_NAME_MAX_WIDTH_CHARS)

    self._entry_for_editing_command_name = Gtk.Entry()
    self._entry_for_editing_command_name.set_no_show_all(True)
    self._entry_for_editing_command_name.hide()

    self._hbox.pack_start(self._entry_for_editing_command_name, True, True, 0)
    self._hbox.reorder_child(
      self._entry_for_editing_command_name,
      self._hbox.child_get_property(self._item_widget, 'position') + 1,
    )

    self._button_edit = self._setup_item_button(icon=GimpUi.ICON_EDIT, position=0)
    self._button_edit.set_tooltip_text(_('Edit'))

    self._menu_options = Gtk.Menu(
      reserve_toggle_size=False,
    )

    self._rename_menu_item = self._add_command_option(_('Rename'), 'document-edit')
    self._move_up_menu_item = self._add_command_option(_('Move up'), 'pan-up')
    self._move_down_menu_item = self._add_command_option(_('Move down'), 'pan-down')

    self._duplicate_menu_item = self._add_command_option(
      _('Duplicate'), GimpUi.ICON_OBJECT_DUPLICATE)
    if commands_.DO_NOT_DUPLICATE_TAG in self._command.tags:
      self._duplicate_menu_item.set_sensitive(False)

    self._remove_menu_item = self._add_command_option(_('Remove'), 'edit-delete')
    if commands_.DO_NOT_REMOVE_TAG in self._command.tags:
      self._remove_menu_item.set_sensitive(False)

    self._menu_options.show_all()

    self._button_options = self._setup_item_button(icon='pan-down')
    self._button_options.set_tooltip_text(_('Options'))

    self._editor = command_editor_.CommandEditor(
      self._command,
      self.widget,
      attach_editor_widget=self._attach_editor_widget,
      title=self._command['display_name'].value,
      attached_to=self.widget,
    )
    self.widget.connect('realize', self._on_command_widget_realize)

    self._button_warning = self._setup_item_indicator_button(
      icon=GimpUi.ICON_DIALOG_WARNING,
      position=0,
      tooltip_text=_('Show error details'),
    )

    self._button_info = self._setup_item_indicator_button(
      icon=GimpUi.ICON_DIALOG_INFORMATION, position=0)

    self.set_tooltip()

  def _add_command_option(self, label, icon_name):
    hbox_menu_item = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._MENU_OPTIONS_ICON_LABEL_SPACING,
      margin_start=self._MENU_OPTIONS_HORIZONTAL_MARGIN,
      margin_end=self._MENU_OPTIONS_HORIZONTAL_MARGIN,
    )
    hbox_menu_item.add(
      Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU),
    )
    hbox_menu_item.add(
      Gtk.Label(
        label=label,
        use_underline=False,
      ),
    )
    menu_item = Gtk.MenuItem()
    menu_item.add(hbox_menu_item)

    self._menu_options.append(menu_item)

    return menu_item

  def _on_command_widget_realize(self, _dialog):
    self.editor.set_transient_for(gui_utils_.get_toplevel_window(self.widget))

  def _on_entry_for_editing_command_name_focus_out_event(self, _entry, _event):
    self._command['display_name'].set_value(self._entry_for_editing_command_name.get_text())

    self._toggle_off_edit_name()

  def _on_entry_for_editing_command_name_key_press_event(self, _entry, event):
    if event.type != Gdk.EventType.KEY_PRESS:
      return False

    if event.keyval in [Gdk.KEY_Return, Gdk.KEY_KP_Enter]:
      self._command['display_name'].set_value(self._entry_for_editing_command_name.get_text())
    elif event.keyval in [Gdk.KEY_Escape]:
      self._entry_for_editing_command_name.set_text(self._command['display_name'].value)
    else:
      return False

    self._toggle_off_edit_name()

    return True

  def _on_button_edit_clicked(self, _button):
    if self.is_being_edited():
      self.editor.present()
    else:
      self.editor.show_all()

  def _on_button_options_clicked(self, button):
    gui_utils_.menu_popup_below_widget(self._menu_options, button)

  @staticmethod
  def _on_button_warning_clicked(_button, main_message, short_message, full_message, parent):
    gui_messages_.display_failure_message(main_message, short_message, full_message, parent=parent)

  @staticmethod
  def _on_button_info_clicked(button, message):
    gui_utils_.display_popover(button, message)

  def _on_command_enabled_changed(self, _setting):
    self._command['arguments'].apply_gui_values_to_settings(force=True)

  def _on_command_edit_dialog_close(self, _dialog):
    self.editor.hide()

  def _on_command_edit_dialog_response(self, _dialog, response_id):
    if response_id == Gtk.ResponseType.CLOSE:
      self.editor.hide()
