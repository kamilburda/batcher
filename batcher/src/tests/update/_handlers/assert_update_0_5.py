import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import setting as setting_


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(
    settings['main/file_extension'].gui_type,
    setting_.NullPresenter,
  )

  test_case.assertIn('export', settings['main/actions'])
  test_case.assertEqual(
    settings['main/actions/export/orig_name'].value, 'export_for_export_layers')

  test_case.assertNotIn(
    'preserve_layer_name_after_export', settings['main/actions/export/arguments'])
  test_case.assertIn('overwrite_mode', settings['main/actions/export/arguments'])
  # This checks whether `overwrite_mode` is the third argument.
  test_case.assertEqual(
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
      settings['main/actions/export/arguments/rotate_flip_image_based_on_exif_metadata'],
      settings['main/actions/export/arguments/merge_filters'],
    ])

  test_case.assertIsInstance(
    settings['main/actions/insert_background/arguments/color_tag'],
    setting_.EnumSetting)
  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/color_tag'].enum_type,
    Gimp.ColorTag)
  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/color_tag'].excluded_values,
    [Gimp.ColorTag.NONE])

  test_case.assertEqual(
    settings['main/actions/merge_background/arguments/merge_type'].excluded_values,
    [Gimp.MergeType.FLATTEN_IMAGE])

  test_case.assertIsInstance(
    settings['main/actions/insert_background_2/arguments/color_tag'],
    setting_.EnumSetting)
  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/color_tag'].enum_type,
    Gimp.ColorTag)
  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/color_tag'].excluded_values,
    [Gimp.ColorTag.NONE])

  test_case.assertIsInstance(
    settings['main/conditions/not_background/arguments/color_tag'],
    setting_.EnumSetting)
  test_case.assertEqual(
    settings['main/conditions/not_background/arguments/color_tag'].enum_type,
    Gimp.ColorTag)
  test_case.assertEqual(
    settings['main/conditions/not_background/arguments/color_tag'].excluded_values,
    [Gimp.ColorTag.NONE])
