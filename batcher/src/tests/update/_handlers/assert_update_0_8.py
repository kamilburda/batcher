def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(settings['main/export/export_mode'].value, 'each_item')
  test_case.assertEqual(settings['main/export/export_mode'].default_value, 'each_item')

  test_case.assertNotIn('remove_folder_structure_for_export_layers', settings['main/actions'])
  test_case.assertIn('remove_folder_structure', settings['main/actions'])

  test_case.assertEqual(
    settings['main/actions/export/arguments/export_mode'].value,
    'each_item')
  test_case.assertEqual(
    settings['main/actions/export/arguments/export_mode'].default_value,
    'each_item')
