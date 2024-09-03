"""Wrapper of ``Gimp.get_pdb()`` to simplify invoking GIMP PDB procedures."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp


__all__ = [
  'pdb',
  'PyPDBProcedure',
  'PDBProcedureError',
]


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
    if name is None:
      return False

    proc_name = name.replace('_', '-')

    return self._procedure_exists(proc_name)

  def remove_from_cache(self, name):
    """Removes a `PyPDBProcedure` instance matching ``name`` from the internal
    cache.

    This method is only ever useful for testing purposes.

    No action is taken if there is no procedure matching ``name`` in the cache.
    """
    proc_name = name.replace('_', '-')

    try:
      del self._proc_cache[proc_name]
    except KeyError:
      pass

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

    self._proc = Gimp.get_pdb().lookup_procedure(self._name)
    self._has_run_mode = self._get_has_run_mode()

  @property
  def name(self):
    """Procedure name as it appears in the GIMP procedural database (PDB)."""
    return self._name

  @property
  def proc(self):
    """`Gimp.Procedure` instance containing procedure metadata."""
    return self._proc

  @property
  def has_run_mode(self):
    """`True` if the procedure has `run-mode` as its first argument, `False`
    otherwise.
    """
    return self._has_run_mode

  def __call__(self, *args, run_mode=Gimp.RunMode.NONINTERACTIVE, **kwargs):
    """Calls the procedure.

    The `run_mode` parameter cannot be specified as a positional argument, only
    as a keyword argument.

    Positional arguments correspond to the arguments specified in the GIMP PDB,
    except the run mode as described above.

    You can alternatively specify the arguments as keyword arguments. This way,
    any omitted arguments earlier in the order will be replaced with their
    default value.
    """
    config = self._create_config(run_mode, *args, **kwargs)

    result = self._proc.run(config)

    if result is None:
      return None

    result_list = [result.index(i) for i in range(result.length())]

    last_status = None
    last_error = None

    if len(result_list) > 0:
      if isinstance(result_list[0], Gimp.PDBStatusType):
        last_status = result_list.pop(0)

    if len(result_list) > 0:
      if last_status not in [Gimp.PDBStatusType.SUCCESS, Gimp.PDBStatusType.PASS_THROUGH]:
        last_error = result_list.pop(0)

    self._pdb_wrapper._last_status = last_status
    self._pdb_wrapper._last_error = last_error

    if (last_status is not None
        and last_status not in [Gimp.PDBStatusType.SUCCESS, Gimp.PDBStatusType.PASS_THROUGH]):
      raise PDBProcedureError(last_error, last_status)

    if result_list:
      if len(result_list) == 1:
        return result_list[0]
      else:
        return result_list
    else:
      return None

  def _get_has_run_mode(self):
    proc_arg_info = self._proc.get_arguments()
    if proc_arg_info:
      return proc_arg_info[0].value_type == Gimp.RunMode.__gtype__
    else:
      return False

  def _create_config(self, run_mode, *proc_args, **proc_kwargs):
    config = self._proc.create_config()

    arg_names = [arg.name for arg in self._proc.get_arguments()]
    if self.has_run_mode:
      config.set_property(arg_names[0].replace('_', '-'), run_mode)
      arg_names = arg_names[1:]

    property_names = set(prop.name for prop in config.list_properties())

    for arg_name, arg_value in zip(arg_names, proc_args):
      processed_arg_name = arg_name.replace('_', '-')

      if processed_arg_name in property_names:
        config.set_property(processed_arg_name, arg_value)
      else:
        raise PDBProcedureError(
          f'argument "{processed_arg_name}" does not exist or is not supported',
          Gimp.PDBStatusType.CALLING_ERROR)

    # Keyword arguments can override positional arguments
    for arg_name, arg_value in proc_kwargs.items():
      processed_arg_name = arg_name.replace('_', '-')

      if processed_arg_name in property_names:
        config.set_property(processed_arg_name, arg_value)
      else:
        raise PDBProcedureError(
          f'argument "{processed_arg_name}" does not exist or is not supported',
          Gimp.PDBStatusType.CALLING_ERROR)

    return config


class PDBProcedureError(Exception):

  def __init__(self, message, status):
    super().__init__(message)

    self.message = message
    self.status = status

  def __str__(self):
    return str(self.message)


pdb = _PyPDB()
