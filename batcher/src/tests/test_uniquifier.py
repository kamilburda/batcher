import unittest

import pygimplib as pg
from pygimplib.tests import utils_itemtree

from src import uniquifier


class TestUniquify(unittest.TestCase):

  def setUp(self):
    self.uniquifier = uniquifier.ItemUniquifier()
    
    items_string = """
      Corners {
        top-left-corner
        top-right-corner
        top-left-corner: {
        }
        top-left-corner:: {
          bottom-right-corner
          bottom-right-corner:
          bottom-left-corner
        }
      }
      Corners: {
        top-left-corner:::
      }
      Frames {
        top-frame
      }
      main-background.jpg
      main-background.jpg:
      Corners::
      top-left-corner::::
      main-background.jpg:: {
        alt-frames
        alt-corners
      }
    """
    
    image = utils_itemtree.parse_layers(items_string)
    self.item_tree = pg.itemtree.LayerTree(image)

  def test_uniquify(self):
    uniquified_names = {
      (('Corners',), 'folder'): ['Corners'],
      ('Corners',): ['Corners (1)'],
      ('Corners', 'top-left-corner'): ['Corners', 'top-left-corner'],
      ('Corners', 'top-right-corner'): ['Corners', 'top-right-corner'],
      (('Corners', 'top-left-corner:'), 'folder'): ['Corners', 'top-left-corner (1)'],
      (('Corners', 'top-left-corner::'), 'folder'): ['Corners', 'top-left-corner (2)'],
      ('Corners', 'top-left-corner::'): ['Corners', 'top-left-corner (3)'],
      ('Corners', 'top-left-corner::', 'bottom-right-corner'): [
        'Corners', 'top-left-corner (2)', 'bottom-right-corner'],
      ('Corners', 'top-left-corner::', 'bottom-right-corner:'): [
        'Corners', 'top-left-corner (2)', 'bottom-right-corner (1)'],
      ('Corners', 'top-left-corner::', 'bottom-left-corner'): [
        'Corners', 'top-left-corner (2)', 'bottom-left-corner'],
      (('Corners:',), 'folder'): ['Corners (2)'],
      ('Corners:',): ['Corners (3)'],
      ('Corners:', 'top-left-corner:::'): ['Corners (2)', 'top-left-corner'],
      (('Frames',), 'folder'): ['Frames'],
      ('Frames',): ['Frames (1)'],
      ('Frames', 'top-frame'): ['Frames', 'top-frame'],
      ('main-background.jpg',): ['main-background.jpg'],
      ('main-background.jpg:',): ['main-background.jpg (1)'],
      ('Corners::',): ['Corners (4)'],
      ('top-left-corner::::',): ['top-left-corner'],
      (('main-background.jpg::',), 'folder'): ['main-background.jpg (2)'],
      ('main-background.jpg::',): ['main-background.jpg (3)'],
      ('main-background.jpg::', 'alt-frames'): ['main-background.jpg (2)', 'alt-frames'],
      ('main-background.jpg::', 'alt-corners'): ['main-background.jpg (2)', 'alt-corners'],
    }

    for item in self.item_tree.iter():
      self._preprocess_name(item)
      item.name = self.uniquifier.uniquify(item)

    self._compare_uniquified_names(self.item_tree, uniquified_names)

  def test_uniquify_with_custom_position(self):
    def _get_file_extension_start_position(str_):
      position = str_.rfind('.')
      if position == -1:
        position = len(str_)
      return position
    
    names_to_uniquify = {
      ('main-background.jpg',): ['main-background.jpg'],
      ('main-background.jpg:',): ['main-background (1).jpg'],
      (('main-background.jpg::',), 'folder'): ['main-background.jpg (1)'],
      ('main-background.jpg::',): ['main-background (2).jpg'],
    }
    
    for item_path in names_to_uniquify:
      item = self.item_tree[item_path]
      
      self._preprocess_name(item)
      if item.type == pg.itemtree.TYPE_FOLDER:
        item.name = self.uniquifier.uniquify(item)
      else:
        item.name = self.uniquifier.uniquify(
          item, position=_get_file_extension_start_position(item.name))
    
    self._compare_uniquified_names(self.item_tree, names_to_uniquify)

  def test_uniquify_does_not_modify_already_passed_items(self):
    names_to_uniquify = {
      ('main-background.jpg',): ['main-background.jpg'],
      ('main-background.jpg:',): ['main-background.jpg (1)'],
      (('main-background.jpg::',), 'folder'): ['main-background.jpg (2)'],
      ('main-background.jpg::',): ['main-background.jpg (3)'],
    }
    
    for item_path in names_to_uniquify:
      item = self.item_tree[item_path]
      
      self._preprocess_name(item)
      item.name = self.uniquifier.uniquify(item)
    
    for item_path in names_to_uniquify:
      item = self.item_tree[item_path]
      item.name = self.uniquifier.uniquify(item)
    
    self._compare_uniquified_names(self.item_tree, names_to_uniquify)

  def test_reset(self):
    names_to_uniquify = {
      ('main-background.jpg',): ['main-background.jpg'],
      ('main-background.jpg:',): ['main-background.jpg (1)'],
    }
    
    for item_path in names_to_uniquify:
      item = self.item_tree[item_path]
      
      self._preprocess_name(item)
      item.name = self.uniquifier.uniquify(item)
    
    self.uniquifier.reset()
    
    self.item_tree[('main-background.jpg:',)].name = 'main-background.jpg'
    
    for item_path in names_to_uniquify:
      item = self.item_tree[item_path]
      item.name = self.uniquifier.uniquify(item)
    
    self._compare_uniquified_names(self.item_tree, names_to_uniquify)
  
  def _compare_uniquified_names(self, item_tree, uniquified_names):
    for key, item_path in uniquified_names.items():
      expected_path_components, name = item_path[:-1], item_path[-1]
      actual_path_components = [parent.name for parent in item_tree[key].parents]
      
      self.assertEqual(
        actual_path_components,
        expected_path_components,
        f'parents: "{key}": "{actual_path_components}" != "{expected_path_components}"')

      self.assertEqual(
        item_tree[key].name,
        name,
        f'item name: "{key}": "{item_tree[key].name}" != "{name}"')
  
  @staticmethod
  def _preprocess_name(item):
    item.name = item.name.replace(':', '')
