"""GTK progress bar updater."""

from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .. import progress as pgprogress

__all__ = [
  'GtkProgressUpdater',
]


class GtkProgressUpdater(pgprogress.ProgressUpdater):
  
  def _fill_progress_bar(self):
    self.progress_bar.set_fraction(self._num_finished_tasks / self.num_total_tasks)
    self._force_update()
  
  def _set_text_progress_bar(self, text: Optional[str]):
    self.progress_bar.set_show_text(bool(text))
    self.progress_bar.set_text(text)
    self._force_update()
  
  @staticmethod
  def _force_update():
    # This is necessary for the GTK progress bar to be updated properly.
    while Gtk.events_pending():
      Gtk.main_iteration()
