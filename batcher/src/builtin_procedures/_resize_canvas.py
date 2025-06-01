"""Built-in "Resize canvas" procedure."""

from src import utils
from src.procedure_groups import *


__all__ = [
  'resize_canvas',
]


def resize_canvas(_batcher, layers):
  if len(layers) == 1:
    layer = layers[0]

    layer_offset_x, layer_offset_y = layer.get_offsets()[1:]
    layer.get_image().resize(
      layer.get_width(), layer.get_height(), -layer_offset_x, -layer_offset_y)
  elif len(layers) > 1:
    image = layers[0].get_image()

    layer_offset_list = [layer.get_offsets()[1:] for layer in layers]

    min_x = min(offset[0] for offset in layer_offset_list)
    min_y = min(offset[1] for offset in layer_offset_list)

    max_x = max(offset[0] + layer.get_width() for layer, offset in zip(layers, layer_offset_list))
    max_y = max(offset[1] + layer.get_height() for layer, offset in zip(layers, layer_offset_list))

    image.resize(max_x - min_x, max_y - min_y, -min_x, -min_y)


RESIZE_CANVAS_FOR_IMAGES_DICT = {
  'name': 'resize_canvas_for_images',
  'function': resize_canvas,
  'display_name': _('Resize canvas'),
  'description': _('Resizes the image or layer extents.'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_layer_array',
      'name': 'layers',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers'),
    },
  ],
}

RESIZE_CANVAS_FOR_LAYERS_DICT = utils.semi_deep_copy(RESIZE_CANVAS_FOR_IMAGES_DICT)
RESIZE_CANVAS_FOR_LAYERS_DICT.update({
  'name': 'resize_canvas_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
RESIZE_CANVAS_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'

_RESIZE_CANVAS_DIMENSION_ARGUMENT_INDEXES = [
  index for index, dict_ in enumerate(RESIZE_CANVAS_FOR_LAYERS_DICT['arguments'])
  if dict_['type'] == 'dimension']
for index in _RESIZE_CANVAS_DIMENSION_ARGUMENT_INDEXES:
  RESIZE_CANVAS_FOR_LAYERS_DICT['arguments'][index]['default_value']['percent_object'] = (
    'current_layer')
