import unittest

import parameterized

from ...path import fileext


class TestGetFilenameWithNewFileExtension(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('', 'background.jpg', 'png', 'background.png'),
    ('empty_string', '', 'png', '.png'),
    ('string_without_extension', 'background', 'png', 'background.png'),
    ('new_extension_with_leading_period', 'background.jpg', '.png', 'background.png'),
    ('string_with_trailing_period', 'background.', 'png', 'background.png'),
    ('new_extension_is_set_lowercase', 'background.jpg', 'PNG', 'background.PNG'),
    ('empty_new_extension_removes_extension', 'background.jpg', '', 'background'),
    ('new_extension_as_none_removes_extension', 'background.jpg', None, 'background'),
    ('new_extension_as_single_period_removes_extension',
     'background.jpg', '.', 'background'),
    ('extension_with_multiple_periods_in_string',
     'background.xcf.bz2', 'png', 'background.png'),
    ('multiple_periods_in_string_single_period_for_extension',
     'background.aaa.jpg', 'png', 'background.aaa.png'),
    ('multiple_consecutive_periods',
     'background..jpg', 'png', 'background..png'),
    ('keep_extra_single_trailing_period',
     'background.', 'png', 'background..png', True),
    ('keep_extra_multiple_trailing_periods',
     'background..', 'png', 'background...png', True),
  ])
  def test_get_filename_with_new_file_extension(
        self,
        test_case_suffix,
        str_,
        new_file_extension,
        expected_output,
        keep_extra_trailing_periods=False):
    self.assertEqual(
      fileext.get_filename_with_new_file_extension(
        str_, new_file_extension, keep_extra_trailing_periods),
      expected_output)


class TestGetBaseName(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('main-background', 'main-background'),
    ('main-background.', 'main-background.'),
    ('main-background.jpg', 'main-background'),
    ('main-background..jpg', 'main-background.'),
    ('..jpg', '.'),
    ('.jpg', ''),
    ('.', '.'),
    ('', ''),
  ])
  def test_get_filename_root(self, filename, expected_output):
    self.assertEqual(fileext.get_filename_root(filename), expected_output)
