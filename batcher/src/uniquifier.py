"""Making item names in `pygimplib.itemtree.ItemTree` unique."""

from typing import Generator, Optional

import pygimplib as pg

from src.path import uniquify


class ItemUniquifier:
  """Class renaming `pygimplib.ItemTree.Item` instances to be unique under the
  same parent.
  """
  
  def __init__(self, generator: Optional[Generator[str, None, None]] = None):
    self.generator = generator
    
    # key: `Item` instance (parent) or `None` (item tree root)
    # value: set of `Item` instances
    self._uniquified_items = {}
    
    # key: `Item` instance (parent) or `None` (item tree root)
    # value: set of `Item.name` strings
    self._uniquified_item_names = {}
  
  def uniquify(
        self,
        item: pg.itemtree.Item,
        item_name: Optional[str] = None,
        position: Optional[int] = None,
  ):
    """Returns a new name for an `Item` instance by making it unique among all
    other `Item` instances under the same parent of `Item`.

    To achieve uniquification, a substring in the form of ``' (<number>)'`` is
    appended to the item name.

    Calling the method with the same `Item` instance will have no effect as
    that instance will be marked as visited. Call `reset()` to clear cache of
    items that were passed to this function.
    
    Args:
      item:
        `Item` instance whose ``name`` attribute will be uniquified.
      item_name:
        A different name to use for uniquification in place of ``item.name``.
        This is useful if you need to use a separate set of item names stored
        externally.
      position:
        Position (index) where a unique substring is inserted into the item's
        name. If ``None``, the substring is inserted at the end of the name
        (i.e. appended).

    Returns:
      The uniquified name.
    """
    parent = item.parent

    if item_name is None:
      item_name = item.name

    if parent not in self._uniquified_items:
      self._uniquified_items[parent] = set()
      self._uniquified_item_names[parent] = set()

    uniquified_item_name = None

    already_visited = item in self._uniquified_items[parent]
    if not already_visited:
      self._uniquified_items[parent].add(item)
      
      has_same_name = item_name in self._uniquified_item_names[parent]
      if has_same_name:
        uniquified_item_name = uniquify.uniquify_string(
          item_name, self._uniquified_item_names[parent], position, generator=self.generator)

      self._uniquified_item_names[parent].add(
        uniquified_item_name if uniquified_item_name is not None else item_name)

    return uniquified_item_name if uniquified_item_name is not None else item_name
  
  def reset(self):
    """Clears cache of items passed to `uniquify()`."""
    self._uniquified_items = {}
    self._uniquified_item_names = {}
