"""Dialog prompt for handling existing files (overwrite, skip, etc.)."""

import os
from typing import Dict, Optional

import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from .. import overwrite as pgoverwrite

__all__ = [
  'GtkDialogOverwriteChooser',
]


class GtkDialogOverwriteChooser(pgoverwrite.InteractiveOverwriteChooser):
  """Class displaying a `Gtk.Dialog` prompting the user to choose how to handle
  already existing files.
  """
  
  _DIALOG_BORDER_WIDTH = 8
  _DIALOG_HBOX_CONTENTS_SPACING = 10
  _DIALOG_VBOX_SPACING = 5
  _DIALOG_ACTION_AREA_SPACING = 8
  
  def __init__(
        self,
        values_and_display_names: Dict[int, str],
        default_value: int,
        default_response: int,
        title: str = '',
        parent: Optional[Gtk.Window] = None):
    super().__init__(values_and_display_names, default_value, default_response)
    
    self._title = title
    self._parent = parent
    
    self._init_gui()
  
  def _init_gui(self):
    self._dialog = GimpUi.Dialog(
      title='',
      role=None,
      parent=self._parent,
      flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
    self._dialog.set_transient_for(self._parent)
    self._dialog.set_title(self._title)
    self._dialog.set_border_width(self._DIALOG_BORDER_WIDTH)
    self._dialog.set_resizable(False)
    
    self._dialog_icon = Gtk.Image()
    self._dialog_icon.set_from_icon_name(GimpUi.ICON_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
    
    self._dialog_label = Gtk.Label()
    self._dialog_label.set_line_wrap(True)
    self._dialog_label.set_use_markup(True)
    
    self._dialog_label_event_box = Gtk.EventBox()
    self._dialog_label_event_box.add(self._dialog_label)
    
    self._hbox_dialog_contents = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=self._DIALOG_HBOX_CONTENTS_SPACING)
    self._hbox_dialog_contents.pack_start(self._dialog_icon, False, False, 0)
    self._hbox_dialog_contents.pack_start(
      self._dialog_label_event_box, False, False, 0)
    
    self._checkbutton_apply_to_all = Gtk.CheckButton(label=_('_Apply action to all files'))
    self._checkbutton_apply_to_all.set_use_underline(True)
    
    self._dialog.vbox.set_spacing(self._DIALOG_VBOX_SPACING)
    self._dialog.vbox.pack_start(self._hbox_dialog_contents, False, False, 0)
    self._dialog.vbox.pack_start(self._checkbutton_apply_to_all, False, False, 0)
    
    self._buttons = {}
    for value, display_name in self.values_and_display_names.items():
      self._buttons[value] = self._dialog.add_button(display_name, value)
    
    self._dialog.action_area.set_spacing(self._DIALOG_ACTION_AREA_SPACING)
    
    self._checkbutton_apply_to_all.connect(
      'toggled', self._on_checkbutton_apply_to_all_toggled)
    
    self._is_dialog_text_allocated_size = False
    self._dialog_label_event_box.connect(
      'size-allocate', self._on_dialog_text_event_box_size_allocate)
    
    self._dialog.set_focus(self._buttons[self.overwrite_mode])
  
  def _choose(self, filepath):
    if filepath is not None:
      dirpath, filename = os.path.split(filepath)
      if dirpath:
        text_choose = (
          _('A file named "{}" already exists in "{}". ').format(
            filename, os.path.basename(dirpath)))
      else:
        text_choose = _('A file named "{}" already exists.\n').format(filename)
    else:
      text_choose = _('A file with the same name already exists.\n')
    
    text_choose += _('What would you like to do?')
    
    self._dialog_label.set_markup(
      '<span font_size="large"><b>{}</b></span>'.format(GLib.markup_escape_text(text_choose)))
    
    self._dialog.show_all()
    
    self._overwrite_mode = self._dialog.run()
    
    if self._overwrite_mode not in self._values:
      self._overwrite_mode = self.default_response
    
    self._dialog.hide()
    
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
