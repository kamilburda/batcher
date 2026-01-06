import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import placeholders
from src import setting_additional


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertNotIn('procedures', settings['main'])
  test_case.assertNotIn('constraints', settings['main'])

  for command in settings['main/actions']:
    test_case.assertNotIn('action_groups', command)
    test_case.assertIn('command_groups', command)

    test_case.assertIn('command', command.tags)
    test_case.assertNotIn('procedure', command.tags)
    test_case.assertIn('action', command.tags)
    test_case.assertNotIn('condition', command.tags)

    test_case.assertNotIn('default_procedures', command['command_groups'].default_value)
    test_case.assertIn('default_actions', command['command_groups'].default_value)
    test_case.assertNotIn('default_procedures', command['command_groups'].value)
    test_case.assertIn('default_actions', command['command_groups'].value)

  for command in settings['main/conditions']:
    test_case.assertNotIn('action_groups', command)
    test_case.assertIn('command_groups', command)

    test_case.assertIn('command', command.tags)
    test_case.assertNotIn('action', command.tags)
    test_case.assertIn('condition', command.tags)
    test_case.assertNotIn('constraint', command.tags)

    test_case.assertNotIn('default_constraints', command['command_groups'].default_value)
    test_case.assertIn('default_conditions', command['command_groups'].default_value)
    test_case.assertNotIn('default_constraints', command['command_groups'].value)
    test_case.assertIn('default_conditions', command['command_groups'].value)

  scale_arguments_path = 'main/actions/scale_for_images/arguments'

  test_case.assertListEqual(
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

  test_case.assertIsInstance(
    settings[f'{scale_arguments_path}/object_to_scale'],
    placeholders.PlaceholderImageOrLayerSetting,
  )
  test_case.assertEqual(
    settings[f'{scale_arguments_path}/object_to_scale'].value,
    'current_image',
  )

  test_case.assertIsInstance(
    settings[f'{scale_arguments_path}/new_width'],
    setting_additional.DimensionSetting,
  )
  test_case.assertEqual(
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
  test_case.assertEqual(settings[f'{scale_arguments_path}/new_width'].min_value, 0.0)

  test_case.assertIsInstance(
    settings[f'{scale_arguments_path}/new_height'],
    setting_additional.DimensionSetting,
  )
  test_case.assertEqual(
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
  test_case.assertEqual(settings[f'{scale_arguments_path}/new_height'].min_value, 0.0)
  test_case.assertEqual(settings[f'{scale_arguments_path}/aspect_ratio'].value, 'stretch')
  test_case.assertEqual(settings[f'{scale_arguments_path}/padding_color'].value, [0.0, 0.0, 0.0, 0.0])
  test_case.assertEqual(settings[f'{scale_arguments_path}/padding_position'].value, 'center')
  test_case.assertEqual(
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
  test_case.assertEqual(settings[f'{scale_arguments_path}/set_image_resolution'].value, False)

  test_case.assertIsInstance(
    settings[f'{scale_arguments_path}/image_resolution'],
    setting_additional.CoordinatesSetting,
  )
  test_case.assertEqual(
    settings[f'{scale_arguments_path}/image_resolution'].value,
    {
      'x': 72.0,
      'y': 72.0,
    },
  )

  align_arguments_path = 'main/actions/align_and_offset_layers/arguments'

  test_case.assertListEqual(
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

  test_case.assertIsInstance(
    settings[f'{align_arguments_path}/reference_object'],
    placeholders.PlaceholderImageOrLayerSetting,
  )

  test_case.assertIsInstance(
    settings[f'{align_arguments_path}/x_offset'],
    setting_additional.DimensionSetting,
  )
  test_case.assertEqual(
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

  test_case.assertIsInstance(
    settings[f'{align_arguments_path}/y_offset'],
    setting_additional.DimensionSetting,
  )
  test_case.assertEqual(
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

  test_case.assertEqual(
    settings['main/actions/resize_to_layer_size/orig_name'].value, 'resize_canvas')

  resize_canvas_arguments_path = 'main/actions/resize_to_layer_size/arguments'

  test_case.assertEqual(
    settings[f'{resize_canvas_arguments_path}/resize_mode'].value, 'resize_to_layer_size')

  test_case.assertListEqual(
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

  test_case.assertNotIn('procedure_browser', settings['gui'])
  test_case.assertIn('action_browser', settings['gui'])
