"""Batch-processing and exporting images."""

import abc
import collections
from collections.abc import Iterable
import contextlib
import os
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import builtin_actions
from src import builtin_commands_common
from src import builtin_conditions
from src import commands
from src import exceptions
from src import invoker as invoker_
from src import itemtree
from src import overwrite
from src import placeholders
from src import progress as progress_
from src import pypdb
from src import setting as setting_
from src import utils
from src import utils_pdb
from src.pypdb import pdb


_BATCHER_ARG_POSITION_IN_COMMANDS = 0
_NAME_ONLY_COMMAND_GROUP = 'name'


class Batcher(metaclass=abc.ABCMeta):
  """Abstract class for batch-processing items with a sequence of commands
  (resize, rename, export, ...).
  """

  def __init__(
        self,
        item_tree: itemtree.ItemTree,
        actions: setting_.Group,
        conditions: setting_.Group,
        refresh_item_tree: bool = True,
        edit_mode: bool = False,
        initial_export_run_mode: Gimp.RunMode = Gimp.RunMode.WITH_LAST_VALS,
        output_directory: Gio.File = Gio.file_new_for_path(utils.get_default_dirpath()),
        name_pattern: str = '',
        file_extension: str = 'png',
        overwrite_mode: str = overwrite.OverwriteModes.RENAME_NEW,
        overwrite_chooser: Optional[overwrite.OverwriteChooser] = None,
        more_export_options: Dict[str, Any] = None,
        progress_updater: Optional[progress_.ProgressUpdater] = None,
        is_preview: bool = False,
        process_contents: bool = True,
        process_names: bool = True,
        process_export: bool = True,
        export_context_manager: Optional[contextlib.AbstractContextManager] = None,
        export_context_manager_args: Optional[Union[List, Tuple]] = None,
        export_context_manager_kwargs: Optional[Dict] = None,
        keep_image_copies: bool = False,
  ):
    self._item_tree = item_tree
    self._actions = actions
    self._conditions = conditions
    self._refresh_item_tree = refresh_item_tree
    self._edit_mode = edit_mode
    self._initial_export_run_mode = initial_export_run_mode
    self._output_directory = output_directory
    self._name_pattern = name_pattern
    self._file_extension = file_extension
    self._overwrite_mode = overwrite_mode
    self._overwrite_chooser = overwrite_chooser
    self._more_export_options = more_export_options
    self._progress_updater = progress_updater
    self._is_preview = is_preview
    self._process_contents = process_contents
    self._process_names = process_names
    self._process_export = process_export
    self._export_context_manager = export_context_manager
    self._export_context_manager_args = export_context_manager_args
    self._export_context_manager_kwargs = export_context_manager_kwargs
    self._keep_image_copies = keep_image_copies

    self._current_item = None
    self._current_image = None
    self._current_layer = None
    self._current_action = None
    self._last_condition = None

    self._matching_items = None
    self._matching_items_and_parents = None
    self._exported_items = []

    self._image_copies = []
    self._orig_images_and_selected_layers = {}

    self._skipped_actions = collections.defaultdict(list)
    self._skipped_conditions = collections.defaultdict(list)
    self._failed_actions = collections.defaultdict(list)
    self._failed_conditions = collections.defaultdict(list)

    self._should_stop = False

    self._invoker = None
    self._initial_invoker = invoker_.Invoker()

  @property
  def item_tree(self) -> itemtree.ItemTree:
    """`itemtree.ItemTree` instance containing items to be processed.

    If the item tree has filters (conditions) set, they will be reset on each
    call to `run()`.
    """
    return self._item_tree

  @property
  def actions(self) -> setting_.Group:
    """Command group containing actions."""
    return self._actions

  @property
  def conditions(self) -> setting_.Group:
    """Command group containing conditions."""
    return self._conditions

  @property
  def refresh_item_tree(self) -> bool:
    """If ``True``, `item_tree` is refreshed on each call to `run()`.

    Specifically, `item_tree.refresh()` is invoked before the start of
    processing. See `itemtree.ItemTree.refresh()` for more information.
    """
    return self._refresh_item_tree

  @property
  def edit_mode(self) -> bool:
    """Determines whether to modify existing items or modify and export copies of
    these items.

    If ``True``, batch processing is perform directly on each item.

    If ``False``, items are copied, and batch processing and export is performed
    on the copies. The original items are kept intact.
    """
    return self._edit_mode

  @property
  def initial_export_run_mode(self) -> Gimp.RunMode:
    """The run mode to use for the first item when exporting if using the
    native file format dialog.

    If ``initial_export_run_mode`` is `Gimp.RunMode.INTERACTIVE`, a native
    file format GUI is displayed for the first item. For subsequent items,
    the same settings are applied and `Gimp.RunMode.WITH_LAST_VALS` is used.

    Instead of using the native file format dialog, one can pass explicit
    file format arguments. This can be done by including
    ``file_format_mode=export.FileFormatModes.USE_EXPLICIT_VALUES`` and
    ``file_format_options=<dictionary of file format-specific options>``
    in the ``more_export_options`` dictionary.

    If the file format cannot handle `Gimp.RunMode.WITH_LAST_VALS`,
    `Gimp.RunMode.INTERACTIVE` is forced for each item.
    """
    return self._initial_export_run_mode

  @property
  def output_directory(self) -> Gio.File:
    """Output directory to save exported items to."""
    return self._output_directory

  @property
  def name_pattern(self) -> str:
    """Name pattern for items to be exported."""
    return self._name_pattern

  @property
  def file_extension(self) -> str:
    """Filename extension for items to be exported."""
    return self._file_extension

  @property
  def overwrite_mode(self) -> str:
    """One of the `overwrite.OverwriteModes` values indicating how to
    handle files with the same name.
    """
    return self._overwrite_mode

  @property
  def overwrite_chooser(self) -> overwrite.OverwriteChooser:
    """`overwrite.OverwriteChooser` instance that is invoked during export if a
    file with the same name already exists.

    By default, `overwrite.NoninteractiveOverwriteChooser` is used.
    """
    return self._overwrite_chooser

  @property
  def more_export_options(self) -> Dict[str, Any]:
    """Dictionary containing export options for each file extension as a key.

    This property returns a shallow copy of the original dictionary to avoid
    modifying the original.
    """
    return dict(self._more_export_options) if self._more_export_options is not None else {}

  @property
  def progress_updater(self) -> progress_.ProgressUpdater:
    """`progress.ProgressUpdater` instance indicating the number of items
    processed so far.

    If ``progress_updater=None`` was passed to `__init__()`, progress update is
    not tracked.
    """
    return self._progress_updater

  @property
  def is_preview(self) -> bool:
    """If ``True``, only actions and conditions that are marked as
    "enabled for previews" will be applied for previews. If ``False``, this
    property has no effect (and effectively allows performing real processing).
    """
    return self._is_preview

  @property
  def process_contents(self) -> bool:
    """If ``True``, actions are invoked on items.

    Setting this to ``False`` is useful if you require only item names to be
    processed.
    """
    return self._process_contents

  @property
  def process_names(self) -> bool:
    """If ``True``, item names are processed before export to be suitable to
    save to disk (in particular to remove characters invalid for a file system).

    If `is_preview` is ``True`` and `process_names` is ``True``, built-in
    actions modifying item names only are also invoked (particularly those
    with the `builtin_commands_common.NAME_ONLY_TAG` tag).
    """
    return self._process_names

  @property
  def process_export(self) -> bool:
    """If ``True``, perform export of items.

    Setting this to ``False`` is useful to preview the processed contents of an
    item without saving it to a file.
    """
    return self._process_export

  @property
  def export_context_manager(self) -> contextlib.AbstractContextManager:
    """Context manager that wraps exporting a single item.

    This can be used to perform GUI updates before and after export.

    Required parameters: current run mode, current image, item to export,
    output filename of the item.
    """
    return self._export_context_manager

  @property
  def export_context_manager_args(self) -> Tuple:
    """Additional positional arguments passed to `export_context_manager`."""
    return self._export_context_manager_args

  @property
  def export_context_manager_kwargs(self) -> Dict:
    """Additional keyword arguments passed to `export_context_manager`."""
    return self._export_context_manager_kwargs

  @property
  def keep_image_copies(self) -> bool:
    """If ``True`` and `edit_mode` is ``False``, image copies are preserved once
    batch processing and export (a `run()` call) is done.
    """
    return self._keep_image_copies

  @property
  def current_item(self) -> itemtree.Item:
    """A `itemtree.Item` instance currently being processed."""
    return self._current_item

  @property
  def current_image(self) -> Optional[Gimp.Image]:
    """A `Gimp.Image` instance currently being processed.

    This property is ``None`` outside the processing.
    """
    return self._current_image

  @current_image.setter
  def current_image(self, value: Gimp.Image):
    self._current_image = value

  @property
  def current_layer(self) -> Optional[Gimp.Layer]:
    """A `Gimp.Layer` instance currently being processed.

    This property is ``None`` outside the processing.
    """
    return self._current_layer

  @current_layer.setter
  def current_layer(self, value: Gimp.Layer):
    self._current_layer = value

  @property
  def current_action(self) -> setting_.Group:
    """The action currently being applied to `current_item`."""
    return self._current_action

  @property
  def last_condition(self) -> setting_.Group:
    """The most recent condition that was evaluated."""
    return self._last_condition

  @property
  def matching_items(self) -> Optional[Dict[itemtree.Item, Optional[itemtree.Item]]]:
    """A dictionary of (item, next item or None) pairs matching the conditions,
    or ``None`` if not initialized.

    This is useful if you need to work with items matching conditions at the
    start of processing as some items may no longer match these conditions
    at the end of processing.
    """
    return self._matching_items

  @property
  def matching_items_and_parents(
        self,
  ) -> Optional[Dict[itemtree.Item, Optional[itemtree.Item]]]:
    """A dictionary of (item, next item or None) pairs matching the conditions,
    including the parents of the matching items, or ``None`` if not initialized.

    This is useful if you need to work with items matching conditions at the
    start of processing as some items may no longer match these conditions
    at the end of processing.
    """
    return self._matching_items_and_parents

  @property
  def exported_items(self) -> List[itemtree.Item]:
    """List of successfully exported items.

    This list does not include items skipped by the user (when files with the
    same names already exist).
    """
    return list(self._exported_items)

  @property
  def image_copies(self) -> List[Gimp.Image]:
    """`Gimp.Image` instances as copies of original images.

    If ``keep_image_copies`` is ``False`` or creating an image copy is not
    applicable (if ``edit_mode`` is ``True``), this will return an empty list.
    """
    return list(self._image_copies)

  @property
  def skipped_actions(self) -> Dict[str, List]:
    """Actions that were skipped during processing.

    A skipped action was not applied to one or more items and causes no
    adverse effects further during processing.
    """
    return dict(self._skipped_actions)

  @property
  def skipped_conditions(self) -> Dict[str, List]:
    """Conditions that were skipped during processing.

    A skipped condition was not evaluated for one or more items and causes no
    adverse effects further during processing.
    """
    return dict(self._skipped_conditions)

  @property
  def failed_actions(self) -> Dict[str, List]:
    """Actions that caused an error during processing.

    Failed actions indicate a problem with the action parameters or
    potentially a bug.
    """
    return dict(self._failed_actions)

  @property
  def failed_conditions(self) -> Dict[str, List]:
    """Conditions that caused an error during processing.

    Failed conditions indicate a problem with the condition parameters or
    potentially a bug.
    """
    return dict(self._failed_conditions)

  @property
  def invoker(self) -> invoker_.Invoker:
    """`invoker.Invoker` instance to manage actions and conditions applied on
    items.

    This property is reset on each call of `run()`.
    """
    return self._invoker

  def add_action(self, *args, **kwargs) -> Union[int, None]:
    """Adds an action to be applied during `run()`.

    The signature is the same as for `invoker.Invoker.add()`.

    Actions added by this method are placed before actions added by
    `commands.add()`.

    Actions are added immediately before the start of processing. Thus,
    calling this method during processing will have no effect.

    Unlike `commands.add()`, actions added by this method do not act as
    settings, i.e. they are merely functions without GUI, are not saved
    persistently and are always enabled.

    This class recognizes several command groups that are invoked at certain
    places when `run()` is called:

    * ``'before_process_items'`` - invoked before starting processing the first
      item. One argument is required - a `Batcher` instance.

    * ``'before_process_items_contents'`` - same as ``'before_process_items'``,
      but applied only if `process_contents` is ``True``.

    * ``'after_process_items'`` - invoked after finishing processing the last
      item. One argument is required - a `Batcher` instance.

    * ``'after_process_items_contents'`` - same as ``'after_process_items'``,
      but applied only if `process_contents` is ``True``.

    * ``'before_process_item'`` - invoked immediately before applying actions
      on an item. One argument is required - a `Batcher` instance.

    * ``'before_process_item_contents'`` - same as ``'before_process_item'``,
      but applied only if `process_contents` is ``True``.

    * ``'after_process_item'`` - invoked immediately after all actions have
      been applied to an item. One argument is required - a `Batcher` instance.

    * ``'after_process_item_contents'`` - same as ``'after_process_item'``, but
      applied only if `process_contents` is ``True``.

    * ``'cleanup_contents'`` - invoked after processing is finished and cleanup
      is commenced (e.g. removing temporary internal images). Use this if you
      create temporary images or items of your own. While you may also achieve
      the same effect with ``'after_process_items_contents'``, using
      ``'cleanup_contents'`` is safer as it is also invoked when an exception is
      raised. One argument is required - a `Batcher` instance.
    """
    return self._initial_invoker.add(*args, **kwargs)

  def add_condition(self, func, *args, **kwargs) -> Union[int, None]:
    """Adds a condition to be applied during `run()`.

    The first argument is the function to act as a filter (returning ``True``
    or ``False``). The rest of the signature is the same as for
    `invoker.Invoker.add()`.

    For more information, see `add_action()`.
    """
    return self._initial_invoker.add(self._get_condition_func(func), *args, **kwargs)

  def remove_command(self, *args, **kwargs):
    """Removes a command originally scheduled to be applied during `run()`.

    The signature is the same as for `invoker.Invoker.remove()`.
    """
    self._initial_invoker.remove(*args, **kwargs)

  def reorder_command(self, *args, **kwargs):
    """Reorders a command to be applied during `run()`.

    The signature is the same as for `invoker.Invoker.reorder()`.
    """
    self._initial_invoker.reorder(*args, **kwargs)

  def run(self, **kwargs):
    """Batch-processes and exports items.

    ``**kwargs`` can contain arguments that can be passed to
    `Batcher.__init__()`. Arguments in ``**kwargs`` overwrite the
    corresponding `Batcher` properties. See the properties for details.
    """
    self._set_attributes(**kwargs)
    self._set_up_item_tree()
    self._prepare_for_processing()

    exception_occurred = False

    if self._process_contents:
      self._setup_contents()
    try:
      self._process_items()
    except Exception:
      exception_occurred = True
      raise
    finally:
      if self._process_contents:
        self._cleanup_contents(exception_occurred)

  def _set_attributes(self, **kwargs):
    for name, value in kwargs.items():
      if hasattr(self, f'_{name}'):
        setattr(self, f'_{name}', value)
      else:
        raise ValueError(f'argument "{name}" is not recognized')

    if self._overwrite_chooser is None:
      self._overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(self._overwrite_mode)
    else:
      self._overwrite_chooser.overwrite_mode = self._overwrite_mode

    if self._more_export_options is None:
      self._more_export_options = {}

    if self._progress_updater is None:
      self._progress_updater = progress_.ProgressUpdater(None)

    if self._export_context_manager is None:
      self._export_context_manager = utils.empty_context

    if self._export_context_manager_args is None:
      self._export_context_manager_args = ()
    else:
      self._export_context_manager_args = tuple(self._export_context_manager_args)

    if self._export_context_manager_kwargs is None:
      self._export_context_manager_kwargs = {}

  def _set_up_item_tree(self):
    if self._refresh_item_tree:
      self._item_tree.refresh()

    self._item_tree.reset_filter()

  def _prepare_for_processing(self):
    self._current_item = None
    self._current_image = None
    self._current_layer = None
    self._current_action = None
    self._last_condition = None

    self._should_stop = False

    self._matching_items = None
    self._matching_items_and_parents = None
    self._exported_items = []

    self._image_copies = []
    self._orig_images_and_selected_layers = {}

    self._skipped_actions = collections.defaultdict(list)
    self._skipped_conditions = collections.defaultdict(list)
    self._failed_actions = collections.defaultdict(list)
    self._failed_conditions = collections.defaultdict(list)

    self._invoker = invoker_.Invoker()

    self._add_commands()
    self._add_name_only_commands()

    self._set_conditions()

    self._progress_updater.reset()

  def _add_commands(self):
    self._add_commands_before_initial_invoker()

    self._invoker.add(
      self._initial_invoker,
      self._initial_invoker.list_groups(include_empty_groups=True))

    self._add_commands_before_actions_from_settings()

    for action in self._actions:
      self._add_command_from_settings(action)

    self._add_commands_after_actions_from_settings()

    for condition in self._conditions:
      self._add_command_from_settings(condition)

  def _add_commands_before_initial_invoker(self):
    pass

  def _add_commands_before_actions_from_settings(self):
    pass

  def _add_commands_after_actions_from_settings(self):
    pass

  def _add_name_only_commands(self):
    self._add_name_only_commands_before_actions_from_settings()

    for action in self._actions:
      self._add_command_from_settings(
        action,
        [builtin_commands_common.NAME_ONLY_TAG],
        [_NAME_ONLY_COMMAND_GROUP])

    self._add_name_only_commands_after_actions_from_settings()

    for condition in self._conditions:
      self._add_command_from_settings(
        condition,
        [builtin_commands_common.NAME_ONLY_TAG],
        [_NAME_ONLY_COMMAND_GROUP])

  def _add_name_only_commands_before_actions_from_settings(self):
    pass

  def _add_name_only_commands_after_actions_from_settings(self):
    pass

  def _add_command_from_settings(
        self,
        command: setting_.Group,
        tags: Optional[Iterable[str]] = None,
        command_groups: Union[str, List[str], None] = None,
  ):
    """Adds a command and wraps/processes the command's function according to the
    command's settings.

    For PDB procedures, the function name is converted to a proper function
    object. For conditions, the function is wrapped to act as a proper filter
    rule for `item_tree.filter`. Any placeholder objects (e.g. "current image")
    as function arguments are replaced with real objects during processing of
    each item.

    If ``tags`` is not ``None``, the command will not be added if it does not
    contain any of the specified tags.

    If ``command_groups`` is not ``None``, the command will be added to the
    specified command groups instead of the groups defined in ``command[
    'command_groups']``.
    """
    if command['origin'].value == 'builtin':
      if 'action' in command.tags:
        function = builtin_actions.BUILTIN_ACTIONS_FUNCTIONS[
          command['orig_name'].value]
      elif 'condition' in command.tags:
        function = builtin_conditions.BUILTIN_CONDITIONS_FUNCTIONS[
          command['orig_name'].value]
      else:
        raise exceptions.CommandError(
          f'invalid command "{command.name}" - must contain "action" or "condition" in tags',
          command,
          None,
          None)
    elif command['origin'].value in ['gimp_pdb', 'gegl']:
      if command['function'].value in pdb:
        function = pdb[command['function'].value]
      else:
        if command['enabled'].value:
          message = f'PDB procedure "{command["function"].value}" not found'

          if 'action' in command.tags:
            self._failed_actions[command.name].append((None, message, None))
          if 'condition' in command.tags:
            self._failed_conditions[command.name].append((None, message, None))

          raise exceptions.CommandError(message, command, None, None)
        else:
          return
    else:
      raise exceptions.CommandError(
        f'invalid origin {command["origin"].value} for command "{command.name}"',
        command,
        None,
        None)

    if function is None:
      return

    if tags is not None and not any(tag in command.tags for tag in tags):
      return

    processed_function = self._get_processed_function(command)

    processed_function = self._handle_exceptions_from_command(processed_function, command)

    if command_groups is None:
      command_groups = command['command_groups'].value

    invoker_args = list(command['arguments']) + [function]

    self._invoker.add(processed_function, command_groups, invoker_args)

  def _get_processed_function(self, command):

    def _function_wrapper(*command_args_and_function):
      command_args, function = command_args_and_function[:-1], command_args_and_function[-1]

      if not self._is_enabled(command):
        return False

      self._set_current_action_and_condition(command)

      args, kwargs = self._get_command_args_and_kwargs(command, command_args)

      if 'condition' in command.tags:
        function = self._set_apply_condition_to_folders(function, command)
        function = self._get_condition_func(function, command['orig_name'].value)

      return function(*args, **kwargs)

    return _function_wrapper

  def _is_enabled(self, command):
    if self._is_preview:
      if not (command['enabled'].value and command['more_options/enabled_for_previews'].value):
        return False
    else:
      if not command['enabled'].value:
        return False

    return True

  def _set_current_action_and_condition(self, command):
    if 'action' in command.tags:
      self._current_action = command

    if 'condition' in command.tags:
      self._last_condition = command

  def _get_command_args_and_kwargs(self, command, command_args):
    args, kwargs = self._get_replaced_args(
      command_args, command['origin'].value in ['gimp_pdb', 'gegl'])

    if command['origin'].value in ['gimp_pdb', 'gegl']:
      args.pop(_BATCHER_ARG_POSITION_IN_COMMANDS)

    return args, kwargs

  def _get_replaced_args(self, command_arguments, is_function_pdb_procedure):
    """Returns positional and keyword arguments for a command, replacing any
    placeholder values with real values.
    """
    replaced_args = []
    replaced_kwargs = {}

    for argument in command_arguments:
      if isinstance(argument, placeholders.PlaceholderArraySetting):
        replaced_arg = placeholders.get_replaced_value(argument, self)
        if is_function_pdb_procedure:
          replaced_kwargs[argument.name] = setting_.array_as_pdb_compatible_type(replaced_arg)
        else:
          replaced_kwargs[argument.name] = replaced_arg
      elif isinstance(argument, placeholders.PlaceholderSetting):
        replaced_kwargs[argument.name] = placeholders.get_replaced_value(argument, self)
      elif isinstance(argument, setting_.Setting):
        if is_function_pdb_procedure:
          replaced_kwargs[argument.name] = argument.value_for_pdb
        else:
          replaced_kwargs[argument.name] = argument.value
      else:
        # Other arguments inserted within `Batcher`
        replaced_args.append(argument)

    return replaced_args, replaced_kwargs

  @staticmethod
  def _set_apply_condition_to_folders(function, command):
    if command['more_options/also_apply_to_parent_folders'].value:

      def _function_wrapper(*command_args, **command_kwargs):
        item = command_args[0]
        result = True
        for item_or_parent in [item] + item.parents[::-1]:
          result = result and function(item_or_parent, *command_args[1:], **command_kwargs)
          if not result:
            break

        return result

      return _function_wrapper
    else:
      return function

  def _get_condition_func(self, func, name=''):

    def _function_wrapper(*args, **kwargs):
      self._item_tree.filter.add(func, args, kwargs, name=name)

    return _function_wrapper

  def _handle_exceptions_from_command(self, function, command):
    def _handle_exceptions(*args, **kwargs):
      try:
        retval = function(*args, **kwargs)
      except exceptions.SkipCommand as e:
        # Log skipped commands and continue processing.
        self._set_skipped_commands(command, str(e))
      except pypdb.PDBProcedureError as e:
        error_message = e.message
        if error_message is None:
          error_message = _(
            'An error occurred. Please check the GIMP error message'
            ' or the error console for details, if any.')

        # Log failed command, but raise error as this may result in unexpected
        # behavior.
        self._set_failed_commands(command, error_message)

        raise exceptions.CommandError(error_message, command, self._current_item)
      except Exception as e:
        trace = traceback.format_exc()
        # Log failed command, but raise error as this may result in unexpected
        # behavior.
        self._set_failed_commands(command, str(e), trace)

        raise exceptions.CommandError(str(e), command, self._current_item, trace)
      else:
        return retval

    return _handle_exceptions

  def _set_skipped_commands(self, command, error_message):
    if 'action' in command.tags:
      self._skipped_actions[command.name].append((self._current_item, error_message))
    if 'condition' in command.tags:
      self._skipped_conditions[command.name].append((self._current_item, error_message))

  def _set_failed_commands(self, command, error_message, trace=None):
    if 'action' in command.tags:
      self._failed_actions[command.name].append((self._current_item, error_message, trace))
    if 'condition' in command.tags:
      self._failed_conditions[command.name].append((self._current_item, error_message, trace))

  def _set_conditions(self):
    self._invoker.invoke(
      [commands.DEFAULT_CONDITIONS_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

  def _setup_contents(self):
    Gimp.context_push()

  def _process_items(self):
    self._matching_items, self._matching_items_and_parents = self._get_items_matching_conditions()

    self._progress_updater.num_total_tasks = len(self._matching_items)

    self._invoker.invoke(
      ['before_process_items'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    if self._process_contents:
      self._invoker.invoke(
        ['before_process_items_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    for item in self._matching_items:
      if self._should_stop:
        raise exceptions.BatcherCancelError('stopped by user')

      if self._edit_mode:
        self._progress_updater.update_text(_('Processing "{}"').format(item.orig_name))

      self._process_item(item)

    if self._process_contents:
      self._invoker.invoke(
        ['after_process_items_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._invoker.invoke(
      ['after_process_items'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

  def _get_items_matching_conditions(self):
    def _get_matching_items_and_next_items(matching_items_list_):
      matching_items_ = {}

      matching_next_items_list_ = list(matching_items_list_)
      if matching_next_items_list_:
        del matching_next_items_list_[0]
        matching_next_items_list_.append(None)

      for item_, next_item_ in zip(matching_items_list_, matching_next_items_list_):
        matching_items_[item_] = next_item_

      return matching_items_

    visited_parents = set()
    matching_items_and_parents_list = []
    matching_items_list = []

    for item in self._item_tree:
      for parent in item.parents:
        if parent not in visited_parents:
          matching_items_and_parents_list.append(parent)
          visited_parents.add(parent)

      matching_items_and_parents_list.append(item)
      matching_items_list.append(item)

    matching_items_and_parents = _get_matching_items_and_next_items(matching_items_and_parents_list)
    matching_items = _get_matching_items_and_next_items(matching_items_list)

    return matching_items, matching_items_and_parents

  def _process_item(self, item):
    self._current_item = item
    self._current_image = self._get_initial_current_image()
    self._current_layer = self._get_initial_current_layer()

    if self._is_preview and self._process_names:
      self._process_item_with_name_only_commands()

    if self._process_contents:
      self._process_item_with_commands()

    self._progress_updater.update_tasks()

  def _process_item_with_name_only_commands(self):
    self._invoker.invoke(
      ['before_process_item'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._invoker.invoke(
      [_NAME_ONLY_COMMAND_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._invoker.invoke(
      ['after_process_item'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

  def _process_item_with_commands(self):
    self._store_selected_layers_in_current_image_and_start_undo_group()

    self._invoker.invoke(
      ['before_process_item'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    if self._process_contents:
      self._invoker.invoke(
        ['before_process_item_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._invoker.invoke(
      [commands.DEFAULT_ACTIONS_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    if self._process_contents:
      self._invoker.invoke(
        ['after_process_item_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._invoker.invoke(
      ['after_process_item'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    if not self._edit_mode and not self._keep_image_copies:
      self._remove_image_copies()

  @abc.abstractmethod
  def _get_initial_current_image(self):
    pass

  @abc.abstractmethod
  def _get_initial_current_layer(self):
    pass

  def _store_selected_layers_in_current_image_and_start_undo_group(self):
    if self._edit_mode and not self._is_preview and self._current_image is not None:
      if self._current_image not in self._orig_images_and_selected_layers:
        self._current_image.undo_group_start()
        self._orig_images_and_selected_layers[self._current_image] = (
          self._current_image.get_selected_layers())

  def _remove_image_copies(self):
    for image in self._image_copies:
      utils_pdb.try_delete_image(image)

    self._image_copies = []

  def _cleanup_contents(self, exception_occurred=False):
    self._invoker.invoke(
      ['cleanup_contents'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._do_cleanup_contents(exception_occurred)

    self._invoker.invoke(
      ['after_cleanup_contents'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_COMMANDS)

    self._current_item = None
    self._current_image = None
    self._current_layer = None
    self._current_action = None
    self._last_condition = None

  def _do_cleanup_contents(self, exception_occurred):
    if not self._edit_mode or self._is_preview:
      if not self._keep_image_copies or exception_occurred:
        self._remove_image_copies()
    else:
      for image, selected_layers in self._orig_images_and_selected_layers.items():
        if not image.is_valid():
          continue

        filtered_selected_layers = [
          layer for layer in selected_layers if layer.is_valid() and layer.get_image() == image]
        if filtered_selected_layers:
          image.set_selected_layers(filtered_selected_layers)

        image.undo_group_end()

      Gimp.displays_flush()

    Gimp.context_pop()

  def queue_stop(self):
    """Instructs `Batcher` to terminate batch processing prematurely.

    The termination occurs after the current item is processed completely.

    This method has no effect if the processing is not running.
    """
    self._should_stop = True

  @abc.abstractmethod
  def create_copy(self, image, layer) -> Tuple[Gimp.Image, Optional[Gimp.Layer]]:
    """Creates a copy of the specified image.

    How the copy is created depends on the subclass.
    """
    pass


class ImageBatcher(Batcher):
  """Class for batch-processing files and opened GIMP images with a sequence of
  commands (resize, rename, export, ...).
  """

  def __init__(self, *args, **kwargs):
    self._should_load_image = False

    super().__init__(*args, **kwargs)

  def _get_initial_current_image(self):
    return self._current_item.raw

  def _get_initial_current_layer(self):
    return None

  def _add_commands_before_initial_invoker(self):
    super()._add_commands_before_initial_invoker()

    self._invoker.add(
      _set_selected_and_current_layer,
      [commands.DEFAULT_ACTIONS_GROUP],
    )

    self._invoker.add(
      _set_selected_and_current_layer_after_command,
      [commands.DEFAULT_ACTIONS_GROUP],
      foreach=True)

  def _add_commands_before_actions_from_settings(self):
    super()._add_commands_before_actions_from_settings()

    self._add_default_rename_action([commands.DEFAULT_ACTIONS_GROUP])

  def _add_commands_after_actions_from_settings(self):
    super()._add_commands_after_actions_from_settings()

    self._add_default_export_action([commands.DEFAULT_ACTIONS_GROUP])

  def _add_name_only_commands_before_actions_from_settings(self):
    self._add_default_rename_action([_NAME_ONLY_COMMAND_GROUP])

  def _add_name_only_commands_after_actions_from_settings(self):
    self._add_default_export_action([_NAME_ONLY_COMMAND_GROUP])

  def _add_default_rename_action(self, command_groups):
    if not self._edit_mode:
      self._invoker.add(
        builtin_actions.rename_image_for_convert,
        groups=command_groups,
        args=[self._name_pattern])

  def _add_default_export_action(self, command_groups):
    if not self._edit_mode:
      self._invoker.add(
        builtin_actions.export,
        groups=command_groups,
        args=[
          self._output_directory,
          self._file_extension,
        ],
        kwargs=self._more_export_options,
      )

  def _process_item_with_commands(self):
    self._should_load_image = self._current_image is None

    if not self._edit_mode or self._is_preview:
      if self._should_load_image:
        loaded_image = self._load_image(self._current_item.id)
        if loaded_image is not None:
          self._current_image = loaded_image
          self._current_item.raw = loaded_image
          self._image_copies.append(loaded_image)
      else:
        image_copy, _not_applicable = self.create_copy(self._current_image, None)

        self._current_image = image_copy
        self._image_copies.append(image_copy)

    self._current_layer = self._get_current_layer(self._current_image)

    if self._current_image is not None:
      super()._process_item_with_commands()

    if self._should_load_image:
      self._current_item.raw = None

    self._current_image = None
    self._current_layer = None

  def _load_image(self, image_filepath):
    if os.path.isfile(image_filepath):
      return pdb.gimp_file_load(
        run_mode=Gimp.RunMode.NONINTERACTIVE,
        file=Gio.file_new_for_path(image_filepath))
    else:
      raise exceptions.BatcherFileLoadError(_('File not found'), self._current_item)

  @staticmethod
  def _get_current_layer(image):
    if image is None or not image.is_valid():
      return None

    layers = image.get_layers()

    if len(layers) == 0:
      return None
    elif len(layers) == 1:
      return layers[0]
    else:
      selected_layers = image.get_selected_layers()
      if selected_layers:
        # There is no way to know which layer is the "right" one, so we resort
        # to taking the first.
        if selected_layers[0].is_valid():
          return selected_layers[0]
      else:
        # There is no way to know which layer is the "right" one, so we resort
        # to taking the first.
        if layers[0].is_valid():
          return layers[0]

    return None

  def create_copy(self, image, layer):
    return image.duplicate(), None

  def _do_cleanup_contents(self, exception_occurred):
    super()._do_cleanup_contents(exception_occurred)

    if self._should_load_image:
      self._current_item.raw = None

    self._should_load_image = False


class LayerBatcher(Batcher):
  """Class for batch-processing layers in the specified image with a sequence of
  commands (resize, rename, export, ...).

  If ``edit_mode`` is ``False``, batch-processing and export of layers is
  performed. The processing and export is applied on a copy of the layer
  within a copy of the original image. Each copy is automatically destroyed
  once the processing of the layer is done. To keep the image and layer
  copies, pass ``keep_image_copies=True`` to `__init__()` or `run()`.
  """

  def _get_initial_current_image(self):
    return self._current_item.raw.get_image()

  def _get_initial_current_layer(self):
    return self._current_item.raw

  def _add_commands_before_initial_invoker(self):
    super()._add_commands_before_initial_invoker()

    self._invoker.add(
      _set_selected_and_current_layer,
      [commands.DEFAULT_ACTIONS_GROUP],
    )

    self._invoker.add(
      _set_selected_and_current_layer_after_command,
      [commands.DEFAULT_ACTIONS_GROUP],
      foreach=True)

    self._invoker.add(
      _sync_item_name_and_layer_name,
      [commands.DEFAULT_ACTIONS_GROUP],
      foreach=True)

    if self._edit_mode:
      self._invoker.add(
        _preserve_layer_locks_between_commands,
        [commands.DEFAULT_ACTIONS_GROUP],
        foreach=True)

  def _add_commands_before_actions_from_settings(self):
    super()._add_commands_before_actions_from_settings()

    self._add_default_rename_action([commands.DEFAULT_ACTIONS_GROUP])

  def _add_commands_after_actions_from_settings(self):
    super()._add_commands_after_actions_from_settings()

    self._add_default_export_action([commands.DEFAULT_ACTIONS_GROUP])

  def _add_name_only_commands_before_actions_from_settings(self):
    self._add_default_rename_action([_NAME_ONLY_COMMAND_GROUP])

  def _add_name_only_commands_after_actions_from_settings(self):
    self._add_default_export_action([_NAME_ONLY_COMMAND_GROUP])
  
  def _add_default_rename_action(self, command_groups):
    if not self._edit_mode:
      self._invoker.add(
        builtin_actions.rename_layer,
        groups=command_groups,
        args=[self._name_pattern])
  
  def _add_default_export_action(self, command_groups):
    if not self._edit_mode:
      self._invoker.add(
        builtin_actions.export,
        groups=command_groups,
        args=[
          self._output_directory,
          self._file_extension,
        ],
        kwargs=self._more_export_options,
      )
  
  def _process_item_with_commands(self):
    if not self._edit_mode or self._is_preview:
      image_copy, layer_copy = self.create_copy(self._current_image, self._current_layer)

      self._current_image = image_copy
      self._current_layer = layer_copy
      self._image_copies.append(image_copy)

    super()._process_item_with_commands()

    self._current_image = None
    self._current_layer = None

  def create_copy(self, image, layer):
    image_copy = utils_pdb.create_empty_image_copy(image)

    layer_copy = utils_pdb.copy_and_paste_layer(
      layer,
      image_copy,
      None,
      0,
      True,
      True,
      True)

    # This eliminates the " copy" suffix appended by GIMP after creating a layer copy.
    layer_copy.set_name(layer.get_name())

    return image_copy, layer_copy


def _set_selected_and_current_layer(batcher):
  # If an image has no layers, there is nothing we do here. An exception may
  # be raised if an action requires at least one layer. An empty image
  # could occur e.g. if all layers were removed by the previous actions.

  image = batcher.current_image

  if image is None or not image.is_valid():
    # The image does not exist anymore and there is nothing we can do.
    return

  if batcher.current_layer.is_valid():
    image.set_selected_layers([batcher.current_layer])
  else:
    selected_layers = image.get_selected_layers()

    if selected_layers:
      # There is no way to know which layer is the "right" one, so we resort to
      # taking the first.
      selected_layer = selected_layers[0]

      if selected_layer.is_valid():
        # The selected layer(s) may have been set by the action.
        batcher.current_layer = selected_layer
      else:
        image_layers = image.get_layers()
        if image_layers:
          # There is no way to know which layer is the "right" one, so we resort
          # to taking the first.
          batcher.current_layer = image_layers[0]
          image.set_selected_layers([image_layers[0]])


def _set_selected_and_current_layer_after_command(batcher):
  command_applied = yield

  if command_applied or command_applied is None:
    _set_selected_and_current_layer(batcher)


def _sync_item_name_and_layer_name(layer_batcher):
  yield

  if layer_batcher.process_names and not layer_batcher.is_preview:
    layer_batcher.current_item.name = layer_batcher.current_layer.get_name()


def _preserve_layer_locks_between_commands(layer_batcher):
  # We assume `edit_mode` is `True`, we can therefore safely use `Item.raw`.
  # We need to use `Item.raw` for parents as well.
  item = layer_batcher.current_item
  locks_content = {}
  locks_visibility = {}

  for item_or_parent in [item] + item.parents:
    if item_or_parent.raw.is_valid():
      locks_content[item_or_parent] = item_or_parent.raw.get_lock_content()
      locks_visibility[
        item_or_parent] = item_or_parent.raw.get_lock_visibility()

  if item.raw.is_valid():
    lock_position = item.raw.get_lock_position()
    lock_alpha = item.raw.get_lock_alpha()
  else:
    lock_position = None
    lock_alpha = None

  for item_or_parent, lock_content in locks_content.items():
    if lock_content:
      item_or_parent.raw.set_lock_content(False)

  for item_or_parent, lock_visibility in locks_visibility.items():
    if lock_visibility:
      item_or_parent.raw.set_lock_visibility(False)

  if lock_position:
    item.raw.set_lock_position(False)
  if lock_alpha:
    item.raw.set_lock_alpha(False)

  yield

  for item_or_parent, lock_content in locks_content.items():
    if lock_content and item_or_parent.raw.is_valid():
      item_or_parent.raw.set_lock_content(lock_content)

  for item_or_parent, lock_visibility in locks_visibility.items():
    if lock_visibility and item_or_parent.raw.is_valid():
      item_or_parent.raw.set_lock_visibility(lock_visibility)

  if item.raw.is_valid():
    if lock_position:
      item.raw.set_lock_position(lock_position)
    if lock_alpha:
      item.raw.set_lock_alpha(lock_alpha)
