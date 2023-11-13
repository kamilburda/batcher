import os
import unittest
import unittest.mock as mock

from .. import utils as pgutils


class TestReprifyObject(unittest.TestCase):

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.utils.id', return_value=2208603083056)
  def test_reprify_object_without_name(self, mock_id):
    object_ = object()
    
    self.assertEqual(
      pgutils.reprify_object(object_),
      f'<builtins.object object at 0x0000002023b009130>')

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.utils.id', return_value=2208603083056)
  def test_reprify_object_with_name(self, mock_id):
    object_ = object()

    self.assertEqual(
      pgutils.reprify_object(object_, 'some_object'),
      f'<builtins.object "some_object" at 0x0000002023b009130>')


class TestGetModuleRoot(unittest.TestCase):

  def test_get_module_root(self):
    self.assertEqual(
      pgutils.get_module_root(
        'batcher.pygimplib.tests.test_utils', 'batcher'),
      'batcher')
    self.assertEqual(
      pgutils.get_module_root('batcher.pygimplib.tests.test_utils', 'pygimplib'),
      'batcher.pygimplib')
    self.assertEqual(
      pgutils.get_module_root('batcher.pygimplib.tests.test_utils', 'tests'),
      'batcher.pygimplib.tests')
    self.assertEqual(
      pgutils.get_module_root(
        'batcher.pygimplib.tests.test_utils', 'test_utils'),
      'batcher.pygimplib.tests.test_utils')
  
  def test_get_module_root_nonexistent_name_component(self):
    self.assertEqual(
      pgutils.get_module_root(
        'batcher.pygimplib.tests.test_utils', 'nonexistent_name_component'),
      'batcher.pygimplib.tests.test_utils')
    
    self.assertEqual(
      pgutils.get_module_root(
        'batcher.pygimplib.tests.test_utils', '.pygimplib'),
      'batcher.pygimplib.tests.test_utils')
    
    self.assertEqual(
      pgutils.get_module_root(
        'batcher.pygimplib.tests.test_utils', 'batcher.pygimplib'),
      'batcher.pygimplib.tests.test_utils')
  
  def test_get_module_root_empty_module_name(self):
    self.assertEqual(pgutils.get_module_root('', 'pygimplib'), '')
    self.assertEqual(pgutils.get_module_root('.', 'pygimplib'), '.')
  
  def test_get_module_root_empty_name_component(self):
    self.assertEqual(
      pgutils.get_module_root('batcher.pygimplib.tests.test_utils', ''),
      'batcher.pygimplib.tests.test_utils')

    self.assertEqual(
      pgutils.get_module_root('batcher.pygimplib.tests.test_utils', '.'),
      'batcher.pygimplib.tests.test_utils')


class TestGetCurrentModuleFilepath(unittest.TestCase):
  
  def test_get_current_module_filepath(self):
    self.assertEqual(
      pgutils.get_current_module_filepath(),
      os.path.abspath(__file__))


class TestCreateOnlyProperty(unittest.TestCase):

  def test_create_read_only_property(self):
    obj = type('SomeClass', (), {})()

    pgutils.create_read_only_property(obj, 'some_property', 'some_value')

    self.assertEqual(obj._some_property, 'some_value')
    self.assertEqual(obj.some_property, 'some_value')

    with self.assertRaises(AttributeError):
      obj.some_property = 'new_value'


class TestBytesRelatedFunctions(unittest.TestCase):

  def test_bytes_to_signed_bytes(self):
    self.assertEqual(
      pgutils.bytes_to_signed_bytes(b'Test\x00\x7f\xffdata'),
      (84, 101, 115, 116, 0, 127, -1, 100, 97, 116, 97),
    )

  def test_signed_bytes_to_bytes(self):
    self.assertEqual(
      pgutils.signed_bytes_to_bytes((84, 101, 115, 116, 0, 127, -1, 100, 97, 116, 97)),
      b'Test\x00\x7f\xffdata',
    )

  def test_string_to_bytes(self):
    self.assertEqual(
      pgutils.string_to_bytes('Test\x00\x7f\xffdata'),
      b'Test\x00\x7f\xffdata',
    )

  def test_string_to_bytes_with_remove_overflow(self):
    self.assertEqual(
      pgutils.string_to_bytes('Test\x00\x7f\xff\u0400data', remove_overflow=True),
      b'Test\x00\x7f\xffdata',
    )

  def test_escaped_string_to_bytes(self):
    self.assertEqual(
      pgutils.escaped_string_to_bytes('Test\\x00\\x7f\\xffdata'),
      b'Test\x00\x7f\xffdata',
    )

  def test_escaped_string_to_bytes_unescaped_special_characters_are_removed_or_processed(self):
    self.assertEqual(
      pgutils.escaped_string_to_bytes('Test\x00\x0a\x0d"\\x7f\\xffdata'),
      b'Test\x00\x0a\x0d"\x7f\xffdata',
    )

  def test_escaped_string_to_bytes_returns_empty_bytes_on_malformed_input(self):
    self.assertEqual(pgutils.escaped_string_to_bytes('\\x0x'),b'')

  def test_escaped_string_to_bytes_with_remove_overflow(self):
    self.assertEqual(
      pgutils.escaped_string_to_bytes('Test\\x00\\x7f\\xff\\u0400data', remove_overflow=True),
      b'Test\x00\x7f\xffdata',
    )

  def test_bytes_to_string(self):
    self.assertEqual(
      pgutils.bytes_to_string(b'Test\x00\x7f\xffdata'),
      'Test\x00\x7f\xffdata',
    )

  def test_bytes_to_escaped_string(self):
    self.assertEqual(
      pgutils.bytes_to_escaped_string(b'Test\x00\x7f\xffdata'),
      'Test\\x00\\x7f\\xffdata',
    )
