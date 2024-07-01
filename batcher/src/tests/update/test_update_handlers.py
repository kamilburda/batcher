import os

import unittest
import unittest.mock as mock

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import plugin_settings
from src import update


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(pg.utils.get_current_module_filepath()))


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):
  
  def setUp(self):
    self.settings = plugin_settings.create_settings_for_export_layers()
    self.plugin_version = pg.config.PLUGIN_VERSION

  def tearDown(self):
    pg.config.PLUGIN_VERSION = self.plugin_version

  def test_update_to_0_3(self, *mocks):
    source = pg.setting.sources.JsonFileSource(
      'plug-in-batch-export-layers', os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_0-2.json'))

    pg.config.PLUGIN_VERSION = '0.3'

    orig_dialog_size_value = self.settings['gui/size/dialog_size'].value
    orig_paned_outside_value = self.settings['gui/size/paned_outside_previews_position'].value
    orig_paned_between_value = self.settings['gui/size/paned_between_previews_position'].value

    status, _message = update.load_and_update(
      self.settings,
      sources={'persistent': source},
      update_sources=False,
    )

    for action in self.settings['main/procedures']:
      self.assertIn('more_options', action)
      self.assertIn('enabled_for_previews', action['more_options'])
      self.assertNotIn('enabled_for_previews', action)

    for action in self.settings['main/constraints']:
      self.assertIn('more_options', action)
      self.assertIn('enabled_for_previews', action['more_options'])
      self.assertNotIn('enabled_for_previews', action)
      self.assertIn('also_apply_to_parent_folders', action['more_options'])
      self.assertNotIn('also_apply_to_parent_folders', action)

    self.assertEqual(self.settings['gui/size/dialog_size'].value, orig_dialog_size_value)
    self.assertEqual(
      self.settings['gui/size/paned_outside_previews_position'].value, orig_paned_outside_value)
    self.assertEqual(
      self.settings['gui/size/paned_between_previews_position'].value, orig_paned_between_value)

    self.assertEqual(status, update.UPDATE)
