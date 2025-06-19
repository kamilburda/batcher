import collections

from src import commands
from src import placeholders
from src.pypdb import pdb


def test_add_all_pdb_procedures_as_commands():
  """Returns a command group containing all PDB procedures and a list of
  unsupported PDB procedures if any.

  This allows to check if all setting types are properly supported.
  """
  procedures = commands.create('all_pdb_procedures')

  unsupported_args = collections.defaultdict(list)

  for procedure_name in sorted(pdb.list_all_procedure_names()):
    command = commands.add(procedures, procedure_name)

    for argument in command['arguments']:
      if isinstance(argument, placeholders.PlaceholderUnsupportedParameterSetting):
        unsupported_args[procedure_name].append((argument.name, argument.pdb_type))

  return procedures, unsupported_args
