import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import actions


def test_add_all_pdb_procedures_as_actions():
  """Returns an action group containing all PDB procedures and a list of
  unsupported PDB procedures if any.

  This allows to check if all setting types are properly supported.
  """
  procedures = actions.create('all_pdb_procedures')

  unsupported_procedures = []

  for procedure_name in Gimp.get_pdb().query_procedures(*([''] * 8)):
    try:
      actions.add(procedures, procedure_name)
    except actions.UnsupportedPdbProcedureError as e:
      unsupported_procedures.append((e.procedure_name, e.unsupported_param_type))

  return procedures, unsupported_procedures
