"""Managing items of a GIMP image (e.g. layers) in a tree-like structure."""

from __future__ import annotations

import abc
from collections.abc import Iterable, Iterator
import os
from typing import Any, Dict, Generator, List, Optional, Union

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


class Item(metaclass=abc.ABCMeta):
  """Wrapper for an object allowing access to various attributes with a unified
  interface.

  Note that the attributes will not be up-to-date if changes were made to the
  original object.
  """

  def __init__(
        self,
        object_: Any,
        item_type: int,
        parents: Optional[Iterable[Any]] = None,
        children: Optional[Iterable[Any]] = None,
        prev_item: Optional[Any] = None,
        next_item: Optional[Any] = None):
    if object_ is None:
      raise TypeError('object_ cannot be None')

    self._object = object_
    self._type = item_type
    self._parents = parents if parents is not None else []
    self._children = children if children is not None else []
    self._prev_item = prev_item
    self._next_item = next_item

    self.name = self._get_name_from_object()
    """Item name as a string, initially equal to ``orig_name``.
    
    This can be used to set a new name to avoid modifying the original object
    in GIMP.
    """

    self._id = self._get_id_from_object()

    self._orig_name = self.name
    self._orig_parents = self._parents
    self._orig_children = self._children

    self._item_attributes = ['name', '_parents', '_children']

    self._saved_states = []
    self._saved_named_states = {}

  @property
  @abc.abstractmethod
  def raw(self):
    """A temporary object derived from the object passed to the instance of
    this class to ``__init__()``.

    Note that this may or may not be equivalent to the object passed to the
    instantiation and may be permanent, depending on the subclass.

    Additionally, this property may be ``None`` initially if the temporary
    object is created externally at a later time. If the created object is
    removed externally, it is recommended to set this property to ``None`` if a
    subclass allows it.

    This property is meant to be used when it is guaranteed that the temporary
    object is ready to be used. Examples of temporary objects include loaded
    images from disk, or layers of an image.
    """
    pass

  @property
  def type(self) -> int:
    """Item type.

    The type can be one of the following values:
      * ``TYPE_ITEM`` - regular item
      * ``TYPE_GROUP`` - item group - an item whose underlying object represents
        a group with children, but acts as a regular item with no children, e.g.
        a group layer acting as a single merged layer.
      * ``TYPE_FOLDER`` - item containing children (e.g. a folder on a file
        system or group layer)
    """
    return self._type

  @property
  def id(self):
    """Item identifier, used to uniquely identify the underlying object among
    all objects of the same type (e.g. file path in a file system or numeric ID
    of a GIMP layer).

    This property is guaranteed to be unchanged for this `Item` instance.
    """
    return self._id

  @abc.abstractmethod
  def _get_name_from_object(self):
    pass

  @abc.abstractmethod
  def _get_id_from_object(self):
    pass

  @property
  def parents(self) -> List[Item]:
    """List of `Item` parents for this item, sorted from the topmost parent
    to the bottommost (immediate) parent.
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
    """The depth of the item in the item tree.

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
    """The original item name as derived from the object passed to
    ``__init__()``.
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

  def get_all_children(self) -> List[Item]:
    """Returns a list of all child items, including items from child folders
    of any depth.

    An empty list returned for items that are not folders (i.e. whose `type`
    property is not `TYPE_FOLDER`).
    """
    if self.type != TYPE_FOLDER:
      return []

    all_children = []

    items = list(self._children)
    while items:
      item = items.pop(0)

      all_children.append(item)

      if item.type == TYPE_FOLDER:
        items.extend(item.children)

    return all_children

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

  def save_state(self, name: str):
    """Saves the current values of item's attributes that can be modified under
    the specified name.

    The saved attributes can be accessed via the `get_named_state()` method.

    Calling this method with the same ``name`` overrides the previously saved
    attributes.
    """
    self._saved_named_states[name] = {
      attr_name.lstrip('_'): getattr(self, attr_name) for attr_name in
      self._item_attributes}

  def get_named_state(self, name: str) -> Optional[Dict[str, Any]]:
    """Returns the saved state for the given ``name``, or ``None`` if not
    available.

    See `save_state()` for more information.
    """
    return self._saved_named_states.get(name, None)

  def delete_named_state(self, name: str):
    """Deletes the saved state having the given ``name``.

    This method has no effect if a state with the name ``name`` does not exist.

    See `save_state()` for more information.
    """
    self._saved_named_states.pop(name, None)

  def reset(self):
    """Resets the item's attributes to the values upon its instantiation."""
    self.name = self._orig_name
    self._parents = list(self._orig_parents)
    self._children = list(self._orig_children)


