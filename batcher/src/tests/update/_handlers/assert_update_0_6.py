from src import builtin_actions
from src import builtin_conditions
from src import placeholders
from src import setting as setting_


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(settings['main/overwrite_mode'].value, 'rename_new')

  test_case.assertEqual(settings['main/tagged_items'].value, [])

  test_case.assertIn('name_preview_items_collapsed_state', settings['gui'])
  test_case.assertNotIn('name_preview_layers_collapsed_state', settings['gui'])

  test_case.assertIn('image_preview_displayed_items', settings['gui'])
  test_case.assertNotIn('image_preview_displayed_layers', settings['gui'])

  test_case.assertIn('images_and_directories', settings['gui'])

  test_case.assertIsInstance(
    settings['gui/size/paned_between_previews_position'], setting_.IntSetting)

  test_case.assertEqual(
    settings['main/actions/export/arguments/file_format_mode'].value,
    'use_explicit_values')
  test_case.assertEqual(
    settings['main/actions/export/arguments/overwrite_mode'].value,
    'ask')

  for action in settings['main/actions']:
    if action['orig_name'].value in builtin_actions.BUILTIN_ACTIONS:
      test_case.assertEqual(action['origin'].value, 'builtin')
    else:
      test_case.assertEqual(action['origin'].value, 'gimp_pdb')

  test_case.assertEqual(
    settings['main/actions/insert_background/arguments/tagged_items'].value, [])

  test_case.assertEqual(
    settings['main/actions/insert_background_2/arguments/tagged_items'].value, [])

  test_case.assertNotIn(
    'drawable',
    settings['main/actions/script-fu-addborder/arguments'])
  test_case.assertIsInstance(
    settings['main/actions/script-fu-addborder/arguments/drawables'],
    placeholders.PlaceholderDrawableArraySetting)

  test_case.assertIsInstance(
    settings['main/actions/script-fu-addborder/arguments/color'],
    setting_.ColorSetting)
  test_case.assertEqual(
    settings['main/actions/script-fu-addborder/arguments/color'].gui_type,
    setting_.ColorButtonPresenter)
  test_case.assertEqual(
    settings['main/actions/script-fu-addborder/arguments/color'].pdb_type.name,
    'GeglColor')

  for condition in settings['main/conditions']:
    if condition['orig_name'].value in builtin_conditions.BUILTIN_CONDITIONS:
      test_case.assertEqual(condition['origin'].value, 'builtin')
    else:
      test_case.assertEqual(condition['origin'].value, 'gimp_pdb')
