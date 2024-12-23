"""Library initialization."""
import builtins
import inspect
import os

PYGIMPLIB_DIRPATH = os.path.dirname(os.path.abspath(__file__))


def _get_root_plugin_dirpath():
  frame_stack = inspect.stack()

  if frame_stack:
    return os.path.dirname(os.path.abspath(frame_stack[-1][1]))
  else:
    return None


ROOT_PLUGIN_DIRPATH = _get_root_plugin_dirpath()

from . import logging

# Enable logging as early as possible to capture any unexpected errors (such
# as missing modules) before pygimplib is fully initialized.
logging.log_output(
  stderr_handles=['file'],
  log_dirpaths=[ROOT_PLUGIN_DIRPATH, os.path.dirname(PYGIMPLIB_DIRPATH), PYGIMPLIB_DIRPATH],
  log_error_filename='error.log',
  log_header_title=ROOT_PLUGIN_DIRPATH)


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


from . import configbase
from . import objectfilter
from . import utils

from .constants import *

__all__ = [
  # Modules
  'logging',
  'objectfilter',
  'utils',
  # Global elements imported to or defined in this module
  'config',
]

if _gimp_modules_available:
  from . import gui
  from . import invocation
  from . import itemtree
  from . import pdbutils
  from . import setting

  from .initnotifier import notifier
  from .procedure import main
  from .procedure import register_procedure
  from .procedure import set_use_locale
  from .pypdb import pdb
  from .pypdb import PDBProcedureError
  from .setting import SETTING_GUI_TYPES
  from .setting import SETTING_TYPES

  __all__.extend([
    # Modules
    'gui',
    'invocation',
    'itemtree',
    'pdbutils',
    'setting',
    # Global elements imported to or defined in this module
    'main',
    'notifier',
    'pdb',
    'PDBProcedureError',
    'register_procedure',
    'set_use_locale',
    'SETTING_GUI_TYPES',
    'SETTING_TYPES',
  ])


config = configbase.create_config(PYGIMPLIB_DIRPATH, ROOT_PLUGIN_DIRPATH)
