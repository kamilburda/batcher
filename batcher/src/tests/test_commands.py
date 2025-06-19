import unittest
import unittest.mock as mock

import parameterized

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import commands as commands_

from src.tests import stubs_gimp


test_actions = [
  {
    'name': 'autocrop',
    'type': 'action',
    'function': '',
    'enabled': True,
    'display_name': 'Autocrop',
    'command_groups': ['basic'],
    'arguments': [
      {
        'type': 'int',
        'name': 'offset_x',
        'default_value': 0,
      },
      {
        'type': 'int',
        'name': 'offset_y',
        'default_value': 0,
      },
    ],
  },
  {
    'name': 'autocrop_background',
    'type': 'action',
    'function': '',
    'enabled': False,
    'display_name': 'Autocrop background layers',
  },
  {
    'name': 'autocrop_foreground',
    'type': 'action',
    'function': '',
    'enabled': False,
    'display_name': 'Autocrop foreground layers',
  },
]

test_conditions = [
  {
    'name': 'layers',
    'type': 'condition',
    'function': '',
    'enabled': True,
    'display_name': 'Layers',
  },
  {
    'name': 'visible',
    'type': 'condition',
    'function': '',
    'enabled': False,
    'display_name': 'Visible',
  },
]


def get_command_data(commands_list):
  return {
    command_dict['name']: dict(command_dict)
    for command_dict in commands_list}


class TestCreateCommands(unittest.TestCase):
  
  def test_create(self):
    commands = commands_.create('actions')
    
    self.assertEqual(len(commands), 0)
  
  @parameterized.parameterized.expand([
    ('action_with_default_group',
     'actions',
     test_actions,
     'autocrop_background',
     ['command', 'action'],
     {'command_groups': [commands_.DEFAULT_ACTIONS_GROUP]}),
    
    ('action_with_custom_group',
     'actions',
     test_actions,
     'autocrop',
     ['command', 'action'],
     {'command_groups': ['basic']}),
    
    ('condition',
     'conditions',
     test_conditions,
     'visible',
     ['command', 'condition'],
     {'command_groups': [commands_.DEFAULT_CONDITIONS_GROUP]}),
  ])
  def test_create_initial_commands_are_added(
        self,
        _test_case_suffix,
        name,
        test_commands_list,
        initial_command_name,
        tags,
        additional_command_attributes):
    initial_command_dict = get_command_data(test_commands_list)[initial_command_name]
    
    commands = commands_.create(name, [initial_command_dict])
    
    self.assertIn(initial_command_dict['name'], commands)
    
    self.assertSetEqual(commands[initial_command_name].tags, set(tags))
    
    for attribute_name, value in additional_command_attributes.items():
      self.assertEqual(commands[initial_command_name][attribute_name].value, value)
    
    self.assertNotIn('type', commands[initial_command_name])
  
  def test_create_initial_command_with_invalid_type_raises_error(self):
    initial_command_dict = get_command_data(test_actions)['autocrop']
    initial_command_dict['type'] = 'invalid_type'
    
    with self.assertRaises(ValueError):
      commands_.create('actions', [initial_command_dict])
  
  def test_create_missing_name_raises_error(self):
    initial_command_dict = get_command_data(test_actions)['autocrop']
    del initial_command_dict['name']
    
    with self.assertRaises(ValueError):
      commands_.create('actions', [initial_command_dict])


@mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
class TestManageCommands(unittest.TestCase):
  
  def setUp(self):
    self.test_actions = get_command_data(test_actions)
    self.autocrop_dict = self.test_actions['autocrop']
    self.actions = commands_.create('actions')
    
    self.expected_dict = dict({'orig_name': 'autocrop'}, **self.autocrop_dict)
  
  def test_add_command_as_dict(self, _mock_get_pdb):
    command = commands_.add(self.actions, self.autocrop_dict)
    
    self.assertEqual(len(self.actions), 1)
    self.assertEqual(command, self.actions['autocrop'])

  def test_add_command_as_instance(self, _mock_get_pdb):
    autocrop_command = commands_.create_command(self.autocrop_dict)

    commands_.add(self.actions, autocrop_command)

    self.assertEqual(len(self.actions), 1)
    self.assertEqual(autocrop_command, self.actions['autocrop'])

  def test_add_command_as_instance_with_the_same_name(self, _mock_get_pdb):
    autocrop_command = commands_.create_command(self.autocrop_dict)
    autocrop_command_2 = commands_.create_command(self.autocrop_dict)

    commands_.add(self.actions, autocrop_command)
    commands_.add(self.actions, autocrop_command_2)

    self.assertEqual(len(self.actions), 2)
    self.assertEqual(autocrop_command, self.actions['autocrop'])
    self.assertEqual(autocrop_command_2, self.actions['autocrop_2'])
    self.assertEqual(autocrop_command['display_name'].value, 'Autocrop')
    self.assertEqual(autocrop_command_2['display_name'].value, 'Autocrop (2)')

  def test_add_passing_invalid_object_raises_error(self, _mock_get_pdb):
    with self.assertRaises(TypeError):
      commands_.add(self.actions, 'invalid_object')
  
  def test_add_existing_name_is_uniquified(self, _mock_get_pdb):
    added_commands = [
      commands_.add(self.actions, self.autocrop_dict) for _unused in range(3)]
    
    orig_name = 'autocrop'
    expected_names = ['autocrop', 'autocrop_2', 'autocrop_3']
    expected_display_names = ['Autocrop', 'Autocrop (2)', 'Autocrop (3)']
    
    for command, expected_name, expected_display_name in zip(
          added_commands, expected_names, expected_display_names):
      self.assertEqual(command, self.actions[expected_name])
      self.assertEqual(
        self.actions[f'{expected_name}/display_name'].value, expected_display_name)
      self.assertEqual(
        self.actions[f'{expected_name}/orig_name'].value, orig_name)
    
    self.assertEqual(len(self.actions), 3)
  
  def test_add_invokes_before_add_command_event(self, _mock_get_pdb):
    invoked_event_args = []
    
    def on_before_add_command(commands, command_dict):
      invoked_event_args.append((commands, command_dict))
      self.assertNotIn('autocrop', self.actions)
    
    self.actions.connect_event('before-add-command', on_before_add_command)
    
    commands_.add(self.actions, self.autocrop_dict)

    self.assertIs(invoked_event_args[0][0], self.actions)
    self.assertDictEqual(invoked_event_args[0][1], self.expected_dict)
    self.assertIsNot(invoked_event_args[0][1], self.autocrop_dict)
  
  @parameterized.parameterized.expand([
    ('',
     ['autocrop'],),
    
    ('and_passes_original_command_dict',
     ['autocrop', 'autocrop'],),
  ])
  def test_add_invokes_after_add_command_event(
        self, _mock_get_pdb, _test_case_suffix, command_names_to_add):
    invoked_event_args = []
    
    def on_after_add_command(commands, command_, orig_command_dict):
      invoked_event_args.append((commands, command_, orig_command_dict))
    
    self.actions.connect_event('after-add-command', on_after_add_command)
    
    for command_name in command_names_to_add:
      command = commands_.add(self.actions, self.test_actions[command_name])
      
      self.assertIs(invoked_event_args[-1][0], self.actions)
      self.assertIs(invoked_event_args[-1][1], command)
      self.assertDictEqual(invoked_event_args[-1][2], self.expected_dict)
      self.assertIsNot(invoked_event_args[-1][2], self.autocrop_dict)
  
  def test_add_modifying_added_command_modifies_nothing_else(self, _mock_get_pdb):
    command = commands_.add(self.actions, self.autocrop_dict)
    command['enabled'].set_value(False)
    command['arguments/offset_x'].set_value(20)
    command['arguments/offset_y'].set_value(10)
    
    self.assertNotEqual(command['enabled'], self.autocrop_dict['enabled'])
    self.assertNotEqual(command['arguments/offset_x'], self.autocrop_dict['arguments'][0])
    self.assertNotEqual(command['arguments/offset_y'], self.autocrop_dict['arguments'][1])
  
  @parameterized.parameterized.expand([
    ('first',
     'autocrop', 0),
    
    ('middle',
     'autocrop_background', 1),
    
    ('last',
     'autocrop_foreground', 2),
    
    ('nonexistent_command',
     'some_command', None),
  ])
  def test_get_index(
        self,
        _mock_get_pdb,
        _test_case_suffix,
        command_name,
        expected_position):
    for command_dict in self.test_actions.values():
      commands_.add(self.actions, command_dict)
    
    self.assertEqual(commands_.get_index(self.actions, command_name), expected_position)
  
  @parameterized.parameterized.expand([
    ('middle_to_first',
     'autocrop_background',
     0,
     ['autocrop_background', 'autocrop', 'autocrop_foreground']),
    
    ('middle_to_last',
     'autocrop_background',
     2,
     ['autocrop', 'autocrop_foreground', 'autocrop_background']),
    
    ('middle_to_last_above_bounds',
     'autocrop_background',
     3,
     ['autocrop', 'autocrop_foreground', 'autocrop_background']),
    
    ('first_to_middle',
     'autocrop',
     1,
     ['autocrop_background', 'autocrop', 'autocrop_foreground']),
    
    ('last_to_middle',
     'autocrop_foreground',
     1,
     ['autocrop', 'autocrop_foreground', 'autocrop_background']),
    
    ('middle_to_last_negative_position',
     'autocrop_background',
     -1,
     ['autocrop', 'autocrop_foreground', 'autocrop_background']),
    
    ('middle_to_middle_negative_position',
     'autocrop_background',
     -2,
     ['autocrop', 'autocrop_background', 'autocrop_foreground']),
  ])
  def test_reorder(
        self,
        _mock_get_pdb,
        _test_case_suffix,
        command_name,
        new_position,
        expected_ordered_command_names):
    for command_dict in self.test_actions.values():
      commands_.add(self.actions, command_dict)
    
    commands_.reorder(self.actions, command_name, new_position)
    
    self.assertEqual([command.name for command in self.actions], expected_ordered_command_names)
  
  def test_reorder_nonexistent_command_name(self, _mock_get_pdb):
    with self.assertRaises(ValueError):
      commands_.reorder(self.actions, 'invalid_command', 0)
  
  @parameterized.parameterized.expand([
    ('single_setting',
     ['autocrop', 'autocrop_background', 'autocrop_foreground'],
     ['autocrop'],
     ['autocrop_background', 'autocrop_foreground']),
    
    ('setting_added_twice_removed_both',
     ['autocrop', 'autocrop', 'autocrop_background', 'autocrop_foreground'],
     ['autocrop', 'autocrop_2'],
     ['autocrop_background', 'autocrop_foreground']),
    
    ('setting_added_twice_removed_first',
     ['autocrop', 'autocrop', 'autocrop_background', 'autocrop_foreground'],
     ['autocrop'],
     ['autocrop_background', 'autocrop_2', 'autocrop_foreground']),
  ])
  def test_remove(
        self,
        _mock_get_pdb,
        _test_case_suffix,
        command_names_to_add,
        names_to_remove,
        names_to_keep):
    for command_name in command_names_to_add:
      commands_.add(self.actions, self.test_actions[command_name])
    
    for command_name in names_to_remove:
      commands_.remove(self.actions, command_name)
      
      self.assertNotIn(command_name, self.actions)
    
    for command_name in names_to_keep:
      self.assertIn(command_name, self.actions)
    
    self.assertEqual(len(self.actions), len(names_to_keep))
  
  def test_remove_nonexistent_command_name(self, _mock_get_pdb):
    with self.assertRaises(ValueError):
      commands_.remove(self.actions, 'invalid_command')
  
  def test_clear(self, _mock_get_pdb):
    for command_dict in self.test_actions.values():
      commands_.add(self.actions, command_dict)
    
    commands_.clear(self.actions)
    
    self.assertFalse(self.actions)
    self.assertTrue(self.test_actions)
  
  def test_clear_resets_to_initial_commands(self, _mock_get_pdb):
    actions = commands_.create('actions', [self.autocrop_dict])
    
    commands_.add(actions, self.test_actions['autocrop_background'])
    commands_.clear(actions)
    
    self.assertEqual(len(actions), 1)
    self.assertIn('autocrop', actions)
    self.assertNotIn('autocrop_background', actions)
  
  def test_clear_triggers_events(self, _mock_get_pdb):
    actions = commands_.create('actions', [self.autocrop_dict])
    
    for command_name in ['autocrop_background', 'autocrop_foreground']:
      commands_.add(actions, self.test_actions[command_name])
    
    before_add_command_list = []
    after_add_command_list = []
    
    actions.connect_event(
      'before-add-command', lambda group, dict_: before_add_command_list.append(dict_))
    actions.connect_event(
      'after-add-command', lambda group, command, dict_: after_add_command_list.append(dict_))
    
    commands_.clear(actions, add_initial_commands=True)
    
    self.assertEqual(len(before_add_command_list), 1)
    self.assertEqual(before_add_command_list[0]['name'], 'autocrop')
    self.assertEqual(len(after_add_command_list), 1)
    self.assertEqual(after_add_command_list[0]['name'], 'autocrop')


