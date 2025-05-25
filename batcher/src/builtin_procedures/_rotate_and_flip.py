"""Built-in "Rotate and flip" procedure."""

import math

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import utils
from src.procedure_groups import *

from . import _utils as builtin_procedures_utils


__all__ = [
  'Angles',
  'AngleUnits',
  'UNIT_DEGREE',
  'UNIT_RADIAN',
  'UNITS',
  'rotate_and_flip',
  'on_after_add_rotate_and_flip_procedure',
]


class Angles:
  ANGLES = (
    NONE,
    DEGREES_90,
    DEGREES_180,
    DEGREES_270,
    CUSTOM,
  ) = (
    'none',
    'degrees_90',
    'degrees_180',
    'degrees_270',
    'custom',
  )


class AngleUnits:
  ANGLE_UNITS = (
    DEGREE,
    RADIAN
  ) = (
    'degree',
    'radian'
  )


class _AngleUnit:

  def __init__(self, name, display_name, scaling_factor):
    self._name = name
    self._display_name = display_name
    self._scaling_factor = scaling_factor

  @property
  def name(self):
    return self._name

  @property
  def display_name(self):
    return self._display_name

  @property
  def scaling_factor(self):
    return self._scaling_factor


UNIT_DEGREE = _AngleUnit('degree', _('degrees'), 180 / math.pi)
UNIT_RADIAN = _AngleUnit('radian', _('radians'), 1.0)

UNITS = {
  UNIT_DEGREE.name: UNIT_DEGREE,
  UNIT_RADIAN.name: UNIT_RADIAN,
}


def rotate_and_flip(
      batcher,
      object_to_rotate_and_flip,
      angle,
      custom_rotation_angle,
      rotation_transform_resize,
      rotation_interpolation,
      rotate_around_center,
      rotation_center_x,
      rotation_center_y,
      flip_horizontally,
      flip_vertically,
):
  Gimp.context_push()
  Gimp.context_set_transform_resize(rotation_transform_resize)
  Gimp.context_set_interpolation(rotation_interpolation)
  Gimp.context_set_transform_direction(Gimp.TransformDirection.FORWARD)

  rotation_center_x_pixels = builtin_procedures_utils.unit_to_pixels(
    batcher,
    rotation_center_x,
    'x',
  )
  rotation_center_y_pixels = builtin_procedures_utils.unit_to_pixels(
    batcher,
    rotation_center_y,
    'y',
  )

  if isinstance(object_to_rotate_and_flip, Gimp.Image):
    if angle == Angles.DEGREES_90:
      object_to_rotate_and_flip.rotate(Gimp.RotationType.DEGREES90)
    elif angle == Angles.DEGREES_180:
      object_to_rotate_and_flip.rotate(Gimp.RotationType.DEGREES180)
    elif angle == Angles.DEGREES_270:
      object_to_rotate_and_flip.rotate(Gimp.RotationType.DEGREES270)
    elif angle == Angles.CUSTOM:
      image_center_x = object_to_rotate_and_flip.get_width() / 2
      image_center_y = object_to_rotate_and_flip.get_width() / 2

      for layer in object_to_rotate_and_flip.get_layers():
        layer.transform_rotate(
          _angle_to_radians(custom_rotation_angle),
          False,
          image_center_x,
          image_center_y,
        )
  else:
    if angle == Angles.DEGREES_90:
      object_to_rotate_and_flip.transform_rotate_simple(
        Gimp.RotationType.DEGREES90,
        rotate_around_center,
        rotation_center_x_pixels,
        rotation_center_y_pixels,
      )
    elif angle == Angles.DEGREES_180:
      object_to_rotate_and_flip.transform_rotate_simple(
        Gimp.RotationType.DEGREES180,
        rotate_around_center,
        rotation_center_x_pixels,
        rotation_center_y_pixels,
      )
    elif angle == Angles.DEGREES_270:
      object_to_rotate_and_flip.transform_rotate_simple(
        Gimp.RotationType.DEGREES270,
        rotate_around_center,
        rotation_center_x_pixels,
        rotation_center_y_pixels,
      )
    elif angle == Angles.CUSTOM:
      object_to_rotate_and_flip.transform_rotate(
        _angle_to_radians(custom_rotation_angle),
        rotate_around_center,
        rotation_center_x_pixels,
        rotation_center_y_pixels,
      )

  if isinstance(object_to_rotate_and_flip, Gimp.Image):
    if flip_horizontally:
      object_to_rotate_and_flip.flip(Gimp.OrientationType.HORIZONTAL)

    if flip_vertically:
      object_to_rotate_and_flip.flip(Gimp.OrientationType.VERTICAL)
  else:
    if flip_horizontally:
      object_to_rotate_and_flip.transform_flip_simple(Gimp.OrientationType.HORIZONTAL, True, 0.0)

    if flip_vertically:
      object_to_rotate_and_flip.transform_flip_simple(Gimp.OrientationType.VERTICAL, True, 0.0)

  Gimp.context_pop()


def _angle_to_radians(angle):
  scaling_factor = UNITS[angle['unit']].scaling_factor

  if scaling_factor != 0.0:
    return angle['value'] / scaling_factor
  else:
    return angle['value']


