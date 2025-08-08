import unittest

import parameterized

from src.setting import group as group_
from src.setting import presenter as presenter_
from src.setting import settings as settings_
from src.setting import utils as utils_

from src.tests.setting import stubs_setting
from src.tests.setting import stubs_group


class TestGroupAttributes(unittest.TestCase):
  
  def setUp(self):
    self.settings = group_.Group(name='main')
  
  def test_invalid_group_name(self):
    with self.assertRaises(ValueError):
      group_.Group(name='main/additional')
    
    with self.assertRaises(ValueError):
      group_.Group(name='main.additional')
  
  def test_get_generated_display_name(self):
    self.assertEqual(self.settings.display_name, 'Main')
  
  def test_get_generated_description(self):
    settings = group_.Group(name='main', display_name='_Main')
    self.assertEqual(settings.description, 'Main')
  
  def test_get_custom_display_name_and_description(self):
    settings = group_.Group(
      name='main', display_name='_Main', description='My description')
    self.assertEqual(settings.display_name, '_Main')
    self.assertEqual(settings.description, 'My description')
  
  def test_get_non_existent_setting_name(self):
    with self.assertRaises(KeyError):
      # noinspection PyStatementEffect
      self.settings['invalid_name']


class TestGroupAddWithSettingDict(unittest.TestCase):
  
  def setUp(self):
    self.settings = group_.Group('main')
    self.setting_dict = {
      'type': 'bool',
      'name': 'resize_to_layer_size',
      'default_value': False,
    }
  
  def test_add(self):
    self.settings.add([self.setting_dict])
    
    self.assertIn('resize_to_layer_size', self.settings)
    self.assertIsInstance(self.settings['resize_to_layer_size'], settings_.BoolSetting)
    self.assertEqual(self.settings['resize_to_layer_size'].value, False)
  
  def test_add_with_missing_type_attribute(self):
    del self.setting_dict['type']
    
    with self.assertRaises(TypeError):
      self.settings.add([self.setting_dict])
  
  def test_add_with_missing_single_required_attribute(self):
    del self.setting_dict['name']
    
    with self.assertRaises(TypeError):
      self.settings.add([self.setting_dict])
  
  def test_add_with_missing_multiple_required_attributes(self):
    del self.setting_dict['name']
    del self.setting_dict['default_value']
    
    with self.assertRaises(TypeError):
      self.settings.add([self.setting_dict])
  
  def test_add_with_invalid_setting_attribute(self):
    self.setting_dict['invalid_setting_attribute'] = None
    
    with self.assertRaises(TypeError):
      self.settings.add([self.setting_dict])
  
  def test_add_with_path_separator(self):
    self.setting_dict['name'] = utils_.SETTING_PATH_SEPARATOR.join(['use', 'layer', 'size'])
    
    with self.assertRaises(ValueError):
      self.settings.add([self.setting_dict])
  
  def test_add_with_same_name_in_same_group(self):
    with self.assertRaises(ValueError):
      self.settings.add([self.setting_dict, self.setting_dict])

  def test_add_with_same_name_in_same_group_if_uniquify_is_true(self):
    self.settings.add([self.setting_dict, self.setting_dict], uniquify_name=True)

    self.assertIn('resize_to_layer_size', self.settings)
    self.assertIn('resize_to_layer_size_2', self.settings)
  
  def test_add_multiple_dicts_with_same_name_in_different_child_groups(self):
    gui_settings = group_.Group('gui')
    gui_settings.add([self.setting_dict])
    
    main_settings = group_.Group('main')
    main_settings.add([self.setting_dict])
    
    self.settings.add([gui_settings, main_settings])
    
    self.assertIn('resize_to_layer_size', gui_settings)
    self.assertIn('resize_to_layer_size', main_settings)
    self.assertNotEqual(gui_settings['resize_to_layer_size'], main_settings['resize_to_layer_size'])


