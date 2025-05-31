"""Utility functions used within the `builtin_procedures` package."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

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
