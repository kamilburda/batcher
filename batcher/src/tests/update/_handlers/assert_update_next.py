from src import directory as directory_
from src import setting as setting_
from src import setting_additional


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(
    settings['main/output_directory'].gui_type, setting_additional.DirectoryChooserPresenter)
  test_case.assertIsInstance(settings['main/output_directory'].value, directory_.Directory)
  test_case.assertIsInstance(settings['main/output_directory'].default_value, directory_.Directory)

  scale_arguments_path = 'main/actions/scale_for_images/arguments'

  test_case.assertFalse(settings[f'{scale_arguments_path}/image_resolution'].gui.show_display_name)

  active_file_format_key = setting_additional.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY

  test_case.assertEqual(
    settings['main/export/file_format_export_options'].value[active_file_format_key],
    ['png'],
  )
  test_case.assertIn('rotate_flip_image_based_on_exif_metadata', settings['main/export'])

  test_case.assertEqual(
    settings['gui/show_original_item_names'].gui_type, setting_.CheckMenuItemPresenter)
