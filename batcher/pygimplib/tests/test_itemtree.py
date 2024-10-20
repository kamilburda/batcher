"""Tests for the `itemtree` module.

Because the public interface to test is identical for all `ItemTree`
subclasses, it is sufficient to test the `itemtree` module using one of the
subclasses. The `LayerTree` class was chosen for this purpose.
"""
import unittest
import unittest.mock as mock

from . import stubs_gimp
from . import utils_itemtree
from .. import itemtree as pgitemtree
from .. import utils as pgutils


class TestLayerTree(unittest.TestCase):

  def setUp(self):
    items_string = """
      Corners {
        top-left-corner
        top-right-corner
        top-left-corner: {
        }
        top-left-corner:: {
          bottom-right-corner
          bottom-left-corner
        }
      }
      Frames {
        top-frame
      }
      main-background.jpg
      Overlay {
      }
    """
    
    image = utils_itemtree.parse_layers(items_string)
    # noinspection PyTypeChecker
    self.item_tree = pgitemtree.LayerTree(image)
    
    self.ITEM = pgitemtree.TYPE_ITEM
    self.GROUP = pgitemtree.TYPE_GROUP
    self.FOLDER = pgitemtree.TYPE_FOLDER
    
    self.FOLDER_KEY = pgitemtree.FOLDER_KEY
    
    self.item_properties = [
      ('Corners',
       self.FOLDER,
       [],
       [('top-left-corner', self.ITEM),
        ('top-right-corner', self.ITEM),
        ('top-left-corner:', self.FOLDER),
        ('top-left-corner:', self.GROUP),
        ('top-left-corner::', self.FOLDER),
        ('top-left-corner::', self.GROUP)]),
      ('top-left-corner', self.ITEM, [('Corners', self.FOLDER)], []),
      ('top-right-corner', self.ITEM, [('Corners', self.FOLDER)], []),
      ('top-left-corner:', self.FOLDER, [('Corners', self.FOLDER)], []),
      ('top-left-corner:', self.GROUP, [('Corners', self.FOLDER)], []),
      ('top-left-corner::',
       self.FOLDER,
       [('Corners', self.FOLDER)],
       [('bottom-right-corner', self.ITEM), ('bottom-left-corner', self.ITEM)]),
      ('bottom-right-corner',
       self.ITEM,
       [('Corners', self.FOLDER), ('top-left-corner::', self.FOLDER)],
       []),
      ('bottom-left-corner',
       self.ITEM,
       [('Corners', self.FOLDER), ('top-left-corner::', self.FOLDER)],
       []),
      ('top-left-corner::', self.GROUP, [('Corners', self.FOLDER)], []),
      ('Corners', self.GROUP, [], []),
      ('Frames', self.FOLDER, [], [('top-frame', self.ITEM)]),
      ('top-frame', self.ITEM, [('Frames', self.FOLDER)], []),
      ('Frames', self.GROUP, [], []),
      ('main-background.jpg', self.ITEM, [], []),
      ('Overlay', self.FOLDER, [], []),
      ('Overlay', self.GROUP, [], []),
    ]

  def test_getitem(self):
    item = next(self.item_tree.iter(with_folders=False))

    self.assertEqual(self.item_tree[item.raw], item)
    self.assertEqual(self.item_tree[item.raw.get_id()], item)

    item_path = tuple(item_.orig_name for item_ in (list(item.parents) + [item]))
    self.assertEqual(self.item_tree[item_path], item)

    folder_item = next(self.item_tree.iter(with_folders=True))

    self.assertEqual(self.item_tree[folder_item.raw, self.FOLDER_KEY], folder_item)
    self.assertEqual(self.item_tree[folder_item.raw.get_id(), self.FOLDER_KEY], folder_item)

    folder_item_path = tuple(
      item_.orig_name for item_ in (list(folder_item.parents) + [folder_item]))
    self.assertEqual(self.item_tree[folder_item_path, self.FOLDER_KEY], folder_item)

  def test_contains(self):
    item = next(self.item_tree.iter())

    self.assertIn(item.raw, self.item_tree)
    self.assertIn(item.raw.get_id(), self.item_tree)

    item_path = tuple(item_.orig_name for item_ in (list(item.parents) + [item]))
    self.assertIn(item_path, self.item_tree)
  
  def test_item_attributes(self):
    for item, properties in zip(
          self.item_tree.iter(with_folders=True, with_empty_groups=True), self.item_properties):
      self.assertEqual(item.orig_name, properties[0])
      self.assertEqual(item.type, properties[1])
      
      parents = properties[2]
      children = properties[3]
      
      for (expected_parent_name, expected_parent_type), parent in zip(parents, item.parents):
        self.assertEqual(parent.orig_name, expected_parent_name)
        self.assertEqual(parent.type, expected_parent_type)
      
      for (expected_child_name, expected_child_type), child in zip(children, item.children):
        self.assertEqual(child.orig_name, expected_child_name)
        self.assertEqual(child.type, expected_child_type)
      
      self.assertEqual(item.parents, list(item.orig_parents))
      self.assertEqual(item.children, list(item.orig_children))
  
  def test_iter_with_different_item_types_excluded(self):
    limited_item_properties = [properties[:2] for properties in self.item_properties]

    item_properties_without_empty_groups = list(limited_item_properties)
    del item_properties_without_empty_groups[
      item_properties_without_empty_groups.index(
        ('Overlay', self.FOLDER)) + 1]
    del item_properties_without_empty_groups[
      item_properties_without_empty_groups.index(
        ('top-left-corner:', self.FOLDER)) + 1]

    item_properties_without_folders_and_empty_groups = [
      (name, type_) for name, type_ in limited_item_properties if type_ != self.FOLDER]
    del item_properties_without_folders_and_empty_groups[
      item_properties_without_folders_and_empty_groups.index(
        ('Overlay', self.GROUP))]
    del item_properties_without_folders_and_empty_groups[
      item_properties_without_folders_and_empty_groups.index(
        ('top-left-corner:', self.GROUP))]

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(with_empty_groups=True), limited_item_properties):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(), item_properties_without_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(with_folders=False),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.item_tree,
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

  def test_reversed(self):
    limited_item_properties = list(
      reversed([properties[:2] for properties in self.item_properties]))

    item_properties_without_empty_groups = list(limited_item_properties)
    del item_properties_without_empty_groups[
      item_properties_without_empty_groups.index(
        ('Overlay', self.FOLDER)) - 1]
    del item_properties_without_empty_groups[
      item_properties_without_empty_groups.index(
        ('top-left-corner:', self.FOLDER)) - 1]

    item_properties_without_folders_and_empty_groups = [
      (name, type_) for name, type_ in limited_item_properties if type_ != self.FOLDER]
    del item_properties_without_folders_and_empty_groups[
      item_properties_without_folders_and_empty_groups.index(
        ('Overlay', self.GROUP))]
    del item_properties_without_folders_and_empty_groups[
      item_properties_without_folders_and_empty_groups.index(
        ('top-left-corner:', self.GROUP))]

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(with_empty_groups=True, reverse=True), limited_item_properties):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(reverse=True), item_properties_without_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.item_tree.iter(with_folders=False, reverse=True),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          reversed(self.item_tree),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

  def test_len(self):
    self.assertEqual(len(list(self.item_tree.iter())), 14)
    self.assertEqual(len(list(self.item_tree.iter(with_empty_groups=True))), 16)
    
    self.assertEqual(len(self.item_tree), 9)
    
    self.item_tree.filter.add(lambda item: item.type == self.ITEM)
    
    self.assertEqual(len(self.item_tree), 6)
  
  def test_prev(self):
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Frames', 'top-frame')]),
      self.item_tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Corners', 'top-right-corner')]),
      self.item_tree[('Corners', 'top-left-corner')])
    
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Frames', 'top-frame')]),
      self.item_tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Frames', 'top-frame')], with_folders=False),
      self.item_tree[('Corners',)])
    
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY]),
      self.item_tree[('Corners', 'top-left-corner:'), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.prev(
        self.item_tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY], with_empty_groups=True),
      self.item_tree[('Corners', 'top-left-corner:')])
    
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Corners',), self.FOLDER_KEY]),
      None)
    
    self.item_tree.filter.add(lambda item: item.type != self.ITEM)
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Corners', 'top-left-corner::')]),
      self.item_tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.prev(self.item_tree[('Corners', 'top-left-corner::')], filtered=False),
      self.item_tree[('Corners', 'top-left-corner::', 'bottom-left-corner')])
  
  def test_next(self):
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Frames',), self.FOLDER_KEY]),
      self.item_tree[('Frames', 'top-frame')])
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Corners', 'top-left-corner')]),
      self.item_tree[('Corners', 'top-right-corner')])
    
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Corners',)]),
      self.item_tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Corners',)], with_folders=False),
      self.item_tree[('Frames', 'top-frame')])
    
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Overlay',), self.FOLDER_KEY]),
      None)
    self.assertEqual(
      self.item_tree.next(
        self.item_tree[('Overlay',), self.FOLDER_KEY], with_empty_groups=True),
      self.item_tree[('Overlay',)])
    
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Overlay',)]),
      None)
    
    self.item_tree.filter.add(lambda item: item.type != self.ITEM)
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Corners',), self.FOLDER_KEY]),
      self.item_tree[('Corners', 'top-left-corner:'), self.FOLDER_KEY])
    self.assertEqual(
      self.item_tree.next(self.item_tree[('Corners',), self.FOLDER_KEY], filtered=False),
      self.item_tree[('Corners', 'top-left-corner')])


