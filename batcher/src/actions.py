"""Creation and management of plug-in actions - procedures and constraints.

Most functions take a `pygimplib.setting.Group` instance containing actions
as its first argument.

Many functions define events invoked on the `pygimplib.setting.Group`
containing actions. These events include:

* ``'before-add-action'``: invoked when:
  * calling `add()` before adding an action,
  * calling `clear()` before resetting actions (due to initial actions
    being added back).
  
  Arguments: action dictionary to be added

* ``'after-add-action'``: invoked when:
  * calling `add()` after adding an action,
  * calling `setting.Group.load()` or `setting.Persistor.load()` after loading
    an action (loading an action counts as adding).
  * calling `clear()` after resetting actions (due to initial actions
    being added back).
  
  Arguments:
  
  * created action,
  
  * original action dictionary (same as in ``'before-add-action'``). When this
    event is triggered in `setting.Group.load()` or `setting.Persistor.load()`,
    this argument is ``None`` as there is no way to obtain the original
    dictionary.

* ``'before-reorder-action'``: invoked when calling `reorder()` before
  reordering an action.
  
  Arguments: action, position before reordering

* ``'after-reorder-action'``: invoked when calling `reorder()` after reordering
  an action.
  
  Arguments: action, position before reordering, new position

* ``'before-remove-action'``: invoked when calling `remove()` before removing
  an action.
  
  Arguments: action to be removed

* ``'after-remove-action'``: invoked when calling `remove()` after removing an
  action.
  
  Arguments: name of the removed action

* ``'before-clear-actions'``: invoked when calling `clear()` before clearing
  actions.

* ``'after-clear-actions'``: invoked when calling `clear()` after clearing
  actions.
"""
import inspect
from typing import Any, Dict, Generator, List, Optional, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib.pypdb import pdb

from src import placeholders


BUILTIN_TAGS = {
  'background': _('Background'),
  'foreground': _('Foreground'),
}

DEFAULT_PROCEDURES_GROUP = 'default_procedures'
DEFAULT_CONSTRAINTS_GROUP = 'default_constraints'

_DEFAULT_ACTION_TYPE = 'procedure'
_REQUIRED_ACTION_FIELDS = ['name']

_ACTIONS_AND_INITIAL_ACTION_DICTS = {}


def create(
      name: str, initial_actions: Optional[List[Dict[str, Any]]] = None,
) -> pg.setting.Group:
  """Creates a `pygimplib.setting.Group` instance containing a group of actions.

  Each action is a nested `pygimplib.setting.Group` instance.
  
  Args:
    name:
      Name of the action group.
    initial_actions:
      List of dictionaries describing actions to be added by default. Calling
      `clear()` will reset the actions returned by this function to the
      initial actions. By default, no initial actions are added.
  
  Each created action in the returned group is a `pygimplib.setting.Group`
  instance. Each action contains the following settings or child groups:

  * ``'function'``: Name of the function to call. If ``'origin'`` is
    ``'builtin'``, then the function is an empty string and the function must
    be replaced during processing with a function object. This allows the
    function to be saved to a persistent setting source.

  * ``'origin'``: Type of the function. If ``'builtin'``, the function is
    defined directly in the plug-in. If ``'gimp_pdb'``, the function is taken
    from the GIMP PDB. The origin affects how the function is modified
    (wrapped) during processing in a `core.Batcher` instance.

  * ``'arguments'``: Arguments to ``'function'`` as a `pygimplib.setting.Group`
    instance containing arguments as separate `Setting` instances.

  * ``'enabled'``: Whether the action should be applied or not.

  * ``'display_name'``: The display name (human-readable name) of the action.

  * ``'action_group'``: List of groups the action belongs to, used in
    `pygimplib.invoker.Invoker` and `core.Batcher`.

  * ``'orig_name'``: The original name of the action. If an action with the
    same ``'name'`` field (see below) was previously added, the name of the new
    action is made unique to allow lookup of both actions. Otherwise,
    ``'orig_name'`` is equal to ``'name'``.

  * ``'tags'``: Additional tags added to each action (the
    `pygimplib.setting.Group` instance).

  * ``'more_options_expanded'``: If ``True``, additional options are displayed
    for an action when editing the action interactively.

  * ``'enabled_for_previews'``: If ``True``, this indicates that the action can
    be applied in the preview.

  * ``'display_options_on_create'``: If ``True``, an action edit dialog is
    displayed upon adding an action interactively.
  
  Each dictionary in the ``initial_actions`` list may contain the following
  fields:

  * ``'name'``: This field is required. This is the ``name`` attribute of the
    created action.

  * ``'type'``: Action type. See below for details.

  * ``'function'``

  * ``'origin'``

  * ``'arguments'``: Specified as list of dictionaries defining settings. Each
    dictionary must contain required attributes and can contain optional
    attributes as stated in `setting.Group.add()`.

  * ``'enabled'``

  * ``'display_name'``

  * ``'action_group'``

  * ``'tags'``

  * ``'more_options_expanded'``

  * ``'enabled_for_previews'``

  * ``'display_options_on_create'``
  
  Depending on the specified ``'type'``, the dictionary may contain additional
  fields and `create()` may generate additional settings.
  
  Allowed values for ``'type'``:

  * ``'procedure'`` (default): Represents a procedure. ``'action_group'``
    defaults to `DEFAULT_PROCEDURES_GROUP` if not defined.

  * ``'constraint'``: Represents a constraint. ``'action_group'`` defaults to
    `DEFAULT_CONSTRAINTS_GROUP` if not defined.
  
  Additional allowed fields for type ``'constraint'`` include:

  * ``'also_apply_to_parent_folders'``: If ``True``, apply the constraint to
    parent groups (folders) as well. The constraint is then satisfied only if
    the item and all of its parents satisfy the constraint.
  
  Custom fields are accepted as well. For each field, a separate setting is
  created, using the field name as the setting name.

  Returns:
    A `pygimplib.setting.Group` instance representing an action group.

  Raises:
    ValueError:
      Invalid ``'type'`` or missing required fields in ``initial_actions``.
  """
  actions = pg.setting.Group(
    name=name,
    setting_attributes={
      'pdb_type': None,
      'setting_sources': None,
    })
  
  _ACTIONS_AND_INITIAL_ACTION_DICTS[actions] = initial_actions
  
  _create_initial_actions(actions, initial_actions)
  
  actions.connect_event('before-load', lambda group: clear(group, add_initial_actions=False))
  actions.connect_event('after-load', _set_up_action_after_loading)
  
  return actions


