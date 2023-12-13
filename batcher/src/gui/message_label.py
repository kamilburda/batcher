"""Widget for displaying inline messages."""

from typing import Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg


class MessageLabel(Gtk.Box):
  """A widget to display a label, and optionally additional information in a
  popup below the label.

  The popup is also available if the label text does not fit the width of the
  parent widget.
  """
  
  _MESSAGE_AND_MORE_BUTTON_SPACING = 2
  _MORE_BUTTON_LABEL_AND_ARROW_SPACING = 5
  
  _TEXT_VIEW_MARGIN = 3
  
  _POPUP_WIDTH = 400
  _MAX_POPUP_HEIGHT = 200
  
  def __init__(self):
    super().__init__(homogeneous=False)
    
    self._label_text = ''
    self._popup_text_lines = []
    self._message_type = None
    self._clear_delay = None
    
    self._init_gui()
    
    self._popup_hide_context = pg.gui.PopupHideContext(
      self._popup_more,
      self._button_more,
      widgets_to_exclude_from_triggering_hiding=[
        self._popup_more,
        self._scrolled_window_more.get_hscrollbar(),
        self._scrolled_window_more.get_vscrollbar(),
      ],
    )
    self._popup_hide_context.enable()
    
    self._label_message.connect('size-allocate', self._on_label_message_size_allocate)
    self._button_more.connect('clicked', self._on_button_more_clicked)
    
    self._popup_more.connect('show', self._on_popup_more_show)
    self._popup_more.connect('hide', self._on_popup_more_hide)
  
  def set_text(
        self,
        text: str,
        message_type: Gtk.MessageType = Gtk.MessageType.ERROR,
        clear_delay: Optional[int] = None,
  ):
    """Sets the text of the label. The text is displayed in bold style.
    
    If the text is too wide to fit the label or the text has multiple lines,
    the label is ellipsized and a button is displayed that displays a popup
    containing the full text when clicked. Only the first line is displayed
    in the label.
    
    If ``clear_delay`` is not ``None`` and ``message_type`` is not
    `Gtk.MessageType.ERROR`, the message automatically disappears after the
    specified delay in milliseconds. The timer is stopped if the popup is
    displayed and restarted if the popup gets hidden.
    """
    if not text:
      self._label_text = ''
      self._popup_text_lines = []
      self._label_message.set_text(self._label_text)
      return
    
    lines = text.strip().split('\n')
    
    first_line = lines[0]
    first_line = first_line[0].upper() + first_line[1:]
    if not first_line.endswith('.'):
      first_line += '.'
    
    self._label_text = first_line
    self._popup_text_lines = lines[1:]
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
    
    self._label_button_more = Gtk.Label(
      label=_('_More'),
      use_underline=True,
    )
    
    self._hbox_button_more = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._MORE_BUTTON_LABEL_AND_ARROW_SPACING,
    )
    self._hbox_button_more.pack_start(self._label_button_more, True, True, 0)

    arrow = Gtk.Arrow(
      arrow_type=Gtk.ArrowType.DOWN,
      shadow_type=Gtk.ShadowType.IN,
    )
    self._hbox_button_more.pack_start(arrow, False, False, 0)
    
    self._button_more = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
    self._button_more.add(self._hbox_button_more)
    self._button_more.show_all()
    self._button_more.hide()
    self._button_more.set_no_show_all(True)
    
    self._text_view_more = Gtk.TextView(
      wrap_mode=Gtk.WrapMode.WORD,
      left_margin=self._TEXT_VIEW_MARGIN,
      right_margin=self._TEXT_VIEW_MARGIN,
      editable=False,
    )
    
    self._scrolled_window_more = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.NEVER,
      shadow_type=Gtk.ShadowType.ETCHED_IN,
    )
    self._scrolled_window_more.add(self._text_view_more)
    
    self._popup_more = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      resizable=False,
      type_hint=Gdk.WindowTypeHint.TOOLTIP,
      width_request=self._POPUP_WIDTH,
    )
    self._popup_more.add(self._scrolled_window_more)
    self._popup_more.show_all()
    self._popup_more.hide()
    
    self.set_spacing(self._MESSAGE_AND_MORE_BUTTON_SPACING)

    self.pack_start(self._label_message, True, True, 0)
    self.pack_start(self._button_more, False, False, 0)
  
  def _on_label_message_size_allocate(self, label, allocation):
    if ((pg.gui.get_label_full_text_width(self._label_message) > self.get_allocation().width)
        or len(self._popup_text_lines) >= 1):
      self._button_more.show()
    else:
      self._button_more.hide()
  
  def _on_button_more_clicked(self, button):
    lines = list(self._popup_text_lines)
    
    if (pg.gui.get_label_full_text_width(self._label_message)
        > self._label_message.get_allocation().width):
      lines.insert(0, self._label_text)
    
    text = '\n'.join(lines).strip()

    self._text_view_more.set_buffer(Gtk.TextBuffer(text=text))

    self._popup_more.show()

    absolute_label_position = pg.gui.get_position_below_widget(self)
    if absolute_label_position is not None:
      self._popup_more.move(*absolute_label_position)
  
  def _on_popup_more_show(self, popup):
    self._popup_more.set_screen(self._button_more.get_screen())
    
    if self._message_type != Gtk.MessageType.ERROR:
      self._timeout_remove(self._clear_delay, self.set_text)
  
  def _on_popup_more_hide(self, popup):
    if self._message_type != Gtk.MessageType.ERROR:
      self._timeout_add_strict(self._clear_delay, self.set_text, None)
  
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
