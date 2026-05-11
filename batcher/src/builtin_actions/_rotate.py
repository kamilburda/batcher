"""Built-in "Rotate" action."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import builtin_commands_common
from src import utils
from src import placeholders as placeholders_
from src.procedure_groups import *

from . import _utils as builtin_actions_utils


__all__ = [
  'Angles',
  'AngleUnits',
  'rotate',
]


class Angles:
  ANGLES = (
    DEGREES_90,
    DEGREES_180,
    DEGREES_270,
    CUSTOM,
  ) = (
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


def rotate(
      batcher,
      object_to_rotate,
      angle,
      custom_angle,
      resize_image_to_fit,
      transform_resize,
      interpolation,
      rotate_around_center,
      center_x,
      center_y,
):
  Gimp.context_push()
  Gimp.context_set_transform_resize(transform_resize)
  Gimp.context_set_interpolation(interpolation)
  Gimp.context_set_transform_direction(Gimp.TransformDirection.FORWARD)

  center_x_pixels = builtin_actions_utils.unit_to_pixels(
    batcher,
    center_x,
    'x',
  )
  center_y_pixels = builtin_actions_utils.unit_to_pixels(
    batcher,
    center_y,
    'y',
  )

  if isinstance(object_to_rotate, Gimp.Image):
    if angle == Angles.DEGREES_90:
      object_to_rotate.rotate(Gimp.RotationType.DEGREES90)
    elif angle == Angles.DEGREES_180:
      object_to_rotate.rotate(Gimp.RotationType.DEGREES180)
    elif angle == Angles.DEGREES_270:
      object_to_rotate.rotate(Gimp.RotationType.DEGREES270)
    elif angle == Angles.CUSTOM:
      image_center_x = object_to_rotate.get_width() / 2
      image_center_y = object_to_rotate.get_width() / 2

      for layer in object_to_rotate.get_layers():
        layer.transform_rotate(
          builtin_actions_utils.angle_to_radians(custom_angle),
          False,
          image_center_x,
          image_center_y,
        )

      if resize_image_to_fit:
        object_to_rotate.resize_to_layers()
  else:
    if angle == Angles.DEGREES_90:
      object_to_rotate.transform_rotate_simple(
        Gimp.RotationType.DEGREES90,
        rotate_around_center,
        center_x_pixels,
        center_y_pixels,
      )
    elif angle == Angles.DEGREES_180:
      object_to_rotate.transform_rotate_simple(
        Gimp.RotationType.DEGREES180,
        rotate_around_center,
        center_x_pixels,
        center_y_pixels,
      )
    elif angle == Angles.DEGREES_270:
      object_to_rotate.transform_rotate_simple(
        Gimp.RotationType.DEGREES270,
        rotate_around_center,
        center_x_pixels,
        center_y_pixels,
      )
    elif angle == Angles.CUSTOM:
      object_to_rotate.transform_rotate(
        builtin_actions_utils.angle_to_radians(custom_angle),
        rotate_around_center,
        center_x_pixels,
        center_y_pixels,
      )

  Gimp.context_pop()


def _on_after_add_rotate_action(_actions, action, _orig_action_dict, _settings):
  _set_visible_for_custom_angle_settings(
    action['arguments/angle'],
    action['arguments/custom_angle'],
    action['arguments/interpolation'],
  )

  action['arguments/angle'].connect_event(
    'value-changed',
    _set_visible_for_custom_angle_settings,
    action['arguments/custom_angle'],
    action['arguments/interpolation'],
  )

  _set_value_and_visible_for_rotation_center_settings(
    action['arguments/object_to_rotate'],
    action['arguments/rotate_around_center'],
    action['arguments/center_x'],
    action['arguments/center_y'],
  )

  action['arguments/object_to_rotate'].connect_event(
    'value-changed',
    _set_value_and_visible_for_rotation_center_settings,
    action['arguments/rotate_around_center'],
    action['arguments/center_x'],
    action['arguments/center_y'],
  )

  _set_visible_for_center_x_y(
    action['arguments/rotate_around_center'],
    action['arguments/object_to_rotate'],
    action['arguments/center_x'],
    action['arguments/center_y'],
  )

  action['arguments/rotate_around_center'].connect_event(
    'value-changed',
    _set_visible_for_center_x_y,
    action['arguments/object_to_rotate'],
    action['arguments/center_x'],
    action['arguments/center_y'],
  )

  _set_visible_for_resize_image_to_fit(
    action['arguments/angle'],
    action['arguments/resize_image_to_fit'],
    action['arguments/object_to_rotate'],
  )

  action['arguments/angle'].connect_event(
    'value-changed',
    _set_visible_for_resize_image_to_fit,
    action['arguments/resize_image_to_fit'],
    action['arguments/object_to_rotate'],
  )

  action['arguments/object_to_rotate'].connect_event(
    'value-changed',
    _set_visible_for_resize_image_to_fit_via_object_to_rotate,
    action['arguments/resize_image_to_fit'],
    action['arguments/angle'],
  )

  builtin_commands_common.set_up_display_name_change_for_command(
    _set_display_name_for_rotate,
    action['arguments/angle'],
    action,
    [
      action['arguments/custom_angle'],
    ],
  )

  action['arguments/custom_angle'].connect_event(
    'value-changed',
    _set_display_name_for_rotate_via_custom_angle,
    action['arguments/angle'],
    action,
  )


def _set_visible_for_custom_angle_settings(
      angle_setting,
      custom_angle_setting,
      interpolation_setting,
):
  custom_angle_setting.gui.set_visible(angle_setting.value == 'custom')
  interpolation_setting.gui.set_visible(angle_setting.value == 'custom')


def _set_value_and_visible_for_rotation_center_settings(
      object_to_rotate_setting,
      rotate_around_center_setting,
      center_x_setting,
      center_y_setting,
):
  is_image = object_to_rotate_setting.value == 'current_image'

  rotate_around_center_setting.gui.set_visible(not is_image)
  center_x_setting.gui.set_visible(not (is_image or rotate_around_center_setting.value))
  center_y_setting.gui.set_visible(not (is_image or rotate_around_center_setting.value))


def _set_visible_for_center_x_y(
      rotate_around_center_setting,
      object_to_rotate_setting,
      center_x_setting,
      center_y_setting,
):
  is_image = object_to_rotate_setting.value == 'current_image'

  center_x_setting.gui.set_visible(not (is_image or rotate_around_center_setting.value))
  center_y_setting.gui.set_visible(not (is_image or rotate_around_center_setting.value))


def _set_visible_for_resize_image_to_fit(
      angle_setting,
      resize_image_to_fit_setting,
      object_to_rotate_setting,
):
  resize_image_to_fit_setting.gui.set_visible(
    object_to_rotate_setting.value == 'current_image'
    and angle_setting.value == 'custom')


def _set_visible_for_resize_image_to_fit_via_object_to_rotate(
      object_to_rotate_setting,
      resize_image_to_fit_setting,
      angle_setting,
):
  _set_visible_for_resize_image_to_fit(
    angle_setting,
    resize_image_to_fit_setting,
    object_to_rotate_setting,
  )


def _set_display_name_for_rotate(
      angle_setting,
      action,
      custom_angle_setting,
):
  if angle_setting.value == Angles.DEGREES_90:
    action['display_name'].set_value(_('Rotate by 90°'))
  elif angle_setting.value == Angles.DEGREES_180:
    action['display_name'].set_value(_('Rotate by 180°'))
  elif angle_setting.value == Angles.DEGREES_270:
    action['display_name'].set_value(_('Rotate by 270°'))
  elif angle_setting.value == Angles.CUSTOM:
    if custom_angle_setting.value['unit'] == AngleUnits.DEGREE:
      angle_unit = '°'
    elif custom_angle_setting.value['unit'] == AngleUnits.RADIAN:
      angle_unit = ' rad'
    else:
      angle_unit = None

    if angle_unit is not None:
      angle_value = round(custom_angle_setting.value['value'], 2)
      action['display_name'].set_value(_('Rotate by {}{}').format(angle_value, angle_unit))
    else:
      action['display_name'].set_value(_('Rotate'))
  else:
    action['display_name'].set_value(_('Rotate'))


def _set_display_name_for_rotate_via_custom_angle(
      custom_angle_setting,
      angle_setting,
      action,
):
  _set_display_name_for_rotate(
    angle_setting,
    action,
    custom_angle_setting,
  )


ROTATE_FOR_IMAGES_DICT = {
  'name': 'rotate_for_images',
  'function': rotate,
  'display_name': _('Rotate'),
  'menu_path': _('Resize and Transform'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_rotate',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'angle',
      'default_value': Angles.DEGREES_90,
      'items': [
        (Angles.DEGREES_90, _('90° (clockwise)')),
        (Angles.DEGREES_180, _('180°')),
        (Angles.DEGREES_270, _('270° (counter-clockwise)')),
        (Angles.CUSTOM, _('Custom')),
      ],
      'display_name': _('Angle'),
    },
    {
      'type': 'angle',
      'name': 'custom_angle',
      'default_value': {
        'value': 0.0,
        'unit': AngleUnits.DEGREE,
      },
      'display_name': _('Custom angle'),
    },
    {
      'type': 'bool',
      'name': 'resize_image_to_fit',
      'default_value': True,
      'display_name': _('Resize image to fit'),
    },
    {
      'type': 'enum',
      'enum_type': Gimp.TransformResize,
      'name': 'transform_resize',
      'default_value': Gimp.TransformResize.ADJUST,
      'display_name': _('How to handle boundaries'),
    },
    {
      'type': 'enum',
      'enum_type': Gimp.InterpolationType,
      'name': 'interpolation',
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
      'name': 'center_x',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          placeholders_.ALL_IMAGE_PLACEHOLDERS: 'width',
          placeholders_.ALL_LAYER_PLACEHOLDERS: 'width',
        },
      },
      'percent_placeholder_names': [
        *placeholders_.ALL_IMAGE_PLACEHOLDERS,
        *placeholders_.ALL_LAYER_PLACEHOLDERS,
      ],
      'display_name': _('Horizontal position of center'),
    },
    {
      'type': 'dimension',
      'name': 'center_y',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_image',
        'percent_property': {
          placeholders_.ALL_IMAGE_PLACEHOLDERS: 'height',
          placeholders_.ALL_LAYER_PLACEHOLDERS: 'height',
        },
      },
      'percent_placeholder_names': [
        *placeholders_.ALL_IMAGE_PLACEHOLDERS,
        *placeholders_.ALL_LAYER_PLACEHOLDERS,
      ],
      'display_name': _('Vertical position of center'),
    },
  ],
  'after_add_handler': _on_after_add_rotate_action,
}

ROTATE_FOR_LAYERS_DICT = utils.semi_deep_copy(ROTATE_FOR_IMAGES_DICT)
ROTATE_FOR_LAYERS_DICT.update({
  'name': 'rotate_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
ROTATE_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'
