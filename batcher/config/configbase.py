"""Class for creating plug-in-wide configuration."""

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

import pygimplib as pg

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

  _init_config_initial(config, _get_root_plugin_dirpath())

  _init_config_logging(config)

  _init_config_from_file(config)

  _init_config_per_procedure(config)

  return config


def _get_root_plugin_dirpath():
  # This depends on the location of the `configbase.py` file.
  return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _init_config_initial(config: _Config, root_plugin_dirpath: str):
  config._DEFAULT_PLUGIN_NAME = os.path.basename(root_plugin_dirpath)
  config.PLUGIN_DIRPATH = root_plugin_dirpath
  config.PLUGINS_DIRPATH = os.path.dirname(root_plugin_dirpath)
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

  config.PLUGINS_LOG_STDOUT_DIRPATH = config.DEFAULT_LOGS_DIRPATH
  config.PLUGINS_LOG_STDERR_DIRPATH = config.DEFAULT_LOGS_DIRPATH

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

  pg.logging.log_output(
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
