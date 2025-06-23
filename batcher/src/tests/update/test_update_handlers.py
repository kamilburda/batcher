import os

import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from config import CONFIG
from src import builtin_actions
from src import builtin_conditions
from src import placeholders
from src import plugin_settings
from src import setting as setting_
from src import setting_additional
from src import update
from src import utils

from src.tests import stubs_gimp


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))

_SETTINGS_MODULE_PATH = 'src.setting.settings'

_MOCK_PNG_CHOICE = Gimp.Choice.new()
_MOCK_PNG_CHOICE.add('auto', 0, 'Automatic', '')
_MOCK_PNG_CHOICE_DEFAULT_VALUE = 'auto'

_LATEST_PLUGIN_VERSION = '1.2'


@mock.patch('src.setting.sources.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):
  
  def setUp(self):
    self.orig_plugin_version = CONFIG.PLUGIN_VERSION
    CONFIG.PLUGIN_VERSION = _LATEST_PLUGIN_VERSION

  def tearDown(self):
    CONFIG.PLUGIN_VERSION = self.orig_plugin_version

  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
  def test_update_export_layers(self, *_mocks):
    settings = plugin_settings.create_settings_for_export_layers()
    source_name = 'plug-in-batch-export-layers'

    source = setting_.sources.JsonFileSource(
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
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
  def test_update_batch_convert(self, *_mocks):
    settings = plugin_settings.create_settings_for_convert()
    source_name = 'plug-in-batch-convert'

    source = setting_.sources.JsonFileSource(
      source_name, os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_1-0.json'))

    status, message = update.load_and_update(
      settings,
      sources={'persistent': source},
      update_sources=False,
      procedure_group=source_name,
    )

    self.assertEqual(status, update.UPDATE, msg=message)

    self._assert_correct_contents_for_update_to_1_1(settings)
    self._assert_correct_contents_for_update_to_1_2(settings)

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
    for command in settings['main/actions']:
      self.assertIn('more_options', command)
      self.assertIn('enabled_for_previews', command['more_options'])
      self.assertNotIn('enabled_for_previews', command)

    for command in settings['main/conditions']:
      self.assertIn('more_options', command)
      self.assertIn('enabled_for_previews', command['more_options'])
      self.assertNotIn('enabled_for_previews', command)
      self.assertIn('also_apply_to_parent_folders', command['more_options'])
      self.assertNotIn('also_apply_to_parent_folders', command)

    for setting_path, orig_value in orig_setting_values_for_0_2.items():
      self.assertEqual(settings[setting_path].value, orig_value)

  def _assert_correct_contents_for_update_to_0_4(self, settings):
    self.assertNotIn('edit_mode', settings['main'])

    self.assertIn('name_pattern', settings['main'])
    self.assertNotIn('layer_filename_pattern', settings['main'])

    self.assertIsInstance(
      settings['main/name_pattern'], setting_additional.NamePatternSetting)

    self.assertIn('insert_background', settings['main/actions'])
    self.assertIn('color_tag', settings['main/actions/insert_background/arguments'])
    self.assertEqual(
      settings['main/actions/insert_background/arguments/merge_action_name'].value,
      'merge_background')
    self.assertEqual(
      settings['main/actions/insert_background/arguments/condition_name'].value,
      'not_background')
    self.assertIn('merge_background', settings['main/actions'])
    self.assertEqual(
      settings['main/actions/merge_background/display_name'].value,
      'Merge background')
    self.assertIn('merge_type', settings['main/actions/merge_background/arguments'])
    self.assertTrue(
      settings['main/actions/merge_background/arguments/last_enabled_value'].value)
    self.assertIn('not_background', settings['main/conditions'])
    self.assertEqual(
      settings['main/conditions/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', settings['main/conditions/not_background/arguments'])
    self.assertTrue(
      settings['main/conditions/not_background/arguments/last_enabled_value'].value)

    self.assertIn('insert_background_2', settings['main/actions'])
    self.assertIn('color_tag', settings['main/actions/insert_background_2/arguments'])
    self.assertEqual(
      settings['main/actions/insert_background_2/arguments/merge_action_name'].value,
      'merge_background_2')
    self.assertEqual(
      settings['main/actions/insert_background_2/arguments/condition_name'].value,
      'not_background_2')
    self.assertIn('merge_background_2', settings['main/actions'])
    self.assertEqual(
      settings['main/actions/merge_background_2/display_name'].value,
      'Merge background (2)')
    self.assertIn('merge_type', settings['main/actions/merge_background_2/arguments'])
    self.assertTrue(
      settings['main/actions/merge_background_2/arguments/last_enabled_value'].value)
    self.assertIn('not_background_2', settings['main/conditions'])
    self.assertEqual(
      settings['main/conditions/not_background/display_name'].value,
      'Not background')
    self.assertIn('color_tag', settings['main/conditions/not_background_2/arguments'])
    self.assertTrue(
      settings['main/conditions/not_background_2/arguments/last_enabled_value'].value)

    self.assertIn('export', settings['main/actions'])
    self.assertNotIn(
      'single_image_filename_pattern', settings['main/actions/export/arguments'])
    self.assertIn('single_image_name_pattern', settings['main/actions/export/arguments'])
    self.assertIsInstance(
      settings['main/actions/export/arguments/single_image_name_pattern'],
      setting_additional.NamePatternSetting,
    )
    self.assertEqual(
      settings['main/actions/export/arguments/single_image_name_pattern'].gui_type,
      setting_additional.NamePatternEntryPresenter,
    )

    self.assertIsInstance(
      settings['main/actions/rename/arguments/pattern'],
      setting_additional.NamePatternSetting,
    )
    self.assertEqual(
      settings['main/actions/rename/arguments/pattern'].gui_type,
      setting_additional.NamePatternEntryPresenter,
    )

  def _assert_correct_contents_for_update_to_0_5(self, settings):
    self.assertEqual(
      settings['main/file_extension'].gui_type,
      setting_.NullPresenter,
    )

    self.assertIn('export', settings['main/actions'])
    self.assertEqual(
      settings['main/actions/export/orig_name'].value, 'export_for_export_layers')

    self.assertNotIn(
      'preserve_layer_name_after_export', settings['main/actions/export/arguments'])
    self.assertIn('overwrite_mode', settings['main/actions/export/arguments'])
    # This checks whether `overwrite_mode` is the third argument.
    self.assertEqual(
      list(settings['main/actions/export/arguments']),
      [
        settings['main/actions/export/arguments/output_directory'],
        settings['main/actions/export/arguments/file_extension'],
        settings['main/actions/export/arguments/file_format_mode'],
        settings['main/actions/export/arguments/file_format_export_options'],
        settings['main/actions/export/arguments/overwrite_mode'],
        settings['main/actions/export/arguments/export_mode'],
        settings['main/actions/export/arguments/single_image_name_pattern'],
        settings['main/actions/export/arguments/use_file_extension_in_item_name'],
        settings['main/actions/export/arguments/convert_file_extension_to_lowercase'],
      ])

    self.assertIsInstance(
      settings['main/actions/insert_background/arguments/color_tag'],
      setting_.EnumSetting)
    self.assertEqual(
      settings['main/actions/insert_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/actions/insert_background/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertEqual(
      settings['main/actions/merge_background/arguments/merge_type'].excluded_values,
      [Gimp.MergeType.FLATTEN_IMAGE])

    self.assertIsInstance(
      settings['main/actions/insert_background_2/arguments/color_tag'],
      setting_.EnumSetting)
    self.assertEqual(
      settings['main/actions/insert_background_2/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/actions/insert_background_2/arguments/color_tag'].excluded_values,
      [Gimp.ColorTag.NONE])

    self.assertIsInstance(
      settings['main/conditions/not_background/arguments/color_tag'],
      setting_.EnumSetting)
    self.assertEqual(
      settings['main/conditions/not_background/arguments/color_tag'].enum_type,
      Gimp.ColorTag)
    self.assertEqual(
      settings['main/conditions/not_background/arguments/color_tag'].excluded_values,
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
      settings['gui/size/paned_between_previews_position'], setting_.IntSetting)

    self.assertEqual(
      settings['main/actions/export/arguments/file_format_mode'].value,
      'use_explicit_values')
    self.assertEqual(
      settings['main/actions/export/arguments/overwrite_mode'].value,
      'ask')

    for action in settings['main/actions']:
      if action['orig_name'].value in builtin_actions.BUILTIN_ACTIONS:
        self.assertEqual(action['origin'].value, 'builtin')
      else:
        self.assertEqual(action['origin'].value, 'gimp_pdb')

    self.assertEqual(
      settings['main/actions/insert_background/arguments/tagged_items'].value, [])

    self.assertEqual(
      settings['main/actions/insert_background_2/arguments/tagged_items'].value, [])

    self.assertNotIn(
      'drawable',
      settings['main/actions/script-fu-addborder/arguments'])
    self.assertIsInstance(
      settings['main/actions/script-fu-addborder/arguments/drawables'],
      placeholders.PlaceholderDrawableArraySetting)

    self.assertIsInstance(
      settings['main/actions/script-fu-addborder/arguments/color'],
      setting_.ColorSetting)
    self.assertEqual(
      settings['main/actions/script-fu-addborder/arguments/color'].gui_type,
      setting_.ColorButtonPresenter)
    self.assertEqual(
      settings['main/actions/script-fu-addborder/arguments/color'].pdb_type.name,
      'GeglColor')

    for condition in settings['main/conditions']:
      if condition['orig_name'].value in builtin_conditions.BUILTIN_CONDITIONS:
        self.assertEqual(condition['origin'].value, 'builtin')
      else:
        self.assertEqual(condition['origin'].value, 'gimp_pdb')

  def _assert_correct_contents_for_update_to_0_8(self, settings):
    self.assertEqual(settings['main/export/export_mode'].value, 'each_item')
    self.assertEqual(settings['main/export/export_mode'].default_value, 'each_item')

    self.assertNotIn('remove_folder_structure_for_export_layers', settings['main/actions'])
    self.assertIn('remove_folder_structure', settings['main/actions'])

    self.assertEqual(
      settings['main/actions/export/arguments/export_mode'].value,
      'each_item')
    self.assertEqual(
      settings['main/actions/export/arguments/export_mode'].default_value,
      'each_item')

  def _assert_correct_contents_for_update_to_1_0_rc1(self, settings):
    self.assertNotIn('selected_items', settings['main'])
    self.assertNotIn('selected_layers', settings['main'])
    self.assertIn('selected_items', settings['gui'])

  def _assert_correct_contents_for_update_to_1_0_rc2(self, settings):
    self.assertEqual(
      settings['main/output_directory'].gui_type, setting_.FileChooserPresenter)
    self.assertIsInstance(settings['main/output_directory'].value, Gio.File)
    self.assertEqual(
      settings['main/output_directory'].action, Gimp.FileChooserAction.SELECT_FOLDER)

  def _assert_correct_contents_for_update_to_1_1(self, settings):
    self.assertNotIn('procedures', settings['main'])
    self.assertNotIn('constraints', settings['main'])

    self.assertEqual(settings['main/output_directory'].set_default_if_not_exists, True)

    for command in settings['main/actions']:
      self.assertNotIn('action_groups', command)
      self.assertIn('command_groups', command)

      self.assertIn('command', command.tags)
      self.assertNotIn('procedure', command.tags)
      self.assertIn('action', command.tags)
      self.assertNotIn('condition', command.tags)

      self.assertNotIn('default_procedures', command['command_groups'].default_value)
      self.assertIn('default_actions', command['command_groups'].default_value)
      self.assertNotIn('default_procedures', command['command_groups'].value)
      self.assertIn('default_actions', command['command_groups'].value)

    for command in settings['main/conditions']:
      self.assertNotIn('action_groups', command)
      self.assertIn('command_groups', command)

      self.assertIn('command', command.tags)
      self.assertNotIn('action', command.tags)
      self.assertIn('condition', command.tags)
      self.assertNotIn('constraint', command.tags)

      self.assertNotIn('default_constraints', command['command_groups'].default_value)
      self.assertIn('default_conditions', command['command_groups'].default_value)
      self.assertNotIn('default_constraints', command['command_groups'].value)
      self.assertIn('default_conditions', command['command_groups'].value)

    scale_arguments_path = 'main/actions/scale_for_images/arguments'

    self.assertListEqual(
      [setting.name for setting in settings[scale_arguments_path]],
      [
        'object_to_scale',
        'new_width',
        'new_height',
        'aspect_ratio',
        'interpolation',
        'local_origin',
        'set_image_resolution',
        'image_resolution',
        'padding_color',
        'padding_position',
        'padding_position_custom',
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
      setting_additional.DimensionSetting,
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
      setting_additional.DimensionSetting,
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
    self.assertEqual(settings[f'{scale_arguments_path}/padding_color'].value, [0.0, 0.0, 0.0, 0.0])
    self.assertEqual(settings[f'{scale_arguments_path}/padding_position'].value, 'center')
    self.assertEqual(
      settings[f'{scale_arguments_path}/padding_position_custom'].value,
      {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
    )
    self.assertEqual(settings[f'{scale_arguments_path}/set_image_resolution'].value, False)

    self.assertIsInstance(
      settings[f'{scale_arguments_path}/image_resolution'],
      setting_additional.CoordinatesSetting,
    )
    self.assertEqual(
      settings[f'{scale_arguments_path}/image_resolution'].value,
      {
        'x': 72.0,
        'y': 72.0,
      },
    )

    align_arguments_path = 'main/actions/align_and_offset_layers/arguments'

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
      setting_additional.DimensionSetting,
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
      setting_additional.DimensionSetting,
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

    self.assertEqual(
      settings['main/actions/resize_to_layer_size/orig_name'].value, 'resize_canvas')

    resize_canvas_arguments_path = 'main/actions/resize_to_layer_size/arguments'

    self.assertEqual(
      settings[f'{resize_canvas_arguments_path}/resize_mode'].value, 'resize_to_layer_size')

    self.assertListEqual(
      [setting.name for setting in settings[resize_canvas_arguments_path]],
      [
        'object_to_resize',
        'resize_mode',
        'set_fill_color',
        'fill_color',
        'resize_from_edges_same_amount_for_each_side',
        'resize_from_edges_amount',
        'resize_from_edges_top',
        'resize_from_edges_bottom',
        'resize_from_edges_left',
        'resize_from_edges_right',
        'resize_from_position_anchor',
        'resize_from_position_width',
        'resize_from_position_height',
        'resize_to_aspect_ratio_ratio',
        'resize_to_aspect_ratio_position',
        'resize_to_aspect_ratio_position_custom',
        'resize_to_area_x',
        'resize_to_area_y',
        'resize_to_area_width',
        'resize_to_area_height',
        'resize_to_layer_size_layers',
        'resize_to_image_size_image',
      ],
    )

    self.assertNotIn('procedure_browser', settings['gui'])
    self.assertIn('action_browser', settings['gui'])

  def _assert_correct_contents_for_update_to_1_2(self, settings):
    scale_arguments_path = 'main/actions/scale_for_images/arguments'

    self.assertFalse(settings[f'{scale_arguments_path}/image_resolution'].gui.show_display_name)