class GimpItem(Item):
  """`Item` subclass for a `Gimp.Item` or `Gimp.Image` object."""

  @property
  def raw(self) -> Union[Gimp.Item, Gimp.Image]:
    """Underlying `Gimp.Item` or `Gimp.Image` object wrapped by this instance.
    """
    return self._object

  @property
  def id(self) -> int:
    """Numeric identifier used to uniquely identify the underlying GIMP object.

    This property is guaranteed to be unchanged for this `Item` instance.
    """
    return self._id

  def _get_name_from_object(self) -> str:
    return self._object.get_name()

  def _get_id_from_object(self) -> int:
    return self._object.get_id()


class ImageFileItem(Item):
  """`Item` subclass for an image file.

  The object passed to ``__init__()`` must be a file path pointing to an
  existing image that can be loaded in GIMP, or a folder.

  The `id` property represents the file path to the item.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._raw = None

  @property
  def raw(self) -> Union[Gimp.Image, None]:
    """`Gimp.Image` object, if loaded from the file path given by the `id`
    property, or ``None`` if not loaded.
    """
    return self._raw

  @raw.setter
  def raw(self, value: Optional[Gimp.Image]):
    """Sets the `raw` property.

    The ``value`` must either be a valid `Gimp.Image` instance loaded from
    the file path given by the `id` property, or ``None`` to reset this
    property (indicating that the image was deleted).
    """
    self._raw = value

  @property
  def id(self) -> str:
    """File path used to locate a file on the file system.

    This property is guaranteed to be unchanged for this `Item` instance.
    """
    return self._id

  def _get_name_from_object(self) -> str:
    return os.path.basename(self._object)

  def _get_id_from_object(self) -> int:
    return self._object


class ItemTree(metaclass=abc.ABCMeta):
  """Interface to store objects in a tree-like structure.

  Each item in the tree is an `Item` instance. Each item contains basic
  attributes such as name or parents.

  Items can be directly accessed via their ID, path or the underlying object.
  Both ID and path are unique in the entire tree.
  """
  
  def __init__(
        self,
        is_filtered: bool = True,
        filter_match_type: int = pgobjectfilter.ObjectFilter.MATCH_ALL,
  ):
    self.is_filtered = is_filtered
    """If ``True``, ignore items that do not match the filter
    (`objectfilter.ObjectFilter`) in this object when iterating.
    """
    
    self._filter_match_type = filter_match_type

    self.filter = pgobjectfilter.ObjectFilter(self._filter_match_type)
    """`objectfilter.ObjectFilter` instance that allows filtering items based
    on rules.
    """

    self._first_item = None
    self._last_item = None

    # Contains all items, including groups, with all supported types (object, ID, string).
    # key: One of the following:
    #  * `Item.raw`
    #  * (`Item.raw`, `FOLDER_KEY`)
    #  * `Item.raw.get_id()
    #  * (`Item.raw.get_id()`, `FOLDER_KEY`)
    #  * tuple of `Item.orig_name`
    #  * (tuple of `Item.orig_name`, `FOLDER_KEY`)
    # value: `Item` instance
    self._itemtree_all_types = {}
  
  def __getitem__(self, key) -> Item:
    """Returns an `Item` instance using a key, particularly `Item.raw` or
    `Item.id`.
    
    To access an item group as a folder, pass a tuple ``(key, 'folder')``.
    For example:

        item_tree[item.id, 'folder']
    """
    return self._itemtree_all_types[key]
  
  def __contains__(self, key) -> bool:
    """Returns ``True`` if an `Item` instance is in the item tree, regardless of
    filters, ``False`` otherwise.

    See `__getitem__()` for information about the possible values for ``key``.
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

    If the `is_filtered` attribute is ``False``, iteration is performed over
    all items. If `is_filtered` is ``True``, iteration is performed only over
    items that match the filter.
    
    Yields:
      The current `Item` instance.
    """
    return self.iter(with_folders=False, with_empty_groups=False)

  def __reversed__(self) -> Generator[Item, None, None]:
    """Iterates over items, excluding folders and empty item groups, in the
    reversed order.

    If the `is_filtered` attribute is ``False``, iteration is performed over
    all items. If `is_filtered` is ``True``, iteration is performed only over
    items that match the filter.

    Yields:
      The current `Item` instance.
    """
    return self.iter(with_folders=False, with_empty_groups=False, reverse=True)

  def add(
        self,
        objects: Iterable,
        parent_item: Optional[Item] = None,
        insert_after_item: Optional[Item] = None,
  ):
    if not objects:
      return

    if parent_item is None:
      parents_for_child_initial = []
    else:
      parents_for_child_initial = parent_item.parents + [parent_item]

    child_items = []
    for object_ in objects:
      self._insert_item(object_, child_items, list(parents_for_child_initial))

    item_tree = child_items
    item_list = []

    while item_tree:
      item = item_tree.pop(0)
      item_list.append(item)

      if item.type == TYPE_FOLDER:
        parents_for_child = self._add_item_to_itemtree_dicts(item)

        child_items = []
        for object_ in self._list_children_from_object(item):
          self._insert_item(object_, child_items, list(parents_for_child))

        # We break the convention here and access a private attribute from `Item`.
        # noinspection PyProtectedMember
        item._orig_children = child_items
        item.children = child_items

        for child_item in reversed(child_items):
          item_tree.insert(0, child_item)
      else:
        self._add_item_to_itemtree_dicts(item)

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

    if self._first_item is not None and self._last_item is not None and len(item_list) >= 1:
      if insert_after_item is None:
        if parent_item is None:
          insert_after_item = self._last_item
        else:
          if parent_item.children:
            insert_after_item = parent_item.children[-1]
          else:
            insert_after_item = parent_item

      # noinspection PyProtectedMember
      item_list[-1]._next_item = insert_after_item.next
      if insert_after_item.next is not None:
        # noinspection PyProtectedMember
        insert_after_item.next._prev_item = item_list[-1]

      # noinspection PyProtectedMember
      item_list[0]._prev_item = insert_after_item
      # noinspection PyProtectedMember
      insert_after_item._next_item = item_list[0]

    if self._first_item is None and self._last_item is None and len(item_list) >= 1:
      self._first_item = item_list[0]
      self._last_item = item_list[-1]

  @abc.abstractmethod
  def _insert_item(self, object_, child_items, parents_for_child=None):
    pass

  @abc.abstractmethod
  def _add_item_to_itemtree_dicts(self, item):
    pass

  @abc.abstractmethod
  def _list_children_from_object(self, item):
    pass

  def remove(self, items: Iterable[Item]):
    """Removes items from the tree.

    Removing items whose `item_type` property is `TYPE_FOLDER` will result in
    also removing all their children (including subfolders and their
    children).

    Items whose `item_type` property is `TYPE_FOLDER` will be removed along
    with corresponding items of type `TYPE_GROUP`, and vice versa.

    Any items that do not exist in the tree will be silently ignored without
    raising an exception.
    """
    # TODO: Delete all keys, including item.raw and item path, if they exist,
    #  or remove this to-do if only IDs will be used as keys.

    for item in items:
      if item.type == TYPE_ITEM:
        item_keys = [item.id]
      else:
        # This ensures that items of type TYPE_FOLDER are always removed
        # along with their corresponding item of TYPE_GROUP, if those exist.
        item_keys = [item.id, (item.id, FOLDER_KEY)]

      items_to_remove = []

      for key in item_keys:
        if key in self._itemtree_all_types:
          items_to_remove.append(self._itemtree_all_types[key])
          items_to_remove.extend(self._itemtree_all_types[key].get_all_children())

      for item_to_remove in items_to_remove:
        self._itemtree_all_types.pop(item_to_remove.id, None)
        self._itemtree_all_types.pop((item_to_remove.id, FOLDER_KEY), None)

        next_item = item_to_remove.next
        previous_item = item_to_remove.prev

        if previous_item is not None:
          # noinspection PyProtectedMember
          previous_item._next_item = next_item

        if next_item is not None:
          # noinspection PyProtectedMember
          next_item._prev_item = previous_item

        if item_to_remove.parent is not None:
          try:
            item_to_remove.parent.children.remove(item_to_remove)
          except ValueError:
            pass

        if item_to_remove == self._first_item:
          self._first_item = next_item

        if item_to_remove == self._last_item:
          self._last_item = previous_item

  def iter(
        self,
        with_folders: bool = True,
        with_empty_groups: bool = False,
        filtered: bool = True,
        reverse: bool = False,
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
      reverse:
        If ``True``, the iteration is performed in reverse, starting from the
        last item in the tree.

    Yields:
      The current `Item` instance.
    """
    if not reverse:
      current_item = self._first_item
    else:
      current_item = self._last_item

    while current_item is not None:
      should_yield_item = True

      if not with_folders and current_item.type == TYPE_FOLDER:
        should_yield_item = False

      if (not with_empty_groups
          and (current_item.type == TYPE_GROUP and not current_item.raw.list_children())):
        should_yield_item = False

      if should_yield_item:
        if (filtered and self.is_filtered) and not self.filter.is_match(current_item):
          should_yield_item = False

      if should_yield_item:
        yield current_item

      if not reverse:
        current_item = current_item.next
      else:
        current_item = current_item.prev
  
  def iter_all(self, reverse: bool = False) -> Generator[Item, None, None]:
    """Iterates over all items.
    
    This is equivalent to ``iter(with_folders=True, with_empty_groups=True,
    filtered=False, reverse=reverse)``.

    Args:
      reverse:
        If ``True``, the iteration is performed in reverse, starting from the
        last item in the tree.
    
    Yields:
      The current `Item` instance.
    """
    if not reverse:
      current_item = self._first_item
    else:
      current_item = self._last_item

    while current_item is not None:
      yield current_item

      if not reverse:
        current_item = current_item.next
      else:
        current_item = current_item.prev
  
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


