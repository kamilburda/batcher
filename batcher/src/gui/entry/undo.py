"""Undo/redo capability for `Gtk.Entry` instances."""

import collections
from typing import List, Tuple

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class EntryUndoContext:
  """Class adding undo/redo capabilities to a `Gtk.Entry` instance."""
  
  _StepData = collections.namedtuple('_StepData', ['step_type', 'position', 'text'])
  
  _STEP_TYPES = ['insert', 'delete']

  def __init__(self, entry: Gtk.Entry):
    self._entry = entry

    self.undo_enabled = True
    """If ``True``, user steps (insert text, delete text) are added to the undo
    history.
    """
    
    self._undo_stack = []
    self._redo_stack = []
    
    self._last_step_group = []
    self._last_step_type = None
    
    self._cursor_changed_by_step = False

  def enable(self):
    self._entry.connect('notify::cursor-position', self._on_entry_notify_cursor_position)
    self._entry.connect('key-press-event', self._on_entry_key_press_event)

  def handle_insert_text(self, new_text, new_text_length, position):
    if self.undo_enabled and new_text:
      self._on_entry_step(self._entry.get_position(), new_text, 'insert')

    self._entry.get_buffer().insert_text(position, new_text, new_text_length)

    return position + new_text_length

  def handle_delete_text(self, start_pos, end_pos):
    if self.undo_enabled:
      text_to_delete = self._entry.get_text()[start_pos:end_pos]
      if text_to_delete:
        self._on_entry_step(start_pos, text_to_delete, 'delete')

    self._entry.get_buffer().delete_text(start_pos, end_pos - start_pos)

  def undo(self):
    self._undo_redo(
      self._undo_stack,
      self._redo_stack,
      step_handlers={
        'insert': lambda step_data: self._entry.delete_text(
          step_data.position, step_data.position + len(step_data.text)),
        'delete': lambda step_data: self._entry.insert_text(
          step_data.text, step_data.position)},
      step_handlers_get_cursor_position={
        'insert': lambda last_step_data: last_step_data.position,
        'delete': lambda last_step_data: (
          last_step_data.position + len(last_step_data.text))},
      steps_iterator=reversed)
  
  def redo(self):
    self._undo_redo(
      self._redo_stack,
      self._undo_stack,
      step_handlers={
        'insert': lambda step_data: self._entry.insert_text(
          step_data.text, step_data.position),
        'delete': lambda step_data: self._entry.delete_text(
          step_data.position, step_data.position + len(step_data.text))},
      step_handlers_get_cursor_position={
        'insert': lambda last_step_data: (
          last_step_data.position + len(last_step_data.text)),
        'delete': lambda last_step_data: last_step_data.position})
  
  def undo_push(self, undo_push_list: List[Tuple[str, int, str]]):
    """Manually adds changes to the undo history.

    The changes are treated as one undo group (i.e. a single ``undo()`` call
    will undo all specified changes at once).
    
    If there are pending changes not yet added to the undo history, they are
    added first (as a separate undo group), followed by the changes specified in
    this method.
    
    Calling this method completely removes the redo history.
    
    Args:
      undo_push_list:
        List of ``(step_type, position, text)`` tuples to add as one undo
        step. ``step_type`` can be ``'insert'`` for text insertion or
        ``'delete'`` for text deletion (other values raise ``ValueError``).
        ``position`` is the starting entry cursor position of the changed
        text. ``text`` is the changed text.
    
    Raises:
      ValueError:
        The step type as the first element of the ``undo_push_list`` tuple
        is not valid.
    """
    self._redo_stack = []
    
    self._undo_stack_push()
    
    for step_type, position, text in undo_push_list:
      if step_type not in self._STEP_TYPES:
        raise ValueError(f'invalid step type "{step_type}"')
      self._last_step_group.append(self._StepData(step_type, position, text))
    
    self._undo_stack_push()
  
  def can_undo(self) -> bool:
    return bool(self._undo_stack)
  
  def can_redo(self) -> bool:
    return bool(self._redo_stack)
  
  def _on_entry_notify_cursor_position(self, entry, property_spec):
    if self._cursor_changed_by_step:
      self._cursor_changed_by_step = False
    else:
      self._undo_stack_push()
  
  def _on_entry_key_press_event(self, entry, event):
    if (event.state & Gtk.accelerator_get_default_mod_mask()) == Gdk.ModifierType.CONTROL_MASK:
      key_name = Gdk.keyval_name(Gdk.keyval_to_lower(event.keyval))
      if key_name == 'z':
        self.undo()
        return True
      elif key_name == 'y':
        self.redo()
        return True

    return False
  
  def _on_entry_step(self, position, text, step_type):
    self._redo_stack = []
    
    if self._last_step_type != step_type:
      self._undo_stack_push()
    
    self._last_step_group.append(self._StepData(step_type, position, text))
    self._last_step_type = step_type
    
    self._cursor_changed_by_step = True
  
  def _undo_redo(
        self,
        stack_to_pop_from,
        stack_to_push_to,
        step_handlers,
        step_handlers_get_cursor_position,
        steps_iterator=None):
    self._undo_stack_push()
    
    if not stack_to_pop_from:
      return
    
    steps = stack_to_pop_from.pop()
    
    if steps_iterator is None:
      step_list = steps
    else:
      step_list = list(steps_iterator(steps))
    
    stack_to_push_to.append(steps)
    
    self.undo_enabled = False
    
    for step in step_list:
      step_handlers[step.step_type](step)
    
    self._entry.set_position(
      step_handlers_get_cursor_position[step_list[-1].step_type](step_list[-1]))
    
    self.undo_enabled = True
  
  def _undo_stack_push(self):
    if self._last_step_group:
      self._undo_stack.append(self._last_step_group)
      self._last_step_group = []
