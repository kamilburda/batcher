"""Helper classes and functions for modules in the `setting` package."""

import collections
import itertools
from typing import Callable, List, Optional, Union

__all__ = [
  'SETTING_PATH_SEPARATOR',
  'SETTING_ATTRIBUTE_SEPARATOR',
  'SettingParentMixin',
  'SettingEventsMixin',
  'get_pdb_name',
  'get_processed_display_name',
  'generate_display_name',
  'get_processed_description',
  'generate_description',
  'get_setting_path',
  'check_setting_name',
]

SETTING_PATH_SEPARATOR = '/'
"""Separator for setting paths. See `get_setting_path()` for more information.
"""

SETTING_ATTRIBUTE_SEPARATOR = '.'
"""Separator between the name of a `setting.Setting` instance and one of its 
attributes.
"""


class SettingParentMixin:
  """Mixin providing `setting.Setting` and `setting.Group` instances with a
  parent reference.

  Parent references allow settings and groups to form a hierarchical structure.
  """
  
  def __init__(self):
    super().__init__()
    
    self._parent = None
  
  @property
  def parent(self) -> 'setting.Group':
    """The immediate parent (`setting.Group` instance) of the current setting or
    group.
    """
    return self._parent
  
  @property
  def parents(self) -> List['setting.Group']:
    """Returns a list of parents (`setting.Group` instances), starting from the
    topmost parent.
    """
    parent = self._parent
    parents = []
    
    while parent is not None:
      parents.insert(0, parent)
      parent = parent.parent
    
    return parents
  
  def _set_as_parent_for_setting(self, setting):
    setting._parent = self


