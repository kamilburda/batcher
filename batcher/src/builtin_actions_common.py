"""Common constants and functions for built-in procedures and constraints."""

CONVERT_TAG = 'convert'
"""Tag indicating that a built-in action is appropriate for Convert."""

EDIT_LAYERS_TAG = 'edit_layers'
"""Tag indicating that a built-in action is appropriate for Edit Layers. For
example, "Use layer size" should not be available for Edit Layers and such a
procedure will hence not have this tag.
"""

EXPORT_LAYERS_TAG = 'export_layers'
"""Tag indicating that a built-in action is appropriate for Export Layers."""

NAME_ONLY_TAG = 'name'
"""Tag indicating that a built-in action is executed for the name preview."""


__all__ = [
  'CONVERT_TAG',
  'EDIT_LAYERS_TAG',
  'EXPORT_LAYERS_TAG',
  'NAME_ONLY_TAG',
]


def get_filtered_builtin_actions(builtin_actions, tags=None):
  if tags is None:
    tags = []

  return {
    name: action_dict
    for name, action_dict in builtin_actions.items()
    if any(tag in action_dict['additional_tags'] for tag in tags)
  }
