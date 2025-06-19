"""Utility functions related to the `itemtree` module."""

import collections

from src import itemtree


def item_tree_items_to_objects(item_tree: itemtree.ItemTree):
  return [
    [item.id, item.orig_parent.id] if item.orig_parent is not None else [item.id, None]
    for item in item_tree.iter_all()]


def add_objects_to_item_tree(item_tree: itemtree.ItemTree, objects_and_parent_objects):
  parent_items = collections.defaultdict(lambda: None)

  for object_, parent_object in objects_and_parent_objects:
    added_items = item_tree.add(
      [object_], parent_item=parent_items[parent_object], expand_folders=False)

    if added_items and added_items[0].type == itemtree.TYPE_FOLDER:
      parent_items[object_] = added_items[0]
