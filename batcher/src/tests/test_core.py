import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib import pdb
from pygimplib.tests import stubs_gimp

from src import actions as actions_
from src import core
from src import builtin_procedures
from src import settings_main
from src import utils as utils_


class TestBatcherInitialActions(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.image = Gimp.Image.new(1, 1, Gimp.ImageBaseType.RGB)
  
  @classmethod
  def tearDownClass(cls):
    pdb.gimp_image_delete(cls.image)
  
  def test_add_procedure_added_procedure_is_first_in_action_list(self):
    settings = settings_main.create_settings()
    settings['special/image'].set_value(self.image)
    settings['main/file_extension'].set_value('xcf')
    
    batcher = core.Batcher(
      settings['special/run_mode'].value,
      settings['special/image'].value,
      settings['main/procedures'],
      settings['main/constraints'],
    )
    
    actions_.add(
      settings['main/procedures'],
      builtin_procedures.BUILTIN_PROCEDURES['insert_background_layers'])
    
    batcher.add_procedure(pg.utils.empty_func, [actions_.DEFAULT_PROCEDURES_GROUP])
    
    batcher.run(
      is_preview=True, process_contents=False, process_names=False, process_export=False,
      **utils_.get_settings_for_batcher(settings['main']))
    
    added_action_items = batcher.invoker.list_actions(group=actions_.DEFAULT_PROCEDURES_GROUP)
    
    # Includes built-in procedures added by default
    self.assertEqual(len(added_action_items), 6)
    
    initial_invoker = added_action_items[1]
    self.assertIsInstance(initial_invoker, pg.invoker.Invoker)
    
    actions_in_initial_invoker = initial_invoker.list_actions(
      group=actions_.DEFAULT_PROCEDURES_GROUP)
    self.assertEqual(len(actions_in_initial_invoker), 1)
    self.assertEqual(actions_in_initial_invoker[0], (pg.utils.empty_func, (), {}))


class TestAddActionFromSettings(unittest.TestCase):
  
  def setUp(self):
    self.batcher = core.Batcher(
      initial_run_mode=0,
      input_image=mock.MagicMock(),
      procedures=mock.MagicMock(),
      constraints=mock.MagicMock(),
      overwrite_chooser=mock.MagicMock(),
      progress_updater=mock.MagicMock())
    
    self.invoker = pg.invoker.Invoker()
    
    self.batcher._invoker = self.invoker
    
    self.procedures = actions_.create('procedures')
    
    self.procedure_stub = stubs_gimp.PdbProcedureStub(
      name='file-png-save',
      type_=gimpenums.PLUGIN,
      params=(
        (gimpenums.PDB_INT32, 'run-mode', 'The run mode'),
        (gimpenums.PDB_INT32ARRAY, 'save-options', 'Save options'),
        (gimpenums.PDB_STRING, 'filename', 'Filename to save the image in')),
      return_vals=None,
      blurb='Saves files in PNG file format')
  
  def test_add_action_from_settings(self):
    procedure = actions_.add(
      self.procedures, builtin_procedures.BUILTIN_PROCEDURES['insert_background_layers'])
    
    self.batcher._add_action_from_settings(procedure)
    
    added_action_items = self.invoker.list_actions(group=actions_.DEFAULT_PROCEDURES_GROUP)
    
    self.assertEqual(len(added_action_items), 1)
    self.assertEqual(
      added_action_items[0][1],
      list(procedure['arguments'])
      + [builtin_procedures.BUILTIN_PROCEDURES_FUNCTIONS['insert_background_layers']])
    self.assertEqual(added_action_items[0][2], {})
  
  def test_add_pdb_proc_as_action_without_run_mode(self):
    self.procedure_stub.params = self.procedure_stub.params[1:]
    self._test_add_pdb_proc_as_action(
      self.procedure_stub, [('save-options', ()), ('filename', '')], {})
  
  def test_add_pdb_proc_as_action_with_run_mode(self):
    self._test_add_pdb_proc_as_action(
      self.procedure_stub, [('run-mode', 0), ('save-options', ()), ('filename', '')], {})
  
  def _test_add_pdb_proc_as_action(
        self, pdb_procedure, expected_arg_names_and_values, expected_kwargs):
    procedure = actions_.add(self.procedures, pdb_procedure)
    
    with mock.patch('batcher.src.batcher.pdb') as pdb_mock:
      pdb_mock.__getitem__.return_value = pdb_procedure
      
      self.batcher._add_action_from_settings(procedure)
    
    added_action_items = self.invoker.list_actions(group=actions_.DEFAULT_PROCEDURES_GROUP)
    
    added_action_item_names_and_values = [
      (setting.name, setting.value) for setting in added_action_items[0][1][:-1]
    ]
    
    self.assertEqual(len(added_action_items), 1)
    self.assertEqual(added_action_item_names_and_values, added_action_item_names_and_values)
    self.assertEqual(added_action_items[0][1][-1], pdb_procedure)
    self.assertDictEqual(added_action_items[0][2], expected_kwargs)


class TestGetReplacedArgsAndKwargs(unittest.TestCase):
  
  def test_get_replaced_args(self):
    batcher = core.Batcher(
      initial_run_mode=0,
      input_image=mock.MagicMock(),
      procedures=mock.MagicMock(),
      constraints=mock.MagicMock(),
      overwrite_chooser=mock.MagicMock(),
      progress_updater=mock.MagicMock())
    
    invoker = pg.invoker.Invoker()
    image = stubs_gimp.Image()
    layer = stubs_gimp.Layer()
    
    batcher._invoker = invoker
    batcher._current_image = image
    batcher._current_raw_item = layer
    
    actions = actions_.create('procedures')
    actions_.add(actions, {
      'name': 'autocrop',
      'type': 'procedure',
      'function': '',
      'enabled': True,
      'display_name': 'Autocrop',
      'action_groups': ['basic'],
      'arguments': [
        {
          'type': 'int',
          'name': 'run_mode',
          'default_value': 0,
        },
        {
          'type': 'placeholder_image',
          'name': 'image',
          'default_value': 'current_image',
        },
        {
          'type': 'placeholder_layer',
          'name': 'layer',
          'default_value': 'current_layer',
        },
        {
          'type': 'int',
          'name': 'offset_x',
          'default_value': 10,
        },
        {
          'type': 'int',
          'name': 'offset_y',
          'default_value': 50,
        },
        {
          'type': 'string',
          'name': 'same_value_as_placeholder_value',
          'default_value': 'current_image',
        },
      ],
    })
    
    replaced_args = batcher._get_replaced_args(actions['autocrop/arguments'])
    
    self.assertListEqual(replaced_args, [0, image, layer, 10, 50, 'current_image'])
