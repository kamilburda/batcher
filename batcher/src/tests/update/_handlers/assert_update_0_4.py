from src import setting_additional


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertNotIn('edit_mode', settings['main'])

  test_case.assertIn('name_pattern', settings['main'])
  test_case.assertNotIn('layer_filename_pattern', settings['main'])

  test_case.assertIsInstance(
    settings['main/name_pattern'], setting_additional.NamePatternSetting)

  test_case.assertIn('insert_background', settings['main/actions'])
  test_case.assertIn('color_tag', settings['main/actions/insert_background/arguments'])
  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/merge_action_name'].value,
    'merge_background')
  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/condition_name'].value,
    'not_background')
  test_case.assertIn('merge_background', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/merge_background/display_name'].value,
    'Merge Background')
  test_case.assertIn('merge_type', settings['main/actions/merge_background/arguments'])
  test_case.assertTrue(
    settings['main/actions/merge_background/arguments/last_enabled_value'].value)
  test_case.assertIn('not_background', settings['main/conditions'])
  test_case.assertEqual(
    settings['main/conditions/not_background/display_name'].value,
    'Not Background')
  test_case.assertIn('color_tag', settings['main/conditions/not_background/arguments'])
  test_case.assertTrue(
    settings['main/conditions/not_background/arguments/last_enabled_value'].value)

  test_case.assertIn('insert_background_2', settings['main/actions'])
  test_case.assertIn('color_tag', settings['main/actions/insert_background_2/arguments'])
  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/merge_action_name'].value,
    'merge_background_2')
  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/condition_name'].value,
    'not_background_2')
  test_case.assertIn('merge_background_2', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/merge_background_2/display_name'].value,
    'Merge Background (2)')
  test_case.assertIn('merge_type', settings['main/actions/merge_background_2/arguments'])
  test_case.assertTrue(
    settings['main/actions/merge_background_2/arguments/last_enabled_value'].value)
  test_case.assertIn('not_background_2', settings['main/conditions'])
  test_case.assertEqual(
    settings['main/conditions/not_background/display_name'].value,
    'Not Background')
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
