"""Built-in "Insert background" and "Insert foreground" procedures."""

import os

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import placeholders as placeholders_
from src.procedure_groups import *

import pygimplib as pg
from pygimplib import pdb


__all__ = [
  'insert_background_from_file',
  'insert_foreground_from_file',
  'insert_background_from_color_tags',
  'insert_foreground_from_color_tags',
  'merge_background',
  'merge_foreground',
]


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
  _merge_layer(batcher, merge_type, _get_background_layer, 'current_layer')


def merge_foreground(batcher, merge_type=Gimp.MergeType.EXPAND_AS_NECESSARY, *_args, **_kwargs):
  _merge_layer(batcher, merge_type, _get_foreground_layer, 'inserted_layer')


def _get_background_layer(batcher):
  return placeholders_.get_background_layer(None, batcher)


def _get_foreground_layer(batcher):
  return placeholders_.get_foreground_layer(None, batcher)


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


INSERT_BACKGROUND_FOR_IMAGES_DICT = {
  'name': 'insert_background_for_images',
  'function': insert_background_from_file,
  'display_name': _('Insert background'),
  'description': _('Inserts the specified image behind the current layer.'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'file',
      'name': 'image_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Image'),
      'none_ok': True,
    },
    {
      'type': 'string',
      'name': 'merge_procedure_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}

INSERT_BACKGROUND_FOR_LAYERS_DICT = {
  'name': 'insert_background_for_layers',
  'function': insert_background_from_color_tags,
  'display_name': _('Insert background'),
  'description': _(
    'Inserts layers having the specified color tag behind the current layer.'),
  'display_options_on_create': True,
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  'arguments': [
    {
      'type': 'enum',
      'name': 'color_tag',
      'enum_type': Gimp.ColorTag,
      'excluded_values': [Gimp.ColorTag.NONE],
      'display_name': _('Color tag'),
      'default_value': Gimp.ColorTag.BLUE,
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'gui_type': None,
      'tags': ['ignore_reset'],
    },
    {
      'type': 'string',
      'name': 'merge_procedure_name',
      'default_value': '',
      'gui_type': None,
    },
    {
      'type': 'string',
      'name': 'constraint_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}

INSERT_FOREGROUND_FOR_IMAGES_DICT = {
  'name': 'insert_foreground_for_images',
  'function': insert_foreground_from_file,
  'display_name': _('Insert foreground'),
  'description': _(
    'Inserts the specified image in front of the current layer.'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'file',
      'name': 'image_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Image'),
      'none_ok': True,
    },
    {
      'type': 'string',
      'name': 'merge_procedure_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}

INSERT_FOREGROUND_FOR_LAYERS_DICT = {
  'name': 'insert_foreground_for_layers',
  'function': insert_foreground_from_color_tags,
  'display_name': _('Insert foreground'),
  'description': _(
    'Inserts layers having the specified color tag in front of the current layer.'),
  'display_options_on_create': True,
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  'arguments': [
    {
      'type': 'enum',
      'name': 'color_tag',
      'enum_type': Gimp.ColorTag,
      'excluded_values': [Gimp.ColorTag.NONE],
      'display_name': _('Color tag'),
      'default_value': Gimp.ColorTag.GREEN,
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'gui_type': None,
      'tags': ['ignore_reset'],
    },
    {
      'type': 'string',
      'name': 'merge_procedure_name',
      'default_value': '',
      'gui_type': None,
    },
    {
      'type': 'string',
      'name': 'constraint_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}

MERGE_BACKGROUND_DICT = {
  'name': 'merge_background',
  'function': merge_background,
  'display_name': _('Merge background'),
  # This procedure is added/removed automatically alongside `insert_background_for_*`.
  'additional_tags': [],
  'arguments': [
    {
      'type': 'enum',
      'name': 'merge_type',
      'enum_type': Gimp.MergeType,
      'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
      'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
      'display_name': _('Merge type'),
    },
    {
      'type': 'bool',
      'name': 'last_enabled_value',
      'default_value': True,
      'gui_type': None,
    },
  ],
}

MERGE_FOREGROUND_DICT = {
  'name': 'merge_foreground',
  'function': merge_foreground,
  'display_name': _('Merge foreground'),
  # This procedure is added/removed automatically alongside `insert_foreground_for_*`.
  'additional_tags': [],
  'arguments': [
    {
      'type': 'enum',
      'name': 'merge_type',
      'enum_type': Gimp.MergeType,
      'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
      'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
      'display_name': _('Merge type'),
    },
    {
      'type': 'bool',
      'name': 'last_enabled_value',
      'default_value': True,
      'gui_type': None,
    },
  ],
}
