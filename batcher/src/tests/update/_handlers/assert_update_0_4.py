from src import builtin_actions
from src import setting_additional


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertNotIn('edit_mode', settings['main'])

  test_case.assertIn('name_pattern', settings['main'])
  test_case.assertNotIn('layer_filename_pattern', settings['main'])

  test_case.assertIsInstance(
    settings['main/name_pattern'], setting_additional.NamePatternSetting)

  test_case.assertIn('insert_background', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/insert_background/orig_name'].value, 'insert_overlay_for_layers')

  insert_background_orig_name = settings['main/actions/insert_background/orig_name'].value
  for argument in builtin_actions.BUILTIN_ACTIONS[insert_background_orig_name]['arguments']:
    argument_name = argument['name']
    if argument_name == 'text_font_family':
      continue
    argument_default_value = argument['default_value']
    test_case.assertEqual(
      settings[f'main/actions/insert_background/arguments/{argument_name}'].default_value,
      argument_default_value)

  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/condition_name'].value,
    'not_background')
  test_case.assertIn('merge_background', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/merge_background/orig_name'].value, 'merge_layer')
  test_case.assertIn('merge_type', settings['main/actions/merge_background/arguments'])
  test_case.assertIn('not_background', settings['main/conditions'])
  test_case.assertEqual(
    settings['main/conditions/not_background/orig_name'].value, 'without_color_tag')
  test_case.assertIn('color_tag', settings['main/conditions/not_background/arguments'])
  test_case.assertTrue(
    settings['main/conditions/not_background/arguments/last_enabled_value'].value)

  test_case.assertIn('insert_background_2', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/insert_background_2/orig_name'].value, 'insert_overlay_for_layers')

  insert_background_orig_name = settings['main/actions/insert_background_2/orig_name'].value
  for argument in builtin_actions.BUILTIN_ACTIONS[insert_background_orig_name]['arguments']:
    argument_name = argument['name']
    if argument_name == 'text_font_family':
      continue
    argument_default_value = argument['default_value']
    test_case.assertEqual(
      settings[f'main/actions/insert_background_2/arguments/{argument_name}'].default_value,
      argument_default_value)

  test_case.assertIn('color_tag', settings['main/actions/insert_background_2/arguments'])
  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/condition_name'].value,
    'not_background_2')
  test_case.assertIn('merge_background_2', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/merge_background_2/orig_name'].value, 'merge_layer')
  test_case.assertIn('merge_type', settings['main/actions/merge_background_2/arguments'])
  test_case.assertIn('not_background_2', settings['main/conditions'])
  test_case.assertEqual(
    settings['main/conditions/not_background_2/orig_name'].value, 'without_color_tag')
  test_case.assertIn('color_tag', settings['main/conditions/not_background_2/arguments'])
  test_case.assertTrue(
    settings['main/conditions/not_background_2/arguments/last_enabled_value'].value)

  test_case.assertIn('export', settings['main/actions'])
  test_case.assertNotIn(
    'single_image_filename_pattern', settings['main/actions/export/arguments'])
  test_case.assertIn('single_image_name_pattern', settings['main/actions/export/arguments'])
  test_case.assertIsInstance(
    settings['main/actions/export/arguments/single_image_name_pattern'],
    setting_additional.NamePatternSetting,
  )
  test_case.assertEqual(
    settings['main/actions/export/arguments/single_image_name_pattern'].gui_type,
    setting_additional.NamePatternEntryPresenter,
  )

  test_case.assertIsInstance(
    settings['main/actions/rename/arguments/pattern'],
    setting_additional.NamePatternSetting,
  )
  test_case.assertEqual(
    settings['main/actions/rename/arguments/pattern'].gui_type,
    setting_additional.NamePatternEntryPresenter,
  )
