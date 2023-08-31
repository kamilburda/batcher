"""Wrapper of ``Gimp.get_pdb()`` to simplify invoking GIMP PDB procedures."""

from typing import Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp


class _PyPDB:

  def __init__(self):
    self._last_status = None
    self._last_error = None

    self._proc_cache = {}

  @property
  def last_status(self):
    """Exit status of the last GIMP PDB procedure invoked by this class."""
    return self._last_status

  @property
  def last_error(self):
    """Error message of the last GIMP PDB procedure invoked by this class."""
    return self._last_error

  def __getattr__(self, name):
    proc_name = name.replace('_', '-')

    if not self._procedure_exists(proc_name):
      raise AttributeError(f'procedure "{proc_name}" does not exist')

    return self._get_proc_by_name(proc_name)

  def __getitem__(self, name):
    proc_name = name.replace('_', '-')

    if not self._procedure_exists(proc_name):
      raise KeyError(f'procedure "{proc_name}" does not exist')

    return self._get_proc_by_name(proc_name)

  def __contains__(self, name):
    return self._procedure_exists(name)

  def _get_proc_by_name(self, proc_name):
    if proc_name not in self._proc_cache:
      self._proc_cache[proc_name] = PyPDBProcedure(self, proc_name)

    return self._proc_cache[proc_name]

  @staticmethod
  def _procedure_exists(proc_name):
    return Gimp.get_pdb().procedure_exists(proc_name)


class PyPDBProcedure:

  def __init__(self, pdb_wrapper, proc_name):
    self._pdb_wrapper = pdb_wrapper
    self._name = proc_name

    self._info = Gimp.get_pdb().lookup_procedure(self._name)
    self._has_run_mode = self._get_has_run_mode()

  @property
  def name(self):
    """Procedure name as it appears in the GIMP procedural database (PDB)."""
    return self._name

  @property
  def info(self):
    """`Gimp.Procedure` instance containing procedure metadata."""
    return self._info

  @property
  def has_run_mode(self):
    """`True` if the procedure has `run-mode` as its first argument, `False`
    otherwise.
    """
    return self._has_run_mode

  def __call__(
        self,
        *args,
        run_mode: Gimp.RunMode = Gimp.RunMode.NONINTERACTIVE,
        config: Optional[Gimp.ProcedureConfig] = None):
    if config is None:
      if self._has_run_mode:
        result = Gimp.get_pdb().run_procedure(self._name, [run_mode, *args])
      else:
        result = Gimp.get_pdb().run_procedure(self._name, args)
    else:
      result = Gimp.get_pdb().run_procedure_config(self._name, config)

    if result is None:
      return None

    result_list = [result.index(i) for i in range(result.length())]

    if len(result_list) > 0:
      if isinstance(result_list[0], Gimp.PDBStatusType):
        self._pdb_wrapper._last_status = result_list.pop(0)

    if len(result_list) > 0:
      if self._pdb_wrapper._last_status in [
            Gimp.PDBStatusType.SUCCESS, Gimp.PDBStatusType.PASS_THROUGH]:
        self._pdb_wrapper._last_error = None
      else:
        self._pdb_wrapper._last_error = result_list.pop(0)

    if result_list:
      if len(result_list) == 1:
        return result_list[0]
      else:
        return result_list
    else:
      return None

  def _get_has_run_mode(self):
    proc_arg_info = self._info.get_arguments()
    if proc_arg_info and proc_arg_info[0].value_type.pytype:
      return issubclass(proc_arg_info[0].value_type.pytype, Gimp.RunMode)
    else:
      return False


pdb = _PyPDB()
