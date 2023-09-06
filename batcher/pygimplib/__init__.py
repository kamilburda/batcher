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

# FIXME: Duplicate logging instead of redirecting it.
#   The latter is not practical in case of e.g. running tests from the IDE or
#   test-running the plug-in while expecting error messages in the GIMP
#   console.
# # Enable logging as early as possible to capture any unexpected errors (such
# # as missing modules) before pygimplib is fully initialized.
# logging.log_output(
#   log_mode='exceptions',
#   log_dirpaths=[os.path.dirname(PYGIMPLIB_DIRPATH), PYGIMPLIB_DIRPATH],
#   log_stdout_filename=None,
#   log_stderr_filename='error.log',
#   log_header_title='pygimplib')


from gi.repository import GLib


def _(message):
  return GLib.dgettext(None, message)


# Install translations as early as possible so that module- or class-level
# strings are translated.
builtins._ = _

# from . import _gui_messages
#
# _gui_messages.set_gui_excepthook(title=None, app_name=None)

# from . import configbase
from . import fileformats
# from . import gui
from . import invocation
from . import invoker
# from . import itemtree
from . import objectfilter
from . import overwrite
from . import path
from . import pdbutils
from . import progress
# from . import setting
from . import utils

from .constants import *
from .procedure import main
from .procedure import register_procedure
from .procedure import set_use_locale
from .pypdb import pdb
# from .setting import SettingGuiTypes
# from .setting import SettingTypes

__all__ = [
  # Modules
  'fileformats',
  # 'gui',
  'invocation',
  'invoker',
  # 'itemtree',
  'logging',
  'objectfilter',
  'overwrite',
  'path',
  'pdbutils',
  'progress',
  # 'setting',
  'utils',
  # Global elements imported to or defined in this module
  'GIMP_ENCODING',
  'TEXT_FILE_ENCODING',
  # 'config',
  'main',
  'pdb',
  'register_procedure',
  'set_use_locale',
  # 'SettingGuiTypes',
  # 'SettingTypes',
]


# config = configbase.create_config(PYGIMPLIB_DIRPATH, ROOT_PLUGIN_DIRPATH)