def _create_initial_actions(actions, initial_actions):
  if initial_actions is not None:
    for action_dict in initial_actions:
      add(actions, action_dict)


def _set_up_action_after_loading(actions):
  for action in actions:
    _set_up_action_post_creation(action)
    actions.invoke_event('after-add-action', action, None)


def add(
      actions: pg.setting.Group, action_dict_or_pdb_proc_name: Union[Dict[str, Any], str],
) -> pg.setting.Group:
  """Creates a new action and adds it to ``actions``.

  The added action is a `pygimplib.setting.Group` instance.

  ``action_dict_or_function`` can be one of the following:
  * a dictionary - see `create()` for the required and accepted fields.
  * a GIMP PDB procedure name.

  The same action can be added multiple times. Each action will be
  assigned a unique name and display name (e.g. ``'rename'`` and ``'Rename'``
  for the first action, ``'rename_2'`` and ``'Rename (2)'`` for the second
  action, and so on).
  
  Objects of other types passed to ``action_dict_or_function`` raise
  `TypeError`.

  Returns:
    The added action.
  """
  if isinstance(action_dict_or_pdb_proc_name, dict):
    action_dict = dict(action_dict_or_pdb_proc_name)
  else:
    if action_dict_or_pdb_proc_name in pdb:
      action_dict = get_action_dict_for_pdb_procedure(action_dict_or_pdb_proc_name)
    else:
      raise TypeError(
        f'"{action_dict_or_pdb_proc_name}" is not a valid GIMP PDB procedure name')
  
  _check_required_fields(action_dict)
  
  orig_action_dict = dict(action_dict)
  
  actions.invoke_event('before-add-action', action_dict)

  action_dict['orig_name'] = action_dict['name']

  _uniquify_name_and_display_name(actions, action_dict)
  
  action = _create_action_by_type(**action_dict)
  
  actions.add([action])
  
  actions.invoke_event('after-add-action', action, orig_action_dict)
  
  return action


def _check_required_fields(action_kwargs):
  for required_field in _REQUIRED_ACTION_FIELDS:
    if required_field not in action_kwargs:
      raise ValueError(f'missing required field: "{required_field}"')


def _uniquify_name_and_display_name(actions, action_dict):
  action_dict['name'] = _uniquify_action_name(actions, action_dict['name'])

  if 'display_name' in action_dict:
    action_dict['display_name'] = _uniquify_action_display_name(
      actions, action_dict['display_name'])