class TestGroupAddFromDict(unittest.TestCase):
  
  def test_add_with_group_level_attributes(self):
    settings = group_.Group(name='main', setting_attributes={'pdb_type': None})
    settings.add([
      {
       'type': 'bool',
       'name': 'flatten',
      },
      {
       'type': 'bool',
       'name': 'resize_to_layer_size',
      }
    ])
    
    self.assertIsNone(settings['flatten'].pdb_type)
    self.assertIsNone(settings['resize_to_layer_size'].pdb_type)
  
  def test_add_with_group_level_attributes_overridden_by_setting_attributes(self):
    settings = group_.Group(name='main', setting_attributes={'display_name': 'some_name'})
    settings.add([
      {'type': 'bool', 'name': 'flatten'},
      {
       'type': 'int',
       'name': 'drawables',
       'display_name': 'some_other_name',
      }
    ])

    self.assertEqual(settings['flatten'].display_name, 'some_name')
    self.assertEqual(settings['drawables'].display_name, 'some_other_name')
  
  def test_add_with_group_level_attributes_overridden_by_child_group_attributes(self):
    additional_settings = group_.Group(
      name='additional', setting_attributes={'display_name': 'some_other_name'})
    additional_settings.add([{'type': 'int', 'name': 'drawables'}])
    
    settings = group_.Group(name='main', setting_attributes={'display_name': 'some_name'})
    settings.add([
      {'type': 'bool', 'name': 'flatten'},
      additional_settings,
    ])

    self.assertEqual(settings['flatten'].display_name, 'some_name')
    self.assertEqual(settings['additional/drawables'].display_name, 'some_other_name')
  
  def test_add_with_top_group_attributes_applied_recursively(self):
    settings = group_.Group(
      name='main', setting_attributes={'display_name': 'some_name'})
    
    additional_settings = group_.Group(name='additional')
    
    settings.add([
      {'type': 'int', 'name': 'images'},
      additional_settings
    ])
    
    additional_settings.add([{'type': 'int', 'name': 'drawables'}])
    
    self.assertEqual(settings['images'].display_name, 'some_name')
    self.assertEqual(settings['additional/drawables'].display_name, 'some_name')
  
  def test_add_with_top_group_attributes_not_applied_recursively_if_disabled(self):
    settings = group_.Group(
      name='main',
      setting_attributes={'display_name': 'some_other_name'},
      recurse_setting_attributes=False)
    
    additional_settings = group_.Group(name='additional')
    
    settings.add([
      {'type': 'int', 'name': 'images', 'display_name': 'some_name'},
      additional_settings,
    ])
    
    additional_settings.add([{'type': 'int', 'name': 'drawables', 'display_name': 'some_name'}])
    
    self.assertEqual(settings['images'].display_name, 'some_name')
    self.assertEqual(settings['additional/drawables'].display_name, 'some_name')


class TestGroupCreateGroupsFromDict(unittest.TestCase):
  
  def test_create_groups_no_groups(self):
    settings = group_.create_groups({
      'name': 'main',
      'groups': None,
    })
    
    self.assertEqual(len(settings), 0)
  
  def test_create_groups(self):
    settings = group_.create_groups({
      'name': 'main',
      'groups': [
        {
          'name': 'actions'
        },
        {
          'name': 'conditions',
          'groups': [
            {
              'name': 'include'
            }
          ]
        }
      ]
    })
    
    self.assertEqual(settings.name, 'main')
    self.assertEqual(len(settings), 2)
    self.assertIn('actions', settings)
    self.assertIn('conditions', settings)
    self.assertIn('conditions/include', settings)
    self.assertIn('include', settings['conditions'])
    self.assertEqual(len(settings['conditions']), 1)
    self.assertNotIn('include', settings)
  
  def test_create_group_invalid_key(self):
    with self.assertRaises(TypeError):
      group_.create_groups({
        'name': 'main',
        'invalid_key': {},
      })


