"""Common constants and functions for built-in actions and conditions."""

NAME_ONLY_TAG = 'name'
"""Tag indicating that a built-in command is executed for the name preview."""


def get_filtered_builtin_commands(builtin_commands, tags=None):
  if tags is None:
    tags = []

  return {
    name: command_dict
    for name, command_dict in builtin_commands.items()
    if any(tag in command_dict['additional_tags'] for tag in tags)
  }
