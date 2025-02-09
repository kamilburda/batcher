"""Background and foreground layer insertion and manipulation."""
import os.path

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import exceptions

import pygimplib as pg
from pygimplib import pdb


def insert_background_from_file(image_batcher, image_file, *_args, **_kwargs):
  return _insert_layer_from_file(image_batcher, image_file, 'after')


def insert_foreground_from_file(image_batcher, image_file, *_args, **_kwargs):
  return _insert_layer_from_file(image_batcher, image_file, 'before')


def _insert_layer_from_file(image_batcher, image_file, insert_mode):
  image_copies = []

  image_batcher.invoker.add(_delete_images_on_cleanup, ['cleanup_contents'], [image_copies])

  if (image_file is not None
      and image_file.get_path() is not None
      and os.path.exists(image_file.get_path())):
    image_to_insert = pdb.gimp_file_load(
      run_mode=Gimp.RunMode.NONINTERACTIVE,
      file=image_file)

    image_copies.append(image_to_insert)
  else:
    image_to_insert = None

  while True:
    if image_to_insert is None:
      yield
      continue

    image = image_batcher.current_image
    current_parent = image_batcher.current_layer.get_parent()

    position = image.get_item_position(image_batcher.current_layer)
    if insert_mode == 'after':
      position += 1

    _insert_layers(image, image_to_insert.get_layers(), current_parent, position)

    yield


def _delete_images_on_cleanup(_batcher, images):
  for image in images:
    pg.pdbutils.try_delete_image(image)

  images.clear()


def insert_background_from_color_tags(
      layer_batcher, color_tag, tagged_items, *_args, **_kwargs):
  return _insert_tagged_layers(layer_batcher, color_tag, tagged_items, 'after')


def insert_foreground_from_color_tags(
      layer_batcher, color_tag, tagged_items, *_args, **_kwargs):
  return _insert_tagged_layers(layer_batcher, color_tag, tagged_items, 'before')


def _insert_tagged_layers(layer_batcher, tag, tagged_items_for_preview, insert_mode):
  if layer_batcher.is_preview:
    tagged_items = tagged_items_for_preview
  else:
    tagged_items = layer_batcher.item_tree.iter(with_folders=False, filtered=False)

  processed_tagged_items = [
    item for item in tagged_items
    if tag != Gimp.ColorTag.NONE and item.raw.is_valid() and item.raw.get_color_tag() == tag]
  
  while True:
    if not processed_tagged_items:
      yield
      continue

    image = layer_batcher.current_image
    current_parent = layer_batcher.current_layer.get_parent()

    position = image.get_item_position(layer_batcher.current_layer)
    if insert_mode == 'after':
      position += 1

    _insert_layers(image, [item.raw for item in processed_tagged_items], current_parent, position)

    yield


def _insert_layers(image, layers, parent, position):
  first_tagged_layer_position = position
  
  for i, layer in enumerate(layers):
    layer_copy = pg.pdbutils.copy_and_paste_layer(
      layer, image, parent, first_tagged_layer_position + i, True, True, True)
    layer_copy.set_visible(True)

  if parent is None:
    children = image.get_layers()
  else:
    children = parent.get_children()

  merged_tagged_layer = None

  if len(layers) == 1:
    merged_tagged_layer = children[first_tagged_layer_position]
  else:
    second_to_last_tagged_layer_position = first_tagged_layer_position + len(layers) - 2
    # It should not matter which items we obtain the color tag from as all
    # items have the same color tag.
    merged_color_tag = children[second_to_last_tagged_layer_position].get_color_tag()

    for i in range(second_to_last_tagged_layer_position, first_tagged_layer_position - 1, -1):
      merged_tagged_layer = image.merge_down(children[i], Gimp.MergeType.EXPAND_AS_NECESSARY)

    # The merged-down layer does not possess the attributes of the original
    # layers, including the color tag, so we set it explicitly. This ensures
    # that tagged group layers are merged properly in "Merge back-/foreground"
    # procedures.
    merged_tagged_layer.set_color_tag(merged_color_tag)

  return merged_tagged_layer


