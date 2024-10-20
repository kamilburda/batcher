"""Batch-processing layers and exporting layers as separate images."""

import abc
import collections
from collections.abc import Iterable
import contextlib
import inspect
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib import pdb

from src import actions
from src import builtin_actions_common
from src import builtin_constraints
from src import builtin_procedures
from src import exceptions
from src import export as export_
from src import invoker as invoker_
from src import overwrite
from src import placeholders
from src import progress as progress_


_BATCHER_ARG_POSITION_IN_ACTIONS = 0
_NAME_ONLY_ACTION_GROUP = 'name'


class Batcher(metaclass=abc.ABCMeta):
  """Abstract class for batch-processing items with a sequence of actions
  (resize, rename, export, ...).
  """

  def __init__(
        self,
        procedures: pg.setting.Group,
        constraints: pg.setting.Group,
        edit_mode: bool = False,
        initial_export_run_mode: Gimp.RunMode = Gimp.RunMode.WITH_LAST_VALS,
        output_directory: str = pg.utils.get_pictures_directory(),
        name_pattern: str = '',
        file_extension: str = 'png',
        overwrite_mode: int = overwrite.OverwriteModes.RENAME_NEW,
        overwrite_chooser: Optional[overwrite.OverwriteChooser] = None,
        more_export_options: Dict[str, Any] = None,
        progress_updater: Optional[progress_.ProgressUpdater] = None,
        item_tree: Optional[pg.itemtree.ItemTree] = None,
        is_preview: bool = False,
        process_contents: bool = True,
        process_names: bool = True,
        process_export: bool = True,
        export_context_manager: Optional[contextlib.AbstractContextManager] = None,
        export_context_manager_args: Optional[Union[List, Tuple]] = None,
        export_context_manager_kwargs: Optional[Dict] = None,
  ):
    self._procedures = procedures
    self._constraints = constraints
    self._edit_mode = edit_mode
    self._initial_export_run_mode = initial_export_run_mode
    self._output_directory = output_directory
    self._name_pattern = name_pattern
    self._file_extension = file_extension
    self._overwrite_mode = overwrite_mode
    self._overwrite_chooser = overwrite_chooser
    self._more_export_options = more_export_options
    self._progress_updater = progress_updater
    self._item_tree = item_tree
    self._is_preview = is_preview
    self._process_contents = process_contents
    self._process_names = process_names
    self._process_export = process_export
    self._export_context_manager = export_context_manager
    self._export_context_manager_args = export_context_manager_args
    self._export_context_manager_kwargs = export_context_manager_kwargs

    self._current_item = None
    self._current_raw_item = None
    self._current_procedure = None
    self._last_constraint = None
    self._current_image = None

    self._exported_raw_items = []

    self._skipped_procedures = collections.defaultdict(list)
    self._skipped_constraints = collections.defaultdict(list)
    self._failed_procedures = collections.defaultdict(list)
    self._failed_constraints = collections.defaultdict(list)

    self._should_stop = False

    self._invoker = None
    self._initial_invoker = invoker_.Invoker()

  @property
  def procedures(self) -> pg.setting.Group:
    """Action group containing procedures."""
    return self._procedures

  @property
  def constraints(self) -> pg.setting.Group:
    """Action group containing constraints."""
    return self._constraints

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
  def output_directory(self) -> str:
    """Output directory path to save exported items to."""
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
  def overwrite_mode(self) -> int:
    """One of the `pygimplib.overwrite.OverwriteModes` values indicating how to
    handle files with the same name.
    """
    return self._overwrite_mode

  @property
  def overwrite_chooser(self) -> overwrite.OverwriteChooser:
    """`pygimplib.overwrite.OverwriteChooser` instance that is invoked during
    export if a file with the same name already exists.

    By default, `pygimplib.overwrite.NoninteractiveOverwriteChooser` is used.
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
  def item_tree(self) -> pg.itemtree.ItemTree:
    """`pygimplib.itemtree.ItemTree` instance containing items to be processed.

    If ``item_tree=None`` was passed to `__init__()`, an item tree is
    automatically created at the start of processing. If the item tree has
    constraints (filters) set, they will be reset on each call to `run()`.
    """
    return self._item_tree

  @property
  def is_preview(self) -> bool:
    """If ``True``, only procedures and constraints that are marked as
    "enabled for previews" will be applied for previews. If ``False``, this
    property has no effect (and effectively allows performing real processing).
    """
    return self._is_preview

  @property
  def process_contents(self) -> bool:
    """If ``True``, procedures are invoked on items.

    Setting this to ``False`` is useful if you require only item names to be
    processed.
    """
    return self._process_contents

  @property
  def process_names(self) -> bool:
    """If ``True``, item names are processed before export to be suitable to
    save to disk (in particular to remove characters invalid for a file system).

    If `is_preview` is ``True`` and `process_names` is ``True``, built-in
    procedures modifying item names only are also invoked (particularly those
    with the `builtin_actions_common.NAME_ONLY_TAG` tag).
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
  def current_item(self) -> pg.itemtree.Item:
    """A `pygimplib.itemtree.Item` instance currently being processed."""
    return self._current_item

  @property
  def current_raw_item(self) -> Gimp.Layer:
    """The raw item (a GIMP object) that is currently being processed."""
    return self._current_raw_item

  @current_raw_item.setter
  def current_raw_item(self, value: Gimp.Layer):
    self._current_raw_item = value

  @property
  def current_procedure(self) -> pg.setting.Group:
    """The procedure currently being applied to `current_item`."""
    return self._current_procedure

  @property
  def last_constraint(self) -> pg.setting.Group:
    """The most recent constraint that was evaluated."""
    return self._last_constraint

  @property
  def current_image(self) -> Gimp.Image:
    """The current `Gimp.Image` being processed."""
    return self._current_image

  @property
  def exported_raw_items(self) -> List:
    """List of items that were successfully exported.

    Does not include items skipped by the user (when files with the same names
    already exist).
    """
    return list(self._exported_raw_items)

  @property
  def skipped_procedures(self) -> Dict[str, List]:
    """Procedures that were skipped during processing.

    A skipped procedure was not applied to one or more items and causes no
    adverse effects further during processing.
    """
    return dict(self._skipped_procedures)

  @property
  def skipped_constraints(self) -> Dict[str, List]:
    """Constraints that were skipped during processing.

    A skipped constraint was not evaluated for one or more items and causes no
    adverse effects further during processing.
    """
    return dict(self._skipped_constraints)

  @property
  def failed_procedures(self) -> Dict[str, List]:
    """Procedures that caused an error during processing.

    Failed procedures indicate a problem with the procedure parameters or
    potentially a bug.
    """
    return dict(self._failed_procedures)

  @property
  def failed_constraints(self) -> Dict[str, List]:
    """Constraints that caused an error during processing.

    Failed constraints indicate a problem with the constraint parameters or
    potentially a bug.
    """
    return dict(self._failed_constraints)

  @property
  def invoker(self) -> invoker_.Invoker:
    """`pygimplib.invoker.Invoker` instance to manage procedures and constraints
    applied on items.

    This property is reset on each call of `run()`.
    """
    return self._invoker

  def add_procedure(self, *args, **kwargs) -> Union[int, None]:
    """Adds a procedure to be applied during `run()`.

    The signature is the same as for `pygimplib.invoker.Invoker.add()`.

    Procedures added by this method are placed before procedures added by
    `actions.add()`.

    Procedures are added immediately before the start of processing. Thus,
    calling this method during processing will have no effect.

    Unlike `actions.add()`, procedures added by this method do not act as
    settings, i.e. they are merely functions without GUI, are not saved
    persistently and are always enabled.

    This class recognizes several action groups that are invoked at certain
    places when `run()` is called:

    * ``'before_process_items'`` - invoked before starting processing the first
      item. One argument is required - a `Batcher` instance.

    * ``'before_process_items_contents'`` - same as ``'before_process_items'``,
      but applied only if `process_contents` is ``True``.

    * ``'after_process_items'`` - invoked after finishing processing the last
      item. One argument is required - a `Batcher` instance.

    * ``'after_process_items_contents'`` - same as ``'after_process_items'``,
      but applied only if `process_contents` is ``True``.

    * ``'before_process_item'`` - invoked immediately before applying procedures
      on an item.
      These arguments are required:
      * a `Batcher` instance
      * the current `pygimplib.itemtree.Item` to be processed
      * the current GIMP object to be processed

    * ``'before_process_item_contents'`` - same as ``'before_process_item'``,
      but applied only if `process_contents` is ``True``.

    * ``'after_process_item'`` - invoked immediately after all procedures have
      been applied to an item.
      These arguments are required:
      * `Batcher` instance
      * the current `pygimplib.itemtree.Item` that has been processed
      * the current GIMP object that has been processed

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

  def add_constraint(self, func, *args, **kwargs) -> Union[int, None]:
    """Adds a constraint to be applied during `run()`.

    The first argument is the function to act as a filter (returning ``True``
    or ``False``). The rest of the signature is the same as for
    `pygimplib.invoker.Invoker.add()`.

    For more information, see `add_procedure()`.
    """
    return self._initial_invoker.add(self._get_constraint_func(func), *args, **kwargs)

  def remove_action(self, *args, **kwargs):
    """Removes an action originally scheduled to be applied during `run()`.

    The signature is the same as for `pygimplib.invoker.Invoker.remove()`.
    """
    self._initial_invoker.remove(*args, **kwargs)

  def reorder_action(self, *args, **kwargs):
    """Reorders an action to be applied during `run()`.

    The signature is the same as for `pygimplib.invoker.Invoker.reorder()`.
    """
    self._initial_invoker.reorder(*args, **kwargs)

  def run(self, **kwargs):
    """Batch-processes and exports items.

    ``**kwargs`` can contain arguments that can be passed to
    `Batcher.__init__()`. Arguments in ``**kwargs`` overwrite the
    corresponding `Batcher` properties. See the properties for details.
    """
    self._set_attributes(**kwargs)
    self._set_up_item_tree(self._item_tree)
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
      self._export_context_manager = pg.utils.empty_context

    if self._export_context_manager_args is None:
      self._export_context_manager_args = ()
    else:
      self._export_context_manager_args = tuple(self._export_context_manager_args)

    if self._export_context_manager_kwargs is None:
      self._export_context_manager_kwargs = {}

  @abc.abstractmethod
  def _set_up_item_tree(self, item_tree):
    pass

  def _prepare_for_processing(self):
    self._current_item = None
    self._current_raw_item = None
    self._current_procedure = None
    self._last_constraint = None

    self._should_stop = False

    self._exported_raw_items = []

    self._skipped_procedures = collections.defaultdict(list)
    self._skipped_constraints = collections.defaultdict(list)
    self._failed_procedures = collections.defaultdict(list)
    self._failed_constraints = collections.defaultdict(list)

    self._invoker = invoker_.Invoker()

    self._add_actions()
    self._add_name_only_actions()

    self._set_constraints()

    self._progress_updater.reset()

  def _add_actions(self):
    self._add_actions_before_initial_invoker()

    self._invoker.add(
      self._initial_invoker,
      self._initial_invoker.list_groups(include_empty_groups=True))

    self._add_actions_before_procedures_from_settings()

    for procedure in self._procedures:
      self._add_action_from_settings(procedure)

    self._add_actions_after_procedures_from_settings()

    for constraint in self._constraints:
      self._add_action_from_settings(constraint)

  def _add_actions_before_initial_invoker(self):
    pass

  def _add_actions_before_procedures_from_settings(self):
    pass

  def _add_actions_after_procedures_from_settings(self):
    pass

  def _add_name_only_actions(self):
    self._add_name_only_actions_before_procedures_from_settings()

    for procedure in self._procedures:
      self._add_action_from_settings(
        procedure,
        [builtin_actions_common.NAME_ONLY_TAG],
        [_NAME_ONLY_ACTION_GROUP])

    self._add_name_only_actions_after_procedures_from_settings()

    for constraint in self._constraints:
      self._add_action_from_settings(
        constraint,
        [builtin_actions_common.NAME_ONLY_TAG],
        [_NAME_ONLY_ACTION_GROUP])

  def _add_name_only_actions_before_procedures_from_settings(self):
    pass

  def _add_name_only_actions_after_procedures_from_settings(self):
    pass

  def _add_action_from_settings(
        self,
        action: pg.setting.Group,
        tags: Optional[Iterable[str]] = None,
        action_groups: Union[str, List[str], None] = None,
  ):
    """Adds an action and wraps/processes the action's function according to the
    action's settings.

    For PDB procedures, the function name is converted to a proper function
    object. For constraints, the function is wrapped to act as a proper filter
    rule for `item_tree.filter`. Any placeholder objects (e.g. "current image")
    as function arguments are replaced with real objects during processing of
    each item.

    If ``tags`` is not ``None``, the action will not be added if it does not
    contain any of the specified tags.

    If ``action_groups`` is not ``None``, the action will be added to the
    specified action groups instead of the groups defined in ``action[
    'action_groups']``.
    """
    if action['origin'].is_item('builtin'):
      if 'procedure' in action.tags:
        function = builtin_procedures.BUILTIN_PROCEDURES_FUNCTIONS[
          action['orig_name'].value]
      elif 'constraint' in action.tags:
        function = builtin_constraints.BUILTIN_CONSTRAINTS_FUNCTIONS[
          action['orig_name'].value]
      else:
        raise exceptions.ActionError(
          f'invalid action "{action.name}" - must contain "procedure" or "constraint" in tags',
          action,
          None,
          None)
    elif action['origin'].is_item('gimp_pdb'):
      if action['function'].value in pdb:
        function = pdb[action['function'].value]
      else:
        if action['enabled'].value:
          message = f'PDB procedure "{action["function"].value}" not found'

          if 'procedure' in action.tags:
            self._failed_procedures[action.name].append((None, message, None))
          if 'constraint' in action.tags:
            self._failed_constraints[action.name].append((None, message, None))

          raise exceptions.ActionError(message, action, None, None)
        else:
          return
    else:
      raise exceptions.ActionError(
        f'invalid origin {action["origin"].value} for action "{action.name}"',
        action,
        None,
        None)

    if function is None:
      return

    if tags is not None and not any(tag in action.tags for tag in tags):
      return

    processed_function = self._get_processed_function(action)

    processed_function = self._handle_exceptions_from_action(processed_function, action)

    if action_groups is None:
      action_groups = action['action_groups'].value

    invoker_args = list(action['arguments']) + [function]

    self._invoker.add(processed_function, action_groups, invoker_args)

  def _get_processed_function(self, action):

    def _function_wrapper(*action_args_and_function):
      action_args, function = action_args_and_function[:-1], action_args_and_function[-1]

      if not self._is_enabled(action):
        return False

      self._set_current_procedure_and_constraint(action)

      orig_function = function

      args, kwargs = self._get_action_args_and_kwargs(action, action_args, orig_function)

      if 'constraint' in action.tags:
        function = self._set_apply_constraint_to_folders(function, action)
        function = self._get_constraint_func(function, orig_function, action['orig_name'].value)

      return function(*args, **kwargs)

    return _function_wrapper

  def _is_enabled(self, action):
    if self._is_preview:
      if not (action['enabled'].value and action['more_options/enabled_for_previews'].value):
        return False
    else:
      if not action['enabled'].value:
        return False

    return True

  def _set_current_procedure_and_constraint(self, action):
    if 'procedure' in action.tags:
      self._current_procedure = action

    if 'constraint' in action.tags:
      self._last_constraint = action

  def _get_action_args_and_kwargs(self, action, action_args, function):
    args = self._get_replaced_args(action_args, action['origin'].is_item('gimp_pdb'))
    kwargs = {}

    if action['origin'].is_item('gimp_pdb'):
      args.pop(_BATCHER_ARG_POSITION_IN_ACTIONS)

      if function.has_run_mode:
        kwargs = {'run_mode': args[0]}
        args = args[1:]

    return args, kwargs

  def _get_replaced_args(self, action_arguments, is_function_pdb_procedure):
    """Returns a list of action arguments, replacing any placeholder values with
    real values.
    """
    replaced_args = []

    for argument in action_arguments:
      if isinstance(argument, placeholders.PlaceholderArraySetting):
        replaced_arg = placeholders.get_replaced_value(argument, self)
        if is_function_pdb_procedure:
          replaced_args.extend([
            len(replaced_arg),
            pg.setting.array_as_pdb_compatible_type(
              replaced_arg,
              element_pdb_type=argument.element_type.get_allowed_pdb_types()[0]),
          ])
        else:
          replaced_args.append(replaced_arg)
      elif isinstance(argument, placeholders.PlaceholderSetting):
        replaced_args.append(placeholders.get_replaced_value(argument, self))
      elif isinstance(argument, pg.setting.Setting):
        if is_function_pdb_procedure:
          if (isinstance(argument, pg.setting.ArraySetting)
              and argument.element_type != pg.setting.StringSetting):
            replaced_args.append(len(argument.value))
            replaced_args.append(argument.value_for_pdb)
          else:
            replaced_args.append(argument.value_for_pdb)
        else:
          replaced_args.append(argument.value)
      else:
        # Other arguments inserted within `Batcher`
        replaced_args.append(argument)

    return replaced_args

  @staticmethod
  def _set_apply_constraint_to_folders(function, action):
    if action['more_options/also_apply_to_parent_folders'].value:

      def _function_wrapper(*action_args, **action_kwargs):
        item = action_args[0]
        result = True
        for item_or_parent in [item] + item.parents[::-1]:
          result = result and function(item_or_parent, *action_args[1:], **action_kwargs)
          if not result:
            break

        return result

      return _function_wrapper
    else:
      return function

  def _get_constraint_func(self, func, orig_func=None, name=''):

    def _function_wrapper(*args, **kwargs):
      func_args = self._get_args_for_constraint_func(
        orig_func if orig_func is not None else func,
        args)

      self._item_tree.filter.add(func, func_args, kwargs, name=name)

    return _function_wrapper

  @staticmethod
  def _get_args_for_constraint_func(func, args):
    try:
      batcher_arg_position = inspect.getfullargspec(func).args.index('batcher')
    except ValueError:
      batcher_arg_position = None

    if batcher_arg_position is not None:
      func_args = args
    else:
      if len(args) > 1:
        batcher_arg_position = _BATCHER_ARG_POSITION_IN_ACTIONS
      else:
        batcher_arg_position = 0

      func_args = args[:batcher_arg_position] + args[batcher_arg_position + 1:]

    return func_args

  def _handle_exceptions_from_action(self, function, action):
    def _handle_exceptions(*args, **kwargs):
      try:
        retval = function(*args, **kwargs)
      except exceptions.SkipAction as e:
        # Log skipped actions and continue processing.
        self._set_skipped_actions(action, str(e))
      except pg.PDBProcedureError as e:
        error_message = e.message
        if error_message is None:
          error_message = _(
            'An error occurred. Please check the GIMP error message'
            ' or the error console for details, if any.')

        # Log failed action, but raise error as this may result in unexpected
        # behavior.
        self._set_failed_actions(action, error_message)

        raise exceptions.ActionError(error_message, action, self._current_item)
      except Exception as e:
        trace = traceback.format_exc()
        # Log failed action, but raise error as this may result in unexpected
        # behavior.
        self._set_failed_actions(action, str(e), trace)

        raise exceptions.ActionError(str(e), action, self._current_item, trace)
      else:
        return retval

    return _handle_exceptions

  def _set_skipped_actions(self, action, error_message):
    if 'procedure' in action.tags:
      self._skipped_procedures[action.name].append((self._current_item, error_message))
    if 'constraint' in action.tags:
      self._skipped_constraints[action.name].append((self._current_item, error_message))

  def _set_failed_actions(self, action, error_message, trace=None):
    if 'procedure' in action.tags:
      self._failed_procedures[action.name].append((self._current_item, error_message, trace))
    if 'constraint' in action.tags:
      self._failed_constraints[action.name].append((self._current_item, error_message, trace))

  def _set_constraints(self):
    self._invoker.invoke(
      [actions.DEFAULT_CONSTRAINTS_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

  def _setup_contents(self):
    pass

  def _process_items(self):
    self._progress_updater.num_total_tasks = len(self._item_tree)

    self._invoker.invoke(
      ['before_process_items'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    if self._process_contents:
      self._invoker.invoke(
        ['before_process_items_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    for item in self._item_tree:
      if self._should_stop:
        raise exceptions.BatcherCancelError('stopped by user')

      if self._edit_mode:
        self._progress_updater.update_text(
          _('Processing "{}"').format(item.orig_name))

      self._process_item(item)

    if self._process_contents:
      self._invoker.invoke(
        ['after_process_items_contents'],
        [self],
        additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._invoker.invoke(
      ['after_process_items'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

  def _process_item(self, item):
    self._current_item = item
    self._current_raw_item = item.raw

    if self._is_preview and self._process_names:
      self._process_item_with_name_only_actions()

    if self._process_contents:
      self._process_item_with_actions()

    self._progress_updater.update_tasks()

  def _process_item_with_name_only_actions(self):
    self._invoker.invoke(
      ['before_process_item'],
      [self, self._current_item, self._current_raw_item],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._invoker.invoke(
      [_NAME_ONLY_ACTION_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._invoker.invoke(
      ['after_process_item'],
      [self, self._current_item, self._current_raw_item],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

  def _process_item_with_actions(self):
    self._invoker.invoke(
      ['before_process_item'],
      [self, self._current_item, self._current_raw_item],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    if self._process_contents:
      self._invoker.invoke(
        ['before_process_item_contents'],
        [self, self._current_item, self._current_raw_item],
        additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._invoker.invoke(
      [actions.DEFAULT_PROCEDURES_GROUP],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    if self._process_contents:
      self._invoker.invoke(
        ['after_process_item_contents'],
        [self, self._current_item, self._current_raw_item],
        additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._invoker.invoke(
      ['after_process_item'],
      [self, self._current_item, self._current_raw_item],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

  def _cleanup_contents(self, exception_occurred=False):
    self._invoker.invoke(
      ['cleanup_contents'],
      [self],
      additional_args_position=_BATCHER_ARG_POSITION_IN_ACTIONS)

    self._do_cleanup_contents(exception_occurred)

    self._current_item = None
    self._current_raw_item = None
    self._current_procedure = None
    self._last_constraint = None
    self._current_image = None

  def _do_cleanup_contents(self, exception_occurred):
    pass

  def queue_stop(self):
    """Instructs `Batcher` to terminate batch processing prematurely.

    The termination occurs after the current item is processed completely.

    This method has no effect if the processing is not running.
    """
    self._should_stop = True


class LayerBatcher(Batcher):
  """Class for batch-processing layers in the specified image with a sequence of
  actions (resize, rename, export, ...).

  If ``edit_mode`` is set to ``'export'``, batch-processing and export of
  layers is performed. A copy of the image and the layers to be processed are
  created so that the original image and its soon-to-be processed layers are
  left intact. The image copy is automatically destroyed once processing is
  done. To keep the image copy, pass ``keep_image_copy=True`` to `__init__()`
  or `run()`.
  """

  def __init__(
        self,
        input_image: Gimp.Image,
        *args,
        keep_image_copy: bool = False,
        **kwargs,
  ):
    super().__init__(*args, **kwargs)

    self._input_image = input_image
    self._keep_image_copy = keep_image_copy

    self._image_copy = None
    self._orig_selected_raw_items = []

  @property
  def current_image(self) -> Gimp.Image:
    """The current `Gimp.Image` being processed.

    If `edit_mode` is ``True``, this is equivalent to `input_image`.

    If `edit_mode` is ``False``, this is a copy of `input_image` to avoid
    modifying original layers.
    """
    return self._current_image

  @property
  def input_image(self) -> Gimp.Image:
    """Input `Gimp.Image` containing layers to process."""
    return self._input_image

  @property
  def keep_image_copy(self) -> bool:
    """If ``True``, a copy of the currently processed image is preserved once
    batch processing and export (a `run()` call) is done.
    """
    return self._keep_image_copy

  @property
  def image_copy(self) -> Union[Gimp.Image, None]:
    """`Gimp.Image` as a copy of the original image used for batch-processing
    and exporting layers.

    If ``keep_image_copy`` is ``False`` or creating an image copy is not
    applicable (e.g. if ``edit_mode`` is ``True``), this property will then
    return ``None``.
    """
    return self._image_copy

  @property
  def orig_selected_raw_items(self) -> List[Gimp.Layer]:
    """List of layers selected in GIMP prior to processing.

    The selection changes during processing and is restored to this value at the
    end of the processing
    """
    return list(self._orig_selected_raw_items)

  def _set_up_item_tree(self, item_tree):
    if item_tree is not None:
      self._item_tree = item_tree
    else:
      self._item_tree = pg.itemtree.LayerTree(self._input_image)

    if self._item_tree.filter:
      self._item_tree.reset_filter()

  def _prepare_for_processing(self):
    super()._prepare_for_processing()

    self._orig_selected_raw_items = []

    self._current_image = self._input_image
    self._image_copy = None

  def _add_actions_before_initial_invoker(self):
    super()._add_actions_before_initial_invoker()

    self._invoker.add(
      builtin_procedures.set_selected_and_current_layer, [actions.DEFAULT_PROCEDURES_GROUP])

    self._invoker.add(
      builtin_procedures.set_selected_and_current_layer_after_action,
      [actions.DEFAULT_PROCEDURES_GROUP],
      foreach=True)

    self._invoker.add(
      builtin_procedures.sync_item_name_and_raw_item_name,
      [actions.DEFAULT_PROCEDURES_GROUP],
      foreach=True)

    if self._edit_mode:
      self._invoker.add(
        builtin_procedures.preserve_locks_between_actions,
        [actions.DEFAULT_PROCEDURES_GROUP],
        foreach=True)

  def _add_actions_before_procedures_from_settings(self):
    super()._add_actions_before_procedures_from_settings()

    self._add_default_rename_procedure([actions.DEFAULT_PROCEDURES_GROUP])

  def _add_actions_after_procedures_from_settings(self):
    super()._add_actions_after_procedures_from_settings()

    self._add_default_export_procedure([actions.DEFAULT_PROCEDURES_GROUP])

  def _add_name_only_actions_before_procedures_from_settings(self):
    self._add_default_rename_procedure([_NAME_ONLY_ACTION_GROUP])

  def _add_name_only_actions_after_procedures_from_settings(self):
    self._add_default_export_procedure([_NAME_ONLY_ACTION_GROUP])
  
  def _add_default_rename_procedure(self, action_groups):
    if not self._edit_mode:
      self._invoker.add(
        builtin_procedures.rename_layer,
        groups=action_groups,
        args=[self._name_pattern])
  
  def _add_default_export_procedure(self, action_groups):
    if not self._edit_mode:
      self._invoker.add(
        export_.export,
        groups=action_groups,
        args=[
          self._output_directory,
          self._file_extension,
        ],
        kwargs=self._more_export_options,
      )

  def _setup_contents(self):
    super()._setup_contents()

    Gimp.context_push()
    
    if not self._edit_mode or self._is_preview:
      self._image_copy = pg.pdbutils.duplicate_image_without_contents(self._input_image)
      self._current_image = self._image_copy
      
      self._current_image.undo_freeze()
    else:
      self._current_image = self._input_image
      self._current_image.undo_group_start()

    self._orig_selected_raw_items = self._input_image.list_selected_layers()
  
  def _do_cleanup_contents(self, exception_occurred):
    super()._do_cleanup_contents(exception_occurred)

    if not self._edit_mode or self._is_preview:
      self._copy_non_modifying_parasites(self._current_image, self._input_image)
      
      self._current_image.undo_thaw()
      
      if not self._keep_image_copy or exception_occurred:
        pg.pdbutils.try_delete_image(self._current_image)
        self._image_copy = None
    else:
      self._current_image.set_selected_layers([
        layer for layer in self._orig_selected_raw_items
        if layer.is_valid() and layer.get_image() == self._current_image])
      self._current_image.undo_group_end()
      Gimp.displays_flush()
    
    Gimp.context_pop()
  
  @staticmethod
  def _copy_non_modifying_parasites(src_image, dest_image):
    parasite_names = src_image.get_parasite_list()
    for parasite_name in parasite_names:
      if dest_image.get_parasite(parasite_name) is None:
        parasite = src_image.get_parasite(parasite_name)
        # Do not attach persistent or undoable parasites to avoid modifying
        # `dest_image`.
        if parasite.get_flags() == 0:
          dest_image.attach_parasite(parasite)
  
  def _process_item_with_actions(self):
    if not self._edit_mode or self._is_preview:
      raw_item_copy = pg.pdbutils.copy_and_paste_layer(
        self._current_raw_item,
        self._current_image,
        None,
        len(self._current_image.list_layers()),
        True,
        True,
        True)

      # This eliminates the " copy" suffix appended by GIMP after creating a copy.
      orig_raw_item_name = self._current_raw_item.get_name()
      self._current_raw_item = raw_item_copy
      self._current_raw_item.set_name(orig_raw_item_name)
    
    if self._edit_mode and not self._is_preview and self._current_raw_item.is_group():
      # Layer groups must be copied and inserted as layers as some procedures
      # do not work on layer groups.
      raw_item_copy = pg.pdbutils.copy_and_paste_layer(
        self._current_raw_item,
        self._current_image,
        self._current_raw_item.get_parent(),
        self._current_image.get_item_position(self._current_raw_item) + 1,
        True,
        True,
        True)

      # This eliminates the " copy" suffix appended by GIMP after creating a copy.
      orig_raw_item_name = self._current_raw_item.get_name()
      self._current_raw_item = raw_item_copy
      self._current_raw_item.set_name(orig_raw_item_name)

    super()._process_item_with_actions()

    self._refresh_current_image()

  def _refresh_current_image(self):
    if not self._edit_mode and not self._keep_image_copy:
      for layer in self._current_image.list_layers():
        self._current_image.remove_layer(layer)
