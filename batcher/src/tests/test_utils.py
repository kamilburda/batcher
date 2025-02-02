import unittest

import parameterized

from src import utils


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
      'type': 'procedure',
    }

    input_copy = utils.semi_deep_copy(input_)

    self.assertDictEqual(input_, input_copy)

    self.assertIsNot(input_, input_copy)

    self.assertIsNot(input_, input_copy)
    self.assertIsNot(input_['additional_tags'], input_copy['additional_tags'])
    self.assertIsNot(input_['arguments'], input_copy['arguments'])
    self.assertIsNot(input_['arguments'][0], input_copy['arguments'][0])
