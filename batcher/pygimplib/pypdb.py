"""Wrapper of ``Gimp.get_pdb()`` to simplify invoking GIMP PDB procedures."""

from __future__ import annotations

import abc
from typing import List, Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp


__all__ = [
  'pdb',
  'GeglProcedure',
  'GimpPDBProcedure',
  'PDBProcedure',
  'PDBProcedureError',
]


class _PyPDB:

  def __init__(self):
    self._last_status = None
    self._last_error = None

    self._proc_cache = {}

  @property
  def last_status(self):
    """Exit status of the last `GimpPDBProcedure` invoked by this class."""
    return self._last_status

  @property
  def last_error(self):
    """Error message of the last `GimpPDBProcedure` invoked by this class."""
    return self._last_error

  def __getattr__(self, name: str) -> PDBProcedure:
    proc_name = name.replace('_', '-')

    if not self._procedure_exists(proc_name):
      raise AttributeError(f'procedure "{proc_name}" does not exist')

    return self._get_proc_by_name(proc_name)

  def __getitem__(self, name: str) -> PDBProcedure:
    proc_name = name.replace('_', '-')

    if not self._procedure_exists(proc_name):
      raise KeyError(f'procedure "{proc_name}" does not exist')

    return self._get_proc_by_name(proc_name)

  def __contains__(self, name: Optional[str]) -> bool:
    if name is None:
      return False

    proc_name = name.replace('_', '-')

    return self._procedure_exists(proc_name)

  @staticmethod
  def list_all_procedure_names() -> List[str]:
    return Gimp.get_pdb().query_procedures(*([''] * 8))

  def remove_from_cache(self, name: str):
    """Removes a `PDBProcedure` instance matching ``name`` from the internal
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
      self._proc_cache[proc_name] = GimpPDBProcedure(self, proc_name)

    return self._proc_cache[proc_name]

  @staticmethod
  def _procedure_exists(proc_name):
    return Gimp.get_pdb().procedure_exists(proc_name)


class PDBProcedure(metaclass=abc.ABCMeta):

  def __init__(self, pypdb_instance, name):
    self._pypdb_instance = pypdb_instance
    self._name = name

    self._has_run_mode = self._get_has_run_mode()

  @abc.abstractmethod
  def __call__(self, *args, run_mode=Gimp.RunMode.NONINTERACTIVE, **kwargs):
    """Calls the procedure.

    The `run_mode` parameter cannot be specified as a positional argument, only
    as a keyword argument. Depending on the subclass, this parameter may be
    ignored.

    Positional arguments correspond to the arguments specified in the procedure,
    except the run mode as described above.

    You can alternatively specify the arguments as keyword arguments. This way,
    any omitted arguments earlier in the order will be replaced with their
    default value.
    """
    pass

  @property
  def has_run_mode(self):
    """``True`` if the procedure has a run mode as its first argument, ``False``
    otherwise.
    """
    return self._has_run_mode

  @property
  @abc.abstractmethod
  def proc(self):
    """Underlying instance used to obtain procedure information."""
    pass

  @property
  @abc.abstractmethod
  def arguments(self):
    pass

  @property
  @abc.abstractmethod
  def aux_arguments(self):
    pass

  @property
  @abc.abstractmethod
  def return_values(self):
    pass

  @property
  @abc.abstractmethod
  def authors(self):
    pass

  @property
  @abc.abstractmethod
  def blurb(self):
    pass

  @property
  @abc.abstractmethod
  def copyright(self):
    pass

  @property
  @abc.abstractmethod
  def date(self):
    pass

  @property
  @abc.abstractmethod
  def help(self):
    pass

  @property
  @abc.abstractmethod
  def menu_label(self):
    pass

  @property
  @abc.abstractmethod
  def menu_paths(self):
    pass

  @property
  def name(self):
    """The procedure name.

    The name can be used to access a `PDBProcedure` instance as `pdb[<name>]`.
    """
    return self._name

  @abc.abstractmethod
  def create_config(self):
    """Creates a procedure config filled with default values."""
    pass

  @abc.abstractmethod
  def _get_has_run_mode(self):
    """Returns ``True`` if the procedure has a run mode as its first argument,
    ``False`` otherwise.
    """
    pass


class GimpPDBProcedure(PDBProcedure):

  def __init__(self, pypdb_instance, name):
    self._proc = Gimp.get_pdb().lookup_procedure(name)

    super().__init__(pypdb_instance, name)

  def __call__(self, *args, run_mode=Gimp.RunMode.NONINTERACTIVE, **kwargs):
    config = self._create_config_for_call(run_mode, *args, **kwargs)

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

    self._pypdb_instance._last_status = last_status
    self._pypdb_instance._last_error = last_error

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

  @property
  def proc(self):
    """`Gimp.Procedure` instance wrapped by this class."""
    return self._proc

  @property
  def arguments(self):
    return self._proc.get_arguments()

  @property
  def aux_arguments(self):
    return self._proc.get_aux_arguments()

  @property
  def return_values(self):
    return self._proc.get_return_values()

  @property
  def authors(self):
    return self._proc.get_authors()

  @property
  def blurb(self):
    return self._proc.get_blurb()

  @property
  def copyright(self):
    return self._proc.get_copyright()

  @property
  def date(self):
    return self._proc.get_date()

  @property
  def help(self):
    return self._proc.get_help()

  @property
  def menu_label(self):
    return self._proc.get_menu_label()

  @property
  def menu_paths(self):
    return self._proc.get_menu_paths()

  def create_config(self):
    return self._proc.create_config()

  def _get_has_run_mode(self):
    proc_arg_info = self._proc.get_arguments()
    if proc_arg_info:
      return proc_arg_info[0].value_type == Gimp.RunMode.__gtype__
    else:
      return False

  def _create_config_for_call(self, run_mode, *proc_args, **proc_kwargs):
    config = self._proc.create_config()

    args = self._proc.get_arguments()

    if self.has_run_mode:
      config.set_property(args[0].name, run_mode)
      args = args[1:]

    for arg, arg_value in zip(args, proc_args):
      config_set_property = _get_set_property_func(arg.value_type.name, config)
      config_set_property(arg.name, arg_value)

    if proc_kwargs:
      args_and_names = {arg.name: arg for arg in args}

      # Keyword arguments can override positional arguments
      for arg_name, arg_value in proc_kwargs.items():
        processed_arg_name = arg_name.replace('_', '-')

        try:
          arg = args_and_names[processed_arg_name]
        except KeyError:
          raise PDBProcedureError(
            f'argument "{processed_arg_name}" does not exist or is not supported',
            Gimp.PDBStatusType.CALLING_ERROR)

        arg_type_name = arg.value_type.name
        config_set_property = _get_set_property_func(arg_type_name, config)
        config_set_property(processed_arg_name, arg_value)

    return config


class GeglProcedure(PDBProcedure):
  pass


def _get_set_property_func(arg_type_name, config):
  if arg_type_name == 'GimpCoreObjectArray':
    return config.set_core_object_array
  elif arg_type_name == 'GimpColorArray':
    return config.set_color_array
  else:
    return config.set_property


class PDBProcedureError(Exception):

  def __init__(self, message, status):
    super().__init__(message)

    self.message = message
    self.status = status

  def __str__(self):
    return str(self.message)


pdb = _PyPDB()
