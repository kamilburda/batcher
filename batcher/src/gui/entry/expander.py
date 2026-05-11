"""Class modifying `Gtk.Entry` instances to expand in width dynamically."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class EntryExpander:
  """Class allowing the specified `Gtk.Entry` instance to expand in width.

  The width is bounded by the specified minimum number of characters and
  maximum width.

  Once expanded, the entry is not shrunk back if characters are removed. This
  prevents excessive jitter due to resizing the entry and possibly the parent
  window.

  ``extra_width_pixels`` represents padding which allows the entry to be
  expanded before reaching its maximum width. This gives a clue to the user
  that the entry is expandable early enough.
  """
  
  def __init__(
        self,
        entry: Gtk.Entry,
        width_chars: int,
        max_expanded_width_pixels: int,
        extra_width_pixels: int,
  ):
    self._entry = entry
    self._width_chars = width_chars
    self._max_expanded_width_pixels = max_expanded_width_pixels
    self._extra_width_pixels = extra_width_pixels

    self._entry.set_width_chars(self._width_chars)

    self._current_width_pixels = -1

    self._entry.connect('changed', self._on_entry_changed)

  def _on_entry_changed(self, _entry):
    if self._entry.get_realized():
      self._update_entry_width()
  
  def _update_entry_width(self):
    layout = self._entry.create_pango_layout(self._entry.get_text())

    offset_pixels = (
      (self._entry.get_layout_offsets()[0] + self._entry.get_property('scroll-offset'))
      * 2
    )

    text_pixel_width = layout.get_pixel_size()[0] + offset_pixels + self._extra_width_pixels

    if text_pixel_width > self._current_width_pixels:
      self._current_width_pixels = text_pixel_width

      text_pixel_width = min(text_pixel_width, self._max_expanded_width_pixels)

      self._entry.set_property('width-request', text_pixel_width)
