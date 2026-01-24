"""Utility functions primarily used in the `handlers` package."""

from src import commands as commands_
from src import setting as setting_
from src.path import uniquify


def get_top_level_group_list(data, name):
  for index, dict_ in enumerate(data[0]['settings']):
    if dict_['name'] == name:
      return dict_['settings'], index

  return None, None


def get_child_group_list(group_list, name):
  for index, dict_ in enumerate(group_list):
    if 'settings' in dict_ and dict_['name'] == name:
      return dict_['settings'], index

  return None, None


def get_child_group_dict(group_list, name):
  for index, dict_ in enumerate(group_list):
    if 'settings' in dict_ and dict_['name'] == name:
      return dict_, index

  return None, None


def get_child_setting(group_list, name):
  for index, dict_ in enumerate(group_list):
    if 'settings' not in dict_ and dict_['name'] == name:
      return dict_, index

  return None, None


def rename_setting(group_list, previous_setting_name, new_setting_name):
  setting_dict, _index = get_child_setting(group_list, previous_setting_name)
  if setting_dict is not None:
    setting_dict['name'] = new_setting_name


def rename_group(group_list, previous_group_name, new_group_name):
  group_dict, _index = get_child_group_dict(group_list, previous_group_name)
  if group_dict is not None:
    group_dict['name'] = new_group_name


def set_setting_attribute_value(group_list, setting_name, attrib_name, new_attrib_value):
  setting_dict, _index = get_child_setting(group_list, setting_name)
  if setting_dict is not None:
    setting_dict[attrib_name] = new_attrib_value


def remove_setting(group_list, setting_name):
  setting_dict, index = get_child_setting(group_list, setting_name)
  if index is not None:
    del group_list[index]

  return setting_dict, index


def remove_command_by_orig_names(commands_list, command_orig_names):
  indexes = []
  for index, command_dict in enumerate(commands_list):
    orig_name_setting_dict, _index = get_child_setting(command_dict['settings'], 'orig_name')
    if orig_name_setting_dict['default_value'] in command_orig_names:
      indexes.append(index)

  for index in reversed(indexes):
    commands_list.pop(index)


def create_command_as_saved_dict(command_dict):
  command = commands_.create_command(command_dict)

  source = setting_.SimpleInMemorySource('')
  source.write(command)

  return source.data[0]


def uniquify_command_name(name, existing_names):
  """Returns ``name`` modified to be unique, i.e. to not match the name of any
  existing command in ``commands``.
  """

  def _generate_unique_command_name():
    i = 2
    while True:
      yield f'_{i}'
      i += 1

  uniquified_name = uniquify.uniquify_string(
    name, existing_names, generator=_generate_unique_command_name())

  existing_names.add(uniquified_name)

  return uniquified_name


def uniquify_command_display_name(display_name, existing_display_names):
  """Returns ``display_name`` modified to be unique, i.e. to not match the
  display name of any existing command in ``commands``.
  """

  def _generate_unique_command_display_name():
    i = 2
    while True:
      yield f' ({i})'
      i += 1

  uniquified_display_name = uniquify.uniquify_string(
    display_name, existing_display_names, generator=_generate_unique_command_display_name())

  existing_display_names.add(uniquified_display_name)

  return uniquified_display_name


def create_and_add_command(command_name, commands_list, builtin_commands_dict, index=None):
  action_names = {command_dict['name'] for command_dict in commands_list}
  action_display_names = {
    get_child_setting(command_dict['settings'], 'display_name')[0]['value']
    for command_dict in commands_list
    if get_child_setting(command_dict['settings'], 'display_name')[0] is not None
  }

  created_group_dict = create_command_as_saved_dict(builtin_commands_dict[command_name])

  created_group_dict['name'] = uniquify_command_name(
    command_name, action_names)

  display_name_dict, _index = get_child_setting(created_group_dict['settings'], 'display_name')
  if display_name_dict is not None:
    display_name_dict['value'] = uniquify_command_display_name(
      display_name_dict['value'], action_display_names)

  display_options_on_create_dict, _index = get_child_setting(
    created_group_dict['settings'], 'display_options_on_create')
  if display_options_on_create_dict is not None:
    display_options_on_create_dict['value'] = False

  if index is not None:
    commands_list.insert(index, created_group_dict)
  else:
    commands_list.append(created_group_dict)

  return created_group_dict
