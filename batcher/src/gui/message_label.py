"""Widget for displaying inline messages."""

from typing import Optional

import gi
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg


class MessageLabel(Gtk.Box):
  """A widget to display a label, and optionally additional information in a
  tooltip.

  The tooltip is also displayed if the label text does not fit the width of
  the parent widget.
  """
  _SPACING = 2
  
  def __init__(self):
    super().__init__(homogeneous=False)
    
    self._label_text = ''
    self._tooltip_text_lines = []
    self._message_type = None
    self._clear_delay = None
    
    self._init_gui()
    
    self._label_message.connect('size-allocate', self._on_label_message_size_allocate)
  
  def set_text(
        self,
        text: str,
        message_type: Gtk.MessageType = Gtk.MessageType.ERROR,
        clear_delay: Optional[int] = None,
  ):
    """Sets the text of the label. The text is displayed in bold style.
    
    If the text is too wide to fit the label or the text has multiple lines,
    the label is ellipsized and a tooltip is displayed containing the full text.

    Only the first line is displayed in the label.
    
    If ``clear_delay`` is not ``None`` and ``message_type`` is not
    `Gtk.MessageType.ERROR`, the message automatically disappears after the
    specified delay in milliseconds.
    """
    if not text:
      self._label_text = ''
      self._tooltip_text_lines = []
      self._label_message.set_text(self._label_text)
      return
    
    lines = text.strip().split('\n')
    
    first_line = lines[0]
    first_line = first_line[0].upper() + first_line[1:]
    if not first_line.endswith('.'):
      first_line += '.'
    
    self._label_text = first_line
    self._tooltip_text_lines = lines[1:]
    self._message_type = message_type
    self._clear_delay = clear_delay
    
    self._label_message.set_markup(f'<b>{GLib.markup_escape_text(self._label_text)}</b>')
    
    if message_type == Gtk.MessageType.ERROR:
      self._timeout_remove(self._clear_delay, self.set_text)
    else:
      self._timeout_add_strict(self._clear_delay, self.set_text, None)
  
  def _init_gui(self):
    self._label_message = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      ellipsize=Pango.EllipsizeMode.END,
    )

    self.set_spacing(self._SPACING)
    self.pack_start(self._label_message, True, True, 0)
  
  def _on_label_message_size_allocate(self, label, allocation):
    if ((pg.gui.get_label_full_text_width(self._label_message) > self.get_allocation().width)
        or len(self._tooltip_text_lines) >= 1):
      lines = list(self._tooltip_text_lines) + [self._label_text]

      self._label_message.set_tooltip_text('\n'.join(lines).strip())
    else:
      self._label_message.set_tooltip_text(None)
  
  def _timeout_add_strict(self, delay, func, *args, **kwargs):
    if self._should_clear_text_after_delay(delay):
      pg.invocation.timeout_add_strict(delay, func, None, *args, **kwargs)
  
  def _timeout_remove(self, delay, func):
    if self._should_clear_text_after_delay(delay):
      pg.invocation.timeout_remove(func)
  
  @staticmethod
  def _should_clear_text_after_delay(clear_delay):
    return clear_delay is not None and clear_delay > 0


GObject.type_register(MessageLabel)