class TestGroup(unittest.TestCase):
  
  def setUp(self):
    self.settings = stubs_group.create_test_settings()
    
    self.edit_mode_setting_dict = {
      'type': 'bool',
      'name': 'edit_mode',
      'default_value': False,
    }
    
    self.gui_settings = group_.Group('gui')
    self.gui_settings.add([self.edit_mode_setting_dict])
  
  def test_add_same_setting_in_same_group(self):
    with self.assertRaises(ValueError):
      self.gui_settings.add([self.gui_settings['edit_mode']])

  def test_add_same_setting_in_same_group_if_uniquify_is_true(self):
    self.gui_settings.add([self.gui_settings['edit_mode']], uniquify_name=True)

    self.assertIn('edit_mode', self.gui_settings)
    self.assertIn('edit_mode_2', self.gui_settings)
  
  def test_add_same_setting_in_different_child_groups(self):
    self.settings.add([self.gui_settings['edit_mode'], self.gui_settings])
    
    self.assertIn('edit_mode', self.settings)
    self.assertIn('edit_mode', self.gui_settings)
    self.assertEqual(self.settings['edit_mode'], self.gui_settings['edit_mode'])
  
  def test_add_group(self):
    self.settings.add([self.gui_settings])
    
    self.assertIn('gui', self.settings)
    self.assertEqual(self.settings['gui'], self.gui_settings)
  
  def test_add_same_group_in_same_parent_group(self):
    self.settings.add([self.gui_settings])
    with self.assertRaises(ValueError):
      self.settings.add([self.gui_settings])

  def test_add_same_group_in_same_group_if_uniquify_is_true(self):
    self.settings.add([self.gui_settings])
    self.settings.add([self.gui_settings], uniquify_name=True)

    self.assertIn('gui', self.settings)
    self.assertIn('gui', self.settings)
  
  def test_add_same_group_as_child_of_itself(self):
    with self.assertRaises(ValueError):
      self.gui_settings.add([self.gui_settings])
  
  def test_add_different_groups_with_same_name_in_different_child_groups(self):
    main_settings = group_.Group('main')
    main_settings.add([self.gui_settings])
    
    different_gui_settings = group_.Group('gui')
    self.settings.add([main_settings, different_gui_settings])
    
    self.assertIn('gui', self.settings)
    self.assertIn('gui', main_settings)
    self.assertNotEqual(self.settings['gui'], main_settings['gui'])
  
  def test_add_same_group_in_different_child_groups(self):
    main_settings = group_.Group('main')
    main_settings.add([self.gui_settings])
    
    self.settings.add([self.gui_settings, main_settings])
    
    self.assertIn('gui', self.settings)
    self.assertIn('gui', main_settings)
    self.assertEqual(self.settings['gui'], main_settings['gui'])
  
  @parameterized.parameterized.expand([
    ('setting_exists_returns_setting_value',
     'file_extension',
     'jpg',
     'bmp'),
    
    ('setting_does_not_exist_returns_default_value',
     'invalid_setting',
     'jpg',
     'jpg'),
  ])
  def test_get_value(
        self,
        test_case_suffix,
        setting_name_or_path,
        default_value,
        expected_value):
    self.assertEqual(self.settings.get_value(setting_name_or_path, default_value), expected_value)

  def test_get_value_raises_error_if_path_does_not_point_to_setting(self):
    settings = stubs_group.create_test_settings_hierarchical()

    with self.assertRaises(TypeError):
      settings.get_value('advanced')

  def test_get_attributes(self):
    setting_attributes_and_values = self.settings.get_attributes([
      'file_extension',
      'file_extension.display_name',
    ])
    
    self.assertEqual(len(setting_attributes_and_values), 2)
    self.assertEqual(setting_attributes_and_values['file_extension'], 'bmp')
    self.assertEqual(
      setting_attributes_and_values['file_extension.display_name'], 'File extension')
  
  def test_get_attributes_getter_properties_only(self):
    setting_attributes_and_values = self.settings.get_attributes(['file_extension.name'])
    self.assertEqual(setting_attributes_and_values['file_extension.name'], 'file_extension')
  
  def test_get_attributes_nonexistent_attribute(self):
    with self.assertRaises(AttributeError):
      self.settings.get_attributes(['file_extension.nonexistent'])
  
  def test_get_attributes_nonexistent_setting(self):
    with self.assertRaises(KeyError):
      self.settings.get_attributes(['nonexistent_setting'])
  
  def test_get_attributes_invalid_number_of_periods(self):
    with self.assertRaises(ValueError):
      self.settings.get_attributes(['file_extension.value.value'])
  
  def test_get_values(self):
    setting_names_and_values = self.settings.get_values()
    
    self.assertEqual(len(setting_names_and_values), 3)
    self.assertEqual(
      setting_names_and_values['file_extension'],
      self.settings['file_extension'].default_value)
    self.assertEqual(
      setting_names_and_values['flatten'],
      self.settings['flatten'].default_value)
    self.assertEqual(
      setting_names_and_values['overwrite_mode'],
      self.settings['overwrite_mode'].default_value)
  
  def test_set_values(self):
    self.settings.set_values({
      'file_extension': 'jpg',
      'flatten': True
    })
    
    self.assertEqual(self.settings['file_extension'].value, 'jpg')
    self.assertEqual(self.settings['flatten'].value, True)
  
  def test_set_values_nonexistent_setting(self):
    with self.assertRaises(KeyError):
      self.settings.set_values({
        'nonexistent_setting': 'jpg',
      })
  
  @parameterized.parameterized.expand([
    ('positive_index',
     'file_extension',
     2,
     ['flatten', 'overwrite_mode', 'file_extension']),
    
    ('positive_index_beyond_group_length',
     'file_extension',
     4,
     ['flatten', 'overwrite_mode', 'file_extension']),
    
    ('same_index',
     'file_extension',
     0,
     ['file_extension', 'flatten', 'overwrite_mode']),
    
    ('negative_index',
     'file_extension',
     -2,
     ['flatten', 'file_extension', 'overwrite_mode']),
  ])
  def test_reorder(self, test_case_suffix, setting_name, new_position, expected_names):
    self.settings.reorder(setting_name, new_position)
    
    expected_list = [self.settings[name] for name in expected_names]
    
    self.assertListEqual(list(self.settings), expected_list)
  
  def test_reorder_multiple_times(self):
    self.settings.reorder('file_extension', 2)
    self.settings.reorder('file_extension', 1)
    
    expected_list = [
      self.settings[name] for name in ['flatten', 'file_extension', 'overwrite_mode']]
    
    self.assertListEqual(list(self.settings), expected_list)
  
  def test_reorder_does_not_affect_order_outside_current_group(self):
    settings = stubs_group.create_test_settings_hierarchical()
    
    settings['main'].add([{'name': 'enabled', 'type': 'bool'}])
    
    settings['advanced'].reorder('flatten', 1)
    
    self.assertListEqual(
      list(settings.walk(include_groups=True)),
      [settings[path] for path in [
        'main', 'main/file_extension', 'main/enabled',
        'advanced', 'advanced/overwrite_mode', 'advanced/flatten']])
  
  def test_remove_settings(self):
    self.settings.remove(['file_extension', 'flatten'])
    self.assertNotIn('file_extension', self.settings)
    self.assertNotIn('flatten', self.settings)
    self.assertIn('overwrite_mode', self.settings)
  
  def test_remove_setting_from_group_and_then_group(self):
    self.settings.add([self.gui_settings])
    
    self.settings['gui'].remove(['edit_mode'])
    self.assertNotIn('edit_mode', self.settings['gui'])
    
    self.settings.remove(['gui'])
    self.assertNotIn('gui', self.settings)
  
  def test_remove_settings_raise_error_if_invalid_name(self):
    with self.assertRaises(KeyError):
      self.settings.remove(['file_extension', 'invalid_setting'])
  
  def test_remove_setting_raise_error_if_already_removed(self):
    self.settings.remove(['file_extension'])
    with self.assertRaises(KeyError):
      self.settings.remove(['file_extension'])
  
  def test_reset_settings_and_nested_groups_and_ignore_specified_settings(self):
    self.settings.add([self.gui_settings])
    self.settings['file_extension'].tags.add('ignore_reset')
    self.settings['overwrite_mode'].tags.update(
      ['ignore_reset', 'ignore_apply_gui_value_to_setting'])
    
    self.settings['file_extension'].set_value('gif')
    self.settings['flatten'].set_value(True)
    self.settings['overwrite_mode'].set_value('skip')
    self.settings['gui/edit_mode'].set_value(True)
    
    self.settings.reset()
    
    self.assertEqual(self.settings['file_extension'].value, 'gif')
    self.assertEqual(self.settings['overwrite_mode'].value, 'skip')
    self.assertEqual(
      self.settings['flatten'].value,
      self.settings['flatten'].default_value)
    self.assertEqual(
      self.settings['gui/edit_mode'].value,
      self.settings['gui/edit_mode'].default_value)
  
  def test_reset_ignore_nested_group(self):
    self.settings.add([self.gui_settings])
    self.settings['gui'].tags.add('ignore_reset')
    
    self.settings['gui/edit_mode'].set_value(True)
    
    self.settings.reset()
    
    self.assertNotEqual(
      self.settings['gui/edit_mode'].value,
      self.settings['gui/edit_mode'].default_value)
  
  def test_to_dict(self):
    group = group_.Group('main', tags=['ignore_load'], setting_attributes={'gui_type': None})
    
    group.add([self.edit_mode_setting_dict])
    
    self.assertDictEqual(
      group.to_dict(),
      {'name': 'main', 'tags': ['ignore_load'], 'setting_attributes': {'gui_type': None}})


