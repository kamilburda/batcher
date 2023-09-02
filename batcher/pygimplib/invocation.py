"""Functions to invoke other functions in various ways, e.g. with a timeout."""

from collections.abc import Iterable
from typing import Callable, Dict

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import GLib


_timer_ids = {}


def timeout_add_strict(
      interval: int, callback: Callable, *callback_args: Iterable, **callback_kwargs: Dict,
) -> int:
  """Wrapper of `GLib.timeout_add()` that cancels the callback if this function
  is called again with the same callback before the timeout.

  Otherwise, this function has the same behavior as `GLib.timeout_add()`.
  Different callbacks before the timeout are invoked normally.

  The same callback with different arguments is still treated as the same
  callback.
  
  This function also supports keyword arguments to the callback.

  Args:
    interval: Timeout interval in milliseconds.
    callback: The callable to invoke with a delay.
    callback_args: Positional arguments to ``callback``.
    callback_kwargs: Keyword arguments to ``callback``.

  Returns:
    ID as returned by `GLib.timeout_add()`. The ID can be used by, for example,
    `GLib.source_remove()` to cancel invoking the callback. The invocation can
    also be canceled via `timeout_remove()` by specifying the ``callback``
    instead of the ID.
  """
  global _timer_ids
  
  def _callback_wrapper(args, kwargs):
    retval = callback(*args, **kwargs)
    if callback in _timer_ids:
      del _timer_ids[callback]
    
    return retval
  
  timeout_remove(callback)
  
  _timer_ids[callback] = GLib.timeout_add(
    interval, _callback_wrapper, callback_args, callback_kwargs)
  
  return _timer_ids[callback]


def timeout_remove(callback: Callable):
  """Removes a callback scheduled by `timeout_add_strict()`.

  If no such callback exists or the callback was already invoked, nothing is
  performed.
  """
  if callback in _timer_ids:
    GLib.source_remove(_timer_ids[callback])
    del _timer_ids[callback]
