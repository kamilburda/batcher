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
