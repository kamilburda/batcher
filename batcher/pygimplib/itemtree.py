"""Managing items of a GIMP image (e.g. layers) in a tree-like structure."""

from __future__ import annotations

import abc
from collections.abc import Iterable, Iterator
from typing import Generator, List, Optional, Union, Tuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from . import objectfilter as pgobjectfilter
from . import utils as pgutils


TYPE_ITEM, TYPE_GROUP, TYPE_FOLDER = (0, 1, 2)

FOLDER_KEY = 'folder'
"""Key used to access items as folders in `ItemTree` via `__getitem__()`.
See `ItemTree.__getitem__()` for more information.
"""


class Item:
  """Wrapper for a `Gimp.Item` object containing additional attributes.

  Note that the attributes will not be up-to-date if changes were made to the
  original `Gimp.Item` object.
  """

  def __init__(
        self,
        raw_item: Gimp.Item,
        item_type: int,
        parents: Optional[Iterable[Item]] = None,
        children: Optional[Iterable[Item]] = None,
        prev_item: Optional[Item] = None,
        next_item: Optional[Item] = None):
    if raw_item is None:
      raise TypeError('item cannot be None')

    self._raw_item = raw_item
    self._type = item_type
    self._parents = parents if parents is not None else []
    self._children = children if children is not None else []
    self._prev_item = prev_item
    self._next_item = next_item

    self.name = raw_item.get_name()
    """Item name as a string, initially equal to ``orig_name``.
    
    Modify this attribute instead of calling ``Gimp.Item.set_name()`` to avoid
    modifying the original item.
    """

    self._orig_name = self.name
    self._orig_parents = self._parents
    self._orig_children = self._children

    self._item_attributes = ['name', '_parents', '_children']

    self._saved_states = []

  @property
  def raw(self) -> Gimp.Item:
    """Underlying `Gimp.Item` object wrapped by this instance."""
    return self._raw_item

  @property
  def type(self) -> int:
    """Item type.
    
    The type can be one of the following values:
      * ``TYPE_ITEM`` - regular item
      * ``TYPE_GROUP`` - item group (item whose raw `Gimp.Item` is a group with
        children; this `Item` has no children and acts as a regular item)
      * ``TYPE_FOLDER`` - item containing children (raw item is a group with
        children)
    """
    return self._type

  @property
  def parents(self) -> List[Item]:
    """List of `Item` parents for this item, sorted from the topmost
    parent to the bottommost (immediate) parent.
    """
    return self._parents

  @parents.setter
  def parents(self, parents: List[Item]):
    self._parents = parents

  @property
  def children(self) -> List[Item]:
    """List of `Item` children for this item."""
    return self._children

  @children.setter
  def children(self, children: List[Item]):
    self._children = children

  @property
  def depth(self) -> int:
    """Integer indicating the depth of the item in the item tree.
    
    0 means the item is at the top level. The greater the depth, the lower
    the item is in the item tree.
    """
    return len(self._parents)

  @property
  def parent(self) -> Union[Item, None]:
    """Immediate `Item` parent of this object.
    
    If this object has no parent, ``None`` is returned.
    """
    return self._parents[-1] if self._parents else None

  @property
  def prev(self) -> Union[Item, None]:
    """Previous `Item` in the `ItemTree`, or ``None`` if there is no previous
    item.
    """
    return self._prev_item

  @property
  def next(self) -> Union[Item, None]:
    """Next `Item` in the `ItemTree`, or ``None`` if there is no next item."""
    return self._next_item

  @property
  def orig_name(self) -> str:
    """The original value of the ``Gimp.Item`` name.
    
    This attribute may be used to access `Item`s in `ItemTree`.
    """
    return self._orig_name

  @property
  def orig_parents(self) -> Iterator[Item]:
    """The initial value of the ``parents`` attribute of this item."""
    return iter(self._orig_parents)

  @property
  def orig_children(self) -> Iterator[Item]:
    """The initial value of the ``children`` attribute of this item."""
    return iter(self._orig_children)

  def __str__(self) -> str:
    return pgutils.stringify_object(self, self.orig_name)

  def __repr__(self) -> str:
    return pgutils.reprify_object(self, f'{self.orig_name} {type(self.raw)}')

  def push_state(self):
    """Saves the current values of item's attributes that can be modified.

    To restore the last saved values, call `pop_state()`.
    """
    self._saved_states.append({
      attr_name: getattr(self, attr_name) for attr_name in
      self._item_attributes})

  def pop_state(self):
    """Sets the values of item's attributes to the values from the last call to
    `push_state()`.

    Calling `pop_state()` without any saved state (e.g. when `push_state()` has
    never been called before) does nothing.
    """
    try:
      saved_states = self._saved_states.pop()
    except IndexError:
      return

    for attr_name, attr_value in saved_states.items():
      setattr(self, attr_name, attr_value)

  def reset(self):
    """Resets the item's attributes to the values upon its instantiation."""
    self.name = self._orig_name
    self._parents = list(self._orig_parents)
    self._children = list(self._orig_children)


