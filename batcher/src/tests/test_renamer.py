import unittest
import unittest.mock as mock

import parameterized

import pygimplib as pg
from pygimplib.tests import utils_itemtree

from src import renamer as renamer_


class TestNumberField(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('two_padding_zeroes',
     1, 3, ['001', '002', '003']),
    ('one_padding_zero',
     1, 2, ['01', '02', '03']),
    ('start_from_number_greater_than_one',
     5, 3, ['005', '006', '007']),
    ('incrementing_number_to_two_digits_removes_one_padded_zero',
     9, 3, ['009', '010', '011']),
    ('incrementing_number_to_digits_without_padding_removes_last_padded_zero',
     99, 3, ['099', '100', '101']),
    ('incrementing_number_to_more_digits_than_padding',
     999, 3, ['999', '1000', '1001']),
  ])
  def test_generate_number(self, test_case_suffix, initial_number, padding, expected_outputs):
    number_generator = renamer_.NumberField.generate_number(initial_number, padding)
    outputs = [next(number_generator) for _unused in range(len(expected_outputs))]
    
    self.assertListEqual(outputs, expected_outputs)


class TestRenameWithNumberField(unittest.TestCase):

  def setUp(self):
    layers_string = """
      foreground
      Corners {
        corner
        top-left-corner {
          bottom-left-corner
          bottom-right-corner
          top-left-corner
        }
        top-right-corner
      }
      Frames {
        top-frame
      }
      background
      Overlay {
      }
      Overlay2
    """
    
    self.image = utils_itemtree.parse_layers(layers_string)[0]
  
  @parameterized.parameterized.expand([
    ('start_from_one',
     'image[001]',
     """
     image001
     Corners {
       image001
       top-left-corner {
         image001
         image002
         image003
       }
       image002
     }
     Frames {
       image001
     }
     image002
     Overlay {
     }
     image003
     """),
    
    ('start_with_offset',
     'image[003]',
     """
     image003
     Corners {
       image003
       top-left-corner {
         image003
         image004
         image005
       }
       image004
     }
     Frames {
       image003
     }
     image004
     Overlay {
     }
     image005
     """),
    
    ('start_from_tree_length_descending',
     'image[0, %d]',
     """
     image3
     Corners {
       image2
       top-left-corner {
         image3
         image2
         image1
       }
       image1
     }
     Frames {
       image1
     }
     image2
     Overlay {
     }
     image1
     """),
    
    ('start_from_tree_length_descending_custom_padding',
     'image[0, %d2]',
     """
     image03
     Corners {
       image02
       top-left-corner {
         image03
         image02
         image01
       }
       image01
     }
     Frames {
       image01
     }
     image02
     Overlay {
     }
     image01
     """),
    
    ('multiple_different_number_fields_increment_independently',
     'image[001]_[005]',
     """
     image001_005
     Corners {
       image001_005
       top-left-corner {
         image001_005
         image002_006
         image003_007
       }
       image002_006
     }
     Frames {
       image001_005
     }
     image002_006
     Overlay {
     }
     image003_007
     """),
  ])
  def test_rename(self, test_case_suffix, pattern, expected_layer_names_str):
    layer_tree = pg.itemtree.LayerTree()
    layer_tree.add_from_image(self.image)
    layer_tree.filter.add(lambda item_: item_.type == pg.itemtree.TYPE_ITEM)
    
    batcher_mock = mock.Mock()
    batcher_mock.item_tree = layer_tree
    batcher_mock.matching_items = layer_tree
    
    renamer = renamer_.ItemRenamer(pattern, fields_raw=[renamer_.FIELDS_FOR_LAYERS['^[0-9]+$']])
    
    for item in layer_tree:
      batcher_mock.current_item = item
      item.name = renamer.rename(batcher_mock)
    
    expected_layer_tree = pg.itemtree.LayerTree()
    expected_layer_tree.add_from_image(utils_itemtree.parse_layers(expected_layer_names_str)[0])
    
    self.assertListEqual(
      [renamed_item.name for renamed_item in layer_tree.iter(with_folders=False, filtered=False)],
      [expected_item.name for expected_item in expected_layer_tree])