def _uniquify_action_name(actions, name):
  """Returns ``name`` modified to be unique, i.e. to not match the name of any
  existing action in ``actions``.
  """
  
  def _generate_unique_action_name():
    i = 2
    while True:
      yield f'_{i}'
      i += 1
  
  return (
    pg.path.uniquify_string(
      name,
      [action.name for action in walk(actions)],
      generator=_generate_unique_action_name()))


def _uniquify_action_display_name(actions, display_name):
  """Returns ``display_name`` to be unique, i.e. modified to not match the
  display name of any existing action in ``actions``.
  """
  
  def _generate_unique_display_name():
    i = 2
    while True:
      yield f' ({i})'
      i += 1
  
  return (
    pg.path.uniquify_string(
      display_name,
      [action['display_name'].value for action in walk(actions)],
      generator=_generate_unique_display_name()))


def _create_action_by_type(**kwargs):
  type_ = kwargs.pop('type', _DEFAULT_ACTION_TYPE)
  
  if type_ not in _ACTION_TYPES_AND_FUNCTIONS:
    raise ValueError(f'invalid type "{type_}"; valid values: {list(_ACTION_TYPES_AND_FUNCTIONS)}')
  
  return _ACTION_TYPES_AND_FUNCTIONS[type_](**kwargs)


def _create_action(
      name,
      function='',
      origin='builtin',
      arguments=None,
      enabled=True,
      display_name=None,
      description=None,
      action_groups=None,
      tags=None,
      more_options_expanded=False,
      enabled_for_previews=True,
      display_options_on_create=False,
      orig_name=None,
):
  action = pg.setting.Group(
    name,
    tags=tags,
    setting_attributes={
      'pdb_type': None,
      'setting_sources': None,
    })
  
  arguments_group = pg.setting.Group(
    'arguments',
    setting_attributes={
      'pdb_type': None,
      'setting_sources': None,
    })
  
  if arguments:
    arguments_group.add(arguments)
  
  action.add([
    {
      'type': 'string',
      'name': 'function',
      'default_value': function,
      'setting_sources': None,
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'origin',
      'default_value': origin,
      'items': [
        ('builtin', _('Built-in')),
        ('gimp_pdb', _('GIMP PDB procedure'))],
      'gui_type': None,
    },
    arguments_group,
    {
      'type': 'bool',
      'name': 'enabled',
      'default_value': enabled,
    },
    {
      'type': 'string',
      'name': 'display_name',
      'default_value': display_name,
      'gui_type': None,
      'tags': ['ignore_initialize_gui'],
    },
    {
      'type': 'string',
      'name': 'description',
      'default_value': description,
      'gui_type': None,
    },
    {
      'type': 'list',
      'name': 'action_groups',
      'default_value': action_groups,
      'nullable': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'more_options_expanded',
      'default_value': more_options_expanded,
      'display_name': _('_More options'),
      'gui_type': 'expander',
    },
    {
      'type': 'bool',
      'name': 'enabled_for_previews',
      'default_value': enabled_for_previews,
      'display_name': _('Enable for previews'),
    },
    {
      'type': 'bool',
      'name': 'display_options_on_create',
      'default_value': display_options_on_create,
      'gui_type': None,
    },
  ])
  
  action.add([
    {
      'type': 'string',
      'name': 'orig_name',
      'default_value': orig_name if orig_name is not None else name,
      'gui_type': None,
    },
  ])
  
  _set_up_action_post_creation(action)
  
  return action


def _create_procedure(
      name,
      additional_tags=None,
      action_groups=(DEFAULT_PROCEDURES_GROUP,),
      **kwargs,
):
  tags = ['action', 'procedure']
  if additional_tags is not None:
    tags += additional_tags
  
  if action_groups is not None:
    action_groups = list(action_groups)
  
  return _create_action(
    name,
    action_groups=action_groups,
    tags=tags,
    **kwargs)


def _create_constraint(
      name,
      additional_tags=None,
      action_groups=(DEFAULT_CONSTRAINTS_GROUP,),
      also_apply_to_parent_folders=False,
      **kwargs,
):
  tags = ['action', 'constraint']
  if additional_tags is not None:
    tags += additional_tags
  
  if action_groups is not None:
    action_groups = list(action_groups)
  
  constraint = _create_action(
    name,
    action_groups=action_groups,
    tags=tags,
    **kwargs)
  
  constraint.add([
    {
      'type': 'bool',
      'name': 'also_apply_to_parent_folders',
      'default_value': also_apply_to_parent_folders,
      'display_name': _('Also apply to parent folders'),
    },
  ])
  
  return constraint


