"""Built-in "Crop" procedure."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from pygimplib import pdb

from src import exceptions
from src import utils
from src.procedure_groups import *

from . import _utils as builtin_procedures_utils


__all__ = [
  'CropModes',
  'crop',
  'on_after_add_crop_procedure',
]


class CropModes:
  CROP_MODES = (
    CROP_FROM_EACH_SIDE_INDIVIDUALLY,
    CROP_TO_AREA,
    REMOVE_EMPTY_BORDERS,
  ) = (
    'crop_from_each_side_individually',
    'crop_to_area',
    'remove_empty_borders',
  )


def crop(
      batcher,
      object_to_crop,
      crop_mode,
      crop_from_side_top,
      crop_from_side_bottom,
      crop_from_side_left,
      crop_from_side_right,
      crop_to_area_x,
      crop_to_area_y,
      crop_to_area_width,
      crop_to_area_height,
):
  if crop_mode == CropModes.CROP_FROM_EACH_SIDE_INDIVIDUALLY:
    crop_from_side_top_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_side_top, 'y')
    crop_from_side_bottom_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_side_bottom, 'y')
    crop_from_side_left_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_side_left, 'x')
    crop_from_side_right_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_side_right, 'x')

    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    x_pixels = _clamp_crop_amount(crop_from_side_left_pixels, True, object_to_crop_width - 1)
    y_pixels = _clamp_crop_amount(crop_from_side_top_pixels, True, object_to_crop_height - 1)
    width_pixels = _clamp_crop_amount(
      object_to_crop_width - crop_from_side_left_pixels - crop_from_side_right_pixels,
      False,
      object_to_crop_width,
    )
    height_pixels = _clamp_crop_amount(
      object_to_crop_height - crop_from_side_top_pixels - crop_from_side_bottom_pixels,
      False,
      object_to_crop_height,
    )

    _do_crop(batcher, object_to_crop, x_pixels, y_pixels, width_pixels, height_pixels)
  elif crop_mode == CropModes.CROP_TO_AREA:
    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    width_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_width, 'x')
    width_pixels = _clamp_crop_amount(width_pixels, False, object_to_crop_width)

    height_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_height, 'y')
    height_pixels = _clamp_crop_amount(height_pixels, False, object_to_crop_height)

    x_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_x, 'x')
    x_pixels = _clamp_crop_amount(x_pixels, True, object_to_crop_width - width_pixels)

    y_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_y, 'y')
    y_pixels = _clamp_crop_amount(y_pixels, True, object_to_crop_height - height_pixels)

    _do_crop(batcher, object_to_crop, x_pixels, y_pixels, width_pixels, height_pixels)
  elif crop_mode == CropModes.REMOVE_EMPTY_BORDERS:
    if isinstance(object_to_crop, Gimp.Image):
      object_to_crop.autocrop(None)
    else:
      image = object_to_crop.get_image()

      orig_selected_layers = image.get_selected_layers()
      image.set_selected_layers([object_to_crop])

      image.autocrop_selected_layers(object_to_crop)

      image.set_selected_layers(orig_selected_layers)


def _do_crop(batcher, object_to_crop, x, y, width, height):
  if isinstance(object_to_crop, Gimp.Image):
    # An image can end up with no layers if cropping in an empty space.
    # We insert an empty layer after cropping to ensure that subsequent
    # procedures work properly.
    matching_layer = _get_best_matching_layer_from_image(batcher, object_to_crop)

    matching_layer_name = matching_layer.get_name()
    matching_layer_type = matching_layer.type()

    object_to_crop.crop(
      width,
      height,
      x,
      y,
    )

    if not object_to_crop.get_layers():
      empty_layer = Gimp.Layer.new(
        object_to_crop,
        matching_layer_name,
        object_to_crop.get_width(),
        object_to_crop.get_width(),
        matching_layer_type,
        100.0,
        Gimp.LayerMode.NORMAL,
      )
      object_to_crop.insert_layer(empty_layer, None, -1)
  else:
    pdb.gegl__crop(
      object_to_crop,
      x=x,
      y=y,
      width=width,
      height=height,
      merge_filter_=True,
    )


def _get_best_matching_layer_from_image(batcher, image):
  if image == batcher.current_image:
    if batcher.current_layer.is_valid():
      return batcher.current_layer

  selected_layers = image.get_selected_layers()
  if selected_layers:
    return image.get_selected_layers()[0]
  else:
    layers = image.get_layers()
    if layers:
      return layers[0]
    else:
      # Rather than returning no layer, we skip this procedure. An image
      # having no layers points to a problem outside this procedure.
      raise exceptions.SkipAction(_('The image has no layers.'))


def _clamp_crop_amount(value, allow_zero_value, max_value):
  if not allow_zero_value:
    if value <= 0:
      value = 1

  if value > max_value:
    value = max_value

  return value


def on_after_add_crop_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('crop_for_'):
    _set_visible_for_crop_mode_settings(
      procedure['arguments/crop_mode'],
      procedure['arguments'],
    )

    procedure['arguments/crop_mode'].connect_event(
      'value-changed',
      _set_visible_for_crop_mode_settings,
      procedure['arguments'],
    )


def _set_visible_for_crop_mode_settings(crop_mode_setting, crop_arguments_group):
  for setting in crop_arguments_group:
    if setting.name in ['object_to_crop', 'crop_mode']:
      continue

    setting.gui.set_visible(False)

  if crop_mode_setting.value == CropModes.CROP_FROM_EACH_SIDE_INDIVIDUALLY:
    crop_arguments_group['crop_from_side_top'].gui.set_visible(True)
    crop_arguments_group['crop_from_side_bottom'].gui.set_visible(True)
    crop_arguments_group['crop_from_side_left'].gui.set_visible(True)
    crop_arguments_group['crop_from_side_right'].gui.set_visible(True)
  elif crop_mode_setting.value == CropModes.CROP_TO_AREA:
    crop_arguments_group['crop_to_area_x'].gui.set_visible(True)
    crop_arguments_group['crop_to_area_y'].gui.set_visible(True)
    crop_arguments_group['crop_to_area_width'].gui.set_visible(True)
    crop_arguments_group['crop_to_area_height'].gui.set_visible(True)


CROP_FOR_IMAGES_DICT = {
  'name': 'crop_for_images',
  'function': crop,
  'display_name': _('Crop'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_crop',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'crop_mode',
      'default_value': CropModes.CROP_FROM_EACH_SIDE_INDIVIDUALLY,
      'items': [
        (CropModes.CROP_FROM_EACH_SIDE_INDIVIDUALLY, _('Crop from each side individually')),
        (CropModes.CROP_TO_AREA, _('Crop to area')),
        (CropModes.REMOVE_EMPTY_BORDERS, _('Remove empty borders')),
      ],
      'display_name': _('How to crop'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_side_top',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Top'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_side_bottom',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Bottom'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_side_left',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Left'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_side_right',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Right'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_x',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Start X'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_y',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Start Y'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_width',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 100.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_height',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 100.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
  ]
}

CROP_FOR_LAYERS_DICT = utils.semi_deep_copy(CROP_FOR_IMAGES_DICT)
CROP_FOR_LAYERS_DICT.update({
  'name': 'crop_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
CROP_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][2]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][3]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][4]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][5]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][6]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][7]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][8]['default_value']['percent_object'] = 'current_layer'
CROP_FOR_LAYERS_DICT['arguments'][9]['default_value']['percent_object'] = 'current_layer'
