"""Creation and management of plug-in commands - actions and conditions.

Most functions take a `setting.Group` instance containing commands
as its first argument.

Many functions define events invoked on the `setting.Group`
containing commands. These events include:

* ``'before-add-command'``: invoked when:
  * calling `add()` before adding a command,
  * calling `clear()` before resetting commands (due to initial commands
    being added back).
  
  Arguments:

  * command dictionary or existing command to be added, depending on the type
    passed to `add()`.

* ``'after-add-command'``: invoked when:
  * calling `add()` after adding a command,
  * calling `setting.Group.load()` or `setting.Persistor.load()` after loading
    a command (loading a command counts as adding).
  * calling `clear()` after resetting commands (due to initial commands
    being added back).
  
  Arguments:
  
  * created command,
  
  * original command dictionary (same as in ``'before-add-command'``). When
    this event is triggered in `setting.Group.load()` or
    `setting.Persistor.load()`, or when a command was passed to `add()`,
    this argument is ``None`` as there is no way to obtain it.

* ``'before-reorder-command'``: invoked when calling `reorder()` before
  reordering a command.
  
  Arguments: command, position before reordering

* ``'after-reorder-command'``: invoked when calling `reorder()` after reordering
  a command.
  
  Arguments: command, position before reordering, new position

* ``'before-remove-command'``: invoked when calling `remove()` before removing
  a command.
  
  Arguments: command to be removed

* ``'after-remove-command'``: invoked when calling `remove()` after removing an
  command.
  
  Arguments: name of the removed command

* ``'before-clear-commands'``: invoked when calling `clear()` before clearing
  commands.

* ``'after-clear-commands'``: invoked when calling `clear()` after clearing
  commands.
"""
from typing import Any, Dict, List, Optional, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import pypdb
from src import setting as setting_
from src import settings_from_pdb
from src import utils
from src.pypdb import pdb
from src.path import uniquify


DEFAULT_ACTIONS_GROUP = 'default_actions'
DEFAULT_CONDITIONS_GROUP = 'default_conditions'

MORE_OPTIONS_TAG = 'more_options'

_DEFAULT_COMMAND_TYPE = 'action'
_REQUIRED_COMMAND_FIELDS = ['name']

_COMMANDS_AND_INITIAL_COMMAND_DICTS = {}