def merge_background(batcher, merge_type=Gimp.MergeType.EXPAND_AS_NECESSARY, *_args, **_kwargs):
  _merge_layer(batcher, merge_type, get_background_layer, 'current_layer')


def merge_foreground(batcher, merge_type=Gimp.MergeType.EXPAND_AS_NECESSARY, *_args, **_kwargs):
  _merge_layer(batcher, merge_type, get_foreground_layer, 'inserted_layer')


def _merge_layer(batcher, merge_type, get_inserted_layer_func, layer_to_merge_str):
  inserted_layer = get_inserted_layer_func(batcher)
  
  if inserted_layer is not None:
    name = batcher.current_layer.get_name()
    visible = batcher.current_layer.get_visible()
    orig_color_tag = batcher.current_layer.get_color_tag()
    
    if layer_to_merge_str == 'current_layer':
      layer_to_merge_down = batcher.current_layer
    elif layer_to_merge_str == 'inserted_layer':
      layer_to_merge_down = inserted_layer
    else:
      raise ValueError('invalid value for "layer_to_merge_str"')
    
    batcher.current_layer.set_visible(True)
    
    merged_layer = batcher.current_image.merge_down(layer_to_merge_down, merge_type)

    # Avoid errors if merge failed for some reason.
    if merged_layer is not None:
      merged_layer.set_name(name)

      batcher.current_layer = merged_layer

      batcher.current_layer.set_visible(visible)
      batcher.current_layer.set_color_tag(orig_color_tag)


def get_background_layer(batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position < num_layers - 1,
    1,
    ['insert_background_for_images', 'insert_background_for_layers'],
    _('There are no background layers.'))


def get_foreground_layer(batcher):
  return _get_adjacent_layer(
    batcher,
    lambda position, num_layers: position > 0,
    -1,
    ['insert_foreground_for_images', 'insert_foreground_for_layers'],
    _('There are no foreground layers.'))


def _get_adjacent_layer(
      batcher,
      position_cond_func,
      adjacent_position_increment,
      insert_layers_procedure_names,
      skip_message,
):
  image = batcher.current_image
  layer = batcher.current_layer

  if layer.get_parent() is None:
    children = image.get_layers()
  else:
    children = layer.get_parent().get_children()
  
  adjacent_layer = None
  
  num_layers = len(children)
  
  if num_layers > 1:
    position = image.get_item_position(layer)
    if position_cond_func(position, num_layers):
      next_layer = children[position + adjacent_position_increment]
      # A `None` element represents a background/foreground layer inserted
      # via other means than color tags (e.g. from a file). If there are no
      # matching color tags and `None` is present at least once, we always
      # consider `next_layer` to be the background/foreground.
      color_tags = [
        procedure['arguments/color_tag'].value
        if 'color_tag' in procedure['arguments'] else None
        for procedure in _get_previous_enabled_procedures(
          batcher, batcher.current_procedure, insert_layers_procedure_names)]
      
      if next_layer.get_color_tag() in color_tags or None in color_tags:
        adjacent_layer = next_layer
  
  if adjacent_layer is not None:
    # This is necessary for some procedures relying on selected layers.
    image.set_selected_layers([adjacent_layer])
    return adjacent_layer
  else:
    raise exceptions.SkipAction(skip_message)


def _get_previous_enabled_procedures(batcher, current_action, action_orig_names_to_match):
  previous_enabled_procedures = []
  
  for procedure in batcher.procedures:
    if procedure == current_action:
      return previous_enabled_procedures
    
    if any(procedure['enabled'].value and procedure['orig_name'].value == orig_name
           for orig_name in action_orig_names_to_match):
      previous_enabled_procedures.append(procedure)
  
  return previous_enabled_procedures
