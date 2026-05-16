def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(settings['main/export/layer_handling'].value, 'merge_and_add_alpha')
