"""Parsing data from a GIMP config/preset file and persisting data to a
config/preset.
"""
import io
from typing import List, Tuple, Union


COMMENT_TOKEN = '#'
START_ARGUMENT_TOKEN = '('
END_ARGUMENT_TOKEN = ')'
START_END_STRING_TOKEN = '"'
ARGUMENT_NAME_WORD_SEPARATOR = '-'
STRING_ESCAPE_TOKEN = '\\'


class ParseStates:

  PARSE_STATES = (
    OUTSIDE_ARGUMENT,
    COMMENT,
    ARGUMENT_NAME,
    ARGUMENT_VALUE,
    OUTSIDE_ARGUMENT_VALUE,
    STRING,
    STRING_NEXT_CHAR_TO_ESCAPE,
    NESTED_ARGUMENT_VALUE,
    NESTED_STRING,
    NESTED_STRING_NEXT_CHAR_TO_ESCAPE,
  ) = (
    'outside_argument',
    'comment',
    'argument_name',
    'argument_value',
    'outside_argument_value',
    'string',
    'string_next_char_to_escape',
    'nested_argument_value',
    'nested_string',
    'nested_string_next_char_to_escape',
  )


class GimpConfigParseError(Exception):
  pass


def parse(filepath: str) -> List[Tuple[str, List[str]]]:
  r"""Parses data from a file containing saved settings for a GIMP plug-in or a
  layer effect (GEGL operation)

  A GIMP settings file usually contains name-values pairs as
  `(name value1 value2 ...)`, e.g. `(hue 0.5)`.

  Strings enclosed in double quotes may contain whitespace or escaped special
  characters using `\`, e.g. `\"` or `\n`. These are kept intact.

  Args:
    filepath: Path to the GIMP settings file.

  Returns:
    A list of (setting name, list of values) pairs.
  """
  with open(filepath, 'r') as file:
    return _parse_data(file)


