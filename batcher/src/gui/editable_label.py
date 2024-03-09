"""Widget containing a text label that can be optionally edited."""

from typing import Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class EditableLabel(Gtk.Box):
  """Class that displays a label and an edit button to allow editing the label.

  Pressing the ``Enter`` key or focusing out of the editable text entry
  displays the label again.
  
  Signals:
    changed: The user finished editing the label text.
  """
  
  _LABEL_EDIT_BUTTON_SPACING = 4
  
  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}
  
  def __init__(self, text: Optional[str] = None, **kwargs):
    super().__init__(self, **kwargs)

    self._text_before_editing = text if text is not None else ''
    
    self._label = Gtk.Label(
      label=self._text_before_editing,
      xalign=0.0,
      yalign=0.5,
    )
    self._label.show_all()
    self._label.set_no_show_all(True)

    self._button_edit = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
    self._button_edit.set_image(Gtk.Image.new_from_icon_name('document-edit', Gtk.IconSize.BUTTON))
    
    self._hbox_label = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=self._LABEL_EDIT_BUTTON_SPACING,
    )
    self._hbox_label.pack_start(self._label, False, False, 0)
    self._hbox_label.pack_start(self._button_edit, False, False, 0)

    self._entry = Gtk.Entry()
    self._entry.show_all()
    self._entry.set_no_show_all(True)

    self._entry.hide()
    
    self.pack_start(self._hbox_label, True, True, 0)
    self.pack_start(self._entry, True, True, 0)

    self._button_edit.connect('clicked', self._on_button_edit_clicked)
    self._entry.connect('activate', self._on_entry_finished_editing)
    self._entry.connect('focus-out-event', self._on_entry_finished_editing)
    self._entry.connect('key-press-event', self._on_entry_canceled_editing)
  
  @property
  def label(self):
    return self._label

  @property
  def entry(self):
    return self._entry

  @property
  def button_edit(self):
    return self._button_edit

  def show_label(self):
    self._entry.hide()
    self._hbox_label.show()
  
  def _on_button_edit_clicked(self, _button):
    self._text_before_editing = self._label.get_text()

    self._hbox_label.hide()
    
    self._entry.set_text(self._label.get_text())
    self._entry.grab_focus()
    self._entry.set_position(-1)
    self._entry.show()
  
  def _on_entry_finished_editing(self, _entry, *_args):
    new_text = self._entry.get_text()

    if new_text:
      self._label.set_text(new_text)
      self._text_before_editing = new_text

    self.show_label()

    if new_text:
      self.emit('changed')

  def _on_entry_canceled_editing(self, _entry, event, *_args):
    if Gdk.keyval_name(event.keyval) == 'Escape':
      self._label.set_text(self._text_before_editing)
      self._entry.set_text(self._text_before_editing)

      self.show_label()

      return True

    return False


GObject.type_register(EditableLabel)
