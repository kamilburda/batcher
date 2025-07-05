def assert_contents(test_case, settings, _orig_setting_values):
  scale_arguments_path = 'main/actions/scale_for_images/arguments'

  test_case.assertFalse(settings[f'{scale_arguments_path}/image_resolution'].gui.show_display_name)
