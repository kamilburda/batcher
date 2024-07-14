import os

import unittest
import unittest.mock as mock

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import plugin_settings
from src import setting_classes
from src import update


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(pg.utils.get_current_module_filepath()))

_LATEST_PLUGIN_VERSION = '0.5'


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):
  
  def setUp(self):
    self.settings = plugin_settings.create_settings_for_export_layers()
    self.plugin_version = pg.config.PLUGIN_VERSION

  def tearDown(self):
    pg.config.PLUGIN_VERSION = self.plugin_version

  def test_update_export_layers(self, *_mocks):
    source = pg.setting.sources.JsonFileSource(
      'plug-in-batch-export-layers', os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_0-2.json'))

    pg.config.PLUGIN_VERSION = _LATEST_PLUGIN_VERSION

    orig_setting_values_for_0_2 = self._get_orig_setting_values_for_0_2()

    status, _message = update.load_and_update(
      self.settings,
      sources={'persistent': source},
      update_sources=False,
    )

    self.assertEqual(status, update.UPDATE)

    self._assert_correct_contents_for_update_to_0_3(orig_setting_values_for_0_2)
    self._assert_correct_contents_for_update_to_0_4()
    self._assert_correct_contents_for_update_to_0_5()

  def _get_orig_setting_values_for_0_2(self):
    return {
      'gui/size/dialog_size': self.settings['gui/size/dialog_size'].value,
      'gui/size/paned_outside_previews_position': (
        self.settings['gui/size/paned_outside_previews_position'].value),
      'gui/size/paned_between_previews_position': (
        self.settings['gui/size/paned_between_previews_position'].value),
    }

  def _assert_correct_contents_for_update_to_0_3(self, orig_setting_values_for_0_2):
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

    for setting_path, orig_value in orig_setting_values_for_0_2.items():
      self.assertEqual(self.settings[setting_path].value, orig_value)

  def _assert_correct_contents_for_update_to_0_4(self):
    self.assertNotIn('edit_mode', self.settings['main'])

    self.assertIn('name_pattern', self.settings['main'])
    self.assertNotIn('layer_filename_pattern', self.settings['main'])

    self.assertIsInstance(
      self.settings['main/name_pattern'], setting_classes.NamePatternSetting)

    self.assertIn('insert_background', self.settings['main/procedures'])
    self.assertIn('color_tag', self.settings['main/procedures/insert_background/arguments'])
    self.assertEqual(
      self.settings['main/procedures/insert_background/arguments/merge_procedure_name'].value,
      'merge_background')
    self.assertEqual(
      self.settings['main/procedures/insert_background/arguments/constraint_name'].value,
      'not_background')
    self.assertIn('merge_background', self.settings['main/procedures'])
    self.assertEqual(
      self.settings['main/procedures/merge_background/display_name'].value,
      'Merge background')
    self.assertIn('merge_type', self.settings['main/procedures/merge_background/arguments'])
    self.assertTrue(
      self.settings['main/procedures/merge_background/arguments/last_enabled_value'].value)
    self.assertIn('not_background', self.settings['main/constraints'])
    self.assertEqual(
      self.settings['main/constraints/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', self.settings['main/constraints/not_background/arguments'])
    self.assertTrue(
      self.settings['main/constraints/not_background/arguments/last_enabled_value'].value)

    self.assertIn('insert_background_2', self.settings['main/procedures'])
    self.assertIn('color_tag', self.settings['main/procedures/insert_background_2/arguments'])
    self.assertEqual(
      self.settings['main/procedures/insert_background_2/arguments/merge_procedure_name'].value,
      'merge_background_2')
    self.assertEqual(
      self.settings['main/procedures/insert_background_2/arguments/constraint_name'].value,
      'not_background_2')
    self.assertIn('merge_background_2', self.settings['main/procedures'])
    self.assertEqual(
      self.settings['main/procedures/merge_background_2/display_name'].value,
      'Merge background (2)')
    self.assertIn('merge_type', self.settings['main/procedures/merge_background_2/arguments'])
    self.assertTrue(
      self.settings['main/procedures/merge_background_2/arguments/last_enabled_value'].value)
    self.assertIn('not_background_2', self.settings['main/constraints'])
    self.assertEqual(
      self.settings['main/constraints/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', self.settings['main/constraints/not_background_2/arguments'])
    self.assertTrue(
      self.settings['main/constraints/not_background_2/arguments/last_enabled_value'].value)

    self.assertIn('export', self.settings['main/procedures'])
    self.assertNotIn(
      'single_image_filename_pattern', self.settings['main/procedures/export/arguments'])
    self.assertIn('single_image_name_pattern', self.settings['main/procedures/export/arguments'])
    self.assertIsInstance(
      self.settings['main/procedures/export/arguments/single_image_name_pattern'],
      setting_classes.NamePatternSetting,
    )
    self.assertEqual(
      self.settings['main/procedures/export/arguments/single_image_name_pattern'].gui_type,
      setting_classes.NamePatternEntryPresenter,
    )

    self.assertNotIn('rename', self.settings['main/procedures'])
    self.assertIn('rename_for_export_layers', self.settings['main/procedures'])
    self.assertIsInstance(
      self.settings['main/procedures/rename_for_export_layers/arguments/pattern'],
      setting_classes.NamePatternSetting,
    )
    self.assertEqual(
      self.settings['main/procedures/rename_for_export_layers/arguments/pattern'].gui_type,
      setting_classes.NamePatternEntryPresenter,
    )

    self.assertNotIn('remove_folder_structure', self.settings['main/procedures'])
    self.assertIn('remove_folder_structure_for_export_layers', self.settings['main/procedures'])

  def _assert_correct_contents_for_update_to_0_5(self):
    self.assertNotIn(
      'preserve_layer_name_after_export', self.settings['main/procedures/export/arguments'])