@mock.patch('src.setting.sources.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestLoadSaveCommands(unittest.TestCase):
  
  def setUp(self):
    self.test_actions = get_command_data(test_actions)
    self.actions = commands_.create('actions')
  
  @parameterized.parameterized.expand([
    ('', False),
    ('with_explicit_clearing', True),
  ])
  def test_save_load_commands(self, _test_case_suffix, remove_before_load, _mock_gimp_module):
    for command_dict in self.test_actions.values():
      commands_.add(self.actions, command_dict)
    
    self.actions['autocrop_background/enabled'].set_value(True)
    self.actions['autocrop_background/command_groups'].set_value(
      ['background'])
    self.actions['autocrop_foreground/enabled'].set_value(True)
    self.actions['autocrop_foreground/command_groups'].set_value(
      ['foreground'])
    self.actions['autocrop/arguments/offset_x'].set_value(20)
    self.actions['autocrop/arguments/offset_y'].set_value(10)
    
    self.actions.save()
    
    if remove_before_load:
      self.actions.remove([child.name for child in self.actions])
    
    self.actions.load()
    
    self.assertEqual(len(self.actions), len(self.test_actions))
    self.assertListEqual(
      list(self.test_actions.keys()), [child.name for child in self.actions])
    
    self.assertEqual(
      self.actions['autocrop_background/enabled'].value, True)
    self.assertEqual(
      self.actions['autocrop_background/command_groups'].value, ['background'])
    self.assertEqual(
      self.actions['autocrop_foreground/enabled'].value, True)
    self.assertEqual(
      self.actions['autocrop_foreground/command_groups'].value, ['foreground'])
    self.assertEqual(self.actions['autocrop/arguments/offset_x'].value, 20)
    self.assertEqual(self.actions['autocrop/arguments/offset_y'].value, 10)
  
  def test_save_load_commands_preserves_uniquified_names_after_load(self, _mock_gimp_module):
    input_names = ['autocrop', 'autocrop', 'autocrop_background', 'autocrop_foreground']
    expected_names = ['autocrop', 'autocrop_2', 'autocrop_background', 'autocrop_foreground']
    
    for command_name in input_names:
      commands_.add(self.actions, self.test_actions[command_name])
    
    self.actions.save()
    
    self.actions.remove([child.name for child in self.actions])
    
    self.actions.load()
    
    self.assertEqual(len(self.actions), len(input_names))
    self.assertListEqual(expected_names, [child.name for child in self.actions])
  
  def test_load_with_no_saved_commands(self, _mock_gimp_module):
    actions = commands_.create('actions', [self.test_actions['autocrop']])
    
    for command_name in ['autocrop_background', 'autocrop_foreground']:
      commands_.add(actions, self.test_actions[command_name])
    
    actions.load()
    
    self.assertEqual(len(actions), 0)
  
  def test_load_initial_commands(self, _mock_gimp_module):
    actions = commands_.create('actions', [self.test_actions['autocrop']])
    
    actions.save()
    actions.load()
    
    self.assertEqual(len(actions), 1)
    self.assertIn('autocrop', actions)
  
  def test_load_overrides_initial_commands(self, _mock_gimp_module):
    actions = commands_.create('actions', [self.test_actions['autocrop']])
    
    for command_name in ['autocrop_background', 'autocrop_foreground']:
      commands_.add(actions, self.test_actions[command_name])
    
    commands_.remove(actions, 'autocrop')
    
    actions.save()
    actions.load()
    
    self.assertEqual(len(actions), 2)
    self.assertNotIn('autocrop', actions)
    self.assertIn('autocrop_background', actions)
    self.assertIn('autocrop_foreground', actions)
  
  def test_load_triggers_after_add_command_events(self, _mock_gimp_module):
    actions = commands_.create('actions')
    
    for command_name in ['autocrop_background', 'autocrop_foreground']:
      commands_.add(actions, self.test_actions[command_name])
    
    after_add_command_list = []
    
    actions.connect_event(
      'after-add-command',
      lambda group, command, dict_: after_add_command_list.append((command, dict_)))
    
    actions.save()
    actions.load()
    
    self.assertEqual(len(after_add_command_list), 2)
    self.assertIn(after_add_command_list[0][0].name, 'autocrop_background')
    self.assertIsNone(after_add_command_list[0][1])
    self.assertIn(after_add_command_list[1][0].name, 'autocrop_foreground')
    self.assertIsNone(after_add_command_list[1][1])


@mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
class TestManagePdbProceduresAsCommands(unittest.TestCase):
  
  def setUp(self):
    self.actions = commands_.create('actions')

    self.procedure_name = 'file-png-export'

    self.procedure_stub = stubs_gimp.Procedure(
      name=self.procedure_name,
      proc_type=Gimp.PDBProcType.PLUGIN,
      arguments_spec=[
        dict(
          value_type=Gimp.RunMode.__gtype__,
          name='run-mode',
          blurb='The run mode',
          default_value=Gimp.RunMode.NONINTERACTIVE),
        dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='Save options'),
        dict(
          value_type=GObject.TYPE_STRING,
          name='filename',
          blurb='Filename to save the image in',
          default_value='some_file'),
      ],
      blurb='Saves files in PNG file format',
      menu_label='Save as _PNG...',
    )

    commands_.pdb.remove_from_cache(self.procedure_name)
    stubs_gimp.PdbStub.add_procedure(self.procedure_stub)
  
  def test_add_pdb_procedure(self, _mock_get_pdb):
    command = commands_.add(self.actions, self.procedure_name)
    
    self.assertIn('file-png-export', self.actions)
    
    self.assertEqual(command.name, 'file-png-export')
    self.assertEqual(command['function'].value, 'file-png-export')
    self.assertEqual(command['origin'].value, 'gimp_pdb')
    self.assertEqual(command['enabled'].value, True)
    self.assertEqual(command['display_name'].value, 'Save as PNG')
    self.assertEqual(command['command_groups'].value, [commands_.DEFAULT_ACTIONS_GROUP])
    
    self.assertEqual(command['arguments/run-mode'].gui.get_visible(), False)

    self.assertEqual(command['arguments/run-mode'].value, Gimp.RunMode.NONINTERACTIVE)
    self.assertEqual(command['arguments/save-options'].value, ())
    self.assertEqual(command['arguments/filename'].value, 'some_file')
    self.assertEqual(command['arguments/filename'].default_value, 'some_file')

  @mock.patch('src.setting.sources.Gimp', new_callable=stubs_gimp.GimpModuleStub)
  def test_load_save_pdb_procedure_as_command(self, _mock_gimp_module, _mock_get_pdb):
    command = commands_.add(self.actions, self.procedure_name)
    
    command['enabled'].set_value(False)
    command['arguments/filename'].set_value('image.png')
    
    self.actions.save()
    self.actions.load()
    
    self.assertEqual(command.name, 'file-png-export')
    self.assertEqual(command['function'].value, 'file-png-export')
    self.assertEqual(command['origin'].value, 'gimp_pdb')
    self.assertEqual(command['enabled'].value, False)
    self.assertEqual(command['arguments/filename'].value, 'image.png')


@mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
class TestGetCommandDictFromPdbProcedure(unittest.TestCase):

  @mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
  def setUp(self, _mock_get_pdb):
    self.procedure_name = 'file-png-export'

    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(value_type=Gimp.RunMode.__gtype__, name='run-mode', blurb='The run mode'),
        dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='Save options'),
        dict(
          value_type=GObject.TYPE_STRING, name='filename', blurb='Filename to save the image in')],
      blurb='Saves files in PNG file format')

    commands_.pdb.remove_from_cache(self.procedure_name)
  
  def test_with_non_unique_param_names(self, _mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='Save options'),
      dict(value_type=GObject.TYPE_STRING, name='filename', blurb='Another filename'),
    ])

    extended_procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    command_dict = commands_.get_command_dict_from_pdb_procedure(extended_procedure_stub.get_name())

    self.assertEqual(command_dict['name'], self.procedure_name)
    self.assertEqual(command_dict['function'], self.procedure_name)
    
    self.assertListEqual(
      [argument_dict['name'] for argument_dict in command_dict['arguments']],
      ['run-mode',
       'save-options',
       'filename',
       'save-options-2',
       'filename-2'])