def _parse_data(file):

  def _add_argument():
    nonlocal parsed_data
    nonlocal current_arg_name_chars
    nonlocal current_arg_name
    nonlocal current_arg_value_chars
    nonlocal current_arg_values

    processed_arg_name = _parsed_argument_name_to_canonical_name(current_arg_name)

    parsed_data.append((processed_arg_name, current_arg_values))

    current_arg_name_chars = []
    current_arg_name = ''
    current_arg_value_chars = []
    current_arg_values = []

  def _add_argument_value(
        convert_null_to_none=True,
        parse_nested=False,
  ):
    nonlocal current_arg_value_chars
    nonlocal current_arg_values

    value = ''.join(current_arg_value_chars)

    if parse_nested:
      stream = io.StringIO()
      stream.write(value)
      stream.seek(0)

      parsed_value = _parse_data(stream)

      current_arg_values.append(parsed_value)
    else:
      if value == 'NULL':
        if convert_null_to_none:
          value = None

      current_arg_values.append(value)

    current_arg_value_chars = []

  parsed_data = []

  state = ParseStates.OUTSIDE_ARGUMENT
  current_arg_name_chars = []
  current_arg_name = ''
  current_arg_value_chars = []
  current_arg_values: List[Union[str, None, List]] = []

  chunk_size = 8192

  line_index = 1
  depth = 0

  while True:
    chunk = file.read(chunk_size)

    if not chunk:
      break

    for char in chunk:
      if char == '\n':
        line_index += 1

      if state == ParseStates.OUTSIDE_ARGUMENT:
        if char == START_ARGUMENT_TOKEN:
          depth += 1

          state = ParseStates.ARGUMENT_NAME
        elif char.isspace():
          continue
        elif char == COMMENT_TOKEN:
          state = ParseStates.COMMENT
        else:
          raise GimpConfigParseError(f'invalid character at line {line_index}: "{char}"')
      elif state == ParseStates.COMMENT:
        if char == '\n':
          state = ParseStates.OUTSIDE_ARGUMENT
        else:
          continue
      elif state == ParseStates.ARGUMENT_NAME:
        if char.isspace():
          if current_arg_name_chars:
            current_arg_name = ''.join(current_arg_name_chars)
            current_arg_name_chars = []

            state = ParseStates.OUTSIDE_ARGUMENT_VALUE
        elif char.isalnum() or char == ARGUMENT_NAME_WORD_SEPARATOR:
          current_arg_name_chars.append(char)
        else:
          raise GimpConfigParseError(f'invalid character at line {line_index}: "{char}"')
      elif state == ParseStates.OUTSIDE_ARGUMENT_VALUE:
        if char.isspace():
          continue
        elif char == START_END_STRING_TOKEN:
          state = ParseStates.STRING
        elif char == END_ARGUMENT_TOKEN:
          if current_arg_values:
            _add_argument()
          else:
            raise GimpConfigParseError(
              f'argument "{current_arg_name}" at line {line_index} has no value(s)')

          depth -= 1

          assert depth == 0, f'Error at line {line_index}: depth is not 0'

          state = ParseStates.OUTSIDE_ARGUMENT
        elif char == START_ARGUMENT_TOKEN:
          current_arg_value_chars.append(char)

          depth += 1

          state = ParseStates.NESTED_ARGUMENT_VALUE
        else:
          current_arg_value_chars.append(char)

          state = ParseStates.ARGUMENT_VALUE
      elif state == ParseStates.ARGUMENT_VALUE:
        if char.isspace():
          if current_arg_value_chars:
            _add_argument_value()

          state = ParseStates.OUTSIDE_ARGUMENT_VALUE
        elif char == END_ARGUMENT_TOKEN:
          if current_arg_value_chars:
            _add_argument_value()

            _add_argument()

          depth -= 1

          assert depth == 0, f'Error at line {line_index}: depth is not 0'

          state = ParseStates.OUTSIDE_ARGUMENT
        elif char == START_END_STRING_TOKEN:
          raise GimpConfigParseError(f'invalid character at line {line_index}: "{char}"')
        elif char == START_ARGUMENT_TOKEN:
          current_arg_value_chars.append(char)

          depth += 1

          state = ParseStates.NESTED_ARGUMENT_VALUE
        else:
          current_arg_value_chars.append(char)
      elif state == ParseStates.STRING:
        if char == START_END_STRING_TOKEN:
          _add_argument_value(convert_null_to_none=False)

          state = ParseStates.OUTSIDE_ARGUMENT_VALUE
        elif char == STRING_ESCAPE_TOKEN:
          current_arg_value_chars.append(char)

          state = ParseStates.STRING_NEXT_CHAR_TO_ESCAPE
        else:
          current_arg_value_chars.append(char)
      elif state == ParseStates.STRING_NEXT_CHAR_TO_ESCAPE:
        current_arg_value_chars.append(char)

        state = ParseStates.STRING
      elif state == ParseStates.NESTED_ARGUMENT_VALUE:
        if char == START_END_STRING_TOKEN:
          current_arg_value_chars.append(char)

          state = ParseStates.NESTED_STRING
        elif char == START_ARGUMENT_TOKEN:
          depth += 1

          current_arg_value_chars.append(char)
        elif char == END_ARGUMENT_TOKEN:
          depth -= 1

          current_arg_value_chars.append(char)

          if depth <= 1:
            _add_argument_value(parse_nested=True)

            state = ParseStates.OUTSIDE_ARGUMENT_VALUE
        else:
          current_arg_value_chars.append(char)
      elif state == ParseStates.NESTED_STRING:
        if char == START_END_STRING_TOKEN:
          current_arg_value_chars.append(char)

          state = ParseStates.NESTED_ARGUMENT_VALUE
        elif char == STRING_ESCAPE_TOKEN:
          current_arg_value_chars.append(char)

          state = ParseStates.NESTED_STRING_NEXT_CHAR_TO_ESCAPE
        else:
          current_arg_value_chars.append(char)
      elif state == ParseStates.NESTED_STRING_NEXT_CHAR_TO_ESCAPE:
        current_arg_value_chars.append(char)

        state = ParseStates.NESTED_STRING
      else:
        raise AssertionError(f'unrecognized parse state: {state}')

  if depth != 0:
    raise GimpConfigParseError('end of config reached without closing an argument')

  return parsed_data


def _parsed_argument_name_to_canonical_name(argument_name):
  return argument_name.replace('_', '-')


def serialize(data: List[Tuple[str, List[str]]], filepath: str):
  with open(filepath, 'w') as file:
    file.write('\n'.join(_serialize_data(data)))


def _serialize_data(data):
  serialized_data = []

  for name, arguments_str in data:
    if arguments_str is not None:
      processed_arguments_str = arguments_str
    else:
      processed_arguments_str = 'NULL'

    separator = ' '

    if (len(processed_arguments_str) >= 1
        and processed_arguments_str[0].startswith(START_ARGUMENT_TOKEN)):
      separator = '\n    '

    serialized_data.append(
      f'{START_ARGUMENT_TOKEN}{name}{separator}{processed_arguments_str}{END_ARGUMENT_TOKEN}')

  return serialized_data
