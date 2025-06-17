"""Library initialization."""

try:
  import gi
  gi.require_version('Gimp', '3.0')
  from gi.repository import Gimp as _Gimp
except (ValueError, ImportError):
  _gimp_modules_available = False
else:
  _gimp_modules_available = True


from . import utils

__all__ = [
  # Modules
  'utils',
]

if _gimp_modules_available:
  from . import gui
  from . import pdbutils

  from .pypdb import pdb
  from .pypdb import PDBProcedureError

  __all__.extend([
    # Modules
    'gui',
    'pdbutils',
    # Global elements imported to or defined in this module
    'pdb',
    'PDBProcedureError',
  ])