def create(
      name: str, initial_commands: Optional[List[Dict[str, Any]]] = None,
) -> setting_.Group:
  """Creates a `setting.Group` instance containing a group of commands.

  Each command is a nested `setting.Group` instance.
  
  Args:
    name:
      Name of the command group.
    initial_commands:
      List of dictionaries describing commands to be added by default. Calling
      `clear()` will reset the commands returned by this function to the
      initial commands. By default, no initial commands are added.
  
  Each created command in the returned group is a `setting.Group`
  instance. Each command contains the following settings or child groups:

  * ``'function'``: Name of the function to call. If ``'origin'`` is
    ``'builtin'``, then the function is an empty string and the function must
    be replaced during processing with a function object. This allows the
    function to be saved to a persistent setting source.

  * ``'origin'``: Type of the function. If ``'builtin'``, the function is
    defined directly in the plug-in. If ``'gimp_pdb'``, the function is a GIMP
    PDB procedure. If ``'gegl'``, the function is a GEGL operation. The origin,
    among other things, can be used to provide an appropriate wrapper during
    processing in a `core.Batcher` instance.

  * ``'arguments'``: Arguments to ``'function'`` as a `setting.Group`
    instance containing arguments as separate `Setting` instances.

  * ``'enabled'``: Whether the command should be applied or not.

  * ``'display_name'``: The display name (human-readable name) of the command.

  * ``'menu_path'``: Menu path allowing to group related commands to submenus.
     The menu path components are separated by ``'/'``.

  * ``'command_group'``: List of groups the command belongs to, used in
    `invoker.Invoker` and `core.Batcher`.

  * ``'orig_name'``: The original name of the command. If a command with the
    same ``'name'`` field (see below) was previously added, the name of the new
    command is made unique to allow lookup of both commands. Otherwise,
    ``'orig_name'`` is equal to ``'name'``.

  * ``'tags'``: Additional tags added to each command (the
    `setting.Group` instance).

  * ``'display_options_on_create'``: If ``True``, a command edit dialog is
    displayed upon adding a command interactively.

  * ``'more_options_expanded'``: If ``True``, additional options are displayed
    for a command when editing the command interactively.

  * ``'enabled_for_previews'``: If ``True``, this indicates that the command can
    be applied in the preview.

  Each dictionary in the ``initial_commands`` list may contain the following
  fields:

  * ``'name'``: This field is required. This is the ``name`` attribute of the
    created command.

  * ``'type'``: Command type. See below for details.

  * ``'arguments'``: Specified as list of dictionaries defining settings. Each
    dictionary must contain required attributes and can contain optional
    attributes as stated in `setting.Group.add()`.

  * any other field matching one of the names of child settings or groups of the
    created command (described above), except ``'orig_name'``.

  Depending on the specified ``'type'``, the dictionary may contain additional
  fields and `create()` may generate additional settings.
  
  Allowed values for ``'type'``:

  * ``'action'`` (default): Represents an action. ``'command_group'``
    defaults to `DEFAULT_ACTIONS_GROUP` if not defined.

  * ``'condition'``: Represents a condition. ``'command_group'`` defaults to
    `DEFAULT_CONDITIONS_GROUP` if not defined.
  
  Additional allowed fields for type ``'condition'`` include:

  * ``'also_apply_to_parent_folders'``: If ``True``, apply the condition to
    parent groups (folders) as well. The condition is then satisfied only if
    the item and all of its parents satisfy the condition.
  
  Custom fields are accepted as well. For each field, a separate setting is
  created, using the field name as the setting name.

  Returns:
    A `setting.Group` instance representing a command group.

  Raises:
    ValueError:
      Invalid ``'type'`` or missing required fields in ``initial_commands``.
  """
  commands = setting_.Group(
    name=name,
    setting_attributes={
      'pdb_type': None,
    })
  
  _COMMANDS_AND_INITIAL_COMMAND_DICTS[commands] = initial_commands
  
  _create_initial_commands(commands, initial_commands)
  
  commands.connect_event('before-load', lambda group: clear(group, add_initial_commands=False))
  commands.connect_event('after-load', _set_up_command_after_loading)
  
  return commands


def _create_initial_commands(commands, initial_commands):
  if initial_commands is not None:
    for command_dict in initial_commands:
      add(commands, command_dict)


def _set_up_command_after_loading(commands):
  for command in commands:
    _set_up_command_post_creation(command)
    commands.invoke_event('after-add-command', command, None)


def add(
      commands: setting_.Group,
      command_dict_or_pdb_proc_name_or_command: Union[Dict[str, Any], str, setting_.Group],
) -> setting_.Group:
  """Adds a new or existing command to ``commands``.

  ``command_dict_or_pdb_proc_name_or_command`` can be one of the following:
  * a dictionary - see `create()` for the required and accepted fields,
  * a PDB procedure name,
  * an existing `setting.Group` instance representing a command,
    created via `create_command()`.

  The same command can be added multiple times. Each command will be
  assigned a unique name and display name (e.g. ``'rename'`` and ``'Rename'``
  for the first command, ``'rename_2'`` and ``'Rename (2)'`` for the second
  command, and so on).
  
  Objects of other types passed to ``command_dict_or_pdb_proc_name_or_command``
  raise `TypeError`.

  Returns:
    The added command.
  """
  command_dict = None
  command = None

  if isinstance(command_dict_or_pdb_proc_name_or_command, dict):
    command_dict = utils.semi_deep_copy(command_dict_or_pdb_proc_name_or_command)
  elif isinstance(command_dict_or_pdb_proc_name_or_command, setting_.Group):
    command = command_dict_or_pdb_proc_name_or_command
  else:
    if command_dict_or_pdb_proc_name_or_command in pdb:
      command_dict = get_command_dict_from_pdb_procedure(command_dict_or_pdb_proc_name_or_command)
    else:
      raise TypeError(
        f'"{command_dict_or_pdb_proc_name_or_command}" is not a valid GIMP PDB procedure name')

  if command_dict is not None:
    _check_required_fields(command_dict)

    if 'orig_name' not in command_dict:
      command_dict['orig_name'] = command_dict['name']

    orig_command_dict = utils.semi_deep_copy(command_dict)

    commands.invoke_event('before-add-command', orig_command_dict)

    _uniquify_name_and_display_name(commands, command_dict)

    command = _create_command_without_copying(command_dict)

    commands.add([command])

    commands.invoke_event('after-add-command', command, orig_command_dict)
  else:  # command is not None
    commands.invoke_event('before-add-command', command)

    command.uniquify_name(commands)

    command['display_name'].set_value(
      _uniquify_command_display_name(commands, command['display_name'].value))

    commands.add([command])

    commands.invoke_event('after-add-command', command, None)
  
  return command


