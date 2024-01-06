import os
import unittest

import parameterized

from src.path import validators as validators_


class TestFilenameValidator(unittest.TestCase):
  
  def test_is_valid_returns_no_status_messages(self):
    self.assertEqual(validators_.FilenameValidator.is_valid('one'), (True, []))
  
  @parameterized.parameterized.expand([
    ('', '0n3_two_,o_O_;-()three.jpg', True),
    ('', 'one/two\x09\x7f\\:|', False),
    ('', '', False),
    ('', ' one ', False),
    ('', 'one.', False),
    ('', '.one', True),
    ('', 'NUL', False),
    ('', 'NUL.txt', False),
    ('', 'NUL (1)', True),
  ])
  def test_is_valid(self, test_case_suffix, str_, expected_is_valid):
    if expected_is_valid:
      self.assertTrue(validators_.FilenameValidator.is_valid(str_)[0])
    else:
      self.assertFalse(validators_.FilenameValidator.is_valid(str_)[0])
  
  @parameterized.parameterized.expand([
    ('', 'one', 'one'),
    ('', '0n3_two_,o_O_;-()three.jpg', '0n3_two_,o_O_;-()three.jpg'),
    ('', 'one/two\x09\x7f\\:|', 'onetwo'),
    ('', '', 'Untitled'),
    ('', ' one ', 'one'),
    ('', 'one.', 'one'),
    ('', '.one', '.one'),
    ('', 'NUL', 'NUL (1)'),
    ('', 'NUL.txt', 'NUL (1).txt'),
  ])
  def test_validate(self, test_case_suffix, str_, expected_output):
    self.assertEqual(validators_.FilenameValidator.validate(str_), expected_output)
  

class TestFilepathValidator(unittest.TestCase):
  
  def test_is_valid_returns_no_status_messages(self):
    self.assertEqual(
      validators_.FilepathValidator.is_valid(os.path.join('one', 'two', 'three')),
      (True, []))
  
  @parameterized.parameterized.expand([
    ('', [
      'zero', '0n3', 'two', f',o_O_;-(){os.sep}{os.sep}{os.sep}', f'three.jpg{os.sep}'],
     True),
    ('', ['one', 'two', '\x09\x7f', ':|'], False),
    ('', ['one', ':two', 'three'], False),
    ('', [f'C:|{os.sep}two', 'three'], False),
    ('', [' one', 'two', 'three '], False),
    ('', ['one', ' two', 'three'], True),
    ('', ['one', 'two ', 'three'], False),
    ('', ['one', 'two', 'three.'], False),
    ('', ['one.', 'two.', 'three'], False),
    ('', ['.one', 'two', '.three'], True),
    ('', ['one', 'two', 'NUL'], False),
    ('', ['one', 'two', 'NUL.txt'], False),
    ('', ['one', 'NUL', 'three'], False),
    ('', ['one', 'NUL (1)', 'three'], True),
    ('', [''], False),
    ('', [f'C:{os.sep}two', 'three'], True, 'nt'),
    ('', [f'C:{os.sep}two', 'three'], False, 'posix'),
  ])
  def test_is_valid(
        self, test_case_suffix, path_components, expected_is_valid, os_name=None):
    if os_name is not None and os.name != os_name:
      return
    
    if expected_is_valid:
      self.assertTrue(
        validators_.FilepathValidator.is_valid(os.path.join(*path_components))[0])
    else:
      self.assertFalse(
        validators_.FilepathValidator.is_valid(os.path.join(*path_components))[0])
  
  @parameterized.parameterized.expand([
    ('',
     ['one', 'two', 'three'],
     ['one', 'two', 'three']),
    ('',
     ['zero', '0n3', 'two', f',o_O_;-(){os.sep}{os.sep}{os.sep}', f'three.jpg{os.sep}'],
     ['zero', '0n3', 'two', ',o_O_;-()', 'three.jpg']),
    ('',
     ['one', 'two\x09\x7f', 'three:|'],
     ['one', 'two', 'three']),
    ('',
     ['one', ':two', 'three'],
     ['one', 'two', 'three']),
    ('',
     [' one', 'two', 'three '],
     ['one', 'two', 'three']),
    ('',
     ['one', 'two ', 'three'],
     ['one', 'two', 'three']),
    ('',
     ['one', 'two', 'three.'],
     ['one', 'two', 'three']),
    ('',
     ['one.', 'two.', 'three'],
     ['one', 'two', 'three']),
    ('',
     ['.one', 'two', '.three'],
     ['.one', 'two', '.three']),
    ('',
     ['one', 'two', 'NUL'],
     ['one', 'two', 'NUL (1)']),
    ('',
     ['one', 'two', 'NUL:|.txt'],
     ['one', 'two', 'NUL (1).txt']),
    ('',
     ['one', 'NUL', 'three'],
     ['one', 'NUL (1)', 'three']),
    ('',
     ['one', 'NUL (1)', 'three'],
     ['one', 'NUL (1)', 'three']),
    ('',
     ['one', ':|', 'three'],
     ['one', 'three']),
    ('',
     [''],
     ['.']),
    ('',
     ['|'],
     ['.']),
    ('',
     [f'C:{os.sep}two', 'three'],
     [f'C:{os.sep}two', 'three'],
     'nt'),
    ('',
     [f'C:|one{os.sep}two', 'three'],
     ['C:', 'one', 'two', 'three'],
     'nt'),
    ('',
     [f'C:|{os.sep}two', 'three'],
     ['C:', 'two', 'three'],
     'nt'),
    ('',
     [f'C:{os.sep}two', 'three'],
     [f'C{os.sep}two', 'three'],
     'posix'),
    ('',
     [f'C:|one{os.sep}two', 'three'],
     ['Cone', 'two', 'three'],
     'posix'),
    ('',
     [f'C:|{os.sep}two', 'three'],
     ['C', 'two', 'three'],
     'posix'),
  ])
  def test_validate(
        self,
        test_case_suffix,
        path_components,
        expected_path_components,
        os_name=None):
    if os_name is not None and os.name != os_name:
      return
    
    self.assertEqual(
      validators_.FilepathValidator.validate(os.path.join(*path_components)),
      os.path.join(*expected_path_components))


class TestFileExtensionValidator(unittest.TestCase):
  
  def test_is_valid_returns_no_status_messages(self):
    self.assertEqual(validators_.FileExtensionValidator.is_valid('jpg'), (True, []))
  
  @parameterized.parameterized.expand([
    ('', '.jpg', True),
    ('', 'tar.gz', True),
    ('', 'one/two\x09\x7f\\:|', False),
    ('', '', False),
    ('', ' jpg ', False),
    ('', 'jpg.', False),
  ])
  def test_is_valid(self, test_case_suffix, str_, expected_is_valid):
    if expected_is_valid:
      self.assertTrue(validators_.FileExtensionValidator.is_valid(str_)[0])
    else:
      self.assertFalse(validators_.FileExtensionValidator.is_valid(str_)[0])
  
  @parameterized.parameterized.expand([
    ('', 'jpg', 'jpg'),
    ('', '.jpg', '.jpg'),
    ('', 'tar.gz', 'tar.gz'),
    ('', ' jpg ', ' jpg'),
    ('', 'jpg.', 'jpg'),
    ('', '', ''),
    ('', 'one/two\x09\x7f\\:|', 'onetwo'),
  ])
  def test_validate(self, test_case_suffix, str_, expected_output):
    self.assertEqual(validators_.FileExtensionValidator.validate(str_), expected_output)
