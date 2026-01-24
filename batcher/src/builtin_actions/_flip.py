"""Built-in "Flip Horizontally" and "Flip Vertically" actions."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import utils
from src.procedure_groups import *


__all__ = [
  'flip_horizontally',
  'flip_vertically',
]


def flip_horizontally(_batcher, object_to_flip):
  if isinstance(object_to_flip, Gimp.Image):
    object_to_flip.flip(Gimp.OrientationType.HORIZONTAL)
  else:
    Gimp.context_push()
    Gimp.context_set_transform_resize(Gimp.TransformResize.ADJUST)

    object_to_flip.transform_flip_simple(Gimp.OrientationType.HORIZONTAL, True, 0.0)

    Gimp.context_pop()


def flip_vertically(_batcher, object_to_flip):
  if isinstance(object_to_flip, Gimp.Image):
    object_to_flip.flip(Gimp.OrientationType.VERTICAL)
  else:
    Gimp.context_push()
    Gimp.context_set_transform_resize(Gimp.TransformResize.ADJUST)

    object_to_flip.transform_flip_simple(Gimp.OrientationType.VERTICAL, True, 0.0)

    Gimp.context_pop()


FLIP_HORIZONTALLY_FOR_IMAGES_DICT = {
  'name': 'flip_horizontally_for_images',
  'function': flip_horizontally,
  'display_name': _('Flip Horizontally'),
  'menu_path': _('Resize and Transform'),
  'additional_tags': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_flip',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
  ]
}

FLIP_HORIZONTALLY_FOR_LAYERS_DICT = utils.semi_deep_copy(FLIP_HORIZONTALLY_FOR_IMAGES_DICT)
FLIP_HORIZONTALLY_FOR_LAYERS_DICT.update({
  'name': 'flip_horizontally_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
FLIP_HORIZONTALLY_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'


FLIP_VERTICALLY_FOR_IMAGES_DICT = {
  'name': 'flip_vertically_for_images',
  'function': flip_vertically,
  'display_name': _('Flip Vertically'),
  'menu_path': _('Resize and Transform'),
  'additional_tags': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_flip',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
  ]
}

FLIP_VERTICALLY_FOR_LAYERS_DICT = utils.semi_deep_copy(FLIP_VERTICALLY_FOR_IMAGES_DICT)
FLIP_VERTICALLY_FOR_LAYERS_DICT.update({
  'name': 'flip_vertically_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
FLIP_VERTICALLY_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'