def _set_up_action_post_creation(action):
  action['enabled'].connect_event(
    'after-set-gui',
    _set_display_name_for_enabled_gui,
    action['display_name'])
  
  if action['origin'].is_item('gimp_pdb'):
    _hide_gui_for_first_run_mode_arguments(action)


def _set_display_name_for_enabled_gui(setting_enabled, setting_display_name):
  setting_display_name.set_gui(
    gui_type='check_button_label',
    widget=setting_enabled.gui.widget)


def _hide_gui_for_first_run_mode_arguments(action):
  first_argument = next(iter(action['arguments']), None)
  if (first_argument is not None
      and isinstance(first_argument, pg.setting.EnumSetting)
      and first_argument.enum_type == Gimp.RunMode):
    first_argument.gui.set_visible(False)


def _remove_array_length_arguments(arguments_list):
  array_length_argument_indexes = []
  
  for i, argument_dict in enumerate(arguments_list):
    setting_type = argument_dict['type']
    if isinstance(setting_type, str):
      setting_type = pg.SETTING_TYPES[setting_type]

    if (issubclass(setting_type, (pg.setting.ArraySetting, placeholders.PlaceholderArraySetting))
        and i > 0):
      array_length_argument_indexes.append(i - 1)

  for index in reversed(array_length_argument_indexes):
    del arguments_list[index]


def get_action_dict_for_pdb_procedure(pdb_procedure_name: str) -> Dict[str, Any]:
  """Returns a dictionary representing the specified GIMP PDB procedure that can
  be added as an action via `add()`.
  
  The ``'function'`` field contains the PDB procedure name.
  
  If the procedure contains arguments with the same name, each subsequent
  identical name is made unique (since arguments are internally represented as
  `pygimplib.setting.Setting` instances, whose names must be unique within a
  `pygimplib.setting.Group` instance).
  """
  
  def _generate_unique_pdb_procedure_argument_name():
    i = 2
    while True:
      yield f'-{i}'
      i += 1

  action_dict = {
    'name': pdb_procedure_name,
    'function': pdb_procedure_name,
    'origin': 'gimp_pdb',
    'arguments': [],
    'display_options_on_create': True,
  }
  
  pdb_procedure_argument_names = []

  pdb_procedure = pdb[pdb_procedure_name].info

  action_dict['display_name'] = _get_pdb_procedure_display_name(pdb_procedure)
  
  for index, proc_arg in enumerate(pdb_procedure.get_arguments()):
    retval = pg.setting.get_setting_type_from_gtype(proc_arg.value_type, proc_arg)

    if retval is None:
      raise UnsupportedPdbProcedureError(action_dict['name'], proc_arg.value_type)

    setting_type, setting_type_init_kwargs = retval

    unique_pdb_param_name = pg.path.uniquify_string(
      proc_arg.name,
      pdb_procedure_argument_names,
      generator=_generate_unique_pdb_procedure_argument_name())
    
    pdb_procedure_argument_names.append(unique_pdb_param_name)

    placeholder_type_name = placeholders.get_placeholder_type_name_from_pdb_type(
      proc_arg.value_type, proc_arg)

    if placeholder_type_name is not None:
      setting_type_init_kwargs = _remove_invalid_init_arguments_for_placeholder_settings(
        setting_type, placeholder_type_name, setting_type_init_kwargs)
      setting_type = placeholder_type_name

    argument_dict = {
      'type': setting_type,
      'name': unique_pdb_param_name,
      'display_name': proc_arg.name,
      **setting_type_init_kwargs,
    }

    if setting_type == pg.setting.BoolSetting:
      argument_dict['gui_type'] = 'check_button_no_text'

    if (hasattr(proc_arg, 'default_value')
        and proc_arg.default_value is not None
        and placeholder_type_name is None):
      argument_dict['default_value'] = proc_arg.default_value

    if inspect.isclass(setting_type) and issubclass(setting_type, pg.setting.NumericSetting):
      if hasattr(proc_arg, 'minimum'):
        argument_dict['min_value'] = proc_arg.minimum
      if hasattr(proc_arg, 'maximum'):
        argument_dict['max_value'] = proc_arg.maximum

    if proc_arg.value_type == Gimp.RunMode.__gtype__:
      argument_dict['default_value'] = Gimp.RunMode.NONINTERACTIVE
    
    action_dict['arguments'].append(argument_dict)

  _remove_array_length_arguments(action_dict['arguments'])
  
  return action_dict


def _get_pdb_procedure_display_name(proc):
  menu_label = proc.get_menu_label()
  if menu_label:
    menu_label = menu_label.replace('_', '')
    if menu_label.endswith('...'):
      menu_label = menu_label[:-len('...')]

    return menu_label
  else:
    return proc.get_name()