class SettingEventsMixin:
  """Mixin for `setting.Setting` and `setting.Group` instances allowing to set
  up and invoke events.
  """
  
  _event_handler_id_counter = itertools.count(start=1)

  # key: event type
  # value: {event handler ID: [event handler, arguments, keyword arguments, is enabled]}
  _global_event_handlers = collections.defaultdict(dict)

  # This allows faster lookup of global events via IDs.
  # key: event handler ID
  # value: event type
  _global_event_handler_ids_and_types = {}
  
  def __init__(self):
    super().__init__()
    
    # key: event type
    # value: {event handler ID: [event handler, arguments, keyword arguments, is enabled]}
    self._event_handlers = collections.defaultdict(dict)
    
    # This allows faster lookup of events via IDs.
    # key: event handler ID
    # value: event type
    self._event_handler_ids_and_types = {}
  
  def connect_event(
        self,
        event_type: str,
        event_handler: Callable,
        *event_handler_args,
        **event_handler_kwargs,
  ) -> int:
    """Connects an event handler.
    
    ``event_type`` can be an arbitrary string. To invoke an event manually, call
    ``invoke_event``.
    
    Several event types are invoked automatically. For the list of such event
    types, consult the documentation for `setting.Setting` or `setting.Group`
    classes.
    
    The ``event_handler`` function must always contain at least one argument -
    the instance this method is called from (a `setting.Setting` or
    `setting.Group`).
    
    Multiple event handlers can be connected. Each new event handler is invoked
    as the last.
    
    Args:
      event_type:
        Event type as a string.
      event_handler:
        Function to be called when the event given by ``event_type`` is invoked.
      *event_handler_args:
        Arguments to ``event_handler``.
      **event_handler_kwargs:
        Keyword arguments to ``event_handler``.
    
    Returns:
      Numeric ID of the event handler. The ID can be used to remove the event
      via `remove_event()`.
    
    Raises:
      TypeError: ``event_handler`` is not a function or the wrong number of
        arguments was passed.
    """
    if not callable(event_handler):
      raise TypeError(f'{event_handler} is not a function')
    
    event_id = next(self._event_handler_id_counter)
    self._event_handlers[event_type][event_id] = [
      event_handler, event_handler_args, event_handler_kwargs, True]
    self._event_handler_ids_and_types[event_id] = event_type
    
    return event_id

  @classmethod
  def connect_event_global(
        cls,
        event_type: str,
        event_handler: Callable,
        *event_handler_args,
        **event_handler_kwargs,
  ) -> int:
    """Connects a global event handler, which is invoked for any `Setting`
    instance.

    For information about parameters, see `connect_event`.

    Returns:
      Numeric ID of the event handler. The ID can be used to remove the event
      via `remove_event_global()`.

    Raises:
      TypeError: ``event_handler`` is not a function or the wrong number of
        arguments was passed.
    """
    if not callable(event_handler):
      raise TypeError(f'{event_handler} is not a function')

    event_id = next(cls._event_handler_id_counter)
    cls._global_event_handlers[event_type][event_id] = [
      event_handler, event_handler_args, event_handler_kwargs, True]
    cls._global_event_handler_ids_and_types[event_id] = event_type

    return event_id

  def remove_event(self, event_id: int):
    """Removes the event handler specified by its ID as returned by
    `connect_event()`.
    """
    if event_id not in self._event_handler_ids_and_types:
      raise ValueError(f'event handler with ID {event_id} does not exist')

    event_type = self._event_handler_ids_and_types[event_id]
    del self._event_handlers[event_type][event_id]
    del self._event_handler_ids_and_types[event_id]

  @classmethod
  def remove_event_global(cls, event_id: int):
    """Removes the global event handler specified by its ID as returned by
    `connect_event_global()`.
    """
    if event_id not in cls._global_event_handler_ids_and_types:
      raise ValueError(f'global event handler with ID {event_id} does not exist')

    event_type = cls._global_event_handler_ids_and_types[event_id]
    del cls._global_event_handlers[event_type][event_id]
    del cls._global_event_handler_ids_and_types[event_id]

  def set_event_enabled(self, event_id: int, enabled: bool):
    """Enables or disables the event handler specified by its ID.

    This method has no effect if the event ID is already enabled and
    ``enabled`` is ``True`` or is already disabled and ``enabled`` is
    ``False``.
    
    Raises:
      ValueError:
        ``event_id`` is not valid.
    """
    if event_id not in self._event_handler_ids_and_types:
      raise ValueError(f'event handler with ID {event_id} does not exist')

    event_type = self._event_handler_ids_and_types[event_id]
    self._event_handlers[event_type][event_id][3] = enabled

  @classmethod
  def set_event_enabled_global(cls, event_id: int, enabled: bool):
    """Enables or disables the global event handler specified by its ID.

    For more information, see `set_event_enabled()`.
    """
    if event_id not in cls._global_event_handler_ids_and_types:
      raise ValueError(f'global event handler with ID {event_id} does not exist')

    event_type = cls._global_event_handler_ids_and_types[event_id]
    cls._global_event_handlers[event_type][event_id][3] = enabled
  
  def has_event(self, event_id: int) -> bool:
    """Returns ``True`` if the event handler specified by its ID exists,
    ``False`` otherwise.
    """
    return (
      event_id in self._event_handler_ids_and_types
      or event_id in self._global_event_handler_ids_and_types
    )
  
  def invoke_event(self, event_type: str, *additional_args, **additional_kwargs):
    """Manually calls all connected event handlers of the specified event type.

    Global event handlers (connected via `connect_event_global()`) are
    invoked before any setting-specific event handlers (connected via
    `connect_event()`).

    Usually you do not need to call this function unless you implement custom
    event types (e.g. in a `setting.Setting` subclass) not provided by any
    existing `setting.Setting` subclasses or the `setting.Group` class.

    Args:
      event_type:
        Event type as a string. All event handlers that are enabled and
        connected with this event type are invoked.
      *additional_args:
        Additional positional arguments prepended to the arguments specified in
        `connect_event()` (if any).
      **additional_kwargs:
        Additional keyword arguments prepended to the arguments specified in
        `connect_event()` (if any). The same keyword arguments in
        `connect_event()` override keyword arguments in ``**additional_kwargs``.
    """
    event_handlers = itertools.chain(
      self._global_event_handlers[event_type].values(),
      self._event_handlers[event_type].values(),
    )

    for (event_handler, args, kwargs, enabled) in event_handlers:
      if enabled:
        event_handler_args = additional_args + tuple(args)
        event_handler_kwargs = dict(additional_kwargs, **kwargs)
        event_handler(self, *event_handler_args, **event_handler_kwargs)


