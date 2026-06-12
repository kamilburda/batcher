import io
import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import parameterized

from src import gimp_config as gimp_config_


class TestParseData(unittest.TestCase):

  @parameterized.parameterized.expand([
    ('simple_arguments',
     """
# GIMP 'Threshold' settings

(channel value) # in-line comment
(low 0.498)
  # This comment and the following argument contain whitespace  
  ( high 0.95 ) 
(points 4 0.25 0.50 0.75 0.45)
     """,
     [
       ('channel', ['value']),
       ('low', ['0.498']),
       ('high', ['0.95']),
       ('points', ['4', '0.25', '0.50', '0.75', '0.45']),
     ],
     ),

    ('string_arguments',
     r"""
# GIMP 'Threshold' settings

(channel "value") # in-line comment
(empty-argument "")
(multi-line-argument "
some value
trailing \
 # this is not a comment\
")
(multi-string-argument "one" "two")
(bytes-argument 4 "P\207\207\377\n\t😊\\")
(string-argument-with-env-variables "${gimp_data_dir}\\one" "one${gimp_data_dir}")
  # This comment and the following argument contain whitespace  
  ( high 0.95 ) 
(points 4 0.25 0.50 0.75 0.45)
     """,
     [
       ('channel', ['value']),
       ('empty-argument', ['']),
       ('multi-line-argument', ['\nsome value\ntrailing \\\n # this is not a comment\\\n']),
       ('multi-string-argument', ['one', 'two']),
       ('bytes-argument', ['4', r'P\207\207\377\n\t😊\\']),
       ('string-argument-with-env-variables', [
         Gimp.data_directory() + '\\\\one', 'one${gimp_data_dir}']),
       ('high', ['0.95']),
       ('points', ['4', '0.25', '0.50', '0.75', '0.45']),
     ],
     ),

    ('nested_arguments',
     r"""
# GIMP 'Colorize' settings

(hue 0.5)
(saturation 0.25)
(lightness
    (value 0.15))
(color
    (color "R'G'B'A u8" 4 "P\207\207\377" 0))
(multiple-colors
    (color "R'G'B'A u8") (another-color "C'M'Y'K'A u8"))
(nested-color
    (color "R'G'B'A u8" (color "(R'G'B')A u8" 4 "P\207\207\"\377" 0)))
     """,
     [
       ('hue', ['0.5']),
       ('saturation', ['0.25']),
       ('lightness', [[('value', ['0.15'])]]),
       ('color', [[('color', ['R\'G\'B\'A u8', '4', 'P\\207\\207\\377', '0'])]]),
       ('multiple-colors', [
         [('color', ['R\'G\'B\'A u8'])],
         [('another-color', ['C\'M\'Y\'K\'A u8'])],
       ]),
       ('nested-color', [
         [('color', [
           'R\'G\'B\'A u8',
           [('color', ['(R\'G\'B\')A u8', '4', 'P\\207\\207\\"\\377', '0'])],
         ])],
       ]),
     ],
     ),

    ('null_arguments',
     """
(channel 2 NULL 1)
(low "NULL")
     """,
     [
       ('channel', ['2', None, '1']),
       ('low', ['NULL']),
     ],
     ),
  ])
  def test_successful_parse(self, _test_case_suffix, data, expected_parsed_data):
    stream = io.StringIO()
    stream.write(data)
    stream.seek(0)

    self.assertEqual(
      expected_parsed_data,
      gimp_config_._parse_data(stream),
    )

  @parameterized.parameterized.expand([
    ('missing_argument_value',
     """
(missing-argument-value)
     """,
     ),

    ('missing_end_argument_token',
     """
(missing-argument-end-token
     """,
     ),

    ('characters_outside_comment_or_argument',
     """
some-random-characters
     """,
     ),

    ('unclosed_string',
     """
(color "hi there)
     """,
     ),

    ('mismatched_num_start_and_end_argument_tokens',
     """
(color
  (color "RGBA")
     """,
     ),

    ('string_token_within_argument_value',
     """
(color some"value")
     """,
     ),
  ])
  def test_parse_on_error(self, _test_case_suffix, data):
    stream = io.StringIO()
    stream.write(data)
    stream.seek(0)

    with self.assertRaises(gimp_config_.GimpConfigParseError):
      gimp_config_._parse_data(stream)
