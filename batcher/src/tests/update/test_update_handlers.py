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

_LATEST_PLUGIN_VERSION = '1.1'


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):
  
  def setUp(self):
    self.orig_plugin_version = pg.config.PLUGIN_VERSION
    pg.config.PLUGIN_VERSION = _LATEST_PLUGIN_VERSION

  def tearDown(self):
    pg.config.PLUGIN_VERSION = self.orig_plugin_version

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
    settings = plugin_settings.create_settings_for_export_layers()
    source_name = 'plug-in-batch-export-layers'

    source = pg.setting.sources.JsonFileSource(
      source_name, os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_0-2.json'))

    orig_setting_values_for_0_2 = self._get_orig_setting_values_for_0_2(settings)

    status, message = update.load_and_update(
      settings,
      sources={'persistent': source},
      update_sources=False,
    )

    self.assertEqual(status, update.UPDATE, msg=message)

    self._assert_correct_contents_for_update_to_0_3(settings, orig_setting_values_for_0_2)
    self._assert_correct_contents_for_update_to_0_4(settings)
    self._assert_correct_contents_for_update_to_0_5(settings)
    self._assert_correct_contents_for_update_to_0_6(settings)
    self._assert_correct_contents_for_update_to_0_8(settings)
    self._assert_correct_contents_for_update_to_1_0_rc1(settings)
    self._assert_correct_contents_for_update_to_1_0_rc2(settings)

  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
  def test_update_batch_convert(self, *_mocks):
    settings = plugin_settings.create_settings_for_convert()
    source_name = 'plug-in-batch-convert'

    source = pg.setting.sources.JsonFileSource(
      source_name, os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_1-0.json'))

    status, message = update.load_and_update(
      settings,
      sources={'persistent': source},
      update_sources=False,
    )

    self.assertEqual(status, update.UPDATE, msg=message)

    self._assert_correct_contents_for_update_to_1_1(settings)

  @staticmethod
  def _get_orig_setting_values_for_0_2(settings):
    return {
      'gui/size/dialog_size': settings['gui/size/dialog_size'].value,
      'gui/size/paned_outside_previews_position': (
        settings['gui/size/paned_outside_previews_position'].value),
      'gui/size/paned_between_previews_position': (
        settings['gui/size/paned_between_previews_position'].value),
    }

  def _assert_correct_contents_for_update_to_0_3(self, settings, orig_setting_values_for_0_2):
    for action in settings['main/procedures']:
      self.assertIn('more_options', action)
      self.assertIn('enabled_for_previews', action['more_options'])
      self.assertNotIn('enabled_for_previews', action)

    for action in settings['main/constraints']:
      self.assertIn('more_options', action)
      self.assertIn('enabled_for_previews', action['more_options'])
      self.assertNotIn('enabled_for_previews', action)
      self.assertIn('also_apply_to_parent_folders', action['more_options'])
      self.assertNotIn('also_apply_to_parent_folders', action)

    for setting_path, orig_value in orig_setting_values_for_0_2.items():
      self.assertEqual(settings[setting_path].value, orig_value)

  def _assert_correct_contents_for_update_to_0_4(self, settings):
    self.assertNotIn('edit_mode', settings['main'])

    self.assertIn('name_pattern', settings['main'])
    self.assertNotIn('layer_filename_pattern', settings['main'])

    self.assertIsInstance(
      settings['main/name_pattern'], setting_classes.NamePatternSetting)

    self.assertIn('insert_background', settings['main/procedures'])
    self.assertIn('color_tag', settings['main/procedures/insert_background/arguments'])
    self.assertEqual(
      settings['main/procedures/insert_background/arguments/merge_procedure_name'].value,
      'merge_background')
    self.assertEqual(
      settings['main/procedures/insert_background/arguments/constraint_name'].value,
      'not_background')
    self.assertIn('merge_background', settings['main/procedures'])
    self.assertEqual(
      settings['main/procedures/merge_background/display_name'].value,
      'Merge background')
    self.assertIn('merge_type', settings['main/procedures/merge_background/arguments'])
    self.assertTrue(
      settings['main/procedures/merge_background/arguments/last_enabled_value'].value)
    self.assertIn('not_background', settings['main/constraints'])
    self.assertEqual(
      settings['main/constraints/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', settings['main/constraints/not_background/arguments'])
    self.assertTrue(
      settings['main/constraints/not_background/arguments/last_enabled_value'].value)

    self.assertIn('insert_background_2', settings['main/procedures'])
    self.assertIn('color_tag', settings['main/procedures/insert_background_2/arguments'])
    self.assertEqual(
      settings['main/procedures/insert_background_2/arguments/merge_procedure_name'].value,
      'merge_background_2')
    self.assertEqual(
      settings['main/procedures/insert_background_2/arguments/constraint_name'].value,
      'not_background_2')
    self.assertIn('merge_background_2', settings['main/procedures'])
    self.assertEqual(
      settings['main/procedures/merge_background_2/display_name'].value,
      'Merge background (2)')
    self.assertIn('merge_type', settings['main/procedures/merge_background_2/arguments'])
    self.assertTrue(
      settings['main/procedures/merge_background_2/arguments/last_enabled_value'].value)
    self.assertIn('not_background_2', settings['main/constraints'])
    self.assertEqual(
      settings['main/constraints/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', settings['main/constraints/not_background_2/arguments'])
    self.assertTrue(
      settings['main/constraints/not_background_2/arguments/last_enabled_value'].value)

    self.assertIn('export', settings['main/procedures'])
    self.assertNotIn(
      'single_image_filename_pattern', settings['main/procedures/export/arguments'])
    self.assertIn('single_image_name_pattern', settings['main/procedures/export/arguments'])
    self.assertIsInstance(
      settings['main/procedures/export/arguments/single_image_name_pattern'],
      setting_classes.NamePatternSetting,
    )
    self.assertEqual(
      settings['main/procedures/export/arguments/single_image_name_pattern'].gui_type,
      setting_classes.NamePatternEntryPresenter,
    )

    self.assertIsInstance(
      settings['main/procedures/rename/arguments/pattern'],
      setting_classes.NamePatternSetting,
    )
    self.assertEqual(
      settings['main/procedures/rename/arguments/pattern'].gui_type,
      setting_classes.NamePatternEntryPresenter,
    )

  def _assert_correct_contents_for_update_to_0_5(self, settings):
    self.assertEqual(
      settings['main/file_extension'].gui_type,
      pg.setting.NullPresenter,
    )

    self.assertIn('export', settings['main/procedures'])
    self.assertEqual(
      settings['main/procedures/export/orig_name'].value, 'export_for_export_layers')

    self.assertNotIn(
      'preserve_layer_name_after_export', settings['main/procedures/export/arguments'])
    self.assertIn('overwrite_mode', settings['main/procedures/export/arguments'])
    # This checks whether `overwrite_mode` is the third argument.
    self.assertEqual(
      list(settings['main/procedures/export/arguments']),
      [
        settings['main/procedures/export/arguments/output_directory'],
        settings['main/procedures/export/arguments/file_extension'],
        settings['main/procedures/export/arguments/file_format_mode'],
        settings['main/procedures/export/arguments/file_format_export_options'],
        settings['main/procedures/export/arguments/overwrite_mode'],
        settings['main/procedures/export/arguments/export_mode'],
        settings['main/procedures/export/arguments/single_image_name_pattern'],
        settings['main/procedures/export/arguments/use_file_extension_in_item_name'],
        settings['main/procedures/export/arguments/convert_file_extension_to_lowercase'],
      ])

    self.assertIsInstance(
      settings['main/procedures/insert_background/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      settings['main/procedures/insert_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/procedures/insert_background/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertEqual(
      settings['main/procedures/merge_background/arguments/merge_type'].excluded_values,
      [Gimp.MergeType.FLATTEN_IMAGE])

    self.assertIsInstance(
      settings['main/procedures/insert_background_2/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      settings['main/procedures/insert_background_2/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/procedures/insert_background_2/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertIsInstance(
      settings['main/constraints/not_background/arguments/color_tag'],
      pg.setting.EnumSetting)
    self.assertEqual(
      settings['main/constraints/not_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/constraints/not_background/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

  def _assert_correct_contents_for_update_to_0_6(self, settings):
    self.assertEqual(settings['main/overwrite_mode'].value, 'rename_new')

    self.assertEqual(settings['main/tagged_items'].value, [])

    self.assertIn('name_preview_items_collapsed_state', settings['gui'])
    self.assertNotIn('name_preview_layers_collapsed_state', settings['gui'])

    self.assertIn('image_preview_displayed_items', settings['gui'])
    self.assertNotIn('image_preview_displayed_layers', settings['gui'])

    self.assertIn('images_and_directories', settings['gui'])

    self.assertIsInstance(
      settings['gui/size/paned_between_previews_position'], pg.setting.IntSetting)

    self.assertEqual(
      settings['main/procedures/export/arguments/file_format_mode'].value,
      'use_explicit_values')
    self.assertEqual(
      settings['main/procedures/export/arguments/overwrite_mode'].value,
      'ask')

    for procedure in settings['main/procedures']:
      if procedure['orig_name'].value in builtin_procedures.BUILTIN_PROCEDURES:
        self.assertEqual(procedure['origin'].value, 'builtin')
      else:
        self.assertEqual(procedure['origin'].value, 'gimp_pdb')

    self.assertEqual(
      settings['main/procedures/insert_background/arguments/tagged_items'].value, [])

    self.assertEqual(
      settings['main/procedures/insert_background_2/arguments/tagged_items'].value, [])

    self.assertNotIn(
      'drawable',
      settings['main/procedures/script-fu-addborder/arguments'])
    self.assertIsInstance(
      settings['main/procedures/script-fu-addborder/arguments/drawables'],
      placeholders.PlaceholderDrawableArraySetting)

    self.assertIsInstance(
      settings['main/procedures/script-fu-addborder/arguments/color'],
      pg.setting.ColorSetting)
    self.assertEqual(
      settings['main/procedures/script-fu-addborder/arguments/color'].gui_type,
      pg.setting.ColorButtonPresenter)
    self.assertEqual(
      settings['main/procedures/script-fu-addborder/arguments/color'].pdb_type.name,
      'GeglColor')

    for procedure in settings['main/constraints']:
      if procedure['orig_name'].value in builtin_constraints.BUILTIN_CONSTRAINTS:
        self.assertEqual(procedure['origin'].value, 'builtin')
      else:
        self.assertEqual(procedure['origin'].value, 'gimp_pdb')

  def _assert_correct_contents_for_update_to_0_8(self, settings):
    self.assertEqual(settings['main/export/export_mode'].value, 'each_item')
    self.assertEqual(settings['main/export/export_mode'].default_value, 'each_item')

    self.assertNotIn('remove_folder_structure_for_export_layers', settings['main/procedures'])
    self.assertIn('remove_folder_structure', settings['main/procedures'])

    self.assertEqual(
      settings['main/procedures/export/arguments/export_mode'].value,
      'each_item')
    self.assertEqual(
      settings['main/procedures/export/arguments/export_mode'].default_value,
      'each_item')

  def _assert_correct_contents_for_update_to_1_0_rc1(self, settings):
    self.assertNotIn('selected_items', settings['main'])
    self.assertNotIn('selected_layers', settings['main'])
    self.assertIn('selected_items', settings['gui'])

    self.assertIn('layers', settings['main/procedures/use_layer_size/arguments'])

  def _assert_correct_contents_for_update_to_1_0_rc2(self, settings):
    self.assertEqual(
      settings['main/output_directory'].gui_type, pg.setting.FileChooserPresenter)
    self.assertIsInstance(settings['main/output_directory'].value, Gio.File)
    self.assertEqual(
      settings['main/output_directory'].action, Gimp.FileChooserAction.SELECT_FOLDER)

  def _assert_correct_contents_for_update_to_1_1(self, settings):
    scale_arguments_path = 'main/procedures/scale_for_images/arguments'

    self.assertListEqual(
      [setting.name for setting in settings[scale_arguments_path]],
      [
        'object_to_scale',
        'new_width',
        'new_height',
        'aspect_ratio',
        'padding_color',
        'interpolation',
        'local_origin',
        'set_image_resolution',
        'image_resolution',
      ],
    )

    self.assertIsInstance(
      settings[f'{scale_arguments_path}/object_to_scale'],
      placeholders.PlaceholderImageOrLayerSetting,
    )
    self.assertEqual(
      settings[f'{scale_arguments_path}/object_to_scale'].value,
      'current_image',
    )

    self.assertIsInstance(
      settings[f'{scale_arguments_path}/new_width'],
      setting_classes.DimensionSetting,
    )
    self.assertEqual(
      settings[f'{scale_arguments_path}/new_width'].value,
      {
        'pixel_value': 50.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
    )
    self.assertEqual(settings[f'{scale_arguments_path}/new_width'].min_value, 0.0)

    self.assertIsInstance(
      settings[f'{scale_arguments_path}/new_height'],
      setting_classes.DimensionSetting,
    )
    self.assertEqual(
      settings[f'{scale_arguments_path}/new_height'].value,
      {
        'pixel_value': 100.0,
        'percent_value': 120.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
    )
    self.assertEqual(settings[f'{scale_arguments_path}/new_height'].min_value, 0.0)
    self.assertEqual(settings[f'{scale_arguments_path}/aspect_ratio'].value, 'stretch')
    self.assertEqual(settings[f'{scale_arguments_path}/set_image_resolution'].value, False)

    self.assertIsInstance(
      settings[f'{scale_arguments_path}/image_resolution'],
      setting_classes.CoordinatesSetting,
    )
    self.assertEqual(
      settings[f'{scale_arguments_path}/image_resolution'].value,
      {
        'x': 72.0,
        'y': 72.0,
      },
    )

    align_arguments_path = 'main/procedures/align_and_offset_layers/arguments'

    self.assertListEqual(
      [setting.name for setting in settings[align_arguments_path]],
      [
        'layers_to_align',
        'reference_object',
        'horizontal_align',
        'vertical_align',
        'x_offset',
        'y_offset',
      ],
    )

    self.assertIsInstance(
      settings[f'{align_arguments_path}/reference_object'],
      placeholders.PlaceholderImageOrLayerSetting,
    )

    self.assertIsInstance(
      settings[f'{align_arguments_path}/x_offset'],
      setting_classes.DimensionSetting,
    )
    self.assertEqual(
      settings[f'{align_arguments_path}/x_offset'].value,
      {
        'pixel_value': 0.0,
        'percent_value': 10.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
    )

    self.assertIsInstance(
      settings[f'{align_arguments_path}/y_offset'],
      setting_classes.DimensionSetting,
    )
    self.assertEqual(
      settings[f'{align_arguments_path}/y_offset'].value,
      {
        'pixel_value': 20.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
    )