def _check_required_fields(command_kwargs):
  for required_field in _REQUIRED_COMMAND_FIELDS:
    if required_field not in command_kwargs:
      raise ValueError(f'missing required field: "{required_field}"')


def _uniquify_name_and_display_name(commands, command_dict):
  command_dict['name'] = _uniquify_command_name(commands, command_dict['name'])

  if 'display_name' in command_dict:
    command_dict['display_name'] = _uniquify_command_display_name(
      commands, command_dict['display_name'])


def _uniquify_command_name(commands, name):
  """Returns ``name`` modified to be unique, i.e. to not match the name of any
  existing command in ``commands``.
  """
  
  def _generate_unique_command_name():
    i = 2
    while True:
      yield f'_{i}'
      i += 1
  
  return (
    uniquify.uniquify_string(
      name,
      [command.name for command in commands],
      generator=_generate_unique_command_name()))


def _uniquify_command_display_name(commands, display_name):
  """Returns ``display_name`` to be unique, i.e. modified to not match the
  display name of any existing command in ``commands``.
  """

  def _generate_unique_display_name():
    i = 2
    while True:
      yield f' ({i})'
      i += 1

  return (
    uniquify.uniquify_string(
      display_name,
      [command['display_name'].value for command in commands],
      generator=_generate_unique_display_name()))


def create_command(command_dict):
  """Creates a single command given the supplied dictionary.

  At the very least, ``command_dict`` must contain the following key-value
  pairs:

  * ``'name'`` - represents the command name,
  * ``'type'`` - represents the command type. Only the following values are
    allowed: ``'action'``, ``'condition'``.

  For the list of available key-value pairs beside ``name`` and ``type``, see
  `create()`.

  A command created by this function is not added to a group of commands. Use
  `add()` to add an existing command to an existing command group.
  """
  command_dict_copy = utils.semi_deep_copy(command_dict)

  return _create_command_without_copying(command_dict_copy)


def _create_command_without_copying(command_dict):
  type_ = command_dict.pop('type', _DEFAULT_COMMAND_TYPE)

  if type_ not in _COMMAND_TYPES_AND_FUNCTIONS:
    raise ValueError(f'invalid type "{type_}"; valid values: {list(_COMMAND_TYPES_AND_FUNCTIONS)}')

  return _COMMAND_TYPES_AND_FUNCTIONS[type_](**command_dict)