class TestGroupHierarchical(unittest.TestCase):
  
  def setUp(self):
    self.settings = stubs_group.create_test_settings_hierarchical()
  
  def test_get_setting_via_paths(self):
    self.assertEqual(
      self.settings['main/file_extension'], self.settings['main']['file_extension'])
    self.assertEqual(
      self.settings['advanced/flatten'],
      self.settings['advanced']['flatten'])
    self.assertEqual(
      self.settings['advanced/overwrite_mode'],
      self.settings['advanced']['overwrite_mode'])
  
  def test_get_setting_via_paths_multiple_levels(self):
    expert_settings = group_.Group('expert')
    expert_settings.add([
        {
         'type': 'int',
         'name': 'file_extension_strip_mode',
         'default_value': 0
        }
    ])
    
    self.settings['advanced'].add([expert_settings])
    
    self.assertEqual(
      self.settings['advanced/expert/file_extension_strip_mode'],
      self.settings['advanced']['expert']['file_extension_strip_mode'])
    
  def test_get_setting_via_paths_invalid_group(self):
    with self.assertRaises(KeyError):
      # noinspection PyStatementEffect
      self.settings['advanced/invalid_group/file_extension_strip_mode']
  
  def test_get_values_returns_paths(self):
    setting_names_and_values = self.settings.get_values()
    
    self.assertEqual(len(setting_names_and_values), 3)
    self.assertEqual(
      setting_names_and_values['main/file_extension'],
      self.settings['main/file_extension'].default_value)
    self.assertEqual(
      setting_names_and_values['advanced/flatten'],
      self.settings['advanced/flatten'].default_value)
    self.assertEqual(
      setting_names_and_values['advanced/overwrite_mode'],
      self.settings['advanced/overwrite_mode'].default_value)
  
  def test_contains_via_paths(self):
    self.assertIn('main/file_extension', self.settings)
    self.assertNotIn('main/invalid_setting', self.settings)
  
  def test_walk(self):
    walked_settings = list(self.settings.walk())
    
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertIn(self.settings['advanced/flatten'], walked_settings)
    self.assertIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_ignore_settings_with_tag(self):
    self.settings['main/file_extension'].tags.add('ignore_reset')
    self.settings['advanced/overwrite_mode'].tags.update(
      ['ignore_reset', 'ignore_apply_gui_value_to_setting'])
    
    walked_settings = list(self.settings.walk(
      include_setting_func=lambda setting: 'ignore_reset' not in setting.tags))
    
    self.assertNotIn(self.settings['main/file_extension'], walked_settings)
    self.assertIn(self.settings['advanced/flatten'], walked_settings)
    self.assertNotIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_ignore_settings_in_group_with_tag(self):
    self.settings['advanced'].tags.add('ignore_reset')
    
    walked_settings = list(self.settings.walk(
      include_setting_func=lambda setting: 'ignore_reset' not in setting.tags))
    
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertNotIn(self.settings['advanced/flatten'], walked_settings)
    self.assertNotIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_include_groups(self):
    walked_settings = list(self.settings.walk(include_groups=True))
    
    self.assertIn(self.settings['main'], walked_settings)
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertIn(self.settings['advanced'], walked_settings)
    self.assertIn(self.settings['advanced/flatten'], walked_settings)
    self.assertIn(self.settings['advanced/overwrite_mode'], walked_settings)
    self.assertNotIn(self.settings, walked_settings)
  
  def test_walk_ignore_settings_in_group_with_tag_include_groups(self):
    self.settings['advanced'].tags.add('ignore_reset')
    
    walked_settings = list(
      self.settings.walk(
        include_setting_func=lambda setting: 'ignore_reset' not in setting.tags,
        include_groups=True))
    
    self.assertIn(self.settings['main'], walked_settings)
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertNotIn(self.settings['advanced'], walked_settings)
    self.assertNotIn(self.settings['advanced/flatten'], walked_settings)
    self.assertNotIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_include_if_parent_skipped(self):
    self.settings['advanced'].tags.add('ignore_reset')
    
    walked_settings = list(
      self.settings.walk(
        include_setting_func=lambda setting: 'ignore_reset' not in setting.tags,
        include_if_parent_skipped=True))
    
    self.assertNotIn(self.settings['main'], walked_settings)
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertNotIn(self.settings['advanced'], walked_settings)
    self.assertIn(self.settings['advanced/flatten'], walked_settings)
    self.assertIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_include_if_parent_skipped_and_include_groups(self):
    self.settings['advanced'].tags.add('ignore_reset')
    
    walked_settings = list(
      self.settings.walk(
        include_setting_func=lambda setting: 'ignore_reset' not in setting.tags,
        include_groups=True,
        include_if_parent_skipped=True))
    
    self.assertIn(self.settings['main'], walked_settings)
    self.assertIn(self.settings['main/file_extension'], walked_settings)
    self.assertNotIn(self.settings['advanced'], walked_settings)
    self.assertIn(self.settings['advanced/flatten'], walked_settings)
    self.assertIn(self.settings['advanced/overwrite_mode'], walked_settings)
  
  def test_walk_with_callbacks(self):
    walked_settings, walk_callbacks = self._get_test_data_for_walking_group()
    
    for _unused in self.settings.walk(include_groups=True, walk_callbacks=walk_callbacks):
      pass
    
    self.assertEqual(
      walked_settings,
      ['main', 'file_extension', 'main_end',
       'advanced', 'flatten', 'overwrite_mode', 'advanced_end'])
  
  def test_walk_with_callbacks_and_ignore_settings(self):
    self.settings['main'].tags.add('ignore_reset')
    self.settings['advanced/overwrite_mode'].tags.update(['ignore_reset'])
    
    walked_settings, walk_callbacks = self._get_test_data_for_walking_group()
    
    for _unused in self.settings.walk(
          include_setting_func=lambda setting: 'ignore_reset' not in setting.tags,
          include_groups=True,
          walk_callbacks=walk_callbacks):
      pass
    
    self.assertEqual(walked_settings, ['advanced', 'flatten', 'advanced_end'])
  
  def test_walk_with_callbacks_empty_group(self):
    self.settings['main'].remove(['file_extension'])
    
    walked_settings, walk_callbacks = self._get_test_data_for_walking_group()
    
    for _unused in self.settings.walk(include_groups=True, walk_callbacks=walk_callbacks):
      pass
    
    self.assertEqual(
      walked_settings,
      ['main', 'main_end',
       'advanced', 'flatten', 'overwrite_mode', 'advanced_end'])
  
  @staticmethod
  def _get_test_data_for_walking_group():
    walked_settings = []
    
    def _append_setting_name(setting):
      walked_settings.append(setting.name)
    
    def _append_setting_name_and_end_group_walk_indicator(setting):
      walked_settings.append(f'{setting.name}_end')
    
    walk_callbacks = group_.GroupWalkCallbacks()
    walk_callbacks.on_visit_setting = _append_setting_name
    walk_callbacks.on_visit_group = _append_setting_name
    walk_callbacks.on_end_group_walk = _append_setting_name_and_end_group_walk_indicator
    
    return walked_settings, walk_callbacks


