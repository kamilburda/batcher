def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertNotIn('selected_items', settings['main'])
  test_case.assertNotIn('selected_layers', settings['main'])
  test_case.assertIn('selected_items', settings['gui'])
