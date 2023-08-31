"""GTK progress bar updater."""

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
  
  def _set_text_progress_bar(self, text):
    self.progress_bar.set_text(text)
    self._force_update()
  
  def _force_update(self):
    # This is necessary for the GTK progress bar to be updated properly.
    # See http://faq.pygtk.org/index.py?req=show&file=faq23.020.htp
    while gtk.events_pending():
      gtk.main_iteration()
