"""Built-in "Align and offset" procedure."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src.procedure_groups import *

from . import _utils as builtin_procedures_utils


__all__ = [
  'HorizontalAlignments',
  'VerticalAlignments',
  'align_and_offset_layers',
]


class HorizontalAlignments:
  HORIZONTAL_ALIGNMENTS = (
    KEEP,
    LEFT,
    CENTER,
    RIGHT,
  ) = (
    'keep',
    'left',
    'center',
    'right',
  )


class VerticalAlignments:
  VERTICAL_ALIGNMENTS = (
    KEEP,
    TOP,
    CENTER,
    BOTTOM,
  ) = (
    'keep',
    'top',
    'center',
    'bottom',
  )


def align_and_offset_layers(
      batcher,
      layers_to_align,
      reference_object,
      horizontal_align,
      vertical_align,
      x_offset,
      y_offset,
):
  image_width = batcher.current_image.get_width()
  image_height = batcher.current_image.get_height()

  if isinstance(reference_object, Gimp.Image):
    reference_object_type = 'image'
  else:
    reference_object_type = 'layer'

  if reference_object_type == 'layer':
    ref_layer_x, ref_layer_y = reference_object.get_offsets()[1:]
    ref_layer_width = reference_object.get_width()
    ref_layer_height = reference_object.get_height()
  else:
    ref_layer_x = 0
    ref_layer_y = 0
    ref_layer_width = 1
    ref_layer_height = 1

  for layer in layers_to_align:
    new_x, new_y = layer.get_offsets()[1:]

    if horizontal_align == HorizontalAlignments.LEFT:
      if reference_object_type == 'image':
        new_x = 0
      elif reference_object_type == 'layer':
        new_x = ref_layer_x
    elif horizontal_align == HorizontalAlignments.CENTER:
      if reference_object_type == 'image':
        new_x = (image_width - layer.get_width()) // 2
      elif reference_object_type == 'layer':
        new_x = ref_layer_x + (ref_layer_width - layer.get_width()) // 2
    elif horizontal_align == HorizontalAlignments.RIGHT:
      if reference_object_type == 'image':
        new_x = image_width - layer.get_width()
      elif reference_object_type == 'layer':
        new_x = ref_layer_x + ref_layer_width - layer.get_width()

    if vertical_align == VerticalAlignments.TOP:
      if reference_object_type == 'image':
        new_y = 0
      elif reference_object_type == 'layer':
        new_y = ref_layer_y
    elif vertical_align == VerticalAlignments.CENTER:
      if reference_object_type == 'image':
        new_y = (image_height - layer.get_height()) // 2
      elif reference_object_type == 'layer':
        new_y = ref_layer_y + (ref_layer_height - layer.get_height()) // 2
    elif vertical_align == VerticalAlignments.BOTTOM:
      if reference_object_type == 'image':
        new_y = image_height - layer.get_height()
      elif reference_object_type == 'layer':
        new_y = ref_layer_y + ref_layer_height - layer.get_height()

    new_x += builtin_procedures_utils.unit_to_pixels(batcher, x_offset, 'x')
    new_y += builtin_procedures_utils.unit_to_pixels(batcher, y_offset, 'y')

    layer.set_offsets(new_x, new_y)


ALIGN_AND_OFFSET_DICT = {
  'name': 'align_and_offset_layers',
  'function': align_and_offset_layers,
  'display_name': _('Align and offset'),
  'description': _(
    'Aligns layer(s) with the image or another layer.'
    '\n\nYou may specify additional offsets after the alignment is applied.'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  'arguments': [
    {
      'type': 'placeholder_layer_array',
      'name': 'layers_to_align',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers to align'),
    },
    {
      'type': 'placeholder_image_or_layer',
      'name': 'reference_object',
      'default_value': 'current_image',
      'display_name': _('Object to align layers with'),
    },
    {
      'type': 'choice',
      'name': 'horizontal_align',
      'default_value': HorizontalAlignments.KEEP,
      'items': [
        (HorizontalAlignments.KEEP, _('Keep')),
        (HorizontalAlignments.LEFT, _('Left')),
        (HorizontalAlignments.CENTER, _('Center')),
        (HorizontalAlignments.RIGHT, _('Right')),
      ],
      'display_name': _('Horizontal alignment'),
    },
    {
      'type': 'choice',
      'name': 'vertical_align',
      'default_value': VerticalAlignments.KEEP,
      'items': [
        (VerticalAlignments.KEEP, _('Keep')),
        (VerticalAlignments.TOP, _('Top')),
        (VerticalAlignments.CENTER, _('Center')),
        (VerticalAlignments.BOTTOM, _('Bottom')),
      ],
      'display_name': _('Vertical alignment'),
    },
    {
      'type': 'dimension',
      'name': 'x_offset',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer',
        'foreground_layer'],
      'display_name': _('Additional X-offset'),
    },
    {
      'type': 'dimension',
      'name': 'y_offset',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer',
        'foreground_layer'],
      'display_name': _('Additional Y-offset'),
    },
  ],
}
