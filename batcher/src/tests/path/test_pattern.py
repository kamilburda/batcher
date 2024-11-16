import unittest

import parameterized

from src.path import pattern as pattern_


def _get_field_value(field, arg1=1, arg2=2):
  return f'{arg1}{arg2}'


def _get_field_value_with_required_args(field, arg1, arg2, arg3):
  return f'{arg1}{arg2}{arg3}'


def _get_field_value_with_varargs(field, arg1, *args):
  return f'{arg1}_{"-".join(args)}'


def _get_field_value_with_kwargs(field, arg1=1, arg2=2, **kwargs):
  return f'{arg1}_{"-".join(kwargs.values())}'


def _get_field_value_raising_exception(field, arg1=1, arg2=2):
  raise ValueError('invalid argument values')


def _generate_number():
  i = 1
  while True:
    yield i
    i += 1


def _generate_string_with_single_character(character='a'):
  while True:
    yield character
    character += 'a'


class TestStringPattern(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('empty_string', '', ''),
    ('nonempty_string', 'image', 'image'),
    ('string_containing_field_delimiters', '[image]', '[image]'),
  ])
  def test_generate_without_fields(
        self, test_case_suffix, pattern, expected_output):
    self.assertEqual(pattern_.StringPattern(pattern).substitute(), expected_output)
  
  @parameterized.parameterized.expand([
    ('fields_without_arguments_with_constant_value',
     [('field1', lambda field: '1'),
      ('field2', lambda field: '2'),
      ('field3', lambda field: '3')],
     'img_[field1][field2]_[field3]',
     'img_12_3'),
    
    ('field_with_explicit_arguments',
     [('field', _get_field_value)], 'img_[field, 3, 4]', 'img_34'),
    
    ('field_with_explicit_arguments_of_length_more_than_one',
     [('field', _get_field_value)], 'img_[field, one, two]', 'img_onetwo'),
    
    ('field_with_last_default_argument',
     [('field', _get_field_value)], 'img_[field, 3]', 'img_32'),
    
    ('field_with_default_arguments',
     [('field', _get_field_value)], 'img_[field]', 'img_12'),
    
    ('field_with_default_arguments_with_trailing_comma',
     [('field', _get_field_value)], 'img_[field,]', 'img_12'),
    
    ('field_with_default_arguments_with_trailing_comma_and_space',
     [('field', _get_field_value)], 'img_[field, ]', 'img_12'),
    
    ('field_with_explicit_arguments_with_trailing_comma_and_space',
     [('field', _get_field_value)], 'img_[field, 3, 4, ]', 'img_34'),
    
    ('field_with_last_default_argument_with_trailing_comma_and_space',
     [('field', _get_field_value)], 'img_[field, 3, ]', 'img_32'),
    
    ('field_with_more_args_than_func',
     [('field', _get_field_value)], 'img_[field, 3, 4, 5]', 'img_[field, 3, 4, 5]'),
    
    ('field_with_zero_args_for_func_with_required_args',
     [('field', _get_field_value_with_required_args)],
     'img_[field]',
     'img_[field]'),
    
    ('field_with_fewer_args_than_required',
     [('field', _get_field_value_with_required_args)],
     'img_[field, 3]',
     'img_[field, 3]'),
    
    ('field_with_one_arg_less_than_required',
     [('field', _get_field_value_with_required_args)],
     'img_[field, 3, 4]',
     'img_[field, 3, 4]'),
    
    ('field_with_no_varargs_for_func_with_varargs',
     [('field', _get_field_value_with_varargs)],
     'img_[field, 3]',
     'img_3_'),
    
    ('field_with_varargs_for_func_with_varargs',
     [('field', _get_field_value_with_varargs)],
     'img_[field, 3, 4, 5, 6]',
     'img_3_4-5-6'),
    
    ('field_args_with_explicit_delimiters',
     [('field', _get_field_value)], 'img_[field, [3], [4],]', 'img_34'),
    
    ('field_args_of_length_more_than_one_with_explicit_delimiters',
     [('field', _get_field_value)], 'img_[field, [one], [two],]', 'img_onetwo'),
    
    ('field_with_multiple_spaces_between_args',
     [('field', _get_field_value)], 'img_[field,   3,  4  ]', 'img_34'),
    
    ('field_args_with_explicit_delimiters_escape_spaces_and_arg_delimiters',
     [('field', _get_field_value)], 'img_[field, [3, ], [4, ],]', 'img_3, 4, '),
    
    ('field_args_with_escaped_delimiters_on_arg_bounds',
     [('field', _get_field_value)],
     'img_[field, [[[3, ]]], [[[4, ]]],]',
     'img_[3, ][4, ]'),
    
    ('field_args_with_escaped_delimiters_inside_args',
     [('field', _get_field_value)], 'img_[field, [on[[e], [t[[w]]o],]', 'img_on[et[w]o'),
    
    ('field_with_function_raising_exception_returns_pattern',
     [('field', _get_field_value_raising_exception)], 'img_[field]', 'img_[field]'),
    
    ('unrecognized_field_is_not_processed',
     [('unrecognized field', _get_field_value)],
     'img_[field]',
     'img_[field]'),
    
    ('field_with_delimiters_is_not_processed',
     [(r'\[field\]', _generate_number)],
     'img_[field]',
     'img_[field]'),
    
    ('escaped_delimiters',
     [('field', _get_field_value)], 'img_[[field]]', 'img_[field]'),
    
    ('escaped_delimiters_alongside_fields',
     [('field', _get_field_value)], '[[img [[1]]_[field]', '[img [1]_12'),
    
    ('uneven_number_of_opening_and_closing_delimiters',
     [('field', _get_field_value)], 'img_[field, [1[, ]', 'img_[field, [1[, ]'),
    
    ('escaped_opening_delimiter',
     [('field', _get_field_value)], 'img_[[field', 'img_[field'),
    
    ('unescaped_opening_delimiter',
     [('field', _get_field_value)], 'img_[field', 'img_[field'),
    
    ('unescaped_opening_delimiter_at_end',
     [('field', _get_field_value)], 'img_[field][', 'img_12['),
    
    ('escaped_closing_delimiter',
     [('field', _get_field_value)], 'img_field]]', 'img_field]'),
    
    ('unescaped_closing_delimiter',
     [('field', _get_field_value)], 'img_field]', 'img_field]'),
    
    ('escaped_opening_delimiter_and_unescaped_closing_delimiter',
     [('field', _get_field_value)], 'img_[[field]', 'img_[field]'),
    
    ('unescaped_opening_delimiter_and_escaped_closing_delimiter',
     [('field', _get_field_value)], 'img_[field]]', 'img_12]'),
    
    ('escaped_delimiters_at_ends_fields_fields_inside',
     [('field', _get_field_value)], 'img_[[field] [field]]', 'img_[field] 12]'),
    
    ('unescaped_opening_and_closing_delimiters_at_end',
     [('field', _get_field_value)], 'img_[field[]', 'img_[field[]'),
  ])
  def test_generate_with_fields(
        self, test_case_suffix, fields, pattern, expected_output):
    self.assertEqual(pattern_.StringPattern(pattern, fields).substitute(), expected_output)
  
  @parameterized.parameterized.expand([
    ('field_with_explicit_arguments',
     [('field', _get_field_value)], 'img_[field, 3, 4]', 'img_34'),
    
    ('field_with_explicit_arguments_of_length_more_than_one',
     [('field', _get_field_value)], 'img_[field, one, two]', 'img_onetwo'),
    
    ('field_with_last_default_argument',
     [('field', _get_field_value)], 'img_[field, 3]', 'img_32'),
    
    ('field_with_default_arguments',
     [('field', _get_field_value)], 'img_[field]', 'img_12'),
  ])
  def test_generate_multiple_times_yields_same_field(
        self, test_case_suffix, fields, pattern, expected_output):
    string_pattern = pattern_.StringPattern(pattern, fields)
    num_repeats = 3
    
    outputs = [string_pattern.substitute() for _unused in range(num_repeats)]
    
    self.assertListEqual(outputs, [expected_output] * num_repeats)
  
  @parameterized.parameterized.expand([
    ('regex_single_matching_character',
     [(r'^[0-9]+$', _generate_number)], 'img_[0]', ['img_1', 'img_2', 'img_3']),
    
    ('regex_multiple_matching_characters',
     [(r'^[0-9]+$', _generate_number)], 'img_[42]', ['img_1', 'img_2', 'img_3']),
    
    ('multple_fields_matching_regex',
     [(r'^[0-9]+$', _generate_number)],
     'img_[42]_[0]',
     ['img_1_2', 'img_3_4', 'img_5_6']),
    
    ('non_matching_regex',
     [(r'^[0-9]+$', _generate_number)],
     'img_[abc]',
     ['img_[abc]']),
    
    ('multiple_fields_one_matching_regex',
     [(r'^[0-9]+$', _generate_number),
      (r'^[a-z]+$', _generate_string_with_single_character)],
     'img_[42]_[##]',
     ['img_1_[##]', 'img_2_[##]', 'img_3_[##]']),
    
    ('multiple_matching_regexes_takes_first_matching_regex',
     [(r'^[0-9]+$', _generate_number),
      (r'^[0-9a-z]+$', _generate_string_with_single_character)],
     'img_[42]',
     ['img_1', 'img_2', 'img_3']),
  ])
  def test_generate_with_field_as_regex(
        self, test_case_suffix, fields, pattern, expected_outputs):
    generators = []
    processed_fields = []
    
    for field_regex, generator_func in fields:
      generator = generator_func()
      generators.append(generator)
      processed_fields.append((field_regex, lambda field, gen=generator: next(gen)))
    
    string_pattern = pattern_.StringPattern(pattern, processed_fields)
    outputs = [string_pattern.substitute() for _unused in range(len(expected_outputs))]
    
    self.assertEqual(outputs, expected_outputs)
  
  @parameterized.parameterized.expand([
    ('one_field', 'img_[field]', ['img_1', 'img_2', 'img_3']),
    ('multiple_fields', 'img_[field]_[field]', ['img_1_2', 'img_3_4', 'img_5_6']),
  ])
  def test_generate_with_field_generator(
        self, test_case_suffix, pattern, expected_outputs):
    field_value_generator = _generate_number()
    fields = [('field', lambda field: next(field_value_generator))]
    
    string_pattern = pattern_.StringPattern(pattern, fields)
    outputs = [string_pattern.substitute() for _unused in range(len(expected_outputs))]
    
    self.assertListEqual(outputs, expected_outputs)
  
  @parameterized.parameterized.expand([
    ('with_all_args', 'img_[field, 3, 4]', 'img_34'),
    ('with_no_args', 'img_[field]', 'img_12'),
  ])
  def test_generate_with_fields_with_bound_method(
        self, test_case_suffix, pattern, expected_output):
    class _Field:
      
      @staticmethod
      def get_field_value(_field, arg1=1, arg2=2):
        return f'{arg1}{arg2}'
    
    string_pattern = pattern_.StringPattern(pattern, [('field', _Field().get_field_value)])
    self.assertEqual(string_pattern.substitute(), expected_output)
  
  def test_generate_field_function_with_kwargs_raises_error(self):
    with self.assertRaises(ValueError):
      pattern_.StringPattern('[field, 3, 4]', [('field', _get_field_value_with_kwargs)])
  
  @parameterized.parameterized.expand([
    ('', '', 0, None),
    ('', 'img_12', 0, None),
    ('', 'img_12', 3, None),
    ('', '[layer name]', 0, None),
    ('', '[layer name]', 1, 'layer name'),
    ('', '[layer name]', 5, 'layer name'),
    ('', '[layer name]', 11, 'layer name'),
    ('', '[layer name]', 12, None),
    ('', '[[layer name]', 1, None),
    ('', '[[layer name]', 2, None),
    ('', '[[layer name]', 3, None),
    ('', '[[[layer name]', 1, None),
    ('', '[[[layer name]', 2, None),
    ('', '[[[layer name]', 3, 'layer name'),
    
    ('', 'layer [name]', 2, None),
    ('', 'layer [name]', 6, None),
    ('', 'layer [name]', 7, 'name'),
    ('', 'layer [name] name', 7, 'name'),
    ('', 'layer [name][layer] name', 7, 'name'),
    ('', 'layer [name][layer] name', 13, 'layer'),
    ('', 'layer [name] [layer] name', 7, 'name'),
    ('', 'layer [name] [layer] name', 14, 'layer'),
    ('', 'layer [name] [layer] name', 13, None),
    
    ('', 'layer [[layer [[ name]', 2, None),
    ('', 'layer [[layer [[ name]', 6, None),
    ('', 'layer [[layer [[ name]', 7, None),
    ('', 'layer [[layer [[ name]', 8, None),
    ('', 'layer [[layer [[ name]', 14, None),
    ('', 'layer [[layer [[ name]', 15, None),
    ('', 'layer [[layer [[ name]', 16, None),
    ('', 'layer [[layer [[[name]', 16, None),
    ('', 'layer [[layer [[[name]', 17, 'name'),
    
    ('', '[layer name', 0, None),
    ('', '[layer name', 1, None),
    ('', '[layer [name', 7, None),
    ('', '[layer [name', 8, None),
    
    ('position_greater_than_pattern_length_returns_none', '[layer name]', 100, None),
    ('negative_position_returns_none', '[layer name]', -1, None),
  ])
  def test_get_field_at_position(
        self, test_case_suffix, pattern, position, expected_output):
    self.assertEqual(
      pattern_.StringPattern.get_field_at_position(pattern, position), expected_output)
  
  @parameterized.parameterized.expand([
    ('no_fields', ['img_12', '_345'], 'img_12_345'),
    ('single_field_without_arguments', ['img_', ['field']], 'img_[field]'),
    ('single_field_with_one_argument', ['img_', ['field', [3]]], 'img_[field, 3]'),
    ('single_field_with_multiple_arguments',
     ['img_', ['field', [3, 4]]], 'img_[field, 3, 4]'),
    ('multiple_fields',
     ['img_', ['field', [3, 4]], '_layer_', ['field2'], '.png'],
     'img_[field, 3, 4]_layer_[field2].png'),
  ])
  def test_reconstruct_pattern(
        self, test_case_suffix, pattern_parts, expected_str):
    self.assertEqual(
      pattern_.StringPattern.reconstruct_pattern(pattern_parts), expected_str)
  
  def test_reconstruct_pattern_empty_list_for_field_raises_error(self):
    with self.assertRaises(ValueError):
      pattern_.StringPattern.reconstruct_pattern(['img_', []])
