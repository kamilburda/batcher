"""Plug-in configuration.

Use `c` to access, create or modify configuration entries.
"""

import os


c.LOG_MODE = 'exceptions'

c.PLUGIN_TITLE = lambda: _('Batcher')
c.PLUGIN_VERSION = '0.0.1'
c.PLUGIN_VERSION_RELEASE_DATE = ''
c.AUTHOR_NAME = 'Kamil Burda'
c.COPYRIGHT_YEARS = '2023'
c.PAGE_URL = 'https://kamilburda.github.io/batcher'
c.DOCS_URL = f'{c.PAGE_URL}/sections'
c.LOCAL_DOCS_PATH = os.path.join(c.PLUGIN_DIRPATH, 'docs', 'sections', 'index.html')
c.REPOSITORY_USERNAME = 'kamilburda'
c.REPOSITORY_NAME = 'batcher'
c.REPOSITORY_URL = 'https://github.com/kamilburda/batcher'
c.BUG_REPORT_URL_LIST = [
  ('GitHub', 'https://github.com/kamilburda/batcher/issues')
]
