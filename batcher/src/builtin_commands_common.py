"""Common constants and functions for built-in actions and conditions."""

NAME_ONLY_TAG = 'name'
"""Tag indicating that a built-in command is executed for the input list (name
preview).
"""


def get_filtered_builtin_commands(builtin_commands, tags=None, availability_funcs=None):
  if tags is None:
    tags = []

  if availability_funcs is None:
    availability_funcs = {}

  filtered_builtin_commands = {}

  for name, command_dict in builtin_commands.items():
    if tags and not any(tag in command_dict['additional_tags'] for tag in tags):
      continue

    if name in availability_funcs and not availability_funcs[name](command_dict):
      continue

    filtered_builtin_commands[name] = command_dict

  return filtered_builtin_commands
