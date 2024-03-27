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
  """A widget to display a label, optionally being cleared after a delay.

  A tooltip is displayed if the label text does not fit the width of the parent
  widget.
  """

  _SPACING = 2
  
  def __init__(self):
    super().__init__()

    self._init_gui()

  def set_text(
        self,
        text: str,
        message_type: Gtk.MessageType = Gtk.MessageType.ERROR,
        clear_delay: Optional[int] = None,
  ):
    """Sets the text of the label. The text is displayed in bold style.

    If the text is too wide to fit the label, the label is ellipsized and a
    tooltip is displayed containing the full text.
    
    If ``clear_delay`` is not ``None`` and ``message_type`` is not
    `Gtk.MessageType.ERROR`, the message automatically disappears after the
    specified delay in milliseconds.
    """
    self._set_text(text)

    if not text:
      return

    if message_type == Gtk.MessageType.ERROR:
      self._timeout_remove(clear_delay, self._set_text)
    else:
      self._timeout_add_strict(clear_delay, self._set_text, None)

  def _set_text(self, text):
    if text:
      self._label_message.set_markup(f'<b>{GLib.markup_escape_text(text)}</b>')

      if not pg.gui.label_fits_text(self._label_message):
        self._label_message.set_tooltip_text(text)
      else:
        self._label_message.set_tooltip_text(None)
    else:
      self._label_message.set_text('')
      self._label_message.set_tooltip_text(None)

  def _init_gui(self):
    self._label_message = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      ellipsize=Pango.EllipsizeMode.END,
    )

    self.set_spacing(self._SPACING)
    self.pack_start(self._label_message, True, True, 0)
  
  def _timeout_add_strict(self, delay, func, *args, **kwargs):
    if self._should_clear_text_after_delay(delay):
      pg.invocation.timeout_add_strict(delay, func, *args, **kwargs)
  
  def _timeout_remove(self, delay, func):
    if self._should_clear_text_after_delay(delay):
      pg.invocation.timeout_remove(func)
  
  @staticmethod
  def _should_clear_text_after_delay(clear_delay):
    return clear_delay is not None and clear_delay > 0


GObject.type_register(MessageLabel)
