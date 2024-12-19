"""Common constants and functions for built-in procedures and constraints."""

NAME_ONLY_TAG = 'name'
"""Tag indicating that a built-in action is executed for the name preview."""


def get_filtered_builtin_actions(builtin_actions, tags=None):
  if tags is None:
    tags = []

  return {
    name: action_dict
    for name, action_dict in builtin_actions.items()
    if any(tag in action_dict['additional_tags'] for tag in tags)
  }