class TestGroupGui(unittest.TestCase):
  
  def setUp(self):
    self.settings = group_.Group('main')
    self.settings.add([
      {
        'type': 'stub_with_gui',
        'name': 'file_extension',
        'default_value': 'bmp',
      },
      {
        'type': 'stub_with_gui',
        'name': 'flatten',
        'default_value': False,
      },
    ])
  
  def test_initialize_gui(self):
    self.settings.initialize_gui()
    
    self.assertIs(
      type(self.settings['file_extension'].gui),
      stubs_setting.CheckButtonStubPresenter)
    self.assertIs(
      type(self.settings['file_extension'].gui.widget),
      stubs_setting.CheckButtonStub)
    self.assertIs(
      type(self.settings['flatten'].gui),
      stubs_setting.CheckButtonStubPresenter)
    self.assertIs(
      type(self.settings['flatten'].gui.widget),
      stubs_setting.CheckButtonStub)

  def test_initialize_gui_ignores_specified_settings(self):
    self.settings['flatten'].tags.add('ignore_initialize_gui')
    self.settings.initialize_gui()
    
    self.assertIs(
      type(self.settings['file_extension'].gui),
      stubs_setting.CheckButtonStubPresenter)
    self.assertIs(
      type(self.settings['flatten'].gui),
      presenter_.NullPresenter)
  
  def test_initialize_gui_with_custom_gui(self):
    file_extension_widget = stubs_setting.GuiWidgetStub('png')
    
    self.settings.initialize_gui(custom_gui={
      'file_extension': dict(gui_type=stubs_setting.StubPresenter, widget=file_extension_widget)})
    
    self.assertIs(
      type(self.settings['file_extension'].gui), stubs_setting.StubPresenter)
    self.assertIs(
      type(self.settings['file_extension'].gui.widget),
      stubs_setting.GuiWidgetStub)
    # The expected value is 'bmp', not 'png', since the setting value overrides
    # the initial GUI widget value.
    self.assertEqual(file_extension_widget.value, 'bmp')
    self.assertIs(
      type(self.settings['flatten'].gui),
      stubs_setting.CheckButtonStubPresenter)
    self.assertIs(
      type(self.settings['flatten'].gui.widget),
      stubs_setting.CheckButtonStub)

  def test_initialize_gui_with_global_arguments(self):
    self.settings['file_extension'].gui.set_visible(False)

    self.settings.initialize_gui(
      copy_previous_visible=True,
    )

    self.assertFalse(self.settings['file_extension'].gui.get_visible())

  def test_initialize_gui_custom_gui_arguments_override_global_arguments(self):
    self.settings['file_extension'].gui.set_visible(False)

    file_extension_widget = stubs_setting.GuiWidgetStub('png')

    self.settings.initialize_gui(
      custom_gui={
        'file_extension': dict(
          gui_type=stubs_setting.StubPresenter,
          widget=file_extension_widget,
          copy_previous_visible=False,
        )},
      copy_previous_visible=True,
    )

    self.assertTrue(self.settings['file_extension'].gui.get_visible())

  def test_apply_gui_values_to_settings(self):
    file_extension_widget = stubs_setting.GuiWidgetStub(None)
    flatten_widget = stubs_setting.GuiWidgetStub(None)
    self.settings['file_extension'].set_gui(stubs_setting.StubPresenter, file_extension_widget)
    self.settings['flatten'].set_gui(stubs_setting.StubPresenter, flatten_widget)
    
    file_extension_widget.set_value('gif')
    flatten_widget.set_value(True)
    
    self.settings.apply_gui_values_to_settings()
    
    self.assertEqual(self.settings['file_extension'].value, 'gif')
    self.assertEqual(self.settings['flatten'].value, True)
