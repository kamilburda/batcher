"""Library initialization."""
import builtins
import os


_ROOT_PLUGIN_DIRPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


from . import logging

# Enable logging as early as possible to capture any unexpected errors (such
# as missing modules) before pygimplib is fully initialized.
logging.log_output(
  stderr_handles=['file'],
  log_dirpaths=[_ROOT_PLUGIN_DIRPATH],
  log_error_filename='error.log',
  log_header_title=_ROOT_PLUGIN_DIRPATH)


try:
  from gi.repository import GLib
except ImportError:
  def _(message):
    return message
else:
  def _(message):
    return GLib.dgettext(None, message)

# Install translations as early as possible so that module- or class-level
# strings are translated.
builtins._ = _


try:
  import gi
  gi.require_version('Gimp', '3.0')
  from gi.repository import Gimp as _Gimp
except (ValueError, ImportError):
  _gimp_modules_available = False
else:
  _gimp_modules_available = True


from . import utils

from .constants import *

__all__ = [
  # Modules
  'logging',
  'utils',
]

if _gimp_modules_available:
  from . import gui
  from . import invocation
  from . import pdbutils

  from .pypdb import pdb
  from .pypdb import PDBProcedureError

  __all__.extend([
    # Modules
    'gui',
    'invocation',
    'pdbutils',
    # Global elements imported to or defined in this module
    'pdb',
    'PDBProcedureError',
  ])
