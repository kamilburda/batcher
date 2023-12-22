"""Class for creating plug-in-wide configuration."""

import builtins
import os
from typing import Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from . import logging as pglogging
from . import setting as pgsetting


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


def create_config(pygimplib_dirpath: str, root_plugin_dirpath: Optional[str]) -> _Config:
  """Creates plug-in configuration.

  The configuration object contains plug-in-wide variables such as plug-in
  identifier (by default equivalent to the main plug-in directory name) or
  title.

  Plug-ins can contain a ``config.py`` file in the ``config`` subdirectory
  under the main plug-in directory to customize the configuration variables.
  Additionally, developers may also include a ``config_dev.py`` file acting as
  a local configuration file for testing purposes.
  """
  config = _Config()

  _init_config_initial(config, pygimplib_dirpath, root_plugin_dirpath)

  _init_config_logging(config)

  _init_config_from_file(config)

  _init_config_per_procedure(config)

  return config


def _init_config_initial(
      config: _Config, pygimplib_dirpath: str, root_plugin_dirpath: Optional[str]):
  config.PYGIMPLIB_DIRPATH = pygimplib_dirpath

  if root_plugin_dirpath is not None:
    config._DEFAULT_PLUGIN_NAME = os.path.basename(root_plugin_dirpath)
    config.PLUGIN_DIRPATH = root_plugin_dirpath
    config.PLUGINS_DIRPATH = os.path.dirname(root_plugin_dirpath)
    config.DEFAULT_LOGS_DIRPATH = lambda: config.PLUGIN_DIRPATH
  else:
    # Fallback in case root_plugin_dirpath is `None` for some reason
    config._DEFAULT_PLUGIN_NAME = None
    config.PLUGIN_DIRPATH = os.path.dirname(pygimplib_dirpath)
    config.PLUGINS_DIRPATH = os.path.dirname(config.PLUGIN_DIRPATH)
    config.DEFAULT_LOGS_DIRPATH = os.path.dirname(pygimplib_dirpath)

  # noinspection PyProtectedMember
  config.PLUGIN_NAME = config._DEFAULT_PLUGIN_NAME
  config.PLUGIN_TITLE = lambda: config.PLUGIN_NAME
  config.PLUGIN_VERSION = '1.0'

  config.LOCALE_DIRPATH = lambda: os.path.join(config.PLUGIN_DIRPATH, 'locale')
  # noinspection PyProtectedMember
  config.DOMAIN_NAME = config._DEFAULT_PLUGIN_NAME

  config.BUG_REPORT_URL_LIST = []

  config.LOG_MODE = 'error'


def _init_config_logging(config: _Config):
  config.PLUGINS_LOG_DIRPATHS = []
  config.PLUGINS_LOG_DIRPATHS.append(config.DEFAULT_LOGS_DIRPATH)

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
  orig_builtin_c = None
  if hasattr(builtins, 'c'):
    orig_builtin_c = builtins.c

  builtins.c = config

  try:
    # Prefer a development version of config if it exists. This is handy if you
    # need to keep a clean config in the remote repository and a local config
    # for development purposes.
    from config import config_dev as plugin_config
  except ImportError:
    try:
      from config import config as plugin_config
    except ImportError:
      pass

  if orig_builtin_c is None:
    del builtins.c
  else:
    builtins.c = orig_builtin_c


def _init_config_per_procedure(config: _Config):
  config.SOURCE_NAME = config.PLUGIN_NAME
  config.DEFAULT_SOURCE = pgsetting.GimpParasiteSource(config.SOURCE_NAME)

  pgsetting.persistor.Persistor.set_default_setting_sources({
    'persistent': config.DEFAULT_SOURCE,
  })

  pglogging.log_output(
    config.LOG_MODE,
    config.PLUGINS_LOG_DIRPATHS,
    config.PLUGINS_LOG_OUTPUT_FILENAME,
    config.PLUGINS_LOG_ERROR_FILENAME,
    config.PLUGIN_TITLE,
  )
