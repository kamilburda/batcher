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
    CROP_FROM_EDGES,
    CROP_FROM_POSITION,
    CROP_TO_ASPECT_RATIO,
    CROP_TO_AREA,
    REMOVE_EMPTY_BORDERS,
  ) = (
    'crop_from_edges',
    'crop_from_position',
    'crop_to_aspect_ratio',
    'crop_to_area',
    'remove_empty_borders',
  )


def crop(
      batcher,
      object_to_crop,
      crop_mode,
      crop_from_edges_same_amount_for_each_side,
      crop_from_edges_amount,
      crop_from_edges_top,
      crop_from_edges_bottom,
      crop_from_edges_left,
      crop_from_edges_right,
      crop_from_position_anchor,
      crop_from_position_width,
      crop_from_position_height,
      crop_to_aspect_ratio_ratio,
      crop_to_aspect_ratio_position,
      crop_to_aspect_ratio_position_custom,
      crop_to_area_x,
      crop_to_area_y,
      crop_to_area_width,
      crop_to_area_height,
):
  if crop_mode == CropModes.CROP_FROM_EDGES:
    if crop_from_edges_same_amount_for_each_side:
      crop_from_edges_top = crop_from_edges_amount
      crop_from_edges_bottom = crop_from_edges_amount
      crop_from_edges_left = crop_from_edges_amount
      crop_from_edges_right = crop_from_edges_amount

    crop_from_edges_top_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_edges_top, 'y')
    crop_from_edges_bottom_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_edges_bottom, 'y')
    crop_from_edges_left_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_edges_left, 'x')
    crop_from_edges_right_pixels = builtin_procedures_utils.unit_to_pixels(
      batcher, crop_from_edges_right, 'x')

    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    x_pixels = _clamp_value(crop_from_edges_left_pixels, True, object_to_crop_width - 1)
    y_pixels = _clamp_value(crop_from_edges_top_pixels, True, object_to_crop_height - 1)
    width_pixels = _clamp_value(
      object_to_crop_width - crop_from_edges_left_pixels - crop_from_edges_right_pixels,
      False,
      object_to_crop_width,
    )
    height_pixels = _clamp_value(
      object_to_crop_height - crop_from_edges_top_pixels - crop_from_edges_bottom_pixels,
      False,
      object_to_crop_height,
    )

    _do_crop(batcher, object_to_crop, x_pixels, y_pixels, width_pixels, height_pixels)
  elif crop_mode == CropModes.CROP_FROM_POSITION:
    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    x_pixels, y_pixels, width_pixels, height_pixels = _get_crop_from_position_area_pixels(
      batcher,
      object_to_crop_width,
      object_to_crop_height,
      crop_from_position_anchor,
      crop_from_position_width,
      crop_from_position_height,
    )

    width_pixels = _clamp_value(width_pixels, False, object_to_crop_width)
    height_pixels = _clamp_value(height_pixels, False, object_to_crop_height)

    x_pixels = _clamp_value(x_pixels, True, object_to_crop_width - width_pixels)
    y_pixels = _clamp_value(y_pixels, True, object_to_crop_height - height_pixels)

    _do_crop(batcher, object_to_crop, x_pixels, y_pixels, width_pixels, height_pixels)
  elif crop_mode == CropModes.CROP_TO_ASPECT_RATIO:
    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    x_pixels, y_pixels, width_pixels, height_pixels = _get_crop_to_aspect_ratio_pixels(
      batcher,
      object_to_crop_width,
      object_to_crop_height,
      crop_to_aspect_ratio_ratio,
      crop_to_aspect_ratio_position,
      crop_to_aspect_ratio_position_custom,
    )

    width_pixels = _clamp_value(width_pixels, False, object_to_crop_width)
    height_pixels = _clamp_value(height_pixels, False, object_to_crop_height)
    x_pixels = _clamp_value(x_pixels, True, object_to_crop_width - width_pixels)
    y_pixels = _clamp_value(y_pixels, True, object_to_crop_height - height_pixels)

    _do_crop(batcher, object_to_crop, x_pixels, y_pixels, width_pixels, height_pixels)
  elif crop_mode == CropModes.CROP_TO_AREA:
    object_to_crop_width = object_to_crop.get_width()
    object_to_crop_height = object_to_crop.get_height()

    x_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_x, 'x')
    y_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_y, 'y')
    width_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_width, 'x')
    height_pixels = builtin_procedures_utils.unit_to_pixels(batcher, crop_to_area_height, 'y')

    width_pixels = _clamp_value(width_pixels, False, object_to_crop_width)
    height_pixels = _clamp_value(height_pixels, False, object_to_crop_height)
    x_pixels = _clamp_value(x_pixels, True, object_to_crop_width - width_pixels)
    y_pixels = _clamp_value(y_pixels, True, object_to_crop_height - height_pixels)

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


