"""Class modifying `gtk.Entry` instances to expand/shrink in width dynamically.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

__all__ = [
  'EntryExpander',
]


class EntryExpander:
  """Class allowing the specified `gtk.Entry` instance to have a flexible width.

  The width is bounded by the specified minimum and maximum number of
  characters.
  """
  
  def __init__(self, entry: Gtk.Entry, minimum_width_chars: int, maximum_width_chars: int):
    self._entry = entry
    self._minimum_width_chars = minimum_width_chars
    self._maximum_width_chars = maximum_width_chars
    
    if self._minimum_width_chars > self._maximum_width_chars:
      raise ValueError(
        (f'minimum width in characters ({self._minimum_width_chars})'
         f' cannot be greater than maximum ({self._maximum_width_chars})'))
    
    self._minimum_width = -1
    self._maximum_width = -1
    self._entry.set_width_chars(self._minimum_width_chars)
    
    self._pango_layout = Pango.Layout.new(self._entry.get_pango_context())
    
    self._entry.connect('changed', self._on_entry_changed)
    self._entry.connect('size-allocate', self._on_entry_size_allocate)
  
  def _on_entry_changed(self, entry):
    if self._entry.get_realized():
      self._update_entry_width()
  
  def _on_entry_size_allocate(self, entry, allocation):
    if self._minimum_width == -1:
      self._minimum_width = self._entry.get_allocation().width
      self._maximum_width = (
        int((self._minimum_width / self._minimum_width_chars) * self._maximum_width_chars)
        + 1)
    
    self._update_entry_width()
  
  def _update_entry_width(self):
    self._pango_layout.set_text(self._entry.get_text(), -1)
    
    offset_pixel_width = (
      (self._entry.get_layout_offsets()[0] + self._entry.get_property('scroll-offset'))
      * 2)
    text_pixel_width = self._pango_layout.get_pixel_size()[0] + offset_pixel_width
    self._entry.set_property(
      'width-request',
      max(min(text_pixel_width, self._maximum_width), self._minimum_width))
