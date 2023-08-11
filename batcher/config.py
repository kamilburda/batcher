"""Plug-in configuration.

Use `c` to access, create or modify configuration entries.
"""

import os


c.PLUGIN_NAME = 'batcher'
c.LOCALE_DIRPATH = os.path.join(c.PLUGIN_DIRPATH, 'locale')

c.PLUGINS_LOG_DIRPATHS.insert(0, c.PLUGIN_DIRPATH)

c.LOG_MODE = 'exceptions'

c.PLUGIN_TITLE = lambda: _('Batcher')
c.PLUGIN_VERSION = '0.0.0'
c.PLUGIN_VERSION_RELEASE_DATE = 'August 06, 2023'
c.AUTHOR_NAME = 'Kamil Burda'
c.COPYRIGHT_YEARS = '2023'
c.PAGE_URL = 'https://kamilburda.github.io/batcher'
c.DOCS_URL = c.PAGE_URL + '/sections'
c.LOCAL_DOCS_PATH = os.path.join(c.PLUGIN_DIRPATH, 'docs', 'sections', 'index.html')
c.REPOSITORY_USERNAME = 'kamilburda'
c.REPOSITORY_NAME = 'batcher'
c.REPOSITORY_URL = 'https://github.com/kamilburda/batcher'
c.BUG_REPORT_URL_LIST = [
  ('GitHub', 'https://github.com/kamilburda/batcher/issues')
]

# If True, display each step of image/layer editing in GIMP.
c.DEBUG_IMAGE_PROCESSING = False
