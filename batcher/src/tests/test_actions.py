import unittest
import unittest.mock as mock

import parameterized

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import actions as actions_


test_procedures = [
  {
    'name': 'autocrop',
    'type': 'procedure',
    'function': '',
    'enabled': True,
    'display_name': 'Autocrop',
    'action_groups': ['basic'],
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
    'type': 'procedure',
    'function': '',
    'enabled': False,
    'display_name': 'Autocrop background layers',
  },
  {
    'name': 'autocrop_foreground',
    'type': 'procedure',
    'function': '',
    'enabled': False,
    'display_name': 'Autocrop foreground layers',
  },
]

test_constraints = [
  {
    'name': 'layers',
    'type': 'constraint',
    'function': '',
    'enabled': True,
    'display_name': 'Layers',
  },
  {
    'name': 'visible',
    'type': 'constraint',
    'function': '',
    'enabled': False,
    'display_name': 'Visible',
  },
]


def get_action_data(actions_list):
  return {
    action_dict['name']: dict(action_dict)
    for action_dict in actions_list}


class TestCreateActions(unittest.TestCase):
  
  def test_create(self):
    actions = actions_.create('procedures')
    
    self.assertEqual(len(actions), 0)
  
  @parameterized.parameterized.expand([
    ('procedure_with_default_group',
     'procedures',
     test_procedures,
     'autocrop_background',
     ['action', 'procedure'],
     {'action_groups': [actions_.DEFAULT_PROCEDURES_GROUP]}),
    
    ('procedure_with_custom_group',
     'procedures',
     test_procedures,
     'autocrop',
     ['action', 'procedure'],
     {'action_groups': ['basic']}),
    
    ('constraint',
     'constraints',
     test_constraints,
     'visible',
     ['action', 'constraint'],
     {'action_groups': [actions_.DEFAULT_CONSTRAINTS_GROUP]}),
  ])
  def test_create_initial_actions_are_added(
        self,
        test_case_suffix,
        name,
        test_actions_list,
        initial_action_name,
        tags,
        additional_action_attributes):
    initial_action_dict = get_action_data(test_actions_list)[initial_action_name]
    
    actions = actions_.create(name, [initial_action_dict])
    
    self.assertIn(initial_action_dict['name'], actions)
    
    self.assertSetEqual(actions[initial_action_name].tags, set(tags))
    
    for attribute_name, value in additional_action_attributes.items():
      self.assertEqual(actions[initial_action_name][attribute_name].value, value)
    
    self.assertNotIn('type', actions[initial_action_name])
  
  def test_create_initial_action_with_invalid_type_raises_error(self):
    initial_action_dict = get_action_data(test_procedures)['autocrop']
    initial_action_dict['type'] = 'invalid_type'
    
    with self.assertRaises(ValueError):
      actions_.create('procedures', [initial_action_dict])
  
  def test_create_missing_name_raises_error(self):
    initial_action_dict = get_action_data(test_procedures)['autocrop']
    del initial_action_dict['name']
    
    with self.assertRaises(ValueError):
      actions_.create('procedures', [initial_action_dict])


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
  return_value=pg.tests.stubs_gimp.PdbStub,
)
class TestManageActions(unittest.TestCase):
  
  def setUp(self):
    self.test_procedures = get_action_data(test_procedures)
    self.autocrop_dict = self.test_procedures['autocrop']
    self.procedures = actions_.create('procedures')
    
    self.expected_dict = dict({'orig_name': 'autocrop'}, **self.autocrop_dict)
  
  def test_add(self, mock_get_pdb):
    action = actions_.add(self.procedures, self.autocrop_dict)
    
    self.assertEqual(len(self.procedures), 1)
    self.assertEqual(action, self.procedures['autocrop'])
  
  def test_add_passing_invalid_object_raises_error(self, mock_get_pdb):
    with self.assertRaises(TypeError):
      actions_.add(self.procedures, 'invalid_object')
  
  def test_add_existing_name_is_uniquified(self, mock_get_pdb):
    added_actions = [
      actions_.add(self.procedures, self.autocrop_dict) for _unused in range(3)]
    
    orig_name = 'autocrop'
    expected_names = ['autocrop', 'autocrop_2', 'autocrop_3']
    expected_display_names = ['Autocrop', 'Autocrop (2)', 'Autocrop (3)']
    
    for action, expected_name, expected_display_name in zip(
          added_actions, expected_names, expected_display_names):
      self.assertEqual(action, self.procedures[expected_name])
      self.assertEqual(
        self.procedures[f'{expected_name}/display_name'].value, expected_display_name)
      self.assertEqual(
        self.procedures[f'{expected_name}/orig_name'].value, orig_name)
    
    self.assertEqual(len(self.procedures), 3)
  
  def test_add_invokes_before_add_action_event(self, mock_get_pdb):
    invoked_event_args = []
    
    def on_before_add_action(actions, action_dict):
      invoked_event_args.append((actions, action_dict))
      self.assertNotIn('autocrop', self.procedures)
    
    self.procedures.connect_event('before-add-action', on_before_add_action)
    
    actions_.add(self.procedures, self.autocrop_dict)
    
    self.assertIs(invoked_event_args[0][0], self.procedures)
    self.assertDictEqual(invoked_event_args[0][1], self.expected_dict)
    self.assertIsNot(invoked_event_args[0][1], self.autocrop_dict)
  
  @parameterized.parameterized.expand([
    ('',
     ['autocrop'],),
    
    ('and_passes_original_action_dict',
     ['autocrop', 'autocrop'],),
  ])
  def test_add_invokes_after_add_action_event(
        self, mock_get_pdb, test_case_suffix, action_names_to_add):
    invoked_event_args = []
    
    def on_after_add_action(actions, action, orig_action_dict):
      invoked_event_args.append((actions, action, orig_action_dict))
    
    self.procedures.connect_event('after-add-action', on_after_add_action)
    
    for action_name in action_names_to_add:
      action = actions_.add(self.procedures, self.test_procedures[action_name])
      
      self.assertIs(invoked_event_args[-1][0], self.procedures)
      self.assertIs(invoked_event_args[-1][1], action)
      self.assertDictEqual(invoked_event_args[-1][2], self.autocrop_dict)
      self.assertIsNot(invoked_event_args[-1][2], self.autocrop_dict)
  
  def test_add_modifying_added_action_modifies_nothing_else(self, mock_get_pdb):
    action = actions_.add(self.procedures, self.autocrop_dict)
    action['enabled'].set_value(False)
    action['arguments/offset_x'].set_value(20)
    action['arguments/offset_y'].set_value(10)
    
    self.assertNotEqual(action['enabled'], self.autocrop_dict['enabled'])
    self.assertNotEqual(action['arguments/offset_x'], self.autocrop_dict['arguments'][0])
    self.assertNotEqual(action['arguments/offset_y'], self.autocrop_dict['arguments'][1])
  
  @parameterized.parameterized.expand([
    ('first',
     'autocrop', 0),
    
    ('middle',
     'autocrop_background', 1),
    
    ('last',
     'autocrop_foreground', 2),
    
    ('nonexistent_action',
     'some_action', None),
  ])
  def test_get_index(
        self,
        mock_get_pdb,
        test_case_suffix,
        action_name,
        expected_position):
    for action_dict in self.test_procedures.values():
      actions_.add(self.procedures, action_dict)
    
    self.assertEqual(actions_.get_index(self.procedures, action_name), expected_position)
  
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
        mock_get_pdb,
        test_case_suffix,
        action_name,
        new_position,
        expected_ordered_action_names):
    for action_dict in self.test_procedures.values():
      actions_.add(self.procedures, action_dict)
    
    actions_.reorder(self.procedures, action_name, new_position)
    
    self.assertEqual([action.name for action in self.procedures], expected_ordered_action_names)
  
  def test_reorder_nonexisting_action_name(self, mock_get_pdb):
    with self.assertRaises(ValueError):
      actions_.reorder(self.procedures, 'invalid_action', 0)
  
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
        mock_get_pdb,
        test_case_suffix,
        action_names_to_add,
        names_to_remove,
        names_to_keep):
    for action_name in action_names_to_add:
      actions_.add(self.procedures, self.test_procedures[action_name])
    
    for action_name in names_to_remove:
      actions_.remove(self.procedures, action_name)
      
      self.assertNotIn(action_name, self.procedures)
    
    for action_name in names_to_keep:
      self.assertIn(action_name, self.procedures)
    
    self.assertEqual(len(self.procedures), len(names_to_keep))
  
  def test_remove_nonexisting_action_name(self, mock_get_pdb):
    with self.assertRaises(ValueError):
      actions_.remove(self.procedures, 'invalid_action')
  
  def test_clear(self, mock_get_pdb):
    for action_dict in self.test_procedures.values():
      actions_.add(self.procedures, action_dict)
    
    actions_.clear(self.procedures)
    
    self.assertFalse(self.procedures)
    self.assertTrue(self.test_procedures)
  
  def test_clear_resets_to_initial_actions(self, mock_get_pdb):
    procedures = actions_.create('procedures', [self.autocrop_dict])
    
    actions_.add(procedures, self.test_procedures['autocrop_background'])
    actions_.clear(procedures)
    
    self.assertEqual(len(procedures), 1)
    self.assertIn('autocrop', procedures)
    self.assertNotIn('autocrop_background', procedures)
  
  def test_clear_triggers_events(self, mock_get_pdb):
    procedures = actions_.create('procedures', [self.autocrop_dict])
    
    for action_name in ['autocrop_background', 'autocrop_foreground']:
      actions_.add(procedures, self.test_procedures[action_name])
    
    before_add_action_list = []
    after_add_action_list = []
    
    procedures.connect_event(
      'before-add-action', lambda group, dict_: before_add_action_list.append(dict_))
    procedures.connect_event(
      'after-add-action', lambda group, action, dict_: after_add_action_list.append(dict_))
    
    actions_.clear(procedures, add_initial_actions=True)
    
    self.assertEqual(len(before_add_action_list), 1)
    self.assertEqual(before_add_action_list[0]['name'], 'autocrop')
    self.assertEqual(len(after_add_action_list), 1)
    self.assertEqual(after_add_action_list[0]['name'], 'autocrop')


