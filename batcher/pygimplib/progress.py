"""Handling progress of the work done so far."""

from typing import Optional


class ProgressUpdater:
  """Class keeping track of progress done whose data can be utilized by progress
  bars.

  This class in particular can be used if no visible progress update is desired,
  but reporting the state is still desirable.

  You may subclass this class to update a GUI- or CLI-based progress bar. To do
  so, override the ``_fill_progress_bar()`` and ``_set_text_progress_bar()``
  methods.
  """
  
  def __init__(self, progress_bar, num_total_tasks=0):
    self.progress_bar = progress_bar
    """Progress bar.
    
    This is usually a GUI element representing a progress bar.
    """

    self.num_total_tasks = num_total_tasks
    """Number of total tasks to complete."""
    
    self._num_finished_tasks = 0
  
  @property
  def num_finished_tasks(self):
    """The number of tasks finished so far."""
    return self._num_finished_tasks
  
  def update_tasks(self, num_tasks: int = 1):
    """Advances the progress bar by the given number of tasks finished.
    
    Raises:
      ValueError: Number of finished tasks exceeds the number of total tasks.
    """
    if self._num_finished_tasks + num_tasks > self.num_total_tasks:
      raise ValueError('number of finished tasks exceeds the number of total tasks')
    
    self._num_finished_tasks += num_tasks
    
    self._fill_progress_bar()
  
  def update_text(self, text: Optional[str]):
    """Updates text in the progress bar.

    Use ``None`` or an empty string to remove the text.
    """
    if text is None:
      text = ''
    self._set_text_progress_bar(text)
  
  def reset(self):
    """Empties the progress bar and removes its text.

    The number of finished tasks done is set to 0.
    """
    self._num_finished_tasks = 0
    if self.num_total_tasks > 0:
      self._fill_progress_bar()
    self._set_text_progress_bar('')
  
  def _fill_progress_bar(self):
    """Fills in a fraction of a progress bar.

    The fraction corresponds to ``num_finished_tasks / num_total_tasks``.
    
    This is a method to be overridden by a subclass that implements a progress
    bar.
    """
    pass
  
  def _set_text_progress_bar(self, text: str):
    """Sets the text of a progress bar.
    
    This is a method to be overridden by a subclass that implements a progress
    bar.
    """
    pass
