"""Background and foreground layer insertion and manipulation."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import exceptions

import pygimplib as pg


def insert_background_layer(batcher, tag):
  return _insert_tagged_layer(batcher, tag, 'after')


def insert_foreground_layer(batcher, tag):
  return _insert_tagged_layer(batcher, tag, 'before')


def _insert_tagged_layer(batcher, tag, insert_mode):
  tagged_items = [
    item for item in batcher.item_tree.iter(with_folders=True, filtered=False)
    if tag in item.tags]
  merged_tagged_layer = None
  orig_merged_tagged_layer = None
  
  def _cleanup_tagged_layers(batcher_):
    if orig_merged_tagged_layer is not None and orig_merged_tagged_layer.is_valid():
      orig_merged_tagged_layer.delete()
    
    batcher_.invoker.remove(cleanup_tagged_layers_action_id, ['cleanup_contents'])
  
  # We use`Invoker.add` instead of `batcher.add_procedure` since the latter
  # would add the function only at the start of processing and we already are in
  # the middle of processing here.
  cleanup_tagged_layers_action_id = batcher.invoker.add(
    _cleanup_tagged_layers, ['cleanup_contents'])
  
  while True:
    image = batcher.current_image
    current_parent = batcher.current_raw_item.get_parent()
    
    position = image.get_item_position(batcher.current_raw_item)
    if insert_mode == 'after':
      position += 1
    
    if not tagged_items:
      yield
      continue
    
    if orig_merged_tagged_layer is None:
      merged_tagged_layer = _insert_merged_tagged_layer(
        batcher, image, tagged_items, current_parent, position)

      if merged_tagged_layer is not None:
        orig_merged_tagged_layer = _copy_layer(merged_tagged_layer)
        _remove_locks_from_layer(orig_merged_tagged_layer)
    else:
      merged_tagged_layer = _copy_layer(orig_merged_tagged_layer)
      _remove_locks_from_layer(merged_tagged_layer)
      image.insert_layer(merged_tagged_layer, current_parent, position)
    
    yield


def _insert_merged_tagged_layer(batcher, image, tagged_items, parent, position):
  first_tagged_layer_position = position
  
  for i, item in enumerate(tagged_items):
    layer_copy = pg.pdbutils.copy_and_paste_layer(
      item.raw, image, parent, first_tagged_layer_position + i, True, True, True)
    layer_copy.set_visible(True)
    
    batcher.invoker.invoke(
      ['before_process_item_contents'], [batcher, batcher.current_item, layer_copy])

  if parent is None:
    children = image.list_layers()
  else:
    children = parent.list_children()

  merged_tagged_layer = None

  if len(tagged_items) == 1:
    merged_tagged_layer = children[first_tagged_layer_position]
  else:
    second_to_last_tagged_layer_position = first_tagged_layer_position + len(tagged_items) - 2
    
    for i in range(second_to_last_tagged_layer_position, first_tagged_layer_position - 1, -1):
      merged_tagged_layer = image.merge_down(children[i], Gimp.MergeType.EXPAND_AS_NECESSARY)
  
  return merged_tagged_layer


def _remove_locks_from_layer(layer):
  layer.set_lock_alpha(False)
  layer.set_lock_content(False)
  layer.set_lock_position(False)
  layer.set_lock_visibility(False)


def _copy_layer(layer, add_alpha=True):
  layer_copy = layer.copy()

  if add_alpha and not layer_copy.has_alpha() and not layer_copy.is_group():
    layer_copy.add_alpha()

  return layer_copy


def merge_background(batcher, merge_type=Gimp.MergeType.EXPAND_AS_NECESSARY):
  _merge_tagged_layer(
    batcher,
    merge_type,
    get_background_layer,
    'current_item')


def merge_foreground(batcher, merge_type=Gimp.MergeType.EXPAND_AS_NECESSARY):
  _merge_tagged_layer(
    batcher,
    merge_type,
    get_foreground_layer,
    'tagged_layer')


def _merge_tagged_layer(batcher, merge_type, get_tagged_layer_func, layer_to_merge_down_str):
  tagged_layer = get_tagged_layer_func(batcher)
  
  if tagged_layer is not None:
    name = batcher.current_raw_item.get_name()
    visible = batcher.current_raw_item.get_visible()
    orig_tags = _get_tags(batcher.current_raw_item)
    
    if layer_to_merge_down_str == 'current_item':
      layer_to_merge_down = batcher.current_raw_item
    elif layer_to_merge_down_str == 'tagged_layer':
      layer_to_merge_down = tagged_layer
    else:
      raise ValueError('invalid value for "layer_to_merge_down_str"')
    
    batcher.current_raw_item.set_visible(True)
    
    merged_layer = batcher.current_image.merge_down(layer_to_merge_down, merge_type)
    merged_layer.set_name(name)
    
    batcher.current_raw_item = merged_layer
    
    batcher.current_raw_item.set_visible(visible)
    _set_tags(batcher.current_raw_item, orig_tags)
    # We do not expect layer groups as folders to be merged since the plug-in
    # manipulates regular layers only (a layer group is merged into a single
    # layer during processing). Therefore, folder tags are ignored.
    _set_tags(batcher.current_raw_item, set(), pg.itemtree.TYPE_FOLDER)


def get_background_layer(batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position < num_layers - 1,
    1,
    'insert_background_layers',
    _('There are no background layers.'))


def get_foreground_layer(batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position > 0,
    -1,
    'insert_foreground_layers',
    _('There are no foreground layers.'))


def _get_adjacent_layer(
      batcher,
      position_cond_func,
      adjacent_position_increment,
      insert_tagged_layers_procedure_name,
      skip_message,
):
  raw_item = batcher.current_raw_item
  if raw_item.get_parent() is None:
    children = batcher.current_image.list_layers()
  else:
    children = raw_item.parent.list_children()
  
  adjacent_layer = None
  
  num_layers = len(children)
  
  if num_layers > 1:
    position = batcher.current_image.get_item_position(batcher.current_raw_item)
    if position_cond_func(position, num_layers):
      next_layer = children[position + adjacent_position_increment]
      tags = [
        procedure['arguments/tag'].value
        for procedure in _get_previous_enabled_procedures(
          batcher, batcher.current_procedure, insert_tagged_layers_procedure_name)]
      
      if _has_tag(next_layer, tags, None) or _has_tag(next_layer, tags, pg.itemtree.TYPE_FOLDER):
        adjacent_layer = next_layer
  
  if adjacent_layer is not None:
    # This is necessary for some procedures relying on selected layers, e.g.
    # `plug-in-autocrop-layer`.
    batcher.current_image.set_selected_layers([adjacent_layer])
    return adjacent_layer
  else:
    raise exceptions.SkipAction(skip_message)


def _get_previous_enabled_procedures(batcher, current_action, action_orig_name_to_match):
  # HACK: This avoids a circular import. To resolve this, one possible way is to
  # refactor `actions` to turn actions into classes.
  from src import actions
  
  previous_enabled_procedures = []
  
  for procedure in actions.walk(batcher.procedures):
    if procedure == current_action:
      return previous_enabled_procedures
    
    if procedure['enabled'].value and procedure['orig_name'].value == action_orig_name_to_match:
      previous_enabled_procedures.append(procedure)
  
  return previous_enabled_procedures


def _has_tag(layer, tags, item_type=None):
  return any(tag in _get_tags(layer, item_type) for tag in tags)


def _get_tags(layer, item_type=None):
  return pg.itemtree.get_tags_from_raw_item(layer, pg.config.SOURCE_NAME, item_type)


def _set_tags(layer, tags, item_type=None):
  return pg.itemtree.set_tags_for_raw_item(layer, tags, pg.config.SOURCE_NAME, item_type)
