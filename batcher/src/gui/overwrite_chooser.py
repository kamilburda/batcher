"""Dialog prompt for handling existing files (overwrite, skip, etc.)."""

import os
from typing import Dict, Optional

import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from src import overwrite
from src.gui import utils as gui_utils_


class GtkDialogOverwriteChooser(overwrite.InteractiveOverwriteChooser):
  """Class displaying a `Gtk.Dialog` prompting the user to choose how to handle
  already existing files.
  """
  
  _DIALOG_CONTENTS_BORDER_WIDTH = 12
  _DIALOG_CONTENTS_SPACING = 12
  _DIALOG_HBOX_ICON_AND_MESSAGE_SPACING = 10

  _DIALOG_LABEL_MAX_WIDTH_CHARS = 100
  
  def __init__(
        self,
        values_and_display_names: Dict[str, str],
        default_value: str,
        default_response: str,
        title: str = '',
        parent: Optional[Gtk.Window] = None,
  ):
    super().__init__(values_and_display_names, default_value, default_response)
    
    self._title = title
    self._parent = parent

    self._response_ids_and_values = {}

    self._init_gui()
  
  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title=self._title,
      parent=self._parent,
      modal=True,
      destroy_with_parent=True,
      attached_to=self._parent,
      transient_for=gui_utils_.get_toplevel_window(self._parent),
      resizable=False,
    )
    
    self._dialog_icon = Gtk.Image(
      icon_name=GimpUi.ICON_DIALOG_WARNING,
      icon_size=Gtk.IconSize.DIALOG,
    )
    
    self._dialog_label = Gtk.Label(
      wrap=True,
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
      max_width_chars=self._DIALOG_LABEL_MAX_WIDTH_CHARS,
    )

    self._dialog_label_event_box = Gtk.EventBox()
    self._dialog_label_event_box.add(self._dialog_label)
    
    self._hbox_icon_and_message = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=self._DIALOG_HBOX_ICON_AND_MESSAGE_SPACING,
    )
    self._hbox_icon_and_message.pack_start(self._dialog_icon, False, False, 0)
    self._hbox_icon_and_message.pack_start(
      self._dialog_label_event_box, False, False, 0)
    
    self._checkbutton_apply_to_all = Gtk.CheckButton(
      label=_('_Apply this choice to all remaining files'),
      use_underline=True,
    )

    self._vbox_contents = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._DIALOG_CONTENTS_SPACING,
      border_width=self._DIALOG_CONTENTS_BORDER_WIDTH,
    )
    self._vbox_contents.pack_start(self._hbox_icon_and_message, False, False, 0)
    self._vbox_contents.pack_start(self._checkbutton_apply_to_all, False, False, 0)

    self._dialog.vbox.pack_start(self._vbox_contents, False, False, 0)
    
    self._buttons = {}
    for response_id, (value, display_name) in enumerate(self.values_and_display_names.items()):
      self._buttons[value] = self._dialog.add_button(display_name, response_id)
      self._response_ids_and_values[response_id] = value
    
    self._checkbutton_apply_to_all.connect(
      'toggled', self._on_checkbutton_apply_to_all_toggled)
    
    self._is_dialog_text_allocated_size = False
    self._dialog_label_event_box.connect(
      'size-allocate', self._on_dialog_text_event_box_size_allocate)

    self._center_buttons()

    self._dialog.set_focus(self._buttons[self.overwrite_mode])

  def _center_buttons(self):
    action_area_parent_box = self._dialog.action_area.get_parent()
    action_area_parent_box.set_child_packing(
      self._dialog.action_area, True, False, 0, Gtk.PackType.END)
    self._dialog.action_area.set_center_widget(None)

  def _choose(
        self,
        filepath: Optional[str] = None,
        message: Optional[str] = None,
  ) -> str:
    if message is None:
      message = '\n'.join(overwrite.get_overwrite_strings(filepath))

    if (os.path.isdir(filepath)
        and overwrite.OverwriteModes.REPLACE in self.values_and_display_names):
      self._buttons[overwrite.OverwriteModes.REPLACE].hide()
      self._buttons[overwrite.OverwriteModes.REPLACE].set_no_show_all(True)

    self._dialog_label.set_markup(
      '<span font_size="large"><b>{}</b></span>'.format(GLib.markup_escape_text(message)))
    
    self._dialog.show_all()
    
    response_id = self._dialog.run()

    self._overwrite_mode = self._response_ids_and_values.get(
      response_id, overwrite.OverwriteModes.CANCEL)
    
    if self._overwrite_mode not in self._values:
      self._overwrite_mode = self.default_response
    
    self._dialog.hide()

    if overwrite.OverwriteModes.REPLACE in self.values_and_display_names:
      self._buttons[overwrite.OverwriteModes.REPLACE].set_no_show_all(False)
      self._buttons[overwrite.OverwriteModes.REPLACE].show()

    return self._overwrite_mode
  
  def _on_checkbutton_apply_to_all_toggled(self, checkbutton):
    self._apply_to_all = self._checkbutton_apply_to_all.get_active()
  
  def _on_dialog_text_event_box_size_allocate(self, dialog_text_event_box, allocation):
    if not self._is_dialog_text_allocated_size:
      self._is_dialog_text_allocated_size = True
      
      # Make sure the label uses as much width as possible in the dialog.
      dialog_text_allocation = dialog_text_event_box.get_allocation()
      dialog_vbox_allocation = self._dialog.vbox.get_allocation()
      self._dialog_label.set_property(
        'width-request', dialog_vbox_allocation.width - dialog_text_allocation.x)