def on_after_add_rotate_and_flip_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('rotate_and_flip_for_'):
    _set_sensitive_for_custom_rotation_angle(
      procedure['arguments/angle'],
      procedure['arguments/custom_rotation_angle'],
    )

    procedure['arguments/angle'].connect_event(
      'value-changed',
      _set_sensitive_for_custom_rotation_angle,
      procedure['arguments/custom_rotation_angle'],
    )

    _set_value_and_sensitive_for_rotation_center_settings(
      procedure['arguments/object_to_rotate_and_flip'],
      procedure['arguments/rotate_around_center'],
      procedure['arguments/rotation_center_x'],
      procedure['arguments/rotation_center_y'],
    )

    procedure['arguments/object_to_rotate_and_flip'].connect_event(
      'value-changed',
      _set_value_and_sensitive_for_rotation_center_settings,
      procedure['arguments/rotate_around_center'],
      procedure['arguments/rotation_center_x'],
      procedure['arguments/rotation_center_y'],
    )

    _set_sensitive_for_rotation_center_x_y(
      procedure['arguments/rotate_around_center'],
      procedure['arguments/object_to_rotate_and_flip'],
      procedure['arguments/rotation_center_x'],
      procedure['arguments/rotation_center_y'],
    )

    procedure['arguments/rotate_around_center'].connect_event(
      'value-changed',
      _set_sensitive_for_rotation_center_x_y,
      procedure['arguments/object_to_rotate_and_flip'],
      procedure['arguments/rotation_center_x'],
      procedure['arguments/rotation_center_y'],
    )


def _set_sensitive_for_custom_rotation_angle(
      angle_setting,
      custom_rotation_angle_setting,
):
  custom_rotation_angle_setting.gui.set_sensitive(angle_setting.value == 'custom')


def _set_value_and_sensitive_for_rotation_center_settings(
      object_to_rotate_and_flip_setting,
      rotate_around_center_setting,
      rotation_center_x_setting,
      rotation_center_y_setting,
):
  is_image = object_to_rotate_and_flip_setting.value == 'current_image'

  rotate_around_center_setting.gui.set_sensitive(not is_image)
  rotation_center_x_setting.gui.set_sensitive(not (is_image or rotate_around_center_setting.value))
  rotation_center_y_setting.gui.set_sensitive(not (is_image or rotate_around_center_setting.value))


def _set_sensitive_for_rotation_center_x_y(
      rotate_around_center_setting,
      object_to_rotate_and_flip_setting,
      rotation_center_x_setting,
      rotation_center_y_setting,
):
  is_image = object_to_rotate_and_flip_setting.value == 'current_image'

  rotation_center_x_setting.gui.set_sensitive(not (is_image or rotate_around_center_setting.value))
  rotation_center_y_setting.gui.set_sensitive(not (is_image or rotate_around_center_setting.value))


ROTATE_AND_FLIP_FOR_IMAGES_DICT = {
  'name': 'rotate_and_flip_for_images',
  'function': rotate_and_flip,
  'display_name': _('Rotate and flip'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_rotate_and_flip',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'angle',
      'default_value': Angles.NONE,
      'items': [
        (Angles.NONE, _('None')),
        (Angles.DEGREES_90, _('90° (clockwise)')),
        (Angles.DEGREES_180, _('180°')),
        (Angles.DEGREES_270, _('270° (counter-clockwise)')),
        (Angles.CUSTOM, _('Custom')),
      ],
      'display_name': _('Rotation angle'),
    },
    {
      'type': 'angle',
      'name': 'custom_rotation_angle',
      'default_value': {
        'value': 0.0,
        'unit': 'degree',
      },
      'display_name': _('Custom rotation angle'),
    },
    {
      'type': 'enum',
      'enum_type': Gimp.TransformResize,
      'name': 'rotation_transform_resize',
      'default_value': Gimp.TransformResize.ADJUST,
      'display_name': _('How to handle boundaries'),
    },
    {
      'type': 'enum',
      'enum_type': Gimp.InterpolationType,
      'name': 'rotation_interpolation',
      'default_value': Gimp.InterpolationType.NONE,
      'display_name': _('Interpolation'),
    },
    {
      'type': 'bool',
      'name': 'rotate_around_center',
      'default_value': True,
      'display_name': _('Rotate around the center'),
    },
    {
      'type': 'dimension',
      'name': 'rotation_center_x',
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
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Horizontal position of rotation center'),
    },
    {
      'type': 'dimension',
      'name': 'rotation_center_y',
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
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Vertical position of rotation center'),
    },
    {
      'type': 'bool',
      'name': 'flip_horizontally',
      'default_value': False,
      'display_name': _('Flip horizontally'),
    },
    {
      'type': 'bool',
      'name': 'flip_vertically',
      'default_value': False,
      'display_name': _('Flip vertically'),
    },
  ]
}

ROTATE_AND_FLIP_FOR_LAYERS_DICT = utils.semi_deep_copy(ROTATE_AND_FLIP_FOR_IMAGES_DICT)
ROTATE_AND_FLIP_FOR_LAYERS_DICT.update({
  'name': 'rotate_and_flip_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
ROTATE_AND_FLIP_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'
