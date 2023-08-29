import unittest
import unittest.mock as mock

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from .. import procedure as pgprocedure
from .. import utils as pgutils


def sample_procedure(*args, **kwargs):
  pass


def sample_procedure_2(*args, **kwargs):
  pass


@mock.patch(f'{pgutils.get_pygimplib_module_path()}.procedure.Gimp.Procedure.new')
class TestProcedure(unittest.TestCase):

  def setUp(self):
    pgprocedure._PROCEDURE_NAMES_AND_DATA = {}
    pgprocedure._PLUGIN_PROPERTIES = {}

    pgprocedure.set_use_locale(False)

  def test_register_single_procedure(self, mock_gimp_procedure):
    pgprocedure.register_procedure(
      sample_procedure,
      arguments=[
        dict(name='run-mode', type=Gimp.RunMode, default=Gimp.RunMode.INTERACTIVE, nick='Run mode'),
        dict(name='output-directory', type=str, default='some_dir', nick='Output directory'),
      ],
      return_values=[
        dict(name='num-layers', type=int, default=0, nick='Number of processed layers'),
      ],
      auxiliary_arguments=[
        dict(name='config-only-arg', type=str, default='', nick='Config-only argument')
      ],
      menu_label='Sample Procedure',
      menu_path='<Image>/Filters',
      image_types='*',
      documentation=('A sample procedure.', 'This is a procedure for testing purposes.'),
      attribution=('Jane Doe, John Doe', 'Jane Doe, John Doe', '2023'),
      argument_sync=Gimp.ArgumentSync.NONE,
      additional_init=lambda proc: proc.set_sensitivity_mask(0),
    )

    # Do not instantiate with `Gimp.PlugIn` as the parent class as objects of
    # these classes should not be instantiated outside `Gimp.main()`.
    # We still need to specify `GObject.GObject` since its metaclass is
    # responsible for initializing `GObject.Property` as class attributes.
    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()
    plugin.do_create_procedure('sample-procedure')

    self.assertEqual(plugin.do_query_procedures(), ['sample-procedure'])

    mock_procedure_object = mock_gimp_procedure.return_value

    self.assertListEqual(
      [call.args[1]
       for call in mock_gimp_procedure.return_value.add_argument_from_property.call_args_list],
      ['run-mode', 'output-directory'],
    )
    self.assertListEqual(
      [call.args[1]
       for call in mock_gimp_procedure.return_value.add_return_value_from_property.call_args_list],
      ['num-layers'],
    )
    self.assertListEqual(
      [call.args[1]
       for call in mock_gimp_procedure.return_value.add_aux_argument_from_property.call_args_list],
      ['config-only-arg'],
    )

    mock_procedure_object.set_menu_label.assert_called_once_with('Sample Procedure')
    mock_procedure_object.add_menu_path.assert_called_once_with('<Image>/Filters')
    mock_procedure_object.set_image_types.assert_called_once_with('*')
    mock_procedure_object.set_documentation.assert_called_once_with(
      'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-procedure')
    mock_procedure_object.set_attribution.assert_called_once_with(
      'Jane Doe, John Doe', 'Jane Doe, John Doe', '2023')
    mock_procedure_object.set_argument_sync.assert_called_once_with(Gimp.ArgumentSync.NONE)
    mock_procedure_object.set_sensitivity_mask.assert_called_once_with(0)

    self.assertTrue(hasattr(plugin, 'do_set_i18n'))

    plugin_class = type(plugin)

    self.assertIsInstance(plugin_class.run_mode, GObject.Property)
    self.assertEqual(plugin_class.run_mode.nick, 'Run mode')
    self.assertEqual(plugin.run_mode, Gimp.RunMode.INTERACTIVE)

    self.assertIsInstance(plugin_class.output_directory, GObject.Property)
    self.assertEqual(plugin_class.output_directory.nick, 'Output directory')
    self.assertEqual(plugin.output_directory, 'some_dir')

    self.assertIsInstance(plugin_class.num_layers, GObject.Property)
    self.assertEqual(plugin_class.num_layers.nick, 'Number of processed layers')
    self.assertEqual(plugin.num_layers, 0)

    self.assertIsInstance(plugin_class.config_only_arg, GObject.Property)
    self.assertEqual(plugin_class.config_only_arg.nick, 'Config-only argument')
    self.assertEqual(plugin.config_only_arg, '')

  def test_create_procedure_no_matching_name(self, mock_gimp_procedure):
    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()
    self.assertIsNone(plugin.do_create_procedure('nonexistent-procedure'))

  def test_register_procedure_with_locale(self, *mocks):
    pgprocedure.set_use_locale(True)
    pgprocedure.register_procedure(sample_procedure)

    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()

    self.assertFalse(hasattr(plugin, 'do_set_i18n'))

  def test_register_procedure_with_multiple_menu_paths(self, mock_gimp_procedure):
    pgprocedure.register_procedure(
      sample_procedure,
      menu_path=['<Image>/Filters', '<Image>/Colors'],
    )

    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()
    plugin.do_create_procedure('sample-procedure')

    self.assertListEqual(
      mock_gimp_procedure.return_value.add_menu_path.call_args_list,
      [(('<Image>/Filters',),), (('<Image>/Colors',),)],
    )

  def test_register_procedure_with_documentation_of_3_elements(self, mock_gimp_procedure):
    pgprocedure.register_procedure(
      sample_procedure,
      documentation=(
        'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-proc'),
    )

    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()
    plugin.do_create_procedure('sample-procedure')

    mock_gimp_procedure.return_value.set_documentation.assert_called_once_with(
      'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-proc')

  def test_register_multiple_procedures(self, mock_gimp_procedure):
    pgprocedure.register_procedure(
      sample_procedure,
      arguments=[
        dict(name='run-mode', type=Gimp.RunMode, default=Gimp.RunMode.INTERACTIVE, nick='Run mode'),
        dict(name='output-directory', type=str, default='some_dir', nick='Output directory'),
      ],
      return_values=[
        dict(name='num-layers', type=int, default=0, nick='Number of processed layers'),
      ],
    )

    pgprocedure.register_procedure(
      sample_procedure_2,
      arguments=[
        'run-mode',
        dict(name='output-directory-2', type=str, default='some_dir_2', nick='Output directory 2'),
      ],
      return_values=[
        dict(name='num-layers', type=int, default=0, nick='Number of processed layers'),
      ],
    )

    plugin = pgprocedure._create_plugin_class(bases=(GObject.GObject,))()
    plugin.do_create_procedure('sample-procedure')
    plugin.do_create_procedure('sample-procedure-2')

    self.assertEqual(
      [call.args[1] for call in mock_gimp_procedure.call_args_list],
      ['sample-procedure', 'sample-procedure-2'])

    plugin_class = type(plugin)

    self.assertIsInstance(plugin_class.run_mode, GObject.Property)
    self.assertEqual(plugin_class.run_mode.nick, 'Run mode')
    self.assertEqual(plugin.run_mode, Gimp.RunMode.INTERACTIVE)

    self.assertIsInstance(plugin_class.output_directory, GObject.Property)
    self.assertEqual(plugin_class.output_directory.nick, 'Output directory')
    self.assertEqual(plugin.output_directory, 'some_dir')

    self.assertIsInstance(plugin_class.output_directory_2, GObject.Property)
    self.assertEqual(plugin_class.output_directory_2.nick, 'Output directory 2')
    self.assertEqual(plugin.output_directory_2, 'some_dir_2')

    self.assertIsInstance(plugin_class.num_layers, GObject.Property)
    self.assertEqual(plugin_class.num_layers.nick, 'Number of processed layers')
    self.assertEqual(plugin.num_layers, 0)

  def test_register_procedure_raises_error_if_dict_is_missing_name(self, *mocks):
    with self.assertRaises(ValueError):
      pgprocedure.register_procedure(
        sample_procedure,
        arguments=[
          dict(type=Gimp.RunMode, default=Gimp.RunMode.INTERACTIVE, nick='Run mode'),
        ],
      )

  def test_register_procedure_raises_error_if_as_string_has_no_corresponding_dict(self, *mocks):
    with self.assertRaises(ValueError):
      pgprocedure.register_procedure(
        sample_procedure,
        arguments=[
          dict(
            name='run-mode', type=Gimp.RunMode, default=Gimp.RunMode.INTERACTIVE, nick='Run mode'),
          'output-directory',
        ],
      )