def _remove_invalid_init_arguments_for_placeholder_settings(
      setting_type, placeholder_type_name, setting_type_init_kwargs):
  if isinstance(setting_type, str):
    setting_type = pg.SETTING_TYPES[setting_type]

  placeholder_type = pg.SETTING_TYPES[placeholder_type_name]

  setting_init_params = inspect.signature(setting_type.__init__).parameters
  placeholder_setting_init_params = inspect.signature(placeholder_type.__init__).parameters

  return {
    key: value for key, value in setting_type_init_kwargs.items()
    if key in setting_init_params or key in placeholder_setting_init_params
  }


def reorder(actions: pg.setting.Group, action_name: str, new_position: int):
  """Modifies the position an action to the new position.

  The action is specified by its name and must exist within the ``actions``
  group.

  A negative ``position`` functions as an n-th to last position (-1 for last,
  -2 for second to last, etc.).
  
  Raises:
    ValueError: No action with ``action_name`` was found in ``actions``.
  """
  current_position = get_index(actions, action_name)
  
  if current_position is None:
    raise ValueError(f'action "{action_name}" not found in action group "{actions.name}"')
  
  action = actions[action_name]
  
  actions.invoke_event('before-reorder-action', action, current_position)
  
  actions.reorder(action_name, new_position)
  
  actions.invoke_event('after-reorder-action', action, current_position, new_position)


def remove(actions: pg.setting.Group, action_name: str):
  """Removes an action specified by its name from ``actions``.
  
  Raises:
    ValueError: No action with ``action_name`` was found in ``actions``.
  """
  if action_name not in actions:
    raise ValueError(f'action "{action_name}" not found in action group "{actions.name}"')
  
  action = actions[action_name]
  
  actions.invoke_event('before-remove-action', action)
  
  actions.remove([action_name])
  
  actions.invoke_event('after-remove-action', action_name)


def get_index(actions: pg.setting.Group, action_name: str) -> Union[int, None]:
  """Returns the index of the action matching ``action_name``.
  
  If there is no such action, ``None`` is returned.
  """
  return next(
    (index for index, action in enumerate(actions)
     if action.name == action_name),
    None)


def clear(actions: pg.setting.Group, add_initial_actions: bool = True):
  """Removes all added actions.
  
  If ``add_initial_actions`` is ``True``, actions specified in
  ``initial_actions`` in `create()` are added back after removing all actions.
  """
  actions.invoke_event('before-clear-actions')
  
  actions.remove([action.name for action in actions])
  
  if add_initial_actions:
    if actions in _ACTIONS_AND_INITIAL_ACTION_DICTS:
      _create_initial_actions(actions, _ACTIONS_AND_INITIAL_ACTION_DICTS[actions])
  
  actions.invoke_event('after-clear-actions')


def walk(
      actions: pg.setting.Group, action_type: Optional[str] = None, setting_name: str = None,
) -> Generator[pg.setting.Group, None, None]:
  """Iterates over an action group, yielding actions or individual settings
  within each action.
  
  The value of ``action_type`` limits the yielded actions to a specific type.
  If ``action_type`` is ``None``, all actions are yielded. For allowed
  action types, see `create()`. For example, ``action_type='procedure'`` would
  only yield procedures. Invalid values for ``action_type`` raise `ValueError`.

  If ``setting_name`` is ``None``, actions as `pygimplib.setting.Group`
  instances are returned.

  If ``setting_name`` is not ``None``, settings or nested groups within each
  action matching the name are returned. For example, ``name='enabled'`` yields
  the ``'enabled'`` setting for each action. For the list of possible names of
  settings and subgroups, see `create()`.
  """
  action_types = list(_ACTION_TYPES_AND_FUNCTIONS)
  
  if action_type is not None and action_type not in action_types:
    raise ValueError(f'invalid action type "{action_type}"')
  
  def has_matching_type(action_):
    if action_type is None:
      return any(type_ in action_.tags for type_ in action_types)
    else:
      return action_type in action_.tags
  
  for action in actions:
    if not has_matching_type(action):
      continue
    
    if setting_name is None:
      yield action
    else:
      if setting_name in action:
        yield action[setting_name]


_ACTION_TYPES_AND_FUNCTIONS = {
  'procedure': _create_procedure,
  'constraint': _create_constraint,
}


class UnsupportedPdbProcedureError(Exception):
  
  def __init__(self, procedure_name, unsupported_param_type):
    self.procedure_name = procedure_name
    self.unsupported_param_type = unsupported_param_type
