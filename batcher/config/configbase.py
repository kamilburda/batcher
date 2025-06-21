"""Class for creating plug-in-wide configuration.

Once a configuration object is instantiated, existing entries can be modified
and new entries can be created at any time.

Configuration entries can also be made dynamic, i.e. resolve dynamically at
the time of accessing the entry, by wrapping the entry in a function accepting
no parameters and returning a single value. For example, suppose that a
``translate`` function takes an input string and returns a translated version
of the string. You can then assign an entry as follows:

  config.PLUGIN_TITLE = lambda: translate('Batcher')

Every time you access `config.PLUGIN_TITLE`, the input string will be processed
and the output will be a translated version of the string.

Dynamic entries are also useful when you need to keep some entries up-to-date
when they depend on the value of other entries, which may be modified.

The following configuration entries are provided by default:

  PLUGIN_DIRPATH:
    Path to the directory containing the main plug-in file and other files
    required to run the plug-in.
  PLUGINS_DIRPATH:
    Path to the directory containing plug-ins where this plug-in is installed.
  PLUGIN_NAME: Name of the plug-in usable as an identifier.
  PLUGIN_TITLE: Human-readable title of the plug-in.
  PLUGIN_VERSION:
    The plug-in version, used predominantly to check if a newer version is
    detected (in that case, settings will be updated to ensure compatibility
    with the newer version).
  LOCALE_DIRPATH:
    Path to the ``'locale'`` directory containing translation files.
  DOMAIN_NAME:
    Domain name used when initializing plug-in internationalization.
  BUG_REPORT_URL_LIST: List of URLs where users can submit bug reports.
  STDOUT_LOG_HANDLES:
    List of strings describing destination sources where standard output will be
    logged. See the `logging` module for possible types.
  STDERR_LOG_HANDLES:
    List of strings describing destination sources where error output will be
    logged. See the `logging` module for possible types.
  DEFAULT_LOGS_DIRPATH:
    Default path to a directory where messages will be logged.
  PLUGINS_LOG_DIRPATHS:
    List of possible directories where messages will be logged. The earliest
    directory in the list takes precedence, if messages can be logged there.
  PLUGINS_LOG_OUTPUT_FILENAME:
    Name of the file to write standard output to.
  PLUGINS_LOG_ERROR_FILENAME:
    Name of the file to write error output to.
  PROCEDURE_GROUP:
    String identifying a group of related plug-in procedures. This is used to
    e.g. filter built-in actions. conditions or name pattern fields that are
    not applicable for particular procedures.
  DEFAULT_SOURCE:
    Default source where settings will be loaded from or saved to.
  WARN_ON_INVALID_SETTING_VALUES:
    If ``True``, warning messages will be issued when a setting is assigned
    a value that is not valid.
  SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE:
    Set of `setting.Setting` instances for which warning messages will not be
    issued if assigning a value that is not valid, even if
    ``WARN_ON_INVALID_SETTING_VALUES`` is set to ``True``.
"""

import os
import sys

try:
  import gi
  gi.require_version('Gimp', '3.0')
  from gi.repository import Gimp
except (ValueError, ImportError):
  _gimp_modules_available = False
else:
  _gimp_modules_available = True

from src import logging
from src import utils

if _gimp_modules_available:
  from src import setting as setting_


class _Config:

  def __init__(self):
    super().__setattr__('_config', {})

  def __setattr__(self, name, value):
    self._config[name] = value

  def __getattr__(self, name):
    if name not in self._config:
      raise AttributeError(f'configuration entry "{name}" not found')

    attr = self._config[name]

    if callable(attr):
      return attr()
    else:
      return attr

  def __hasattr__(self, name):
    return name in self._config


def create_config() -> _Config:
  """Creates plug-in configuration.

  The configuration object contains plug-in-wide variables such as plug-in
  title, version, author information or documentation-related metadata.

  The release-type configuration is located in the ``config.py`` file. For
  development purposes, you can create a ``config_dev.py`` file which will
  take precedence.
  """
  config = _Config()

  _init_config_initial(config, _get_plugin_dirpath())

  _init_config_logging(config)

  _init_config_from_file(config)

  _init_config_per_procedure(config)

  return config


