import os
import unittest
import unittest.mock as mock

import parameterized

from src import utils


class TestReprifyObject(unittest.TestCase):

  @mock.patch('src.utils.id', return_value=2208603083056)
  def test_reprify_object_without_name(self, mock_id):
    object_ = object()

    self.assertEqual(
      utils.reprify_object(object_),
      f'<builtins.object object at 0x0000002023b009130>')

  @mock.patch('src.utils.id', return_value=2208603083056)
  def test_reprify_object_with_name(self, mock_id):
    object_ = object()

    self.assertEqual(
      utils.reprify_object(object_, 'some_object'),
      f'<builtins.object "some_object" at 0x0000002023b009130>')


class TestGetModuleRoot(unittest.TestCase):

  def test_get_module_root(self):
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'batcher'),
      'batcher')
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'src'),
      'batcher.src')
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'tests'),
      'batcher.src.tests')
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'test_utils'),
      'batcher.src.tests.test_utils')

  def test_get_module_root_nonexistent_name_component(self):
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'nonexistent_name_component'),
      'batcher.src.tests.test_utils')

    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', '.src'),
      'batcher.src.tests.test_utils')

    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', 'batcher.src'),
      'batcher.src.tests.test_utils')

  def test_get_module_root_empty_module_name(self):
    self.assertEqual(utils.get_module_root('', 'src'), '')
    self.assertEqual(utils.get_module_root('.', 'src'), '.')

  def test_get_module_root_empty_name_component(self):
    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', ''),
      'batcher.src.tests.test_utils')

    self.assertEqual(
      utils.get_module_root('batcher.src.tests.test_utils', '.'),
      'batcher.src.tests.test_utils')


class TestGetCurrentModuleFilepath(unittest.TestCase):

  def test_get_current_module_filepath(self):
    self.assertEqual(
      utils.get_current_module_filepath(),
      os.path.abspath(__file__))


class TestCreateOnlyProperty(unittest.TestCase):

  def test_create_read_only_property(self):
    obj = type('SomeClass', (), {})()

    utils.create_read_only_property(obj, 'some_property', 'some_value')

    self.assertEqual(obj._some_property, 'some_value')
    self.assertEqual(obj.some_property, 'some_value')

    with self.assertRaises(AttributeError):
      obj.some_property = 'new_value'


class TestBytesRelatedFunctions(unittest.TestCase):

  def test_bytes_to_signed_bytes(self):
    self.assertEqual(
      utils.bytes_to_signed_bytes(b'Test\x00\x7f\xffdata'),
      (84, 101, 115, 116, 0, 127, -1, 100, 97, 116, 97),
    )

  def test_signed_bytes_to_bytes(self):
    self.assertEqual(
      utils.signed_bytes_to_bytes((84, 101, 115, 116, 0, 127, -1, 100, 97, 116, 97)),
      b'Test\x00\x7f\xffdata',
    )

  def test_string_to_bytes(self):
    self.assertEqual(
      utils.string_to_bytes('Test\x00\x7f\xffdata'),
      b'Test\x00\x7f\xffdata',
    )

  def test_string_to_bytes_with_remove_overflow(self):
    self.assertEqual(
      utils.string_to_bytes('Test\x00\x7f\xff\u0400data', remove_overflow=True),
      b'Test\x00\x7f\xffdata',
    )

  def test_escaped_string_to_bytes(self):
    self.assertEqual(
      utils.escaped_string_to_bytes('Test\\x00\\x7f\\xffdata'),
      b'Test\x00\x7f\xffdata',
    )

  def test_escaped_string_to_bytes_unescaped_special_characters_are_removed_or_processed(self):
    self.assertEqual(
      utils.escaped_string_to_bytes('Test\x00\x0a\x0d"\\x7f\\xffdata'),
      b'Test\x00\x0a\x0d"\x7f\xffdata',
    )

  def test_escaped_string_to_bytes_returns_empty_bytes_on_malformed_input(self):
    self.assertEqual(utils.escaped_string_to_bytes('\\x0x'), b'')

  def test_escaped_string_to_bytes_with_remove_overflow(self):
    self.assertEqual(
      utils.escaped_string_to_bytes('Test\\x00\\x7f\\xff\\u0400data', remove_overflow=True),
      b'Test\x00\x7f\xffdata',
    )

  def test_bytes_to_string(self):
    self.assertEqual(
      utils.bytes_to_string(b'Test\x00\x7f\xffdata'),
      'Test\x00\x7f\xffdata',
    )

  def test_bytes_to_escaped_string(self):
    self.assertEqual(
      utils.bytes_to_escaped_string(b'Test\x00\x7f\xffdata'),
      'Test\\x00\\x7f\\xffdata',
    )