class ItemTree(metaclass=abc.ABCMeta):
  """Interface to store `Gimp.Item` objects in a tree-like structure.

  Use one of the subclasses for items of a certain type:
    * `LayerTree` for layers,
    * `ChannelTree` for channels,
    * `VectorTree` for vectors (paths).

  Each item in the tree is an `Item` instance. Each item contains `Gimp.Item`
  attributes and additional derived attributes.

  Items can be directly accessed via their ID, name or the underlying
  `Gimp.Item` instance. Both ID and name are unique in the entire tree (GIMP
  readily ensures that item names are unique).

  Item groups (e.g. layer groups) are inserted twice in the tree - as folders
  and as items. Parents of items are always folders.

  `ItemTree` is a static data structure - it does not account for
  modifications, additions or removal of GIMP items by GIMP procedures outside
  this class. To refresh the contents of the tree, create a new `ItemTree`
  instance instead.
  """
  
  def __init__(
        self,
        image: Gimp.Image,
        is_filtered: bool = True,
        filter_match_type: int = pgobjectfilter.ObjectFilter.MATCH_ALL):
    self._image = image
    
    self.is_filtered = is_filtered
    """If ``True``, ignore items that do not match the filter
    (`objectfilter.ObjectFilter`) in this object when iterating.
    """
    
    self._filter_match_type = filter_match_type
    
    # Filters applied to all items in `self._itemtree`
    self.filter = pgobjectfilter.ObjectFilter(self._filter_match_type)
    """`objectfilter.ObjectFilter` instance that allows filtering items based on
    rules.
    """
    
    # Contains all items, including groups.
    # key: `Item.raw` or (`Item.raw`, `FOLDER_KEY`) in case of folders
    # value: `Item` instance
    self._itemtree = {}

    # Contains all items, including groups, with all supported types (object, ID, string).
    # key: One of the following:
    #  * `Item.raw`
    #  * (`Item.raw`, `FOLDER_KEY`)
    #  * `Item.raw.get_id()
    #  * (`Item.raw.get_id()`, `FOLDER_KEY`)
    #  * `Item.orig_name`
    #  * (`Item.orig_name`, `FOLDER_KEY`)
    # value: `Item` instance
    self._itemtree_all_types = {}
    
    self._build_tree()
  
  @property
  def image(self) -> Gimp.Image:
    """GIMP image to generate item tree from."""
    return self._image
  
  def __getitem__(
        self, key: Union[int, str, Gimp.Item, Tuple[Union[int, str, Gimp.Item], str]],
  ) -> Item:
    """Returns an `Item` instance using a corresponding `Gimp.Item` instance, ID
     or original name.

    An item's ID is the return value of ``Item.raw.get_id()``. An item's
    original name is the `orig_name` property.
    
    To access an item group as a folder, pass a tuple ``(key, 'folder')``.
    For example:

        item_tree['Frames', 'folder']
    """
    return self._itemtree_all_types[key]
  
  def __contains__(
        self, key: Union[int, str, Gimp.Item, Tuple[Union[int, str, Gimp.Item], str]],
  ) -> bool:
    """Returns ``True`` if an `Item` instance is in the item tree, regardless of
    filters, ``False`` otherwise.
    
    ``key`` can be a `Gimp.Item` instance, ID (obtained via
    ``Item.raw.get_id()``) or original name (obtained via ``Item.orig_name``).
    """
    return key in self._itemtree_all_types
  
  def __len__(self) -> int:
    """Returns the number of items in the tree.
    
    This includes immediate children of the image and nested children. Empty
    item groups (i.e. groups with no children) are excluded.
    
    The returned number of items depends on whether `is_filtered` is
    ``True`` or ``False``.
    """
    return len([item for item in self])
  
  def __iter__(self) -> Generator[Item, None, None]:
    """Iterates over items, excluding folders and empty item groups.
    
    If the `is_filtered` attribute is ``False``, iterate over all items. If
    `is_filtered` is ``True``, iterate only over items that match the filter.
    
    Yields:
      The current `Item` instance.
    """
    return self.iter(with_folders=False, with_empty_groups=False)
  
  def iter(
        self,
        with_folders: bool = True,
        with_empty_groups: bool = False,
        filtered: bool = True,
  ) -> Generator[Item, None, None]:
    """Iterates over items, optionally including folders and empty item groups.

    Args:
      with_folders:
        If ``True``, folder items are included. Topmost folders are yielded
        first. Items are always yielded after all of its parent folders.
      with_empty_groups:
        If ``True``, empty item groups are included. Empty item groups as
        folders are still yielded if ``with_folders`` is ``True``.
      filtered:
        If ``True`` and the `is_filtered` attribute is also ``True``,
        the iteration is performed only over items matching the filter. Set
        this to ``False`` if you need to iterate over all items.

    Yields:
      The current `Item` instance.
    """
    for item in self._itemtree.values():
      should_yield_item = True
      
      if not with_folders and item.type == TYPE_FOLDER:
        should_yield_item = False
      
      if not with_empty_groups and (item.type == TYPE_GROUP and not item.raw.list_children()):
        should_yield_item = False
      
      if should_yield_item:
        if (filtered and self.is_filtered) and not self.filter.is_match(item):
          should_yield_item = False
      
      if should_yield_item:
        yield item
  
  def iter_all(self) -> Generator[Item, None, None]:
    """Iterates over all items.
    
    This is equivalent to ``iter(with_folders=True, with_empty_groups=True,
    filtered=False)``.
    
    Yields:
      The current `Item` instance.
    """
    for item in self._itemtree.values():
      yield item
  
  def prev(
        self,
        item: Item,
        with_folders: bool = True,
        with_empty_groups: bool = False,
        filtered: bool = True,
  ) -> Union[Item, None]:
    """Returns the previous item in the tree, or ``None`` if there is no such
    item.
    
    Depending on the values of the parameters, some items may be skipped. For
    the description of the parameters, see `iter()`.
    """
    return self._prev_next(item, with_folders, with_empty_groups, filtered, 'prev')
  
  def next(
        self,
        item: Item,
        with_folders: bool = True,
        with_empty_groups: bool = False,
        filtered: bool = True,
  ) -> Union[Item, None]:
    """Returns the next item in the tree, or ``None`` if there is no such
    item.
    
    Depending on the values of the parameters, some items may be skipped. For
    the description of the parameters, see `iter()`.
    """
    return self._prev_next(item, with_folders, with_empty_groups, filtered, 'next')
  
  def _prev_next(self, item, with_folders, with_empty_groups, filtered, adjacent_attr_name):
    adjacent_item = item
    
    while True:
      adjacent_item = getattr(adjacent_item, adjacent_attr_name)
      
      if adjacent_item is None:
        break
      
      if with_folders:
        if adjacent_item.type == TYPE_FOLDER:
          break
      else:
        if adjacent_item.type == TYPE_FOLDER:
          continue
      
      if with_empty_groups:
        if adjacent_item.type == TYPE_GROUP and not adjacent_item.raw.list_children():
          break
      else:
        if adjacent_item.type == TYPE_GROUP and not adjacent_item.raw.list_children():
          continue
      
      if filtered and self.is_filtered:
        if self.filter.is_match(adjacent_item):
          break
      else:
        break
    
    return adjacent_item
  
  def reset_filter(self):
    """Resets the filter, creating a new empty `objectfilter.ObjectFilter`."""
    self.filter = pgobjectfilter.ObjectFilter(self._filter_match_type)
  
  def _build_tree(self):
    child_items = []
    for raw_item in self._get_children_from_image(self._image):
      if raw_item.is_group():
        child_items.append(Item(raw_item, TYPE_FOLDER, [], [], None, None))
        child_items.append(Item(raw_item, TYPE_GROUP, [], [], None, None))
      else:
        child_items.append(Item(raw_item, TYPE_ITEM, [], [], None, None))
    
    item_tree = child_items
    item_list = []
    
    while item_tree:
      item = item_tree.pop(0)
      item_list.append(item)
      
      if item.type == TYPE_FOLDER:
        self._itemtree[item.raw.get_id(), FOLDER_KEY] = item

        self._itemtree_all_types[item.raw, FOLDER_KEY] = item
        self._itemtree_all_types[item.raw.get_id(), FOLDER_KEY] = item
        self._itemtree_all_types[item.orig_name, FOLDER_KEY] = item
        
        parents_for_child = list(item.parents)
        parents_for_child.append(item)
        
        child_items = []
        for raw_item in item.raw.list_children():
          if raw_item.is_group():
            child_items.append(Item(raw_item, TYPE_FOLDER, parents_for_child, [], None, None))
            child_items.append(Item(raw_item, TYPE_GROUP, parents_for_child, [], None, None))
          else:
            child_items.append(Item(raw_item, TYPE_ITEM, parents_for_child, [], None, None))
        
        # We break the convention here and access a private attribute from `Item`.
        item._orig_children = child_items
        item.children = child_items
        
        for child_item in reversed(child_items):
          item_tree.insert(0, child_item)
      else:
        self._itemtree[item.raw.get_id()] = item

        self._itemtree_all_types[item.raw] = item
        self._itemtree_all_types[item.raw.get_id()] = item
        self._itemtree_all_types[item.orig_name] = item
    
    for i in range(1, len(item_list) - 1):
      # We break the convention here and access private attributes from `Item`.
      # noinspection PyProtectedMember
      item_list[i]._prev_item = item_list[i - 1]
      # noinspection PyProtectedMember
      item_list[i]._next_item = item_list[i + 1]
    
    if len(item_list) > 1:
      # noinspection PyProtectedMember
      item_list[0]._next_item = item_list[1]
      # noinspection PyProtectedMember
      item_list[-1]._prev_item = item_list[-2]
  
  @abc.abstractmethod
  def _get_children_from_image(self, image: Gimp.Image):
    """Returns a list of immediate child items from the specified `Gimp.Image`.
    
    If no child items exist, an empty list is returned.
    """
    pass


class LayerTree(ItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Layer]:
    return image.list_layers()


class ChannelTree(ItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Channel]:
    return image.list_channels()


class VectorTree(ItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Vectors]:
    return image.list_vectors()
