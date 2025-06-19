"""Utility functions used in `gui.main`."""

from src import core


def get_batcher_class(item_type):
  if item_type == 'image':
    return core.ImageBatcher
  elif item_type == 'layer':
    return core.LayerBatcher
  else:
    raise ValueError('item_type must be either "image" or "layer"')
