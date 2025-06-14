"""Managing and invoking a list of functions sequentially."""

from __future__ import annotations

import collections
from collections.abc import Iterable
import inspect
import itertools
from typing import Callable, Dict, List, Optional, Union


class Invoker:
  """Class to invoke (call) a sequence of functions or nested instances,
  hereinafter "commands".
  
  Features include:
  * adding and removing commands,
  * reordering commands,
  * grouping commands and invoking only commands in specified groups,
  * adding commands to be invoked before or after each command, hereinafter
    "for-each commands",
  * adding another `Invoker` instance as a command (i.e. nesting the current
    instance inside another instance).
  """
  
  _COMMAND_TYPES = _TYPE_COMMAND, _TYPE_FOREACH_COMMAND, _TYPE_INVOKER = (0, 1, 2)
  
  _command_id_counter = itertools.count(start=1)
  
  def __init__(self):
    # key: command group; value: list of `_CommandItem` instances
    self._commands = {}
    
    # key: command group; value: list of `_CommandItem` instances
    self._foreach_commands = {}
    
    # key: command group; value: dict of (command function: count) pairs
    self._command_functions = collections.defaultdict(lambda: collections.defaultdict(int))
    
    # key: command group; value: dict of (command function: count) pairs
    self._foreach_command_functions = collections.defaultdict(lambda: collections.defaultdict(int))
    
    # key: command group; value: dict of (`Invoker` instance: count) pairs
    self._invokers = collections.defaultdict(lambda: collections.defaultdict(int))
    
    # key: command ID; value: `_CommandItem` instance
    self._command_items = {}
  
  def add(
        self,
        command: Union[Callable, Invoker],
        groups: Union[None, str, List[str]] = None,
        args: Optional[Iterable] = None,
        kwargs: Optional[Dict] = None,
        foreach: bool = False,
        ignore_if_exists: bool = False,
        position: Optional[int] = None,
        run_generator: bool = True,
  ) -> Optional[int]:
    """Adds a command to be invoked by `invoke()`.

    The ID of the newly added command is returned.
    
    A command can be:
    * a function, in which case optional arguments (``args``) and
      keyword arguments (``kwargs``) can be specified,
    * another `Invoker` instance.
    
    To control which commands are invoked, you may want to group them.
    
    If ``groups`` is ``None`` or ``'default'``, the command is added to a
    default group appropriately named ``'default'``.
    
    If ``groups`` is a list of group names (strings), the command is added to
    the specified groups. Groups are created automatically if they previously
    did not exist.
    
    If ``groups`` is ``'all'``, the command is added to all existing groups.
    The command will not be added to the default group if it does not exist.
    
    By default, the command is added at the end of the list of commands in the
    specified group(s). Pass an integer to the ``position`` parameter to
    customize the insertion position. A negative value represents an n-th to
    last position.
    
    Command as a function can also be a generator function or return a generator.
    This allows customizing which parts of the code of the function are called
    on each invocation. For example:
    
      def foo():
        print('bar')
        while True:
          args, kwargs = yield
          print('baz')
    
    prints ``'bar'`` the first time the function is called and ``'baz'`` all
    subsequent times. This allows to e.g. initialize objects to an initial state
    in the first part and then use that state in subsequent invocations of this
    function, effectively eliminating the need for global variables for the same
    purpose.
    
    The generator must contain at least one ``yield`` statement. If you pass
    arguments and want to use the arguments in the function, the yield statement
    must be in the form ``args, kwargs = yield``.
    
    To make sure the generator can be called an arbitrary number of times, place
    a ``yield`` statement in an infinite loop. To limit the number of calls,
    simply do not use an infinite loop. In such a case, the command is
    permanently removed for the group(s) `invoke()` was called for once no more
    yield statements are encountered.
    
    To prevent activating generators and to treat generator functions as regular
    functions, pass ``run_generator=False``.
    
    If ``foreach`` is ``True`` and the command is a function, the command is
    treated as a "for-each" command. By default, a for-each command is
    invoked after each regular command (function or `Invoker` instance). To
    customize this behavior, use the ``yield`` statement in the for-each command
    to specify where it is desired to invoke each command.
    For example:
    
      def foo():
        print('bar')
        yield
        print('baz')
    
    first prints ``'bar'``, then invokes the command and finally prints
    ``'baz'``. Multiple ``yield`` statements can be specified to invoke the
    wrapped command multiple times.
    
    If multiple for-each commands are added, they are invoked in the order
    they were added by this method. For example:
      
      def foo1():
        print('bar1')
        yield
        print('baz1')
      
      def foo2():
        print('bar2')
        yield
        print('baz2')
    
    will print ``'bar1'``, ``'bar2'``, then invoke the command (only once), and
    then print ``'baz1'`` and ``'baz2'``.
    
    To make an `Invoker` instance behave as a for-each command, wrap
    the instance in a function as shown above. For example:
      
      def invoke_before_each_command():
        invoker.invoke()
        yield

    If ``ignore_if_exists`` is ``True``, the command is not added if the same
    function or `Invoker` instance is already added in at least one of the
    specified groups. In this case, ``None`` is returned. Note that the same
    function with different arguments is still treated as one function.
    """
    if ignore_if_exists and self.contains(command, groups, foreach):
      return None
    
    command_id = self._get_command_id()
    
    if callable(command):
      if not foreach:
        add_command_func = self._add_command
      else:
        add_command_func = self._add_foreach_command
      
      for group in self._process_groups_arg(groups):
        add_command_func(
          command_id,
          command,
          group,
          args if args is not None else (),
          kwargs if kwargs is not None else {},
          position,
          run_generator)
    else:
      for group in self._process_groups_arg(groups):
        self._add_invoker(command_id, command, group, position)
    
    return command_id
  
  def invoke(
        self,
        groups: Union[None, str, List[str]] = None,
        additional_args: Optional[Iterable] = None,
        additional_kwargs: Optional[Dict] = None,
        additional_args_position: Optional[int] = None):
    """Invokes commands.
    
    If ``groups`` is ``None`` or ``'default'``, commands in the default group
    are invoked.
    
    If ``groups`` is a list of group names (strings), invoke commands in the
    specified groups.
    
    If ``groups`` is ``'all'``, commands in all existing groups are invoked.
    
    If any of the ``groups`` do not exist, ``ValueError`` is raised.
    
    If ``command`` is an `Invoker` instance, the instance will invoke
    commands in the specified groups.
    
    Additional arguments and keyword arguments to all commands in the group
    are given by ``additional_args`` and ``additional_kwargs``, respectively.
    If some keyword arguments appear in both the ``kwargs`` parameter in `add()`
    and in ``additional_kwargs``, values from the latter override the values in
    the former.
    
    ``additional_args`` are appended to the argument list by default. Specify
    ``additional_args_position`` as an integer to change the insertion
    position of ``additional_args``. ``additional_args_position`` also
    applies to nested `Invoker` instances.
    """
    
    def _invoke_command(item_, group_):
      command, command_args, command_kwargs = item_.command
      args = _get_args(command_args)
      kwargs = dict(command_kwargs, **additional_kwargs)
      
      result = command(*args, **kwargs)
      
      if inspect.isgenerator(result):
        item_.is_generator = True
      
      if not (item_.is_generator and item_.run_generator):
        return result
      else:
        if group_ not in item_.generators_per_group:
          item_.generators_per_group[group_] = result
          return next(item_.generators_per_group[group_])
        else:
          try:
            return item_.generators_per_group[group_].send([args, kwargs])
          except StopIteration:
            item_.should_be_removed_from_group = True
    
    def _prepare_foreach_command(command, command_args, command_kwargs):
      args = _get_args(command_args)
      kwargs = dict(command_kwargs, **additional_kwargs)
      return command(*args, **kwargs)
    
    def _get_args(command_args):
      if additional_args_position is None:
        return tuple(command_args) + tuple(additional_args)
      else:
        args = list(command_args)
        args[additional_args_position:additional_args_position] = additional_args
        return tuple(args)
    
    def _invoke_command_with_foreach_commands(item_, group_):
      command_generators = [
        _prepare_foreach_command(*foreach_item.command)
        for foreach_item in self._foreach_commands[group_]]
      
      _invoke_foreach_commands_once(command_generators)
      
      while command_generators:
        result_from_command = _invoke_command(item_, group_)
        _invoke_foreach_commands_once(command_generators, result_from_command)
        
        if item_.should_be_removed_from_group:
          self.remove(item_.command_id, [group_])
          item_.should_be_removed_from_group = False
          return
    
    def _invoke_foreach_commands_once(command_generators, result_from_command=None):
      command_generators_to_remove = []
      
      for command_generator in command_generators:
        try:
          command_generator.send(result_from_command)
        except StopIteration:
          command_generators_to_remove.append(command_generator)
      
      for command_generator_to_remove in command_generators_to_remove:
        command_generators.remove(command_generator_to_remove)

    def _invoke_invoker(invoker, group_):
      invoker.invoke([group_], additional_args, additional_kwargs, additional_args_position)
    
    additional_args = additional_args if additional_args is not None else ()
    additional_kwargs = additional_kwargs if additional_kwargs is not None else {}
    
    for group in self._process_groups_arg(groups):
      if group not in self._commands:
        self._init_group(group)
      
      # A command could be removed during invocation, hence create a list and
      # later check for validity.
      items = list(self._commands[group])
      
      for item in items:
        if item not in self._commands[group]:
          continue
        
        if item.command_type != self._TYPE_INVOKER:
          if self._foreach_commands[group]:
            _invoke_command_with_foreach_commands(item, group)
          else:
            _invoke_command(item, group)
            
            if item.should_be_removed_from_group:
              self.remove(item.command_id, [group])
              item.should_be_removed_from_group = False
        else:
          _invoke_invoker(item.command, group)
  
  def add_to_groups(
        self,
        command_id: int,
        groups: Union[None, str, List[str]] = None,
        position: Optional[int] = None):
    """Adds an existing command specified by its ID to the specified groups.

    For more information about the ``groups`` parameter, see `add()`.
    
    If the command was already added to one of the specified groups, it will
    not be added again (call `add()` for that purpose).
    
    By default, the command is added at the end of the list of commands in the
    specified group(s). Pass an integer to the ``position`` parameter to
    customize the insertion position. A negative value represents an
    n-th-to-last position.
    
    If the command ID is not valid, `ValueError` is raised.
    """
    self._check_command_id_is_valid(command_id)
    
    for group in self._process_groups_arg(groups):
      if group not in self._command_items[command_id].groups:
        self._add_command_to_group(self._command_items[command_id], group, position)
  
  def contains(
        self,
        command: Union[Callable, Invoker],
        groups: Union[None, str, List[str]] = None,
        foreach: bool = False,
  ) -> bool:
    """Returns ``True`` if the specified command exists, ``False`` otherwise.

    ``command`` can be a function or `Invoker` instance.
    
    For information about the ``groups`` parameter, see `has_command()`.
    
    If ``foreach`` is ``True``, the command is treated as a for-each command.
    """
    command_functions = self._get_command_lists_and_functions(
      self._get_command_type(command, foreach))[1]
    
    for group in self._process_groups_arg(groups):
      if command in command_functions[group]:
        return True
    
    return False
  
  def find(
        self,
        command: Union[Callable, Invoker],
        groups: Union[None, str, List[str]] = None,
        foreach: bool = False,
  ) -> List[int]:
    """Returns command IDs matching the specified command.

    ``command`` can be a function or `Invoker` instance.
    
    For information about the ``groups`` parameter, see `has_command()`.
    
    If ``foreach`` is ``True``, the command is treated as a for-each command.
    """
    command_type = self._get_command_type(command, foreach)
    command_lists = self._get_command_lists_and_functions(command_type)[0]
    
    processed_groups = [
      group for group in self._process_groups_arg(groups)
      if group in self.list_groups()]
    
    found_command_ids = []
    
    for group in processed_groups:
      found_command_ids.extend([
        command_item.command_id
        for command_item in command_lists[group]
        if (command_item.command_function == command and command_item.command_type == command_type)
      ])
    
    return found_command_ids
  
  def has_command(self, command_id: int, groups: Union[None, str, List[str]] = None) -> bool:
    """Returns ``True`` if a command exists in at least one of the specified
    groups, ``False`` otherwise.

    The command is specified by its ID returned from `add()`.
    
    ``groups`` can have one of the following values:
     * ``None`` or ``'default'`` - the default group,
     * list of group names (strings) - specific groups,
     * ``'all'`` - all existing groups.
    """
    return (
          command_id in self._command_items
          and any(group in self._command_items[command_id].groups
              for group in self._process_groups_arg(groups)))
  
  def get_command(self, command_id: int) -> Union[Callable, Invoker, None]:
    """Returns a command specified by its ID.

    If the ID is not valid, ``None`` is returned.
    """
    if command_id in self._command_items:
      return self._command_items[command_id].command
    else:
      return None
  
  def get_position(self, command_id: int, group: Union[None, str, List[str]] = None) -> int:
    """Returns the position of the command specified by its ID in the specified
    group.

    If ``group`` is ``None`` or ``'default'``, use the default group.
    
    If the ID is not valid or the command is not in the group, `ValueError` is
    raised.
    """
    if group is None:
      group = 'default'
    
    self._check_command_id_is_valid(command_id)
    self._check_command_in_group(command_id, group)
    
    command_item = self._command_items[command_id]
    command_lists, _unused = self._get_command_lists_and_functions(command_item.command_type)

    return command_lists[group].index(command_item)
  
  def list_commands(
        self, group: Optional[str] = None, foreach: bool = False,
  ) -> Optional[List[Union[Callable, Invoker]]]:
    """Returns all commands for the specified group in the order they would be
    invoked.

    Commands are returned along with their arguments and keyword arguments.

    If the group does not exist, ``None`` is returned.

    If ``foreach`` is ``True``, for-each commands are returned instead.
    """
    if group is None:
      group = 'default'
    
    if not foreach:
      command_items = self._commands
    else:
      command_items = self._foreach_commands
    
    if group in self._commands:
      return [item.command for item in command_items[group]]
    else:
      return None
  
  def list_groups(self, include_empty_groups: bool = True) -> List[str]:
    """Returns a list of all groups in the invoker.
    
    If ``include_empty_groups`` is ``False``, groups with no commands are not
    included.
    """
    if include_empty_groups:
      return list(self._commands)
    else:
      def _is_group_non_empty(group):
        return any(
          (group in command_lists and command_lists[group])
          for command_lists in [self._commands, self._foreach_commands])
      
      return [group for group in self._commands if _is_group_non_empty(group)]
  
  def reorder(self, command_id: int, position: int, group: Optional[str] = None):
    """Change the order in which a command is invoked.
    
    The command is specified by its ID (as returned by `add()`).
    
    If ``group`` is ``None`` or ``'default'``, the default group is used.
    
    A position of 0 moves the command to the beginning.
    Negative numbers move the command to the n-th to last position, i.e. -1
    for the last position, -2 for the second to last position, etc.
    
    `ValueError` is raised if:
    * ``command_id`` is not valid
    * ``group`` does not exist
    * the command having ``command_id`` is not in ``group``
    """
    if group is None:
      group = 'default'
    
    self._check_command_id_is_valid(command_id)
    self._check_group_exists(group)
    self._check_command_in_group(command_id, group)
    
    command_item = self._command_items[command_id]
    command_lists, _unused = self._get_command_lists_and_functions(command_item.command_type)
    
    command_lists[group].pop(command_lists[group].index(command_item))
    
    if position < 0:
      position = max(len(command_lists[group]) + position + 1, 0)
    
    command_lists[group].insert(position, command_item)
  
  def remove(
        self,
        command_id: int,
        groups: Union[None, str, List[str]] = None,
        ignore_if_not_exists: bool = False):
    """Removes a command specified by its ID from the specified groups.
    
    For information about the ``groups`` parameter, see `has_command()`.
    
    For existing groups where the command is not added, nothing is removed.
    
    If ``ignore_if_not_exists`` is ``True``, ``ValueError`` is not raised if
    ``command_id`` does not match any added command.
    
    `ValueError` is raised if:
    * ``command_id`` is invalid and ``ignore_if_not_exists`` is ``False``
    * at least one of the specified groups does not exist
    """
    if ignore_if_not_exists:
      if command_id not in self._command_items:
        return
    else:
      self._check_command_id_is_valid(command_id)
    
    command_list, command_functions = self._get_command_lists_and_functions(
      self._command_items[command_id].command_type)
    
    for group in self._process_groups_arg(groups):
      self._check_group_exists(group)
      
      if group in self._command_items[command_id].groups:
        self._remove_command(command_id, group, command_list, command_functions)
        if command_id not in self._command_items:
          break
  
  def remove_groups(self, groups: Union[None, str, List[str]] = None):
    """Removes the specified groups and their commands (including for-each
    commands).
    
    For information about the ``groups`` parameter, see `has_command()`.
    
    Non-existent groups in ``groups`` are ignored.
    """
    processed_groups = [
      group for group in self._process_groups_arg(groups)
      if group in self.list_groups()]
    
    for group in processed_groups:
      for command_item in self._commands[group]:
        if command_item.command_type == self._TYPE_COMMAND:
          self._remove_command(
            command_item.command_id, group, self._commands, self._command_functions)
        else:
          self._remove_command(command_item.command_id, group, self._commands, self._invokers)
      
      for command_item in self._foreach_commands[group]:
        self._remove_command(
          command_item.command_id, group, self._foreach_commands, self._foreach_command_functions)
      
      del self._commands[group]
      del self._foreach_commands[group]
  
  def _init_group(self, group):
    if group not in self._commands:
      self._commands[group] = []
      self._foreach_commands[group] = []
  
  def _add_command_to_group(self, command_item, group, position):
    if command_item.command_type == self._TYPE_COMMAND:
      self._add_command(
        command_item.command_id,
        command_item.command[0],
        group,
        command_item.command[1],
        command_item.command[2],
        position,
        command_item.run_generator)
    elif command_item.command_type == self._TYPE_FOREACH_COMMAND:
      self._add_foreach_command(
        command_item.command_id,
        command_item.command[0],
        group,
        command_item.command[1],
        command_item.command[2],
        position,
        command_item.run_generator)
    elif command_item.command_type == self._TYPE_INVOKER:
      self._add_invoker(command_item.command_id, command_item.command, group, position)
  
  def _add_command(
        self, command_id, command, group, command_args, command_kwargs, position, run_generator):
    self._init_group(group)
    
    command_item = self._set_command_item(
      command_id,
      group,
      (command, command_args, command_kwargs),
      self._TYPE_COMMAND,
      command,
      run_generator)
    
    if position is None:
      self._commands[group].append(command_item)
    else:
      self._commands[group].insert(position, command_item)
    
    self._command_functions[group][command] += 1
  
  def _add_foreach_command(
        self,
        command_id,
        foreach_command,
        group,
        foreach_command_args,
        foreach_command_kwargs,
        position,
        run_generator):
    self._init_group(group)
    
    if not inspect.isgeneratorfunction(foreach_command):
      def invoke_foreach_command_after_command(*args, **kwargs):
        yield
        foreach_command(*args, **kwargs)
      
      foreach_command_generator_function = invoke_foreach_command_after_command
    else:
      foreach_command_generator_function = foreach_command
    
    command_item = self._set_command_item(
      command_id,
      group,
      (foreach_command_generator_function,
       foreach_command_args,
       foreach_command_kwargs),
      self._TYPE_FOREACH_COMMAND,
      foreach_command,
      run_generator)
    
    if position is None:
      self._foreach_commands[group].append(command_item)
    else:
      self._foreach_commands[group].insert(position, command_item)
    
    self._foreach_command_functions[group][foreach_command] += 1
  
  def _add_invoker(self, command_id, invoker, group, position):
    self._init_group(group)
    
    command_item = self._set_command_item(
      command_id, group, invoker, self._TYPE_INVOKER, invoker, False)
    
    if position is None:
      self._commands[group].append(command_item)
    else:
      self._commands[group].insert(position, command_item)
    
    self._invokers[group][invoker] += 1
  
  def _get_command_id(self):
    return next(self._command_id_counter)
  
  def _set_command_item(
        self,
        command_id,
        group,
        command,
        command_type,
        command_function,
        run_generator):
    if command_id not in self._command_items:
      self._command_items[command_id] = _CommandItem(
        command, command_id, None, command_type, command_function, run_generator)
    
    self._command_items[command_id].groups.add(group)
    
    return self._command_items[command_id]
  
  def _remove_command(self, command_id, group, command_lists, command_functions):
    command_item = self._command_items[command_id]
    command_lists[group].remove(command_item)
    
    command_functions[group][command_item.command_function] -= 1
    if command_functions[group][command_item.command_function] == 0:
      del command_functions[group][command_item.command_function]
    
    self._remove_command_item(command_id, group)
  
  def _remove_command_item(self, command_id, group):
    self._command_items[command_id].groups.remove(group)
    
    if not self._command_items[command_id].groups:
      del self._command_items[command_id]
  
  def _process_groups_arg(self, groups):
    if groups is None or groups == 'default':
      return ['default']
    elif groups == 'all':
      return self.list_groups()
    else:
      return groups
  
  def _get_command_type(self, command, is_foreach):
    if is_foreach:
      return self._TYPE_FOREACH_COMMAND
    else:
      if callable(command):
        return self._TYPE_COMMAND
      else:
        return self._TYPE_INVOKER
  
  def _get_command_lists_and_functions(self, command_type):
    if command_type == self._TYPE_COMMAND:
      return self._commands, self._command_functions
    elif command_type == self._TYPE_FOREACH_COMMAND:
      return self._foreach_commands, self._foreach_command_functions
    elif command_type == self._TYPE_INVOKER:
      return self._commands, self._invokers
    else:
      raise ValueError(
        f'invalid command type {command_type}; must be one of {self._COMMAND_TYPES}')
  
  def _check_command_id_is_valid(self, command_id):
    if command_id not in self._command_items:
      raise ValueError(f'command with ID {command_id} does not exist')
  
  def _check_group_exists(self, group, groups=None):
    if groups is None:
      groups = self.list_groups()
    
    if group not in groups:
      raise ValueError(f'group "{group}" does not exist')
  
  def _check_command_in_group(self, command_id, group):
    if group not in self._command_items[command_id].groups:
      raise ValueError(f'command with ID {command_id} is not in group "{group}"')


class _CommandItem:
  
  def __init__(self, command, command_id, groups, command_type, command_function, run_generator):
    self.command = command
    self.command_id = command_id
    self.groups = groups if groups is not None else set()
    # noinspection PyProtectedMember
    self.command_type = command_type if command_type is not None else Invoker._TYPE_COMMAND
    self.command_function = command_function
    self.run_generator = run_generator
    
    self.is_generator = False
    self.generators_per_group = {}
    self.should_be_removed_from_group = False
