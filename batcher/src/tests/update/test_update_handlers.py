import os

import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import builtin_procedures
from src import builtin_constraints
from src import placeholders
from src import plugin_settings
from src import setting_classes
from src import update


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(pg.utils.get_current_module_filepath()))

_SETTINGS_MODULE_PATH = f'{pg.utils.get_pygimplib_module_path()}.setting.settings'

_MOCK_PNG_CHOICE = Gimp.Choice.new()
_MOCK_PNG_CHOICE.add('auto', 0, 'Automatic', '')
_MOCK_PNG_CHOICE_DEFAULT_VALUE = 'auto'

_LATEST_PLUGIN_VERSION = '1.0'


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):
  
  def setUp(self):
    self.settings = plugin_settings.create_settings_for_export_layers()
    self.plugin_version = pg.config.PLUGIN_VERSION

  def tearDown(self):
    pg.config.PLUGIN_VERSION = self.plugin_version

  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
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
    self._assert_correct_contents_for_update_to_0_6()
    self._assert_correct_contents_for_update_to_0_7()
    self._assert_correct_contents_for_update_to_0_8()
    self._assert_correct_contents_for_update_to_1_0_rc1()
    self._assert_correct_contents_for_update_to_1_0_rc2()

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

    self.assertIsInstance(
      self.settings['main/procedures/rename/arguments/pattern'],
      setting_classes.NamePatternSetting,
    )
    self.assertEqual(
      self.settings['main/procedures/rename/arguments/pattern'].gui_type,
      setting_classes.NamePatternEntryPresenter,
    )

  def _assert_correct_contents_for_update_to_0_5(self):
    self.assertEqual(
      self.settings['main/file_extension'].gui_type,
      pg.setting.NullPresenter,
    )

    self.assertIn('export', self.settings['main/procedures'])
    self.assertEqual(
      self.settings['main/procedures/export/orig_name'].value, 'export_for_export_layers')

    self.assertNotIn(
      'preserve_layer_name_after_export', self.settings['main/procedures/export/arguments'])
    self.assertIn('overwrite_mode', self.settings['main/procedures/export/arguments'])
    # This checks whether `overwrite_mode` is the third argument.
    self.assertEqual(
      list(self.settings['main/procedures/export/arguments']),
      [
        self.settings['main/procedures/export/arguments/output_directory'],
        self.settings['main/procedures/export/arguments/file_extension'],
        self.settings['main/procedures/export/arguments/file_format_mode'],
        self.settings['main/procedures/export/arguments/file_format_export_options'],
        self.settings['main/procedures/export/arguments/overwrite_mode'],
        self.settings['main/procedures/export/arguments/export_mode'],
        self.settings['main/procedures/export/arguments/single_image_name_pattern'],
        self.settings['main/procedures/export/arguments/use_file_extension_in_item_name'],
        self.settings['main/procedures/export/arguments/convert_file_extension_to_lowercase'],
      ])

    self.assertIsInstance(
      self.settings['main/procedures/insert_background/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      self.settings['main/procedures/insert_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      self.settings['main/procedures/insert_background/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertEqual(
      self.settings['main/procedures/merge_background/arguments/merge_type'].excluded_values,
      [Gimp.MergeType.FLATTEN_IMAGE])

    self.assertIsInstance(
      self.settings['main/procedures/insert_background_2/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      self.settings['main/procedures/insert_background_2/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      self.settings['main/procedures/insert_background_2/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertIsInstance(
      self.settings['main/constraints/not_background/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      self.settings['main/constraints/not_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      self.settings['main/constraints/not_background/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

  def _assert_correct_contents_for_update_to_0_6(self):
    self.assertEqual(self.settings['main/overwrite_mode'].value, 'rename_new')

    self.assertEqual(self.settings['main/tagged_items'].value, [])

    self.assertIn('name_preview_items_collapsed_state', self.settings['gui'])
    self.assertNotIn('name_preview_layers_collapsed_state', self.settings['gui'])

    self.assertIn('image_preview_displayed_items', self.settings['gui'])
    self.assertNotIn('image_preview_displayed_layers', self.settings['gui'])

    self.assertIn('images_and_directories', self.settings['gui'])

    self.assertIsInstance(
      self.settings['gui/size/paned_between_previews_position'], pg.setting.IntSetting)

    self.assertEqual(
      self.settings['main/procedures/export/arguments/file_format_mode'].value,
      'use_explicit_values')
    self.assertEqual(
      self.settings['main/procedures/export/arguments/overwrite_mode'].value,
      'ask')

    for procedure in self.settings['main/procedures']:
      if procedure['orig_name'].value in builtin_procedures.BUILTIN_PROCEDURES:
        self.assertEqual(procedure['origin'].value, 'builtin')
      else:
        self.assertEqual(procedure['origin'].value, 'gimp_pdb')

    self.assertEqual(
      self.settings['main/procedures/insert_background/arguments/tagged_items'].value, [])

    self.assertEqual(
      self.settings['main/procedures/insert_background_2/arguments/tagged_items'].value, [])

    self.assertIsInstance(
      self.settings['main/procedures/scale/arguments/new_width'],
      pg.setting.DoubleSetting)
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/new_width'].gui_type,
      pg.setting.DoubleSpinButtonPresenter)

    self.assertIsInstance(
      self.settings['main/procedures/scale/arguments/new_height'],
      pg.setting.DoubleSetting)
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/new_height'].gui_type,
      pg.setting.DoubleSpinButtonPresenter)

    self.assertEqual(
      self.settings['main/procedures/scale/arguments/width_unit'].value,
      'percentage_of_layer_width')

    self.assertEqual(
      self.settings['main/procedures/scale/arguments/height_unit'].value,
      'percentage_of_layer_height')

    self.assertNotIn(
      'drawable',
      self.settings['main/procedures/script-fu-addborder/arguments'])
    self.assertIsInstance(
      self.settings['main/procedures/script-fu-addborder/arguments/drawables'],
      placeholders.PlaceholderDrawableArraySetting)

    self.assertIsInstance(
      self.settings['main/procedures/script-fu-addborder/arguments/color'],
      pg.setting.ColorSetting)
    self.assertEqual(
      self.settings['main/procedures/script-fu-addborder/arguments/color'].gui_type,
      pg.setting.ColorButtonPresenter)
    self.assertEqual(
      self.settings['main/procedures/script-fu-addborder/arguments/color'].pdb_type.name,
      'GeglColor')

    for procedure in self.settings['main/constraints']:
      if procedure['orig_name'].value in builtin_constraints.BUILTIN_CONSTRAINTS:
        self.assertEqual(procedure['origin'].value, 'builtin')
      else:
        self.assertEqual(procedure['origin'].value, 'gimp_pdb')

  def _assert_correct_contents_for_update_to_0_7(self):
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/scale_to_fit'].value,
      False)
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/keep_aspect_ratio'].value,
      False)
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/dimension_to_keep'].value,
      'width')

  def _assert_correct_contents_for_update_to_0_8(self):
    self.assertEqual(self.settings['main/export/export_mode'].value, 'each_item')
    self.assertEqual(self.settings['main/export/export_mode'].default_value, 'each_item')

    self.assertNotIn('remove_folder_structure_for_export_layers', self.settings['main/procedures'])
    self.assertIn('remove_folder_structure', self.settings['main/procedures'])

    self.assertEqual(
      self.settings['main/procedures/export/arguments/export_mode'].value,
      'each_item')
    self.assertEqual(
      self.settings['main/procedures/export/arguments/export_mode'].default_value,
      'each_item')

  def _assert_correct_contents_for_update_to_1_0_rc1(self):
    self.assertNotIn('selected_items', self.settings['main'])
    self.assertNotIn('selected_layers', self.settings['main'])
    self.assertIn('selected_items', self.settings['gui'])

    self.assertEqual(
      list(self.settings['main/procedures/scale/arguments'])[2].name,
      'object_to_scale',
    )
    self.assertEqual(
      self.settings['main/procedures/scale/arguments/object_to_scale'].value,
      builtin_procedures.ScaleObjects.LAYER,
    )

    self.assertIn('layers', self.settings['main/procedures/use_layer_size/arguments'])

  def _assert_correct_contents_for_update_to_1_0_rc2(self):
    self.assertEqual(
      self.settings['main/output_directory'].gui_type, pg.setting.FileChooserPresenter)
    self.assertIsInstance(self.settings['main/output_directory'].value, Gio.File)
    self.assertEqual(
      self.settings['main/output_directory'].action, Gimp.FileChooserAction.SELECT_FOLDER)
