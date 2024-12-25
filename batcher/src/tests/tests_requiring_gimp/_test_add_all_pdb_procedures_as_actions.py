import collections

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from pygimplib import pdb

from src import actions
from src import placeholders


def test_add_all_pdb_procedures_as_actions():
  """Returns an action group containing all PDB procedures and a list of
  unsupported PDB procedures if any.

  This allows to check if all setting types are properly supported.
  """
  procedures = actions.create('all_pdb_procedures')

  unsupported_args = collections.defaultdict(list)

  for procedure_name in sorted(pdb.list_all_procedure_names()):
    action = actions.add(procedures, procedure_name)

    for argument in action['arguments']:
      if isinstance(argument, placeholders.PlaceholderUnsupportedParameterSetting):
        unsupported_args[procedure_name].append((argument.name, argument.pdb_type))

  return procedures, unsupported_args
