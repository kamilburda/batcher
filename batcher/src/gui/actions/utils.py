"""Utility functions for the `gui.actions` package."""


def get_action_description(action_or_action_dict, pdb_procedure):
  if pdb_procedure is not None:
    blurb = pdb_procedure.get_blurb()
    return blurb if blurb is not None else ''
  else:
    if isinstance(action_or_action_dict, dict):
      return action_or_action_dict.get('description', '')
    else:
      description = action_or_action_dict['description'].value
      return description
