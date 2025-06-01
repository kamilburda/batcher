"""Built-in "Resize canvas" procedure."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import utils
from src.procedure_groups import *


__all__ = [
  'ResizeModes',
  'resize_canvas',
  'on_after_add_resize_canvas_procedure',
]


class ResizeModes:
  RESIZE_MODES = (
    RESIZE_FROM_EDGES,
    RESIZE_FROM_POSITION,
    RESIZE_TO_ASPECT_RATIO,
    RESIZE_TO_AREA,
    RESIZE_TO_LAYER_SIZE,
    RESIZE_TO_IMAGE_SIZE,
  ) = (
    'resize_from_edges',
    'resize_from_position',
    'resize_to_aspect_ratio',
    'resize_to_area',
    'resize_to_layer_size',
    'resize_to_image_size',
  )


def resize_canvas(
      _batcher,
      object_to_resize,
      resize_mode,
      resize_to_layer_size_layers,
      resize_to_image_size_image,
):
  if resize_mode == ResizeModes.RESIZE_FROM_EDGES:
    # TODO
    pass
  elif resize_mode == ResizeModes.RESIZE_FROM_POSITION:
    # TODO
    pass
  elif resize_mode == ResizeModes.RESIZE_FROM_POSITION:
    # TODO
    pass
  elif resize_mode == ResizeModes.RESIZE_TO_ASPECT_RATIO:
    # TODO
    pass
  elif resize_mode == ResizeModes.RESIZE_TO_AREA:
    # TODO
    pass
  elif resize_mode == ResizeModes.RESIZE_TO_LAYER_SIZE:
    layers = resize_to_layer_size_layers

    if len(layers) == 1:
      layer = layers[0]

      layer_offsets = layer.get_offsets()

      object_to_resize.resize(
        layer.get_width(), layer.get_height(), -layer_offsets.offset_x, -layer_offsets.offset_y)
    elif len(layers) > 1:
      layer_offset_list = [layer.get_offsets() for layer in layers]

      min_x = min(offset.offset_x for offset in layer_offset_list)
      min_y = min(offset.offset_y for offset in layer_offset_list)

      max_x = max(
        offset.offset_x + layer.get_width() for layer, offset in zip(layers, layer_offset_list))
      max_y = max(
        offset.offset_y + layer.get_height() for layer, offset in zip(layers, layer_offset_list))

      object_to_resize.resize(max_x - min_x, max_y - min_y, -min_x, -min_y)
  elif resize_mode == ResizeModes.RESIZE_TO_IMAGE_SIZE:
    if isinstance(object_to_resize, Gimp.Image):
      offset_x = 0
      offset_y = 0
    else:
      offsets = object_to_resize.get_offsets()
      offset_x = offsets.offset_x
      offset_y = offsets.offset_y

    object_to_resize.resize(
      resize_to_image_size_image.get_width(),
      resize_to_image_size_image.get_height(),
      offset_x,
      offset_y,
    )


def on_after_add_resize_canvas_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('resize_canvas_for_'):
    _set_visible_for_resize_mode_settings(
      procedure['arguments/resize_mode'],
      procedure['arguments'],
    )

    procedure['arguments/resize_mode'].connect_event(
      'value-changed',
      _set_visible_for_resize_mode_settings,
      procedure['arguments'],
    )


def _set_visible_for_resize_mode_settings(
      resize_mode_setting,
      resize_canvas_arguments_group,
):
  for setting in resize_canvas_arguments_group:
    if setting.name in ['object_to_resize', 'resize_mode']:
      continue

    setting.gui.set_visible(False)

  if resize_mode_setting.value == ResizeModes.RESIZE_FROM_EDGES:
    # TODO
    pass
  elif resize_mode_setting.value == ResizeModes.RESIZE_FROM_POSITION:
    # TODO
    pass
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_ASPECT_RATIO:
    # TODO
    pass
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_AREA:
    # TODO
    pass
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_LAYER_SIZE:
    resize_canvas_arguments_group['resize_to_layer_size_layers'].gui.set_visible(True)
  elif resize_mode_setting.value == ResizeModes.RESIZE_TO_IMAGE_SIZE:
    resize_canvas_arguments_group['resize_to_image_size_image'].gui.set_visible(True)


RESIZE_CANVAS_FOR_IMAGES_DICT = {
  'name': 'resize_canvas_for_images',
  'function': resize_canvas,
  'display_name': _('Resize canvas'),
  'description': _(
    'Resizes the image or layer extents, optionally filling the newly added space with a color.'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_resize',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'resize_mode',
      'default_value': ResizeModes.RESIZE_FROM_EDGES,
      'items': [
        (ResizeModes.RESIZE_FROM_EDGES, _('Resize from edges')),
        (ResizeModes.RESIZE_FROM_POSITION, _('Resize from position')),
        (ResizeModes.RESIZE_TO_ASPECT_RATIO, _('Resize to aspect ratio')),
        (ResizeModes.RESIZE_TO_AREA, _('Resize to area')),
        (ResizeModes.RESIZE_TO_LAYER_SIZE, _('Resize to layer size')),
        (ResizeModes.RESIZE_TO_IMAGE_SIZE, _('Resize to image size')),
      ],
      'display_name': _('How to resize'),
    },
    {
      'type': 'placeholder_layer_array',
      'name': 'resize_to_layer_size_layers',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers'),
    },
    {
      'type': 'placeholder_image',
      'name': 'resize_to_image_size_image',
      'element_type': 'image',
      'default_value': 'current_image',
      'display_name': _('Image'),
    },
  ],
}

RESIZE_CANVAS_FOR_LAYERS_DICT = utils.semi_deep_copy(RESIZE_CANVAS_FOR_IMAGES_DICT)
RESIZE_CANVAS_FOR_LAYERS_DICT.update({
  'name': 'resize_canvas_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})

_RESIZE_CANVAS_DIMENSION_ARGUMENT_INDEXES = [
  index for index, dict_ in enumerate(RESIZE_CANVAS_FOR_LAYERS_DICT['arguments'])
  if dict_['type'] == 'dimension']
for index in _RESIZE_CANVAS_DIMENSION_ARGUMENT_INDEXES:
  RESIZE_CANVAS_FOR_LAYERS_DICT['arguments'][index]['default_value']['percent_object'] = (
    'current_layer')