def check_setting_name(setting_name: str):
  """Checks if the specified setting name is valid.

  A setting name must not contain `SETTING_PATH_SEPARATOR` or
  `SETTING_ATTRIBUTE_SEPARATOR`.

  If the setting name is not valid, `ValueError` is raised.
  """
  if not isinstance(setting_name, str):
    raise TypeError('setting name must be a string')

  if SETTING_PATH_SEPARATOR in setting_name or SETTING_ATTRIBUTE_SEPARATOR in setting_name:
    raise ValueError(f'setting name "{setting_name}" is not valid')


def get_unique_setting_name(setting_name: str, group: 'setting.Group') -> str:
  """Returns a setting name modified to be unique within all immediate children
  of the specified ``group``.

  To make the name unique, ``'_2'`` is appended. If such a name exists, ``_3``
  is appended instead, and so on.

  Args:
    setting_name: A setting name to be made unique.
    group: A setting group to compare ``setting_name`` against.

  Returns:
    A setting name made unique, or ``setting_name`` if no modification is
    necessary.
  """
  children_names = set(setting.name for setting in group)

  new_setting_name = setting_name
  i = 2
  while new_setting_name in children_names:
    new_setting_name = f'{setting_name}_{i}'
    i += 1

  return new_setting_name


def get_pdb_name(setting_name: str) -> str:
  """Returns a setting name suitable for the description of the setting in the
  GIMP Procedural Database (PDB).
  """
  return setting_name.replace('_', '-')


def get_processed_display_name(
      setting_display_name: Optional[str],
      setting_name: str,
) -> str:
  """Returns ``setting_display_name`` if not ``None``, otherwise returns a
  string as returned by `generate_display_name()` using ``setting_name``.
  """
  if setting_display_name is not None:
    return setting_display_name
  else:
    return generate_display_name(setting_name)


def generate_display_name(setting_name: str) -> str:
  """Returns a string representing the setting name in a format suitable to be
  displayed to the user (i.e. a display name).
  """
  return setting_name.replace('_', ' ').capitalize()


def get_processed_description(
      setting_description: Optional[str],
      setting_display_name: str,
) -> str:
  """Returns ``setting_description`` if not ``None``, otherwise returns a
  string as returned by `generate_description()` using ``setting_display_name``.
  """
  if setting_description is not None:
    return setting_description
  else:
    return generate_description(setting_display_name)


def generate_description(display_name: str) -> str:
  """Returns setting description from the specified display name.
  
  Underscores in display names used as mnemonics are usually undesired in
  descriptions, hence their removal.
  """
  return display_name.replace('_', '')


def get_setting_path(
      setting: 'setting.Setting',
      relative_path_group: Union['setting.Group', str, None] = None,
      separator: str = SETTING_PATH_SEPARATOR,
) -> str:
  """Returns the full path of a setting.

  The path consists of names of parent `setting.Group` instances and the
  ``setting``. The path components are separated by ``separator``.

  For example, if ``setting`` is named 'file_extension' and parent groups
  (starting from the topmost group) are 'settings' and 'main', then the
  returned setting path is ``'settings/main/file_extension'`` (if using the
  default ``separator``).

  If ``relative_path_group`` is a `setting.Group`, it is used to make the
  setting path relative to this group. If the path of the group to
  the topmost parent does not match, the full path is returned.
  
  If ``relative_path_group`` is ``'root'`` and the setting has at least one
  parent, the topmost parent is omitted.
  """
  def _get_setting_path(path_components):
    return separator.join(setting_.name for setting_ in path_components)
  
  if relative_path_group == 'root':
    if setting.parents:
      setting_path_without_root = _get_setting_path((setting.parents + [setting])[1:])
      return setting_path_without_root
    else:
      return setting.name
  else:
    setting_path = _get_setting_path(setting.parents + [setting])
    
    if relative_path_group is not None:
      root_path = _get_setting_path(relative_path_group.parents + [relative_path_group])
      if setting_path.startswith(root_path):
        return setting_path[len(root_path + separator):]
    
    return setting_path
