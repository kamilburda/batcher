"""Utility functions used within the `builtin_procedures` package."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib import pdb

from src import exceptions
from src import placeholders as placeholders_


class AnchorPoints:
  ANCHOR_POINTS = (
    TOP_LEFT,
    TOP,
    TOP_RIGHT,
    LEFT,
    CENTER,
    RIGHT,
    BOTTOM_LEFT,
    BOTTOM,
    BOTTOM_RIGHT,
  ) = (
    'top_left',
    'top',
    'top_right',
    'left',
    'center',
    'right',
    'bottom_left',
    'bottom',
    'bottom_right',
  )


class Positions:
  POSITIONS = (
    START,
    CENTER,
    END,
    CUSTOM,
  ) = (
    'start',
    'center',
    'end',
    'custom',
  )


def unit_to_pixels(batcher, dimension, resolution_axis):
  """Converts the value of a `setting_classes.DimensionSetting` to pixels.

  ``resolution_axis`` is either ``'x'`` or ``'y'`` and represents the image
  resolution along the x- or y-axis, respectively. The resolution is used to
  convert units other than pixels or percentages (e.g. inches) to pixels. The
  image to obtain resolution from is the currently processed image
  (`batcher.current_image`).
  """
  if dimension['unit'] == Gimp.Unit.percent():
    placeholder_object = placeholders_.PLACEHOLDERS[dimension['percent_object']]
    gimp_object = placeholder_object.replace_args(None, batcher)

    percent_property = _get_percent_property_value(
      dimension['percent_property'], dimension['percent_object'])

    if percent_property == 'width':
      gimp_object_dimension = gimp_object.get_width()
    elif percent_property == 'height':
      gimp_object_dimension = gimp_object.get_height()
    elif percent_property == 'x_offset':
      if isinstance(gimp_object, Gimp.Image):
        gimp_object_dimension = 0
      else:
        gimp_object_dimension = gimp_object.get_offsets().offset_x
    elif percent_property == 'y_offset':
      if isinstance(gimp_object, Gimp.Image):
        gimp_object_dimension = 0
      else:
        gimp_object_dimension = gimp_object.get_offsets().offset_y
    else:
      raise ValueError(f'unrecognized percent property: {percent_property}')

    pixels = (dimension['percent_value'] / 100) * gimp_object_dimension
  elif dimension['unit'] == Gimp.Unit.pixel():
    pixels = dimension['pixel_value']
  else:
    image_resolution = batcher.current_image.get_resolution()
    if resolution_axis == 'x':
      image_resolution_for_axis = image_resolution.xresolution
    elif resolution_axis == 'y':
      image_resolution_for_axis = image_resolution.yresolution
    else:
      raise ValueError(f'unrecognized value for resolution_axis: {resolution_axis}')

    pixels = (
      dimension['other_value'] / dimension['unit'].get_factor() * image_resolution_for_axis)

  int_pixels = round(pixels)

  return int_pixels


def _get_percent_property_value(percent_property, percent_object):
  """Returns the property (e.g. width, X-offset) for the current value of
  ``'percent_object'`` within the `DimensionSetting` value's
  ``percent_property`` entry.
  """
  for key in percent_property:
    if percent_object in key:
      return percent_property[key]

  return None


def add_color_layer(
      padding_color,
      image,
      drawable,
      color_layer_offset_x,
      color_layer_offset_y,
      color_layer_width,
      color_layer_height,
      selection_x,
      selection_y,
      selection_width,
      selection_height,
):
  Gimp.context_push()
  Gimp.context_set_foreground(pg.setting.ColorSetting.get_value_as_color(padding_color))
  Gimp.context_set_opacity(
    pg.setting.ColorSetting.get_value_as_color(padding_color).get_rgba().alpha * 100)

  channel = pdb.gimp_selection_save(image=image)
  image.select_rectangle(
    Gimp.ChannelOps.REPLACE,
    selection_x,
    selection_y,
    selection_width,
    selection_height,
  )

  pdb.gimp_selection_invert(image=image)

  selection_is_non_empty = pdb.gimp_selection_bounds(image=image)[0]
  if selection_is_non_empty:
    color_layer = Gimp.Layer.new(
      image,
      drawable.get_name(),
      color_layer_width,
      color_layer_height,
      Gimp.ImageType.RGBA_IMAGE,
      100.0,
      Gimp.LayerMode.NORMAL,
    )
    color_layer.set_offsets(color_layer_offset_x, color_layer_offset_y)
    image.insert_layer(
      color_layer,
      drawable.get_parent(),
      image.get_item_position(drawable) + 1,
    )

    color_layer.edit_fill(Gimp.FillType.FOREGROUND)

    image.merge_down(drawable, Gimp.MergeType.EXPAND_AS_NECESSARY)

  image.select_item(Gimp.ChannelOps.REPLACE, channel)
  image.remove_channel(channel)

  Gimp.context_pop()


def get_best_matching_layer_from_image(batcher, image):
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
      # Rather than returning no layer, we skip the current procedure. An image
      # having no layers points to a problem outside the procedure.
      raise exceptions.SkipAction(_('The image has no layers.'))