def _get_crop_from_position_area_pixels(
      batcher,
      object_to_crop_width,
      object_to_crop_height,
      crop_from_position_anchor,
      width,
      height,
):
  width_pixels = builtin_procedures_utils.unit_to_pixels(batcher, width, 'x')
  height_pixels = builtin_procedures_utils.unit_to_pixels(batcher, height, 'y')

  position = [0, 0]

  if crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.TOP_LEFT:
    position = [0, 0]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.TOP:
    position = [
      round((object_to_crop_width - width_pixels) / 2),
      0,
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.TOP_RIGHT:
    position = [
      object_to_crop_width - width_pixels,
      0,
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.LEFT:
    position = [
      0,
      round((object_to_crop_height - height_pixels) / 2),
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.CENTER:
    position = [
      round((object_to_crop_width - width_pixels) / 2),
      round((object_to_crop_height - height_pixels) / 2),
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.RIGHT:
    position = [
      object_to_crop_width - width_pixels,
      round((object_to_crop_height - height_pixels) / 2),
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.BOTTOM_LEFT:
    position = [
      0,
      object_to_crop_height - height_pixels,
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.BOTTOM:
    position = [
      round((object_to_crop_width - width_pixels) / 2),
      object_to_crop_height - height_pixels,
    ]
  elif crop_from_position_anchor == builtin_procedures_utils.AnchorPoints.BOTTOM_RIGHT:
    position = [
      object_to_crop_width - width_pixels,
      object_to_crop_height - height_pixels,
    ]

  return position[0], position[1], width_pixels, height_pixels


def _get_crop_to_aspect_ratio_pixels(
      batcher,
      object_to_crop_width,
      object_to_crop_height,
      crop_to_aspect_ratio_ratio,
      crop_to_aspect_ratio_position,
      crop_to_aspect_ratio_position_custom,
):
  ratio_width = crop_to_aspect_ratio_ratio['x']
  ratio_height = crop_to_aspect_ratio_ratio['y']

  width_unit_length = object_to_crop_width / ratio_width
  height_pixels = width_unit_length * ratio_height
  if height_pixels <= object_to_crop_height:
    width_pixels = object_to_crop_width
    height_pixels = round(height_pixels)
    x_pixels = 0

    y_pixels = 0
    if crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.START:
      y_pixels = 0
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.CENTER:
      y_pixels = round((object_to_crop_height - height_pixels) / 2)
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.END:
      y_pixels = object_to_crop_height - height_pixels
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.CUSTOM:
      y_pixels = builtin_procedures_utils.unit_to_pixels(
        batcher, crop_to_aspect_ratio_position_custom, 'y')
  else:
    height_unit_length = object_to_crop_height / ratio_height
    width_pixels = round(height_unit_length * ratio_width)
    height_pixels = object_to_crop_height
    y_pixels = 0

    x_pixels = 0
    if crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.START:
      x_pixels = 0
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.CENTER:
      x_pixels = round((object_to_crop_width - width_pixels) / 2)
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.END:
      x_pixels = object_to_crop_width - width_pixels
    elif crop_to_aspect_ratio_position == builtin_procedures_utils.Positions.CUSTOM:
      x_pixels = builtin_procedures_utils.unit_to_pixels(
        batcher, crop_to_aspect_ratio_position_custom, 'x')

  return x_pixels, y_pixels, width_pixels, height_pixels


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


def _clamp_value(value, allow_zero_value, max_value):
  if allow_zero_value:
    if value < 0:
      value = 0
  else:
    if value <= 0:
      value = 1

  if value > max_value:
    value = max_value

  return value


def on_after_add_crop_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('crop_for_'):
    procedure['arguments/crop_from_edges_same_amount_for_each_side'].connect_event(
      'value-changed',
      _set_visible_for_crop_from_edges_settings,
      procedure['arguments'],
    )

    procedure['arguments/crop_from_edges_same_amount_for_each_side'].connect_event(
      'gui-visible-changed',
      _set_visible_for_crop_from_edges_settings,
      procedure['arguments'],
    )

    procedure['arguments/crop_to_aspect_ratio_position'].connect_event(
      'value-changed',
      _set_visible_for_crop_to_aspect_ratio_position_custom,
      procedure['arguments/crop_to_aspect_ratio_position_custom'],
    )

    procedure['arguments/crop_to_aspect_ratio_position'].connect_event(
      'gui-visible-changed',
      _set_visible_for_crop_to_aspect_ratio_position_custom,
      procedure['arguments/crop_to_aspect_ratio_position_custom'],
    )

    _set_visible_for_crop_mode_settings(
      procedure['arguments/crop_mode'],
      procedure['arguments'],
    )

    procedure['arguments/crop_mode'].connect_event(
      'value-changed',
      _set_visible_for_crop_mode_settings,
      procedure['arguments'],
    )


def _set_visible_for_crop_from_edges_settings(
      crop_from_edges_same_amount_for_each_side_setting,
      crop_arguments_group,
):
  is_visible = crop_from_edges_same_amount_for_each_side_setting.gui.get_visible()
  is_checked = crop_from_edges_same_amount_for_each_side_setting.value

  crop_arguments_group['crop_from_edges_amount'].gui.set_visible(is_visible and is_checked)
  crop_arguments_group['crop_from_edges_top'].gui.set_visible(is_visible and not is_checked)
  crop_arguments_group['crop_from_edges_bottom'].gui.set_visible(is_visible and not is_checked)
  crop_arguments_group['crop_from_edges_left'].gui.set_visible(is_visible and not is_checked)
  crop_arguments_group['crop_from_edges_right'].gui.set_visible(is_visible and not is_checked)


def _set_visible_for_crop_to_aspect_ratio_position_custom(
      crop_to_aspect_ratio_position_setting,
      crop_to_aspect_ratio_position_custom_setting,
):
  is_visible = crop_to_aspect_ratio_position_setting.gui.get_visible()
  is_selected = (
    crop_to_aspect_ratio_position_setting.value == builtin_procedures_utils.Positions.CUSTOM)

  crop_to_aspect_ratio_position_custom_setting.gui.set_visible(is_visible and is_selected)


def _set_visible_for_crop_mode_settings(crop_mode_setting, crop_arguments_group):
  for setting in crop_arguments_group:
    if setting.name in ['object_to_crop', 'crop_mode']:
      continue

    setting.gui.set_visible(False)

  if crop_mode_setting.value == CropModes.CROP_FROM_EDGES:
    crop_arguments_group['crop_from_edges_same_amount_for_each_side'].gui.set_visible(True)
  elif crop_mode_setting.value == CropModes.CROP_FROM_POSITION:
    crop_arguments_group['crop_from_position_anchor'].gui.set_visible(True)
    crop_arguments_group['crop_from_position_width'].gui.set_visible(True)
    crop_arguments_group['crop_from_position_height'].gui.set_visible(True)
  elif crop_mode_setting.value == CropModes.CROP_TO_ASPECT_RATIO:
    crop_arguments_group['crop_to_aspect_ratio_ratio'].gui.set_visible(True)
    crop_arguments_group['crop_to_aspect_ratio_position'].gui.set_visible(True)
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
      'default_value': CropModes.CROP_FROM_EDGES,
      'items': [
        (CropModes.CROP_FROM_EDGES, _('Crop from edges')),
        (CropModes.CROP_FROM_POSITION, _('Crop from position')),
        (CropModes.CROP_TO_ASPECT_RATIO, _('Crop to aspect ratio')),
        (CropModes.CROP_TO_AREA, _('Crop to area')),
        (CropModes.REMOVE_EMPTY_BORDERS, _('Remove empty borders')),
      ],
      'display_name': _('How to crop'),
    },
    {
      'type': 'bool',
      'name': 'crop_from_edges_same_amount_for_each_side',
      'default_value': False,
      'display_name': _('Crop by the same amount from each side'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_edges_amount',
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
      'display_name': _('Amount'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_edges_top',
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
      'name': 'crop_from_edges_bottom',
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
      'name': 'crop_from_edges_left',
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
      'name': 'crop_from_edges_right',
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
      'type': 'anchor',
      'name': 'crop_from_position_anchor',
      'default_value': builtin_procedures_utils.AnchorPoints.CENTER,
      'items': [
        (builtin_procedures_utils.AnchorPoints.TOP_LEFT, _('Top left')),
        (builtin_procedures_utils.AnchorPoints.TOP, _('Top')),
        (builtin_procedures_utils.AnchorPoints.TOP_RIGHT, _('Top right')),
        (builtin_procedures_utils.AnchorPoints.LEFT, _('Left')),
        (builtin_procedures_utils.AnchorPoints.CENTER, _('Center')),
        (builtin_procedures_utils.AnchorPoints.RIGHT, _('Right')),
        (builtin_procedures_utils.AnchorPoints.BOTTOM_LEFT, _('Bottom left')),
        (builtin_procedures_utils.AnchorPoints.BOTTOM, _('Bottom')),
        (builtin_procedures_utils.AnchorPoints.BOTTOM_RIGHT, _('Bottom right')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_position_width',
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
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'crop_from_position_height',
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
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
    {
      'type': 'coordinates',
      'name': 'crop_to_aspect_ratio_ratio',
      'default_value': {
        'x': 1.0,
        'y': 1.0,
      },
      'min_x': 1.0,
      'min_y': 1.0,
      'display_name': _('Aspect ratio (width:height)'),
    },
    {
      'type': 'choice',
      'name': 'crop_to_aspect_ratio_position',
      'default_value': builtin_procedures_utils.Positions.CENTER,
      'items': [
        (builtin_procedures_utils.Positions.START, _('Start')),
        (builtin_procedures_utils.Positions.CENTER, _('Center')),
        (builtin_procedures_utils.Positions.END, _('End')),
        (builtin_procedures_utils.Positions.CUSTOM, _('Custom')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_aspect_ratio_position_custom',
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
      'display_name': _('Custom start position'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_x',
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
      'display_name': _('Start X'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_y',
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
      'display_name': _('Start Y'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
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
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'crop_to_area_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
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

_CROP_DIMENSION_ARGUMENT_INDEXES = [
  index for index, dict_ in enumerate(CROP_FOR_LAYERS_DICT['arguments'])
  if dict_['type'] == 'dimension']
for index in _CROP_DIMENSION_ARGUMENT_INDEXES:
  CROP_FOR_LAYERS_DICT['arguments'][index]['default_value']['percent_object'] = 'current_layer'
