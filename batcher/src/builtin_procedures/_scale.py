"""Built-in "Scale" procedure."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import utils
from src.procedure_groups import *

from . import _utils as builtin_procedures_utils


__all__ = [
  'AspectRatios',
  'scale',
]


class AspectRatios:
  ASPECT_RATIOS = (
    STRETCH,
    KEEP_ADJUST_WIDTH,
    KEEP_ADJUST_HEIGHT,
    FIT,
    FIT_WITH_PADDING,
  ) = (
    'stretch',
    'keep_adjust_width',
    'keep_adjust_height',
    'fit',
    'fit_with_padding',
  )


def scale(
      batcher,
      object_to_scale,
      new_width,
      new_height,
      interpolation,
      local_origin,
      aspect_ratio,
      padding_color,
      set_image_resolution,
      image_resolution,
):
  if set_image_resolution:
    if isinstance(object_to_scale, Gimp.Image):
      object_to_scale.set_resolution(image_resolution['x'], image_resolution['y'])
    elif isinstance(object_to_scale, Gimp.Item):
      object_to_scale.get_image().set_resolution(image_resolution['x'], image_resolution['y'])

  new_width_pixels = builtin_procedures_utils.unit_to_pixels(batcher, new_width, 'x')
  if new_width_pixels <= 0:
    new_width_pixels = 1

  new_height_pixels = builtin_procedures_utils.unit_to_pixels(batcher, new_height, 'y')
  if new_height_pixels <= 0:
    new_height_pixels = 1

  orig_width_pixels = object_to_scale.get_width()
  if orig_width_pixels == 0:
    orig_width_pixels = 1

  orig_height_pixels = object_to_scale.get_height()
  if orig_height_pixels == 0:
    orig_height_pixels = 1

  if aspect_ratio in [AspectRatios.KEEP_ADJUST_WIDTH, AspectRatios.KEEP_ADJUST_HEIGHT]:
    processed_width_pixels, processed_height_pixels = _get_scale_keep_aspect_ratio_values(
      aspect_ratio,
      orig_width_pixels,
      orig_height_pixels,
      new_width_pixels,
      new_height_pixels)
  elif aspect_ratio in [AspectRatios.FIT, AspectRatios.FIT_WITH_PADDING]:
    processed_width_pixels, processed_height_pixels = _get_scale_fit_values(
      orig_width_pixels, orig_height_pixels, new_width_pixels, new_height_pixels)
  else:
    processed_width_pixels = new_width_pixels
    processed_height_pixels = new_height_pixels

  Gimp.context_push()
  Gimp.context_set_interpolation(interpolation)

  if processed_width_pixels == 0:
    processed_width_pixels = 1

  if processed_height_pixels == 0:
    processed_height_pixels = 1

  if isinstance(object_to_scale, Gimp.Image):
    object_to_scale.scale(processed_width_pixels, processed_height_pixels)
  else:
    object_to_scale.scale(processed_width_pixels, processed_height_pixels, local_origin)

  if aspect_ratio == AspectRatios.FIT_WITH_PADDING:
    _fill_with_padding(
      batcher,
      object_to_scale,
      new_width_pixels,
      new_height_pixels,
      padding_color,
    )

  Gimp.context_pop()


def _get_scale_keep_aspect_ratio_values(
      aspect_ratio,
      orig_width_pixels,
      orig_height_pixels,
      new_width_pixels,
      new_height_pixels,
):
  if aspect_ratio == AspectRatios.KEEP_ADJUST_WIDTH:
    processed_new_width_pixels = new_width_pixels
    processed_new_height_pixels = round(
      orig_height_pixels * (processed_new_width_pixels / orig_width_pixels))
  elif aspect_ratio == AspectRatios.KEEP_ADJUST_HEIGHT:
    processed_new_height_pixels = new_height_pixels
    processed_new_width_pixels = round(
      orig_width_pixels * (processed_new_height_pixels / orig_height_pixels))
  else:
    raise ValueError(
      'invalid value for dimension_to_keep; must be "width" or "height"')

  return processed_new_width_pixels, processed_new_height_pixels


def _get_scale_fit_values(
      orig_width_pixels, orig_height_pixels, new_width_pixels, new_height_pixels):
  processed_new_width_pixels = new_width_pixels
  processed_new_height_pixels = round(orig_height_pixels * (new_width_pixels / orig_width_pixels))

  if processed_new_height_pixels > new_height_pixels:
    processed_new_height_pixels = new_height_pixels
    processed_new_width_pixels = round(orig_width_pixels * (new_height_pixels / orig_height_pixels))

  return processed_new_width_pixels, processed_new_height_pixels


def _fill_with_padding(
      batcher,
      gimp_object,
      new_width_pixels,
      new_height_pixels,
      padding_color,
):
  if isinstance(gimp_object, Gimp.Image):
    drawable_with_padding = batcher.current_layer
    image_of_drawable_with_padding = gimp_object
  else:
    drawable_with_padding = gimp_object
    image_of_drawable_with_padding = gimp_object.get_image()

  object_width = gimp_object.get_width()
  object_height = gimp_object.get_height()

  if new_width_pixels > object_width:
    offset_x = (new_width_pixels - object_width) // 2
    offset_y = 0
    layer_to_fill_start_width = offset_x
    layer_to_fill_start_height = new_height_pixels
    layer_to_fill_end_width = offset_x + (new_width_pixels - object_width) % 2
    layer_to_fill_end_height = new_height_pixels
  else:
    offset_x = 0
    offset_y = (new_height_pixels - object_height) // 2
    layer_to_fill_start_width = new_width_pixels
    layer_to_fill_start_height = offset_y
    layer_to_fill_end_width = new_width_pixels
    layer_to_fill_end_height = offset_y + (new_height_pixels - object_height) % 2

  if isinstance(gimp_object, Gimp.Image):
    if new_width_pixels > object_width:
      layer_to_fill_start_offset_x = 0
      layer_to_fill_start_offset_y = 0
      layer_to_fill_end_offset_x = offset_x + object_width
      layer_to_fill_end_offset_y = offset_y
    else:
      layer_to_fill_start_offset_x = 0
      layer_to_fill_start_offset_y = 0
      layer_to_fill_end_offset_x = offset_x
      layer_to_fill_end_offset_y = offset_y + object_height

    gimp_object.resize(new_width_pixels, new_height_pixels, offset_x, offset_y)
  else:
    drawable_with_padding_offsets = gimp_object.get_offsets()

    if new_width_pixels > object_width:
      layer_to_fill_start_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_start_offset_y = drawable_with_padding_offsets.offset_y
      layer_to_fill_end_offset_x = drawable_with_padding_offsets.offset_x + object_width + offset_x
      layer_to_fill_end_offset_y = drawable_with_padding_offsets.offset_y
    else:
      layer_to_fill_start_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_start_offset_y = drawable_with_padding_offsets.offset_y
      layer_to_fill_end_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_end_offset_y = drawable_with_padding_offsets.offset_y + object_height + offset_y

    gimp_object.set_offsets(
      drawable_with_padding_offsets.offset_x + offset_x,
      drawable_with_padding_offsets.offset_y + offset_y)

  Gimp.context_set_foreground(pg.setting.ColorSetting.get_value_as_color(padding_color))
  Gimp.context_set_opacity(
    pg.setting.ColorSetting.get_value_as_color(padding_color).get_rgba().alpha * 100)

  if layer_to_fill_start_width != 0 and layer_to_fill_start_height != 0:
    layer_to_fill_start = Gimp.Layer.new(
      image_of_drawable_with_padding,
      drawable_with_padding.get_name(),
      layer_to_fill_start_width,
      layer_to_fill_start_height,
      Gimp.ImageType.RGBA_IMAGE,
      100.0,
      Gimp.LayerMode.NORMAL,
    )
    layer_to_fill_start.set_offsets(layer_to_fill_start_offset_x, layer_to_fill_start_offset_y)
    image_of_drawable_with_padding.insert_layer(
      layer_to_fill_start,
      drawable_with_padding.get_parent(),
      image_of_drawable_with_padding.get_item_position(drawable_with_padding) + 1,
    )
    layer_to_fill_start.edit_fill(Gimp.FillType.FOREGROUND)
    merged_drawable_with_padding = image_of_drawable_with_padding.merge_down(
      drawable_with_padding, Gimp.MergeType.EXPAND_AS_NECESSARY)
  else:
    merged_drawable_with_padding = drawable_with_padding

  if layer_to_fill_end_width != 0 and layer_to_fill_end_height != 0:
    layer_to_fill_end = Gimp.Layer.new(
      image_of_drawable_with_padding,
      merged_drawable_with_padding.get_name(),
      layer_to_fill_end_width,
      layer_to_fill_end_height,
      Gimp.ImageType.RGBA_IMAGE,
      100.0,
      Gimp.LayerMode.NORMAL,
    )
    layer_to_fill_end.set_offsets(layer_to_fill_end_offset_x, layer_to_fill_end_offset_y)
    image_of_drawable_with_padding.insert_layer(
      layer_to_fill_end,
      merged_drawable_with_padding.get_parent(),
      image_of_drawable_with_padding.get_item_position(merged_drawable_with_padding) + 1,
    )
    layer_to_fill_end.edit_fill(Gimp.FillType.FOREGROUND)
    image_of_drawable_with_padding.merge_down(
      merged_drawable_with_padding, Gimp.MergeType.EXPAND_AS_NECESSARY)


SCALE_PROCEDURE_DICT_FOR_IMAGES = {
  'name': 'scale_for_images',
  'function': scale,
  'display_name': _('Scale'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_scale',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'dimension',
      'name': 'new_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer',
        'foreground_layer'],
      'display_name': _('New width'),
    },
    {
      'type': 'dimension',
      'name': 'new_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer',
        'foreground_layer'],
      'display_name': _('New height'),
    },
    {
      'type': 'choice',
      'name': 'aspect_ratio',
      'default_value': AspectRatios.STRETCH,
      'items': [
        (AspectRatios.STRETCH, _('None (Stretch)')),
        (AspectRatios.KEEP_ADJUST_WIDTH, _('Keep, adjust width')),
        (AspectRatios.KEEP_ADJUST_HEIGHT, _('Keep, adjust height')),
        (AspectRatios.FIT, _('Fit')),
        (AspectRatios.FIT_WITH_PADDING, _('Fit with padding')),
      ],
      'display_name': _('Aspect ratio'),
    },
    {
      'type': 'color',
      'name': 'padding_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Padding color'),
    },
    {
      'type': 'enum',
      'enum_type': Gimp.InterpolationType,
      'name': 'interpolation',
      'display_name': _('Interpolation'),
    },
    {
      'type': 'bool',
      'name': 'local_origin',
      'default_value': False,
      'display_name': _('Use local origin'),
    },
    {
      'type': 'bool',
      'name': 'set_image_resolution',
      'default_value': False,
      'display_name': _('Set image resolution in DPI'),
    },
    {
      'type': 'resolution',
      'name': 'image_resolution',
      'default_value': {
        'x': 72.0,
        'y': 72.0,
      },
    },
  ],
}

SCALE_PROCEDURE_DICT_FOR_LAYERS = utils.semi_deep_copy(SCALE_PROCEDURE_DICT_FOR_IMAGES)

SCALE_PROCEDURE_DICT_FOR_LAYERS.update({
  'name': 'scale_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][0]['default_value'] = 'current_layer'
SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][1]['default_value']['percent_object'] = (
  'current_layer')
SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][2]['default_value']['percent_object'] = (
  'current_layer')
