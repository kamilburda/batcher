def assert_contents(test_case, settings, orig_setting_values):
  for command in settings['main/actions']:
    test_case.assertIn('more_options', command)
    test_case.assertIn('enabled_for_previews', command['more_options'])
    test_case.assertNotIn('enabled_for_previews', command)

  for command in settings['main/conditions']:
    test_case.assertIn('more_options', command)
    test_case.assertIn('enabled_for_previews', command['more_options'])
    test_case.assertNotIn('enabled_for_previews', command)
    test_case.assertIn('also_apply_to_parent_folders', command['more_options'])
    test_case.assertNotIn('also_apply_to_parent_folders', command)

  orig_setting_paths_to_test = [
    'gui/size/dialog_size',
    'gui/size/paned_outside_previews_position',
    'gui/size/paned_between_previews_position',
  ]

  for setting_path in orig_setting_paths_to_test:
    test_case.assertEqual(settings[setting_path].value, orig_setting_values[setting_path])