def _create_command(
      name,
      function='',
      origin='builtin',
      arguments=None,
      enabled=True,
      display_name=None,
      menu_path=None,
      description=None,
      command_groups=None,
      tags=None,
      display_options_on_create=False,
      more_options_expanded=False,
      enabled_for_previews=True,
      orig_name=None,
):
  command = setting_.Group(
    name,
    tags=tags,
    setting_attributes={
      'pdb_type': None,
    })
  
  arguments_group = setting_.Group(
    'arguments',
    setting_attributes={
      'pdb_type': None,
    })

  more_options_group = setting_.Group(
    'more_options',
    setting_attributes={
      'pdb_type': None,
    })

  if arguments:
    arguments_group.add(arguments)

  command.add([
    {
      'type': 'string',
      'name': 'function',
      'default_value': function,
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'origin',
      'default_value': origin,
      'items': [
        ('builtin', _('Built-in')),
        ('gimp_pdb', _('GIMP PDB procedure')),
        ('gegl', _('GEGL operation'))],
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
      'name': 'menu_path',
      'default_value': menu_path,
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
      'name': 'command_groups',
      'default_value': command_groups,
      'nullable': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'display_options_on_create',
      'default_value': display_options_on_create,
      'gui_type': None,
    },
    more_options_group,
    {
      'type': 'bool',
      'name': 'more_options_expanded',
      'default_value': more_options_expanded,
      'display_name': _('_More options'),
      'gui_type': 'expander',
    },
  ])

  more_options_group.add([
    {
      'type': 'bool',
      'name': 'enabled_for_previews',
      'default_value': enabled_for_previews,
      'display_name': _('Enable for previews'),
    },
  ])
  
  command.add([
    {
      'type': 'string',
      'name': 'orig_name',
      'default_value': orig_name if orig_name is not None else name,
      'gui_type': None,
    },
  ])
  
  _set_up_command_post_creation(command)
  
  return command


def _create_action(
      name,
      additional_tags=None,
      command_groups=(DEFAULT_ACTIONS_GROUP,),
      **kwargs,
):
  tags = ['command', 'action']
  if additional_tags is not None:
    tags += additional_tags
  
  if command_groups is not None:
    command_groups = list(command_groups)
  
  return _create_command(
    name,
    command_groups=command_groups,
    tags=tags,
    **kwargs)


def _create_condition(
      name,
      additional_tags=None,
      command_groups=(DEFAULT_CONDITIONS_GROUP,),
      also_apply_to_parent_folders=False,
      **kwargs,
):
  tags = ['command', 'condition']
  if additional_tags is not None:
    tags += additional_tags
  
  if command_groups is not None:
    command_groups = list(command_groups)
  
  condition = _create_command(
    name,
    command_groups=command_groups,
    tags=tags,
    **kwargs)
  
  condition['more_options'].add([
    {
      'type': 'bool',
      'name': 'also_apply_to_parent_folders',
      'default_value': also_apply_to_parent_folders,
      'display_name': _('Also apply to parent folders'),
    },
  ])
  
  return condition


def _set_up_command_post_creation(command):
  command['enabled'].connect_event(
    'after-set-gui',
    _set_display_name_for_enabled_gui,
    command['display_name'])

  if command['origin'].value == 'gimp_pdb':
    _hide_gui_for_first_run_mode_arguments(command)


def _set_display_name_for_enabled_gui(setting_enabled, setting_display_name):
  setting_display_name.set_gui(
    gui_type='check_button_label',
    widget=setting_enabled.gui.widget)


def _hide_gui_for_first_run_mode_arguments(command):
  first_argument = next(iter(command['arguments']), None)
  if (first_argument is not None
      and isinstance(first_argument, setting_.EnumSetting)
      and first_argument.enum_type == Gimp.RunMode):
    first_argument.gui.set_visible(False)


def get_command_dict_from_pdb_procedure(
      pdb_procedure_or_name: Union[pypdb.PDBProcedure, str]) -> Dict[str, Any]:
  """Returns a dictionary representing the specified GIMP PDB procedure that can
  be added as a command via `add()`.
  
  The ``'function'`` field contains the PDB procedure name.
  
  If the procedure contains arguments with the same name, each subsequent
  identical name is made unique (since arguments are internally represented as
  `setting.Setting` instances, whose names must be unique within a
  `setting.Group` instance).
  """

  pdb_procedure, pdb_procedure_name, arguments = (
    settings_from_pdb.get_setting_data_from_pdb_procedure(pdb_procedure_or_name))

  origin = _get_pdb_procedure_origin(pdb_procedure)

  if origin == 'gegl':
    _mark_less_used_common_gegl_procedure_arguments_as_more_options(arguments)

  command_dict = {
    'name': _sanitize_pdb_procedure_name(pdb_procedure_name),
    'function': pdb_procedure_name,
    'orig_name': pdb_procedure_name,
    'origin': origin,
    'arguments': arguments,
    'display_name': _get_pdb_procedure_display_name(pdb_procedure),
    'description': _get_pdb_procedure_description(pdb_procedure),
  }

  return command_dict