def _get_plugin_dirpath():
  # This depends on the location of the `configbase.py` file.
  return os.path.dirname(os.path.dirname(os.path.abspath(utils.get_current_module_filepath())))


def _init_config_initial(config: _Config, plugin_dirpath: str):
  config._DEFAULT_PLUGIN_NAME = os.path.basename(plugin_dirpath)
  config.PLUGIN_DIRPATH = plugin_dirpath
  config.PLUGINS_DIRPATH = os.path.dirname(plugin_dirpath)
  config.DEFAULT_LOGS_DIRPATH = lambda: config.PLUGIN_DIRPATH

  # noinspection PyProtectedMember
  config.PLUGIN_NAME = config._DEFAULT_PLUGIN_NAME
  config.PLUGIN_TITLE = lambda: config.PLUGIN_NAME
  config.PLUGIN_VERSION = '1.0'

  config.LOCALE_DIRPATH = lambda: os.path.join(config.PLUGIN_DIRPATH, 'locale')
  # noinspection PyProtectedMember
  config.DOMAIN_NAME = config._DEFAULT_PLUGIN_NAME

  config.BUG_REPORT_URL_LIST = []

  config.STDOUT_LOG_HANDLES = []
  config.STDERR_LOG_HANDLES = ['file']

  config.WARN_ON_INVALID_SETTING_VALUES = True
  config.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE = set()


def _init_config_logging(config: _Config):
  config.PLUGINS_LOG_DIRPATHS = []
  config.PLUGINS_LOG_DIRPATHS.append(config.DEFAULT_LOGS_DIRPATH)

  if _gimp_modules_available:
    plugins_dirpath_alternate = Gimp.directory()
    if plugins_dirpath_alternate != config.DEFAULT_LOGS_DIRPATH:
      # Add the GIMP directory in the user directory as another log path in
      # case the plug-in was installed system-wide and there is no permission to
      # create log files there.
      config.PLUGINS_LOG_DIRPATHS.append(plugins_dirpath_alternate)

  config.PLUGINS_LOG_OUTPUT_FILENAME = 'output.log'
  config.PLUGINS_LOG_ERROR_FILENAME = 'error.log'


def _init_config_from_file(config: _Config):
  try:
    # Prefer a development version of config if it exists. This keeps the
    # config for releases clean.
    from config import config_dev as plugin_config
  except ImportError:
    pass
  else:
    plugin_config.initialize_config(config)
    return

  try:
    from config import config as plugin_config
  except ImportError:
    pass
  else:
    plugin_config.initialize_config(config)
    return


def _init_config_per_procedure(config: _Config):
  config.PROCEDURE_GROUP = config.PLUGIN_NAME

  if _gimp_modules_available:
    config.DEFAULT_SOURCE = setting_.GimpParasiteSource(config.PROCEDURE_GROUP)

    setting_.persistor.Persistor.set_default_setting_sources({
      'persistent': config.DEFAULT_SOURCE,
    })
  else:
    config.DEFAULT_SOURCE = None

  logging.log_output(
    config.STDOUT_LOG_HANDLES,
    config.STDERR_LOG_HANDLES,
    config.PLUGINS_LOG_DIRPATHS,
    config.PLUGINS_LOG_OUTPUT_FILENAME,
    config.PLUGINS_LOG_ERROR_FILENAME,
    config.PLUGIN_TITLE,
  )

  if _gimp_modules_available:
    setting_.Setting.connect_event_global('value-not-valid', _on_setting_value_not_valid, config)


def _on_setting_value_not_valid(setting, message, _message_id, _details, config):
  if (config.WARN_ON_INVALID_SETTING_VALUES
      and setting not in config.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE):
    print(f'Warning: setting "{setting.get_path()}": {message}', file=sys.stderr)
