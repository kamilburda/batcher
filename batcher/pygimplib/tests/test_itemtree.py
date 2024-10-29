"""Tests for the `itemtree` module.

Because the public interface for `GimpItemTree` is identical for all its
subclasses and their implementation only differs in which types of child
objects are listed, it is sufficient to test the `GimpItemTree` using only
one of its subclasses. The `LayerTree` class was chosen for this purpose.
"""
import os

import unittest
import unittest.mock as mock

import parameterized

from . import stubs_gimp
from . import utils_itemtree
from .. import itemtree as pgitemtree
from .. import utils as pgutils


@mock.patch(f'{pgutils.get_pygimplib_module_path()}.itemtree.os.path.isdir')
@mock.patch(f'{pgutils.get_pygimplib_module_path()}.itemtree.os.listdir')
@mock.patch(f'{pgutils.get_pygimplib_module_path()}.itemtree.os.path.abspath')
class TestImageTree(unittest.TestCase):

  def setUp(self):
    self.paths = [
      ['Corners', 'Frames', 'main-background.jpg', 'Overlay'],
      ['Corners', ['top-left.png', 'top-right.png', 'top-left2', 'top-left3']],
      ['top-left2', []],
      ['top-left3', ['bottom-right.png', 'bottom-left.png']],
      ['Frames', ['top.png']],
      ['Overlay', []],
    ]

    self.expected_keys_and_paths = {
      ('Corners',): (['Corners'], True),
      ('Corners', 'top-left.png'): (['Corners', 'top-left.png'], False),
      ('Corners', 'top-left2'): (['Corners', 'top-left2'], True),
      ('Corners', 'top-left3'): (['Corners', 'top-left3'], True),
      ('Corners', 'top-left3', 'bottom-left.png'): (
        ['Corners', 'top-left3', 'bottom-left.png'], False),
      ('Corners', 'top-left3', 'bottom-right.png'): (
        ['Corners', 'top-left3', 'bottom-right.png'], False),
      ('Corners', 'top-right.png'): (['Corners', 'top-right.png'], False),
      ('Frames',): (['Frames'], True),
      ('Frames', 'top.png'): (['Frames', 'top.png'], False),
      ('main-background.jpg',): (['main-background.jpg'], False),
      ('Overlay',): (['Overlay'], True),
    }

    self.mock_isdir_return_values = [
      True, True, False, True, False, True, True, False, False, False, False]

    self.root_path = 'some_path'

    self.FOLDER_KEY = pgitemtree.FOLDER_KEY

    self.tree = pgitemtree.ImageTree()

  def test_add(self, mock_abspath, mock_listdir, mock_isdir):
    self._set_up_tree_before_add(mock_abspath, mock_listdir, mock_isdir)

    self.tree.add(self.paths[0])

    self.assertEqual(mock_isdir.call_count, len(self.mock_isdir_return_values))

    for key, path_and_is_folder in self.expected_keys_and_paths.items():
      path, is_folder = path_and_is_folder
      if is_folder:
        self.assertEqual(
          self.tree[os.path.join(self.root_path, *key), self.FOLDER_KEY].id,
          os.path.join(self.root_path, *path))
      else:
        self.assertEqual(
          self.tree[os.path.join(self.root_path, *key)].id,
          os.path.join(self.root_path, *path))

  @parameterized.parameterized.expand([
    ('after_last_item',
     None,
     [('bottom-left2.png', False)],
     (['Overlay'], True),
     None,
     ),

    ('after_first_item',
     (['Corners'], True),
     [('bottom-left2.png', False)],
     (['Corners'], True),
     (['Corners', 'top-left.png'], False),
     ),

    ('multiple_items_after_not_first_or_last_item',
     (['Corners', 'top-left3'], True),
     [('bottom-left2.png', False), ('bottom-left3.png', False), ('bottom-left4.png', False)],
     (['Corners', 'top-left3'], True),
     (['Corners', 'top-left3', 'bottom-left.png'], False),
     ),
  ])
  def test_add_additional_time(
        self,
        mock_abspath,
        mock_listdir,
        mock_isdir,
        test_case_name_suffix,
        insert_after_path_and_is_folder_indicator,
        paths_and_is_folder_indicators,
        prev_item_path_and_is_folder_indicator,
        next_item_path_and_is_folder_indicator,
  ):
    self._set_up_tree_before_add(mock_abspath, mock_listdir, mock_isdir)

    self.tree.add(self.paths[0])

    mock_isdir.side_effect = [item[1] for item in paths_and_is_folder_indicators]
    objects_to_add = [item[0] for item in paths_and_is_folder_indicators]

    if insert_after_path_and_is_folder_indicator is None:
      insert_after_item = None
    else:
      insert_after_path = os.path.join(self.root_path, *insert_after_path_and_is_folder_indicator[0])
      insert_after_key = (
        (insert_after_path, self.FOLDER_KEY)
        if insert_after_path_and_is_folder_indicator[1] else insert_after_path
      )
      insert_after_item = self.tree[insert_after_key]

    self.tree.add(objects_to_add, insert_after_item=insert_after_item)

    added_keys = [os.path.join(self.root_path, object_to_add) for object_to_add in objects_to_add]

    prev_item_path = os.path.join(self.root_path, *prev_item_path_and_is_folder_indicator[0])
    prev_item_key = (
      (prev_item_path, self.FOLDER_KEY)
      if prev_item_path_and_is_folder_indicator[1] else prev_item_path
    )

    if insert_after_item is None:
      next_item = None
      next_item_key = None
    else:
      next_item_path = os.path.join(self.root_path, *next_item_path_and_is_folder_indicator[0])
      next_item_key = (
        (next_item_path, self.FOLDER_KEY)
        if next_item_path_and_is_folder_indicator[1] else next_item_path
      )
      next_item = self.tree[next_item_key]

    self.maxDiff = None

    for key in added_keys:
      self.assertIn(key, self.tree)

    self.assertEqual(self.tree[added_keys[0]].prev, self.tree[prev_item_key])
    self.assertEqual(self.tree[prev_item_key].next, self.tree[added_keys[0]])
    self.assertEqual(self.tree[added_keys[-1]].next, next_item)
    if next_item_key is not None:
      self.assertEqual(self.tree[next_item_key].prev, self.tree[added_keys[-1]])

    expected_keys = self._get_keys_from_expected_paths()
    prev_item_key_index = expected_keys.index(prev_item_key) + 1

    expected_keys = (
      expected_keys[:prev_item_key_index] + added_keys + expected_keys[prev_item_key_index:])

    self.assertListEqual(
      [item for item in self.tree.iter_all()],
      [self.tree[key] for key in expected_keys])

  def _set_up_tree_before_add(self, mock_abspath, mock_listdir, mock_isdir):
    mock_abspath.side_effect = (
      lambda path_: (
        os.path.join(self.root_path, path_)
        if not path_.startswith(self.root_path) else path_))
    mock_listdir.side_effect = [item[1] for item in self.paths[1:]]
    mock_isdir.side_effect = self.mock_isdir_return_values

  def _get_keys_from_expected_paths(self):
    return [
      (os.path.join(self.root_path, *path[0]), self.FOLDER_KEY)
      if path[1]
      else os.path.join(self.root_path, *path[0])
      for path in self.expected_keys_and_paths.values()
    ]


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
    self.tree = pgitemtree.LayerTree(image)
    
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
    item = next(self.tree.iter(with_folders=False))

    self.assertEqual(self.tree[item.raw], item)
    self.assertEqual(self.tree[item.raw.get_id()], item)

    item_path = tuple(item_.orig_name for item_ in (list(item.parents) + [item]))
    self.assertEqual(self.tree[item_path], item)

    folder_item = next(self.tree.iter(with_folders=True))

    self.assertEqual(self.tree[folder_item.raw, self.FOLDER_KEY], folder_item)
    self.assertEqual(self.tree[folder_item.raw.get_id(), self.FOLDER_KEY], folder_item)

    folder_item_path = tuple(
      item_.orig_name for item_ in (list(folder_item.parents) + [folder_item]))
    self.assertEqual(self.tree[folder_item_path, self.FOLDER_KEY], folder_item)

  def test_contains(self):
    item = next(self.tree.iter())

    self.assertIn(item.raw, self.tree)
    self.assertIn(item.raw.get_id(), self.tree)

    item_path = tuple(item_.orig_name for item_ in (list(item.parents) + [item]))
    self.assertIn(item_path, self.tree)
  
  def test_item_attributes(self):
    for item, properties in zip(
          self.tree.iter(with_folders=True, with_empty_groups=True), self.item_properties):
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
          self.tree.iter(with_empty_groups=True), limited_item_properties):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.tree.iter(), item_properties_without_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.tree.iter(with_folders=False),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.tree,
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
          self.tree.iter(with_empty_groups=True, reverse=True), limited_item_properties):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.tree.iter(reverse=True), item_properties_without_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          self.tree.iter(with_folders=False, reverse=True),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

    for item, (item_name, item_type) in zip(
          reversed(self.tree),
          item_properties_without_folders_and_empty_groups):
      self.assertEqual(item.name, item_name)
      self.assertEqual(item.type, item_type)

  def test_len(self):
    self.assertEqual(len(list(self.tree.iter())), 14)
    self.assertEqual(len(list(self.tree.iter(with_empty_groups=True))), 16)
    
    self.assertEqual(len(self.tree), 9)
    
    self.tree.filter.add(lambda item: item.type == self.ITEM)
    
    self.assertEqual(len(self.tree), 6)
  
  def test_prev(self):
    self.assertEqual(
      self.tree.prev(self.tree[('Frames', 'top-frame')]),
      self.tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.prev(self.tree[('Corners', 'top-right-corner')]),
      self.tree[('Corners', 'top-left-corner')])
    
    self.assertEqual(
      self.tree.prev(self.tree[('Frames', 'top-frame')]),
      self.tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.prev(self.tree[('Frames', 'top-frame')], with_folders=False),
      self.tree[('Corners',)])
    
    self.assertEqual(
      self.tree.prev(self.tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY]),
      self.tree[('Corners', 'top-left-corner:'), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.prev(
        self.tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY], with_empty_groups=True),
      self.tree[('Corners', 'top-left-corner:')])
    
    self.assertEqual(
      self.tree.prev(self.tree[('Corners',), self.FOLDER_KEY]),
      None)
    
    self.tree.filter.add(lambda item: item.type != self.ITEM)
    self.assertEqual(
      self.tree.prev(self.tree[('Corners', 'top-left-corner::')]),
      self.tree[('Corners', 'top-left-corner::'), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.prev(self.tree[('Corners', 'top-left-corner::')], filtered=False),
      self.tree[('Corners', 'top-left-corner::', 'bottom-left-corner')])
  
  def test_next(self):
    self.assertEqual(
      self.tree.next(self.tree[('Frames',), self.FOLDER_KEY]),
      self.tree[('Frames', 'top-frame')])
    self.assertEqual(
      self.tree.next(self.tree[('Corners', 'top-left-corner')]),
      self.tree[('Corners', 'top-right-corner')])
    
    self.assertEqual(
      self.tree.next(self.tree[('Corners',)]),
      self.tree[('Frames',), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.next(self.tree[('Corners',)], with_folders=False),
      self.tree[('Frames', 'top-frame')])
    
    self.assertEqual(
      self.tree.next(self.tree[('Overlay',), self.FOLDER_KEY]),
      None)
    self.assertEqual(
      self.tree.next(
        self.tree[('Overlay',), self.FOLDER_KEY], with_empty_groups=True),
      self.tree[('Overlay',)])
    
    self.assertEqual(
      self.tree.next(self.tree[('Overlay',)]),
      None)
    
    self.tree.filter.add(lambda item: item.type != self.ITEM)
    self.assertEqual(
      self.tree.next(self.tree[('Corners',), self.FOLDER_KEY]),
      self.tree[('Corners', 'top-left-corner:'), self.FOLDER_KEY])
    self.assertEqual(
      self.tree.next(self.tree[('Corners',), self.FOLDER_KEY], filtered=False),
      self.tree[('Corners', 'top-left-corner')])


class TestGimpItem(unittest.TestCase):

  def setUp(self):
    self.ITEM = pgitemtree.TYPE_ITEM
    self.GROUP = pgitemtree.TYPE_GROUP
    self.FOLDER = pgitemtree.TYPE_FOLDER

    # noinspection PyTypeChecker
    self.item = pgitemtree.GimpItem(stubs_gimp.Layer(name='main-background.jpg'), self.ITEM)
  
  def test_str(self):
    self.assertEqual(str(self.item), '<GimpItem "main-background.jpg">')
    
    self.item.name = 'main-background'
    
    self.assertEqual(str(self.item), '<GimpItem "main-background.jpg">')

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.utils.id', return_value=2208603083056)
  def test_repr(self, mock_id):
    self.assertEqual(
      repr(self.item),
      '<{}.itemtree.GimpItem "main-background.jpg {}" at 0x0000002023b009130>'.format(
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
