import builtins
import os

PYGIMPLIB_DIRPATH = os.path.dirname(os.path.abspath(__file__))

try:
  import gi
  gi.require_version('Gimp', '3.0')
  from gi.repository import Gimp
  from gi.repository import GLib
except ImportError:
  _gimp_dependent_modules_available = False
else:
  _gimp_dependent_modules_available = True

from . import logging


if _gimp_dependent_modules_available:
  # Enable logging as early as possible to capture any unexpected errors (such
  # as missing modules) before pygimplib is fully initialized.
  logging.log_output(
    log_mode='exceptions',
    log_dirpaths=[os.path.dirname(PYGIMPLIB_DIRPATH), PYGIMPLIB_DIRPATH],
    log_stdout_filename=None,
    log_stderr_filename='error.log',
    log_header_title='pygimplib')

  def _(message):
    return GLib.dgettext(None, message)

  # Install translations as early as possible so that module- or class-level
  # strings are translated.
  builtins._ = _

  from . import _gui_messages

  _gui_messages.set_gui_excepthook(title=None, app_name=None)
else:
  # Make sure `_` is always defined to avoid errors
  def _(message):
    return message

  builtins._ = _


from .constants import *

from . import configbase
from . import utils
from . import version

if _gimp_dependent_modules_available:
  gi.require_version('GimpUi', '3.0')
  from gi.repository import GimpUi

  from . import fileformats
  from . import gui
  from . import invocation
  from . import invoker
  from . import itemtree
  from . import objectfilter
  from . import overwrite
  from . import path
  from . import pdbutils
  from . import progress
  from . import setting

  from .procedure import main
  from .procedure import register_procedure
  from .pypdb import pdb
  from .setting import SettingGuiTypes
  from .setting import SettingTypes

__all__ = [
  # Modules
  'logging',
  'utils',
  'version',
  # Global elements imported to or defined in this module
  'config',
]

if _gimp_dependent_modules_available:
  __all__.extend([
    # Modules
    'fileformats',
    'gui',
    'invocation',
    'invoker',
    'itemtree',
    'objectfilter',
    'overwrite',
    'path',
    'pdbutils',
    'progress',
    'setting',
    # Global elements imported to or defined in this module
    'main',
    'pdb',
    'register_procedure',
    'SettingGuiTypes',
    'SettingTypes',
  ])


config = None


def _init_config():
  global config
  
  if config is not None:
    return
  
  config = configbase.create_config(PYGIMPLIB_DIRPATH, _gimp_dependent_modules_available)


_init_config()


if _gimp_dependent_modules_available:
  
  _procedures = {}
  _procedures_names = {}
  
  def procedure(**kwargs):
    """Installs a function as a GIMP procedure.
    
    Use this function as a decorator over a function to be exposed to the GIMP
    procedural database (PDB).
    
    The installed procedure can then be accessed via the GIMP (PDB) and,
    optionally, from the GIMP user interface.
    
    The function name is used as the procedure name as found in the GIMP PDB.
    
    The following keyword arguments are accepted:
    
    * `blurb` - Short description of the procedure.
    
    * `description` - More detailed information about the procedure.
    
    * `author` - Author of the plug-in.
    
    * `copyright_holder` - Copyright holder of the plug-in.
    
    * `date` - Dates (usually years) at which the plug-in development was
      active.
    
    * `menu_name` - Name of the menu entry in the GIMP user interface.
    
    * `menu_path` - Path of the menu entry in the GIMP user interface.
    
    * `image_types` - Image types to which the procedure applies (e.g. RGB or
      indexed). Defaults to `'*'` (any image type).
    
    * `parameters` - Procedure parameters. This is a list of tuples of three
      elements: `(PDB type, name, description)`. Alternatively, you may pass a
      `setting.Group` instance or a list of `setting.Group` instances containing
      plug-in settings.
    
    * `return_values` - Return values of the procedure, usable when calling the
      procedure programmatically. The format of `return_values` is the same as
      `parameters`.
    
    Example:
      
      import pygimplib as pg
      
      \@pg.procedure(
        blurb='Export layers as separate images',
        author='John Doe',
        menu_name=_('E_xport Layers...'),
        menu_path='<Image>/File/Export',
        parameters=[
          (gimpenums.PDB_INT32, 'run-mode', 'The run mode'),
          (gimpenums.PDB_IMAGE, 'image', 'The current image'),
          (gimpenums.PDB_STRING, 'dirpath', 'Output directory path')]
      )
      def plug_in_export_layers(run_mode, image, *args):
        ...
    """
    
    def procedure_wrapper(procedure):
      _procedures[procedure] = kwargs
      _procedures_names[procedure.__name__] = procedure
      return procedure
    
    return procedure_wrapper
  
  def main():
    """Enables installation and running of GIMP procedures.
    
    Call this function at the end of your main plug-in file.
    """
    gimp.main(None, None, _query, _run)
  
  def _install_procedure(
        procedure,
        blurb='',
        description='',
        author='',
        copyright_notice='',
        date='',
        menu_name='',
        menu_path=None,
        image_types='*',
        parameters=None,
        return_values=None):
    
    def _get_pdb_params(params):
      pdb_params = []
      
      if params:
        has_settings = isinstance(
          params[0], (setting.Setting, setting.Group))
        if has_settings:
          pdb_params = setting.create_params(*params)
        else:
          pdb_params = params
      
      return pdb_params
    
    gimp.install_procedure(
      procedure.__name__,
      blurb,
      description,
      author,
      copyright_notice,
      date,
      menu_name,
      image_types,
      gimpenums.PLUGIN,
      _get_pdb_params(parameters),
      _get_pdb_params(return_values))
    
    if menu_path:
      gimp.menu_register(procedure.__name__, menu_path)
  
  def _query():
    for procedure, kwargs in _procedures.items():
      _install_procedure(procedure, **kwargs)
  
  def _run(procedure_name, procedure_params):
    procedure = _add_gui_excepthook(
      _procedures_names[procedure_name], procedure_params[0])
    
    if hasattr(gimpui, 'gimp_ui_init'):
      gimpui.gimp_ui_init()
    
    procedure(*procedure_params)
  
  def _add_gui_excepthook(procedure, run_mode):
    if run_mode == gimpenums.RUN_INTERACTIVE:
      gui.set_gui_excepthook_additional_callback(
        _display_message_on_setting_value_error)
      
      add_gui_excepthook_func = gui.add_gui_excepthook(
        title=config.PLUGIN_TITLE,
        app_name=config.PLUGIN_TITLE,
        report_uri_list=config.BUG_REPORT_URL_LIST)
      
      return add_gui_excepthook_func(procedure)
    else:
      return procedure
  
  def _display_message_on_setting_value_error(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, setting.SettingValueError):
      gimp.message(utils.safe_encode_gimp(str(exc_value)))
      return True
    else:
      return False