class TestItem(unittest.TestCase):

  def setUp(self):
    self.ITEM = pgitemtree.TYPE_ITEM
    self.GROUP = pgitemtree.TYPE_GROUP
    self.FOLDER = pgitemtree.TYPE_FOLDER

    # noinspection PyTypeChecker
    self.item = pgitemtree.Item(stubs_gimp.Layer(name='main-background.jpg'), self.ITEM)
  
  def test_str(self):
    self.assertEqual(str(self.item), '<Item "main-background.jpg">')
    
    self.item.name = 'main-background'
    
    self.assertEqual(str(self.item), '<Item "main-background.jpg">')

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.utils.id', return_value=2208603083056)
  def test_repr(self, mock_id):
    self.assertEqual(
      repr(self.item),
      '<{}.itemtree.Item "main-background.jpg {}" at 0x0000002023b009130>'.format(
        pgutils.get_pygimplib_module_path(),
        type(self.item.raw),
      ),
    )
  
  def test_reset(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']
    
    self.item.reset()
    
    self.assertEqual(self.item.name, 'main-background.jpg')
    self.assertEqual(self.item.parents, [])
    self.assertEqual(self.item.children, [])
  
  def test_push_and_pop_state(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']
    
    self.item.push_state()
    self.item.reset()
    self.item.pop_state()
    
    self.assertEqual(self.item.name, 'main')
    self.assertEqual(self.item.parents, ['one', 'two'])
    self.assertEqual(self.item.children, ['three', 'four'])
  
  def test_pop_state_with_no_saved_state(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']
    
    self.item.pop_state()
    
    self.assertEqual(self.item.name, 'main')
    self.assertEqual(self.item.parents, ['one', 'two'])
    self.assertEqual(self.item.children, ['three', 'four'])

  def test_save_and_get_named_state(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']

    self.item.save_state('export')

    named_state = self.item.get_named_state('export')

    self.assertDictEqual(
      named_state, {'name': 'main', 'parents': ['one', 'two'], 'children': ['three', 'four']})

  def test_save_and_get_named_state_for_the_same_name_overrides_previous_calls(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']

    self.item.save_state('export')

    self.item.name = 'advanced'

    self.item.save_state('export')

    named_state = self.item.get_named_state('export')

    self.assertDictEqual(
      named_state, {'name': 'advanced', 'parents': ['one', 'two'], 'children': ['three', 'four']})

  def test_get_named_state_for_no_saved_state(self):
    self.item.name = 'main'
    self.item.parents = ['one', 'two']
    self.item.children = ['three', 'four']

    self.assertIsNone(self.item.get_named_state('export'))