class ImageTree(ItemTree):

  def _insert_item(self, object_, child_items, parents_for_child=None):
    if parents_for_child is None:
      parents_for_child = []

    if isinstance(object_, str):
      if os.path.isdir(object_):
        path = os.path.abspath(object_)
        child_items.append(ImageFileItem(path, TYPE_FOLDER, parents_for_child, [], None, None))
      else:
        # Files and non-existent files/folders are treated as regular items.
        # How non-existent files are handled depends on the client code.
        path = os.path.abspath(object_)
        child_items.append(ImageFileItem(path, TYPE_ITEM, parents_for_child, [], None, None))
    else:  # GIMP image
      child_items.append(GimpItem(object_, TYPE_ITEM, parents_for_child, [], None, None))

  def _add_item_to_itemtree_dicts(self, item):
    parents_for_child = list(item.parents)
    parents_for_child.append(item)

    if item.type == TYPE_FOLDER:
      self._itemtree_all_types[item.id, FOLDER_KEY] = item

      item_path = tuple(item_.orig_name for item_ in parents_for_child)
      self._itemtree_all_types[item_path, FOLDER_KEY] = item
    else:
      self._itemtree_all_types[item.id] = item

      item_path = tuple(item_.orig_name for item_ in parents_for_child)
      self._itemtree_all_types[item_path] = item

    return parents_for_child

  def _list_children_from_object(self, item):
    try:
      filenames = os.listdir(item.id)
    except FileNotFoundError:
      return []
    else:
      return sorted(os.path.abspath(os.path.join(item.id, filename)) for filename in filenames)


