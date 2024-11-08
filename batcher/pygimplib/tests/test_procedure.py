import unittest
import unittest.mock as mock

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
from gi.repository import GObject

from .. import procedure as pgprocedure
from .. import utils as pgutils


def sample_procedure(*_args, **_kwargs):
  pass


def sample_procedure_2(*_args, **_kwargs):
  pass


@mock.patch(f'{pgutils.get_pygimplib_module_path()}.procedure.Gimp')
class TestProcedure(unittest.TestCase):

  def setUp(self):
    pgprocedure._PROCEDURE_NAMES_AND_DATA = {}
    pgprocedure._PLUGIN_PROPERTIES = {}

    pgprocedure.set_use_locale(False)

    self.run_mode_argument = [
      'enum',
      'run-mode',
      'Run mode',
      'The run mode',
      Gimp.RunMode,
      Gimp.RunMode.NONINTERACTIVE,
      GObject.ParamFlags.READWRITE,
    ]

    self.output_directory_argument = [
      'string',
      'output-directory',
      'Output directory',
      'Output directory',
      'some_dir',
      GObject.ParamFlags.READWRITE,
    ]

    self.num_layers_return_value = [
      'integer',
      'num-layers',
      'Number of processed layers',
      'Number of processed layers',
      0,
      GLib.MAXINT,
      0,
      GObject.ParamFlags.READWRITE,
    ]

    self.aux_argument = [
      'string',
      'config-only-arg',
      'Config-only argument',
      'Config-only argument',
      '',
      GObject.ParamFlags.READWRITE,
    ]

  def test_register_single_procedure(self, mock_gimp_module):
    pgprocedure.register_procedure(
      sample_procedure,
      # We pass an explicit `procedure_type` argument since the default
      # argument value would have to be mocked (the default value is the
      # non-mocked `Gimp.ImageProcedure` class despite the `Gimp` module being
      # mocked as the module was mocked after the `procedure` module was
      # imported). This is more readable.
      procedure_type=mock_gimp_module.ImageProcedure,
      arguments=[
        self.run_mode_argument,
        self.output_directory_argument,
      ],
      return_values=[
        self.num_layers_return_value,
      ],
      auxiliary_arguments=[
        self.aux_argument,
      ],
      menu_label='Sample Procedure',
      menu_path='<Image>/Filters',
      image_types='*',
      documentation=('A sample procedure.', 'This is a procedure for testing purposes.'),
      attribution=('Jane Doe, John Doe', 'Jane Doe, John Doe', '2023'),
      additional_init=lambda proc: proc.set_sensitivity_mask(0),
    )

    # Do not instantiate with `Gimp.PlugIn` as the parent class as objects of
    # these classes should not be instantiated outside `Gimp.main()`.
    plugin = pgprocedure._create_plugin_class(bases=())()

    mock_procedure = plugin.do_create_procedure('sample-procedure')

    self.assertEqual(plugin.do_query_procedures(), ['sample-procedure'])

    mock_procedure.add_enum_argument.assert_called_once_with(*self.run_mode_argument[1:])
    mock_procedure.add_string_argument.assert_called_once_with(*self.output_directory_argument[1:])
    mock_procedure.add_integer_return_value.assert_called_once_with(
      *self.num_layers_return_value[1:])
    mock_procedure.add_string_aux_argument.assert_called_once_with(*self.aux_argument[1:])

    mock_procedure.set_menu_label.assert_called_once_with('Sample Procedure')
    mock_procedure.add_menu_path.assert_called_once_with('<Image>/Filters')
    mock_procedure.set_image_types.assert_called_once_with('*')
    mock_procedure.set_documentation.assert_called_once_with(
      'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-procedure')
    mock_procedure.set_attribution.assert_called_once_with(
      'Jane Doe, John Doe', 'Jane Doe, John Doe', '2023')
    mock_procedure.set_sensitivity_mask.assert_called_once_with(0)

    self.assertTrue(hasattr(plugin, 'do_set_i18n'))

  def test_create_procedure_no_matching_name(self, _mock_gimp_module):
    plugin = pgprocedure._create_plugin_class(bases=())()
    self.assertIsNone(plugin.do_create_procedure('nonexistent-procedure'))

  def test_register_procedure_with_locale(self, mock_gimp_module):
    pgprocedure.set_use_locale(True)
    pgprocedure.register_procedure(
      sample_procedure,
      procedure_type=mock_gimp_module.ImageProcedure
    )

    plugin = pgprocedure._create_plugin_class(bases=())()

    self.assertFalse(hasattr(plugin, 'do_set_i18n'))

  def test_register_procedure_with_multiple_menu_paths(self, mock_gimp_module):
    pgprocedure.register_procedure(
      sample_procedure,
      procedure_type=mock_gimp_module.ImageProcedure,
      menu_path=['<Image>/Filters', '<Image>/Colors'],
    )

    plugin = pgprocedure._create_plugin_class(bases=())()
    mock_procedure = plugin.do_create_procedure('sample-procedure')

    self.assertListEqual(
      mock_procedure.add_menu_path.call_args_list,
      [(('<Image>/Filters',),), (('<Image>/Colors',),)],
    )

  def test_register_procedure_with_documentation_of_3_elements(self, mock_gimp_module):
    pgprocedure.register_procedure(
      sample_procedure,
      procedure_type=mock_gimp_module.ImageProcedure,
      documentation=(
        'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-proc'),
    )

    plugin = pgprocedure._create_plugin_class(bases=())()
    mock_procedure = plugin.do_create_procedure('sample-procedure')

    mock_procedure.set_documentation.assert_called_once_with(
      'A sample procedure.', 'This is a procedure for testing purposes.', 'sample-proc')

  def test_register_multiple_procedures(self, mock_gimp_module):
    mock_gimp_module.ImageProcedure.new.side_effect = [
      mock.Mock(),
      mock.Mock(),
    ]

    pgprocedure.register_procedure(
      sample_procedure,
      procedure_type=mock_gimp_module.ImageProcedure,
      arguments=[
        self.run_mode_argument,
        self.output_directory_argument,
      ],
      return_values=[
        self.num_layers_return_value,
      ],
    )

    pgprocedure.register_procedure(
      sample_procedure_2,
      procedure_type=mock_gimp_module.ImageProcedure,
      arguments=[
        self.run_mode_argument,
        self.output_directory_argument,
      ],
      return_values=[
        self.num_layers_return_value,
      ],
    )

    plugin = pgprocedure._create_plugin_class(bases=())()
    mock_procedure = plugin.do_create_procedure('sample-procedure')
    mock_procedure_2 = plugin.do_create_procedure('sample-procedure-2')

    self.assertEqual(plugin.do_query_procedures(), ['sample-procedure', 'sample-procedure-2'])

    mock_procedure.add_enum_argument.assert_called_once_with(*self.run_mode_argument[1:])
    mock_procedure.add_string_argument.assert_called_once_with(*self.output_directory_argument[1:])
    mock_procedure.add_integer_return_value.assert_called_once_with(
      *self.num_layers_return_value[1:])

    mock_procedure_2.add_enum_argument.assert_called_once_with(*self.run_mode_argument[1:])
    mock_procedure_2.add_string_argument.assert_called_once_with(*self.output_directory_argument[1:])
    mock_procedure_2.add_integer_return_value.assert_called_once_with(
      *self.num_layers_return_value[1:])

  def test_register_procedure_raises_error_if_type_is_not_string(self, mock_gimp_module):
    with self.assertRaises(TypeError):
      pgprocedure.register_procedure(
        sample_procedure,
        procedure_type=mock_gimp_module.ImageProcedure,
        arguments=[
          [
            Gimp.RunMode,
            'run-mode',
            'Run mode',
            'The run mode',
            Gimp.RunMode,
            Gimp.RunMode.NONINTERACTIVE,
            GObject.ParamFlags.READWRITE,
          ],
        ],
      )

  def test_register_procedure_raises_error_if_multiple_arguments_have_same_name(
        self, mock_gimp_module):
    with self.assertRaises(ValueError):
      pgprocedure.register_procedure(
        sample_procedure,
        procedure_type=mock_gimp_module.ImageProcedure,
        arguments=[
          [
            'enum',
            'run-mode',
            'Run mode',
            'The run mode',
            Gimp.RunMode,
            Gimp.RunMode.NONINTERACTIVE,
            GObject.ParamFlags.READWRITE,
          ],
          [
            'enum',
            'run-mode',
            'Run mode',
            'The run mode',
            Gimp.RunMode,
            Gimp.RunMode.NONINTERACTIVE,
            GObject.ParamFlags.READWRITE,
          ],
        ],
      )

  def test_register_procedure_raises_error_if_missing_mandatory_args(self, mock_gimp_module):
    with self.assertRaises(ValueError):
      pgprocedure.register_procedure(
        sample_procedure,
        procedure_type=mock_gimp_module.ImageProcedure,
        arguments=[
          [
            'enum',
          ],
        ],
      )

  def test_register_procedure_raises_error_if_proc_with_same_name_already_exists(self, *mocks):
    pgprocedure.register_procedure(sample_procedure)
    with self.assertRaises(ValueError):
      pgprocedure.register_procedure(sample_procedure)
