"""Base class for preview widgets."""

from typing import Callable, Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Preview(Gtk.Box):
  
  def __init__(self):
    super().__init__(homogeneous=False)
    
    self._update_locked = False
    self._lock_keys = set()
    
    self._functions_to_invoke_at_update = []
  
  def update(self) -> bool:
    """Updates the preview if update is not locked (see `lock_update()`)."""
    if self._update_locked:
      return True
    
    while self._functions_to_invoke_at_update:
      func, func_args, func_kwargs = self._functions_to_invoke_at_update.pop(0)
      func(*func_args, **func_kwargs)
    
    return False
  
  def lock_update(self, lock: bool, key: Optional[str] = None):
    """Prevents or allows updating the preview via `update()`.

    If ``lock`` is ``True``, calling `update()` will have no effect. If ``lock``
    is ``False``, the preview will be updated on subsequent calls to `update()`.

    If ``key`` is specified to lock the update, the same key must be
    specified to unlock the preview. Multiple keys can be used to lock the
    preview; to unlock the preview, call this method with each of the keys.
    
    If ``key`` is specified and ``lock`` is ``False`` and the key was not
    used to lock the preview before, nothing happens.
    
    If ``key`` is ``None``, the preview is locked/unlocked regardless of
    which function called this method. Passing ``None`` also removes previous
    keys that were used to lock the preview.
    """
    if key is None:
      self._lock_keys.clear()
      self._update_locked = lock
    else:
      if lock:
        self._lock_keys.add(key)
      else:
        if key in self._lock_keys:
          self._lock_keys.remove(key)
      
      self._update_locked = bool(self._lock_keys)
  
  def add_function_at_update(self, func: Callable, *func_args, **func_kwargs):
    """Adds a function to a list of functions to invoke at the beginning of
    `update()`.
    
    The functions will be invoked in the order in which they were added and
    only if the preview is unlocked. This is useful to postpone invocation of
    functions until the preview is available again.
    """
    self._functions_to_invoke_at_update.append((func, func_args, func_kwargs))