def _get_pdb_procedure_origin(pdb_procedure):
  if isinstance(pdb_procedure, pypdb.GimpPDBProcedure):
    return 'gimp_pdb'
  elif isinstance(pdb_procedure, pypdb.GeglProcedure):
    return 'gegl'
  else:
    raise TypeError(f'unsupported PDB procedure type {type(pdb_procedure)} for {pdb_procedure}')


def _mark_less_used_common_gegl_procedure_arguments_as_more_options(arguments):
  for argument_dict in arguments:
    if argument_dict['name'] in ['visible-', 'name-']:
      if 'tags' not in argument_dict:
        argument_dict['tags'] = []

      argument_dict['tags'].append(MORE_OPTIONS_TAG)


def _sanitize_pdb_procedure_name(pdb_procedure_name):
  return (
    pdb_procedure_name
      .replace(setting_.SETTING_PATH_SEPARATOR, '_')
      .replace(setting_.SETTING_ATTRIBUTE_SEPARATOR, '_')
  )


def _get_pdb_procedure_display_name(pdb_procedure):
  menu_label = pdb_procedure.menu_label
  if menu_label:
    menu_label = menu_label.replace('_', '')
    if menu_label.endswith('...'):
      menu_label = menu_label[:-len('...')]

    return menu_label
  else:
    return pdb_procedure.name


def _get_pdb_procedure_description(pdb_procedure):
  blurb = pdb_procedure.blurb
  return blurb if blurb is not None else ''


def reorder(commands: setting_.Group, command_name: str, new_position: int):
  """Modifies the position a command to the new position.

  The command is specified by its name and must exist within the ``commands``
  group.

  A negative ``position`` functions as an n-th to last position (-1 for last,
  -2 for second to last, etc.).
  
  Raises:
    ValueError: No command with ``command_name`` was found in ``commands``.
  """
  current_position = get_index(commands, command_name)
  
  if current_position is None:
    raise ValueError(f'command "{command_name}" not found in command group "{commands.name}"')
  
  command = commands[command_name]
  
  commands.invoke_event('before-reorder-command', command, current_position)
  
  commands.reorder(command_name, new_position)
  
  commands.invoke_event('after-reorder-command', command, current_position, new_position)


def remove(commands: setting_.Group, command_name: str):
  """Removes a command specified by its name from ``commands``.
  
  Raises:
    ValueError: No command with ``command_name`` was found in ``commands``.
  """
  if command_name not in commands:
    raise ValueError(f'command "{command_name}" not found in command group "{commands.name}"')
  
  command = commands[command_name]
  
  commands.invoke_event('before-remove-command', command)
  
  commands.remove([command_name])
  
  commands.invoke_event('after-remove-command', command_name)


def get_index(commands: setting_.Group, command_name: str) -> Union[int, None]:
  """Returns the index of the command matching ``command_name``.
  
  If there is no such command, ``None`` is returned.
  """
  return next(
    (index for index, command in enumerate(commands)
     if command.name == command_name),
    None)


def clear(commands: setting_.Group, add_initial_commands: bool = True):
  """Removes all added commands.
  
  If ``add_initial_commands`` is ``True``, commands specified in
  ``initial_commands`` in `create()` are added back after removing all commands.
  """
  commands.invoke_event('before-clear-commands')
  
  commands.remove([command.name for command in commands])
  
  if add_initial_commands:
    if commands in _COMMANDS_AND_INITIAL_COMMAND_DICTS:
      _create_initial_commands(commands, _COMMANDS_AND_INITIAL_COMMAND_DICTS[commands])
  
  commands.invoke_event('after-clear-commands')


_COMMAND_TYPES_AND_FUNCTIONS = {
  'action': _create_action,
  'condition': _create_condition,
}