class TestWalkActions(unittest.TestCase):
  
  def setUp(self):
    self.test_procedures = get_action_data(test_procedures)
    self.test_constraints = get_action_data(test_constraints)
    self.actions = actions_.create('actions')
  
  @parameterized.parameterized.expand([
    ('all_types_entire_actions',
     None,
     None,
     ['autocrop',
      'autocrop_background',
      'autocrop_foreground',
      'layers',
      'visible']),
    
    ('specific_type_entire_actions',
     'procedure',
     None,
     ['autocrop',
      'autocrop_background',
      'autocrop_foreground']),
    
    ('all_types_specific_setting',
     None,
     'enabled',
     ['autocrop/enabled',
      'autocrop_background/enabled',
      'autocrop_foreground/enabled',
      'layers/enabled',
      'visible/enabled']),
    
    ('specific_types_specific_setting',
     'procedure',
     'enabled',
     ['autocrop/enabled',
      'autocrop_background/enabled',
      'autocrop_foreground/enabled']),
    
    ('nonexistent_setting',
     None,
     'nonexistent_setting',
     []),
  ])
  def test_walk(
        self,
        test_case_suffix,
        action_type,
        setting_name,
        expected_setting_paths):
    for action_dict in self.test_procedures.values():
      actions_.add(self.actions, action_dict)
    
    for action_dict in self.test_constraints.values():
      actions_.add(self.actions, action_dict)
    
    self.assertListEqual(
      list(actions_.walk(self.actions, action_type, setting_name)),
      [self.actions[path] for path in expected_setting_paths])
  
  @parameterized.parameterized.expand([
    ('reorder_first',
     [('autocrop', 1)],
     ['autocrop_background',
      'autocrop',
      'autocrop_foreground']),
    
    ('reorder_middle',
     [('autocrop_background', 0)],
     ['autocrop_background',
      'autocrop',
      'autocrop_foreground']),
    
    ('reorder_last',
     [('autocrop_foreground', 1)],
     ['autocrop',
      'autocrop_foreground',
      'autocrop_background']),
  ])
  def test_walk_after_reordering(
        self,
        test_case_suffix,
        actions_to_reorder,
        expected_setting_paths):
    for action_dict in self.test_procedures.values():
      actions_.add(self.actions, action_dict)
    
    for action_name, new_position in actions_to_reorder:
      actions_.reorder(self.actions, action_name, new_position)
    
    self.assertListEqual(
      list(actions_.walk(self.actions)),
      [self.actions[path] for path in expected_setting_paths])


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestLoadSaveActions(unittest.TestCase):
  
  def setUp(self):
    self.test_procedures = get_action_data(test_procedures)
    self.procedures = actions_.create('procedures')

    pg.setting.GimpSessionSource._SESSION_DATA = {}
  
  @parameterized.parameterized.expand([
    ('', False),
    ('with_explicit_clearing', True),
  ])
  def test_save_load_actions(self, test_case_suffix, remove_before_load, mock_gimp_module):
    for action_dict in self.test_procedures.values():
      actions_.add(self.procedures, action_dict)
    
    self.procedures['autocrop_background/enabled'].set_value(True)
    self.procedures['autocrop_background/action_groups'].set_value(
      ['background'])
    self.procedures['autocrop_foreground/enabled'].set_value(True)
    self.procedures['autocrop_foreground/action_groups'].set_value(
      ['foreground'])
    self.procedures['autocrop/arguments/offset_x'].set_value(20)
    self.procedures['autocrop/arguments/offset_y'].set_value(10)
    
    self.procedures.save()
    
    if remove_before_load:
      self.procedures.remove([child.name for child in self.procedures])
    
    self.procedures.load()
    
    self.assertEqual(len(self.procedures), len(self.test_procedures))
    self.assertListEqual(
      list(self.test_procedures.keys()), [child.name for child in self.procedures])
    
    self.assertEqual(
      self.procedures['autocrop_background/enabled'].value, True)
    self.assertEqual(
      self.procedures['autocrop_background/action_groups'].value, ['background'])
    self.assertEqual(
      self.procedures['autocrop_foreground/enabled'].value, True)
    self.assertEqual(
      self.procedures['autocrop_foreground/action_groups'].value, ['foreground'])
    self.assertEqual(self.procedures['autocrop/arguments/offset_x'].value, 20)
    self.assertEqual(self.procedures['autocrop/arguments/offset_y'].value, 10)
  
  def test_save_load_actions_preserves_uniquified_names_after_load(self, mock_gimp_module):
    input_names = ['autocrop', 'autocrop', 'autocrop_background', 'autocrop_foreground']
    expected_names = ['autocrop', 'autocrop_2', 'autocrop_background', 'autocrop_foreground']
    
    for action_name in input_names:
      actions_.add(self.procedures, self.test_procedures[action_name])
    
    self.procedures.save()
    
    self.procedures.remove([child.name for child in self.procedures])
    
    self.procedures.load()
    
    self.assertEqual(len(self.procedures), len(input_names))
    self.assertListEqual(expected_names, [child.name for child in self.procedures])
  
  def test_load_with_no_saved_actions(self, mock_gimp_module):
    procedures = actions_.create('procedures', [self.test_procedures['autocrop']])
    
    for action_name in ['autocrop_background', 'autocrop_foreground']:
      actions_.add(procedures, self.test_procedures[action_name])
    
    procedures.load()
    
    self.assertEqual(len(procedures), 0)
  
  def test_load_initial_actions(self, mock_gimp_module):
    procedures = actions_.create('procedures', [self.test_procedures['autocrop']])
    
    procedures.save()
    procedures.load()
    
    self.assertEqual(len(procedures), 1)
    self.assertIn('autocrop', procedures)
  
  def test_load_overrides_initial_actions(self, mock_gimp_module):
    procedures = actions_.create('procedures', [self.test_procedures['autocrop']])
    
    for action_name in ['autocrop_background', 'autocrop_foreground']:
      actions_.add(procedures, self.test_procedures[action_name])
    
    actions_.remove(procedures, 'autocrop')
    
    procedures.save()
    procedures.load()
    
    self.assertEqual(len(procedures), 2)
    self.assertNotIn('autocrop', procedures)
    self.assertIn('autocrop_background', procedures)
    self.assertIn('autocrop_foreground', procedures)
  
  def test_load_triggers_after_add_action_events(self, mock_gimp_module):
    procedures = actions_.create('procedures')
    
    for action_name in ['autocrop_background', 'autocrop_foreground']:
      actions_.add(procedures, self.test_procedures[action_name])
    
    after_add_action_list = []
    
    procedures.connect_event(
      'after-add-action',
      lambda group, action, dict_: after_add_action_list.append((action, dict_)))
    
    procedures.save()
    procedures.load()
    
    self.assertEqual(len(after_add_action_list), 2)
    self.assertIn(after_add_action_list[0][0].name, 'autocrop_background')
    self.assertIsNone(after_add_action_list[0][1])
    self.assertIn(after_add_action_list[1][0].name, 'autocrop_foreground')
    self.assertIsNone(after_add_action_list[1][1])


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
  return_value=pg.tests.stubs_gimp.PdbStub,
)
class TestManagePdbProceduresAsActions(unittest.TestCase):
  
  def setUp(self):
    self.procedures = actions_.create('procedures')

    self.procedure_name = 'file-png-save'

    self.procedure_stub = stubs_gimp.PdbProcedureStub(
      name=self.procedure_name,
      proc_type=Gimp.PDBProcType.PLUGIN,
      arguments_spec=[
        dict(value_type=Gimp.RunMode.__gtype__, name='run-mode', blurb='The run mode'),
        dict(value_type=GObject.TYPE_INT, name='num-save-options', blurb='Number of save options'),
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

    actions_.pdb.remove_from_cache(self.procedure_name)
    stubs_gimp.PdbStub.add_procedure(self.procedure_stub)
  
  def test_add_pdb_procedure(self, mock_get_pdb):
    action = actions_.add(self.procedures, self.procedure_name)
    
    self.assertIn('file-png-save', self.procedures)
    
    self.assertEqual(action.name, 'file-png-save')
    self.assertEqual(action['function'].value, 'file-png-save')
    self.assertTrue(action['origin'].is_item('gimp_pdb'))
    self.assertEqual(action['enabled'].value, True)
    self.assertEqual(action['display_name'].value, 'Save as PNG')
    self.assertEqual(action['action_groups'].value, [actions_.DEFAULT_PROCEDURES_GROUP])
    
    self.assertEqual(action['arguments/run-mode'].gui.get_visible(), False)

    self.assertNotIn('num-save-options', action['arguments'])

    self.assertEqual(action['arguments/run-mode'].value, Gimp.RunMode.NONINTERACTIVE)
    self.assertEqual(action['arguments/save-options'].value, ())
    self.assertEqual(action['arguments/filename'].value, 'some_file')
    self.assertEqual(action['arguments/filename'].default_value, 'some_file')

  @mock.patch(
    f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
    new_callable=stubs_gimp.GimpModuleStub)
  def test_load_save_pdb_procedure_as_action(self, mock_gimp_module, mock_get_pdb):
    action = actions_.add(self.procedures, self.procedure_name)
    
    action['enabled'].set_value(False)
    action['arguments/filename'].set_value('image.png')
    
    self.procedures.save()
    self.procedures.load()
    
    self.assertEqual(action.name, 'file-png-save')
    self.assertEqual(action['function'].value, 'file-png-save')
    self.assertTrue(action['origin'].is_item('gimp_pdb'))
    self.assertEqual(action['enabled'].value, False)
    self.assertEqual(action['arguments/filename'].value, 'image.png')


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
  return_value=pg.tests.stubs_gimp.PdbStub,
)
class TestGetActionDictAsPdbProcedure(unittest.TestCase):

  @mock.patch(
    f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
    return_value=pg.tests.stubs_gimp.PdbStub,
  )
  def setUp(self, mock_get_pdb):
    self.procedure_name = 'file-png-save'

    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(value_type=Gimp.RunMode.__gtype__, name='run-mode', blurb='The run mode'),
        dict(value_type=GObject.TYPE_INT, name='num-save-options', blurb='Number of save options'),
        dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='Save options'),
        dict(
          value_type=GObject.TYPE_STRING, name='filename', blurb='Filename to save the image in')],
      blurb='Saves files in PNG file format')

    actions_.pdb.remove_from_cache(self.procedure_name)
  
  def test_with_non_unique_param_names(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='More save options'),
      dict(value_type=GObject.TYPE_STRING, name='filename', blurb='Another filename'),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    action_dict = actions_.get_action_dict_for_pdb_procedure(extended_procedure_stub.get_name())
    
    self.assertListEqual(
      [argument_dict['name'] for argument_dict in action_dict['arguments']],
      ['run-mode',
       'num-save-options',
       'save-options',
       'filename',
       'save-options-2',
       'filename-2'])
  
  def test_unsupported_pdb_param_type(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type='unsupported', name='param-with-unsupported-type', blurb=''),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    with self.assertRaises(actions_.UnsupportedPdbProcedureError):
      actions_.get_action_dict_for_pdb_procedure(extended_procedure_stub.get_name())
  
  def test_default_run_mode_is_noninteractive(self, mock_get_pdb):
    self.procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(self.procedure_stub)

    action_dict = actions_.get_action_dict_for_pdb_procedure(self.procedure_name)

    self.assertEqual(action_dict['arguments'][0]['default_value'], Gimp.RunMode.NONINTERACTIVE)
  
  def test_gimp_object_types_are_replaced_with_placeholders(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type=Gimp.Image.__gtype__, name='image', blurb='The image'),
      dict(value_type=Gimp.Layer.__gtype__, name='layer', blurb='The layer to process'),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)
    
    action_dict = actions_.get_action_dict_for_pdb_procedure(self.procedure_name)
    
    self.assertEqual(action_dict['arguments'][-2]['type'], 'placeholder_image')
    self.assertEqual(action_dict['arguments'][-1]['type'], 'placeholder_layer')
