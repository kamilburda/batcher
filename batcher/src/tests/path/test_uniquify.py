import unittest

import parameterized

from src.path import uniquify


class TestUniquifyString(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('one_identical_string', 'one', ['one', 'two', 'three'], 'one (1)'),
    
    ('identical_string_and_existing_string_with_unique_substring',
     'one', ['one', 'one (1)', 'three'], 'one (2)'),
    
    ('multiple_identical_strings', 'one', ['one', 'one', 'three'], 'one (1)'),
    
    ('existing_string_with_unique_substring',
     'one (1)', ['one (1)', 'two', 'three'], 'one (1) (1)'),
    
    ('multiple_existing_strings_with_unique_substring',
     'one (1)', ['one (1)', 'one (2)', 'three'], 'one (1) (1)'),
  ])
  def test_uniquify_string(
        self, test_case_suffix, str_, existing_strings, expected_str):
    self.assertEqual(uniquify.uniquify_string(str_, existing_strings), expected_str)
  
  @parameterized.parameterized.expand([
    ('one_identical_string',
     'one.png', ['one.png', 'two', 'three'], 'one (1).png'),
    
    ('identical_string_and_existing_string_with_unique_substring',
     'one.png', ['one.png', 'one (1).png', 'three'], 'one (2).png'),
    
    ('existing_string_with_unique_substring',
     'one (1).png', ['one (1).png', 'two', 'three'], 'one (1) (1).png'),
  ])
  def test_uniquify_string_with_custom_position(
        self, test_case_suffix, str_, existing_strings, expected_str):
    self.assertEqual(
      uniquify.uniquify_string(str_, existing_strings, len(str_) - len('.png')),
      expected_str)
