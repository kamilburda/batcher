"""Built-in "Resize to layer size" procedure."""

from src.procedure_groups import *


__all__ = [
  'resize_to_layer_size',
]


def resize_to_layer_size(_batcher, layers):
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


RESIZE_TO_LAYER_SIZE_DICT = {
  'name': 'resize_to_layer_size',
  'function': resize_to_layer_size,
  'display_name': _('Resize to layer size'),
  'description': _('Resizes the image canvas to fit the specified layer(s).'),
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EXPORT_LAYERS_GROUP],
  'arguments': [
    {
      'type': 'placeholder_layer_array',
      'name': 'layers',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers'),
    },
  ]
}
