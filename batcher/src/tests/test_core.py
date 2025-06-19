import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import builtin_actions
from src import commands as commands_
from src import core
from src import invoker as invoker_
from src import itemtree
from src import plugin_settings
from src import utils
from src import utils_setting as utils_setting_
from src.pypdb import pdb

from src.tests import stubs_gimp


class TestBatcherInitialCommands(unittest.TestCase):
  
  def test_add_action_added_action_is_first_in_command_list(self):
    settings = plugin_settings.create_settings_for_export_layers()
    settings['main/file_extension'].set_value('xcf')
    
    batcher = core.LayerBatcher(
      item_tree=itemtree.LayerTree(),
      actions=settings['main/actions'],
      conditions=settings['main/conditions'],
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
    )
    
    commands_.add(
      settings['main/actions'],
      builtin_actions.BUILTIN_ACTIONS['insert_background_for_layers'])
    
    batcher.add_action(utils.empty_func, [commands_.DEFAULT_ACTIONS_GROUP])
    
    batcher.run(
      is_preview=True,
      process_contents=False,
      process_names=False,
      process_export=False,
      **utils_setting_.get_settings_for_batcher(settings['main']))
    
    added_command_items = batcher.invoker.list_commands(group=commands_.DEFAULT_ACTIONS_GROUP)
    
    # Includes built-in actions added by default
    self.assertEqual(len(added_command_items), 6)
    
    initial_invoker = added_command_items[1]
    self.assertIsInstance(initial_invoker, invoker_.Invoker)
    
    commands_in_initial_invoker = initial_invoker.list_commands(
      group=commands_.DEFAULT_ACTIONS_GROUP)
    self.assertEqual(len(commands_in_initial_invoker), 1)
    self.assertEqual(commands_in_initial_invoker[0], (utils.empty_func, (), {}))


@mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
class TestAddCommandFromSettings(unittest.TestCase):
  
  def setUp(self):
    self.batcher = core.LayerBatcher(
      item_tree=itemtree.LayerTree(),
      actions=mock.MagicMock(),
      conditions=mock.MagicMock(),
      initial_export_run_mode=Gimp.RunMode.INTERACTIVE,
      overwrite_chooser=mock.MagicMock(),
      progress_updater=mock.MagicMock())
    
    self.invoker = invoker_.Invoker()
    
    self.batcher._invoker = self.invoker
    
    self.actions = commands_.create('actions')

    self.procedure_name = 'file-png-export'

    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(
          value_type=Gimp.RunMode.__gtype__,
          name='run-mode',
          blurb='The run mode',
          default_value=Gimp.RunMode.NONINTERACTIVE),
        dict(value_type=Gimp.Int32Array.__gtype__, name='save-options', blurb='Save options'),
        dict(
          value_type=GObject.TYPE_STRING, name='filename', blurb='Filename to save the image in')],
      blurb='Saves files in PNG file format')

    commands_.pdb.remove_from_cache(self.procedure_name)
  
  def test_add_command_from_settings(self, mock_get_pdb):
    action = commands_.add(
      self.actions, builtin_actions.BUILTIN_ACTIONS['insert_background_for_layers'])
    
    self.batcher._add_command_from_settings(action)
    
    added_command_items = self.invoker.list_commands(group=commands_.DEFAULT_ACTIONS_GROUP)
    
    self.assertEqual(len(added_command_items), 1)
    self.assertEqual(
      added_command_items[0][1],
      list(action['arguments'])
      + [builtin_actions.BUILTIN_ACTIONS_FUNCTIONS['insert_background_for_layers']])
    self.assertEqual(added_command_items[0][2], {})
  
  def test_add_pdb_proc_as_command_without_run_mode(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'] = self.procedure_stub_kwargs['arguments_spec'][1:]

    procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(procedure_stub)

    self._test_add_pdb_proc_as_command(procedure_stub, [('save-options', ()), ('filename', '')], {})
  
  def test_add_pdb_proc_as_command_with_run_mode(self, mock_get_pdb):
    procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(procedure_stub)

    self._test_add_pdb_proc_as_command(
      procedure_stub, [('run-mode', 0), ('save-options', ()), ('filename', '')], {})
  
  def _test_add_pdb_proc_as_command(
        self, pdb_procedure, expected_arg_names_and_values, expected_kwargs):
    action = commands_.add(self.actions, pdb_procedure.get_name())

    self.batcher._add_command_from_settings(action)
    
    added_command_items = self.invoker.list_commands(group=commands_.DEFAULT_ACTIONS_GROUP)
    
    added_command_item_names_and_values = [
      (setting.name, setting.value) for setting in added_command_items[0][1][:-1]
    ]
    
    self.assertEqual(len(added_command_items), 1)
    self.assertEqual(added_command_item_names_and_values, added_command_item_names_and_values)
    self.assertEqual(added_command_items[0][1][-1], pdb[pdb_procedure.get_name()])
    self.assertDictEqual(added_command_items[0][2], expected_kwargs)


class TestGetReplacedArgsAndKwargs(unittest.TestCase):
  
  def test_get_replaced_args(self):
    batcher = core.LayerBatcher(
      item_tree=itemtree.LayerTree(),
      actions=mock.MagicMock(),
      conditions=mock.MagicMock(),
      initial_export_run_mode=Gimp.RunMode.INTERACTIVE,
      overwrite_chooser=mock.MagicMock(),
      progress_updater=mock.MagicMock())
    
    invoker = invoker_.Invoker()
    image = stubs_gimp.Image()
    layer = stubs_gimp.Layer(image=image)
    
    batcher._invoker = invoker
    batcher.current_image = image
    batcher.current_layer = layer

    commands = commands_.create('actions')
    commands_.add(commands, {
      'name': 'autocrop',
      'type': 'action',
      'function': '',
      'enabled': True,
      'display_name': 'Autocrop',
      'command_groups': ['basic'],
      'arguments': [
        {
          'type': 'enum',
          'name': 'run_mode',
          'enum_type': Gimp.RunMode,
          'default_value': Gimp.RunMode.NONINTERACTIVE,
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
          'type': 'array',
          'element_type': 'drawable',
          'name': 'selected_drawables',
          'default_value': [],
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
    
    replaced_args, replaced_kwargs = batcher._get_replaced_args(commands['autocrop/arguments'], True)

    self.assertFalse(replaced_args)

    self.assertDictEqual(
      replaced_kwargs,
      {
        'run_mode': Gimp.RunMode.NONINTERACTIVE,
        'image': image,
        'layer': layer,
        'selected_drawables': (),
        'offset_x': 10,
        'offset_y': 50,
        'same_value_as_placeholder_value': 'current_image',
      })
