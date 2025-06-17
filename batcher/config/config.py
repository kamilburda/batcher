"""Plug-in configuration."""

import os


def initialize_config(config):
  config.STDOUT_LOG_HANDLES = []
  config.STDERR_LOG_HANDLES = ['file']

  config.WARN_ON_INVALID_SETTING_VALUES = True

  config.PLUGIN_NAME = 'batcher'
  config.DOMAIN_NAME = 'batcher'
  config.PLUGIN_TITLE = lambda: _('Batcher')
  config.PLUGIN_VERSION = '1.1.1'
  config.PLUGIN_VERSION_RELEASE_DATE = 'June 15, 2025'
  config.AUTHOR_NAME = 'Kamil Burda'
  config.COPYRIGHT_YEARS = '2023-2025'
  config.PAGE_URL = 'https://kamilburda.github.io/batcher'
  config.DOCS_URL = f'{config.PAGE_URL}/docs/usage'
  config.LOCAL_DOCS_PATH = os.path.join(config.PLUGIN_DIRPATH, 'docs', 'usage', 'index.html')
  config.REPOSITORY_USERNAME = 'kamilburda'
  config.REPOSITORY_NAME = 'batcher'
  config.REPOSITORY_URL = 'https://github.com/kamilburda/batcher'
  config.BUG_REPORT_URL_LIST = [
    ('GitHub', 'https://github.com/kamilburda/batcher/issues')
  ]