class TestSemiDeepCopy(unittest.TestCase):

  def test_primitive_type(self):
    input_ = 'hello'
    input_copy = utils.semi_deep_copy(input_)

    self.assertEqual(input_, input_copy)
    self.assertIs(input_, input_copy)

  @parameterized.parameterized.expand([
    ['list', [1, 4, 2]],
    ['tuple', (1, 4, 2)],
    ['set', {1, 4, 2}],
    ['frozenset', frozenset({1, 4, 2})],
    ['dict', {1: 'a', 4: 'd', 2: 'b'}],
  ])
  def test_single_level_container(self, test_case_suffix, input_):
    input_copy = utils.semi_deep_copy(input_)

    self.assertIsNot(input_, input_copy)

    if isinstance(input_, list):
      self.assertListEqual(input_, input_copy)
    elif isinstance(input_, tuple):
      self.assertTupleEqual(input_, input_copy)
    elif isinstance(input_, (set, frozenset)):
      self.assertSetEqual(input_, input_copy)
    elif isinstance(input_, dict):
      self.assertDictEqual(input_, input_copy)

  def test_nested_list(self):
    input_ = [
      {
        'name': 'export',
        'additional_tags': {'name', 'export', 'edit'},
        'display_options_on_create': True,
        'arguments': [
          {
            'type': 'string',
            'name': 'output_directory',
          },
          {
            'type': 'choice',
            'name': 'overwrite_mode',
            'items': [
              ('replace', 'Replace', 0),
              ('skip', 'Skip', 1),
              ('rename_new', 'Rename _new file', 2),
              ('rename_existing', 'Rename existing file', 3)],
            'gui_type': None,
          },
        ],
      },
      {
        'name': 'apply_opacity_from_group_layers',
        'additional_tags': frozenset({'edit', 'export'}),
      },
    ]

    input_copy = utils.semi_deep_copy(input_)

    self.assertListEqual(input_, input_copy)

    self.assertIsNot(input_, input_copy)

    self.assertIsNot(input_[0], input_copy[0])
    self.assertIsNot(input_[0]['additional_tags'], input_copy[0]['additional_tags'])
    self.assertIsNot(input_[0]['arguments'], input_copy[0]['arguments'])
    self.assertIsNot(input_[0]['arguments'][0], input_copy[0]['arguments'][0])
    self.assertIsNot(input_[0]['arguments'][1], input_copy[0]['arguments'][1])
    self.assertIsNot(input_[0]['arguments'][1]['items'], input_copy[0]['arguments'][1]['items'])
    for i in range(len(input_[0]['arguments'][1]['items'])):
      self.assertIsNot(
        input_[0]['arguments'][1]['items'][i], input_copy[0]['arguments'][1]['items'][i])

    self.assertIsNot(input_[1], input_copy[1])
    self.assertIsNot(input_[1]['additional_tags'], input_copy[1]['additional_tags'])

  def test_nested_dict(self):
    input_ = {
      'name': 'export',
      'additional_tags': {'name', 'export', 'edit'},
      'display_options_on_create': True,
      'arguments': [
        {
          'type': 'string',
          'name': 'output_directory',
        },
      ],
      'type': 'action',
    }

    input_copy = utils.semi_deep_copy(input_)

    self.assertDictEqual(input_, input_copy)

    self.assertIsNot(input_, input_copy)

    self.assertIsNot(input_, input_copy)
    self.assertIsNot(input_['additional_tags'], input_copy['additional_tags'])
    self.assertIsNot(input_['arguments'], input_copy['arguments'])
    self.assertIsNot(input_['arguments'][0], input_copy['arguments'][0])