class GimpItemTree(ItemTree):
  """Interface to store `Gimp.Item` objects in a tree-like structure.

  Use one of the subclasses for items of a certain type:
    * `LayerTree` for layers,
    * `ChannelTree` for channels,
    * `VectorTree` for vectors (paths).

  Item groups (e.g. layer groups) are inserted twice in the tree - as folders
  and as items. Parents of items are always folders.

  While you may add or remove items from `GimpItemTree`, it does not account for
  modifications, additions or removal of GIMP items by GIMP procedures outside
  this class. To refresh the contents of the tree, create a new `GimpItemTree`
  instance instead.
  """

  def __init__(
        self,
        image: Gimp.Image,
        *args,
        **kwargs,
  ):
    self._image = image

    super().__init__(*args, **kwargs)

    self.add(self._get_children_from_image(self._image))

  @property
  def image(self) -> Gimp.Image:
    """GIMP image to generate item tree from."""
    return self._image

  def _insert_item(self, object_, child_items, parents_for_child=None):
    if parents_for_child is None:
      parents_for_child = []

    if object_.is_group():
      child_items.append(GimpItem(object_, TYPE_FOLDER, parents_for_child, [], None, None))
      # Make sure each item keeps its own list of parents.
      child_items.append(GimpItem(object_, TYPE_GROUP, list(parents_for_child), [], None, None))
    else:
      child_items.append(GimpItem(object_, TYPE_ITEM, parents_for_child, [], None, None))

  def _add_item_to_itemtree_dicts(self, item):
    parents_for_child = list(item.parents)
    parents_for_child.append(item)

    if item.type == TYPE_FOLDER:
      self._itemtree_all_types[item.raw, FOLDER_KEY] = item
      self._itemtree_all_types[item.id, FOLDER_KEY] = item

      item_path = tuple(item_.orig_name for item_ in parents_for_child)
      self._itemtree_all_types[item_path, FOLDER_KEY] = item
    else:
      self._itemtree_all_types[item.raw] = item
      self._itemtree_all_types[item.id] = item

      item_path = tuple(item_.orig_name for item_ in parents_for_child)
      self._itemtree_all_types[item_path] = item

    return parents_for_child

  def _list_children_from_object(self, item):
    return item.raw.list_children()

  @abc.abstractmethod
  def _get_children_from_image(self, image: Gimp.Image):
    """Returns a list of immediate child items from the specified `Gimp.Image`.

    If no child items exist, an empty list is returned.
    """
    pass


class LayerTree(GimpItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Layer]:
    return image.list_layers()


class ChannelTree(GimpItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Channel]:
    return image.list_channels()


class VectorTree(GimpItemTree):
  
  def _get_children_from_image(self, image: Gimp.Image) -> List[Gimp.Vectors]:
    return image.list_vectors()
