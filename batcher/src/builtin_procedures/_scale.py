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
  'on_after_add_scale_procedure',
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
      aspect_ratio,
      interpolation,
      local_origin,
      set_image_resolution,
      image_resolution,
      padding_color,
      padding_position,
      padding_position_custom,
):
  if set_image_resolution:
    processed_resolution_x = image_resolution['x'] if image_resolution['x'] > 0 else 1.0
    processed_resolution_y = image_resolution['y'] if image_resolution['y'] > 0 else 1.0

    if isinstance(object_to_scale, Gimp.Image):
      object_to_scale.set_resolution(processed_resolution_x, processed_resolution_y)
    elif isinstance(object_to_scale, Gimp.Item):
      object_to_scale.get_image().set_resolution(processed_resolution_x, processed_resolution_y)

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
      padding_position,
      padding_position_custom,
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
      padding_position,
      padding_position_custom,
):
  object_width = gimp_object.get_width()
  object_height = gimp_object.get_height()

  if isinstance(gimp_object, Gimp.Image):
    drawable_with_padding = batcher.current_layer
    image_of_drawable_with_padding = gimp_object
  else:
    drawable_with_padding = gimp_object
    image_of_drawable_with_padding = gimp_object.get_image()

  if new_width_pixels > object_width:
    offset_x = 0
    if padding_position == builtin_procedures_utils.Positions.START:
      offset_x = 0
    elif padding_position == builtin_procedures_utils.Positions.CENTER:
      offset_x = round((new_width_pixels - object_width) / 2)
    elif padding_position == builtin_procedures_utils.Positions.END:
      offset_x = new_width_pixels - object_width
    elif padding_position == builtin_procedures_utils.Positions.CUSTOM:
      offset_x = builtin_procedures_utils.unit_to_pixels(batcher, padding_position_custom, 'x')
      offset_x = min(offset_x, new_width_pixels - object_width)

    offset_y = 0
  else:
    offset_y = 0
    if padding_position == builtin_procedures_utils.Positions.START:
      offset_y = 0
    elif padding_position == builtin_procedures_utils.Positions.CENTER:
      offset_y = round((new_height_pixels - object_height) / 2)
    elif padding_position == builtin_procedures_utils.Positions.END:
      offset_y = new_height_pixels - object_height
    elif padding_position == builtin_procedures_utils.Positions.CUSTOM:
      offset_y = builtin_procedures_utils.unit_to_pixels(batcher, padding_position_custom, 'y')
      offset_y = min(offset_y, new_height_pixels - object_height)

    offset_x = 0

  if isinstance(gimp_object, Gimp.Image):
    color_layer_offset_x = 0
    color_layer_offset_y = 0

    new_object_offset_x = offset_x
    new_object_offset_y = offset_y

    gimp_object.resize(new_width_pixels, new_height_pixels, offset_x, offset_y)
  else:
    drawable_with_padding_offsets = gimp_object.get_offsets()

    color_layer_offset_x = drawable_with_padding_offsets.offset_x
    color_layer_offset_y = drawable_with_padding_offsets.offset_y

    new_object_offset_x = drawable_with_padding_offsets.offset_x + offset_x
    new_object_offset_y = drawable_with_padding_offsets.offset_y + offset_y

    gimp_object.set_offsets(new_object_offset_x, new_object_offset_y)

  builtin_procedures_utils.add_color_layer(
    padding_color,
    image_of_drawable_with_padding,
    drawable_with_padding,
    color_layer_offset_x,
    color_layer_offset_y,
    new_width_pixels,
    new_height_pixels,
    new_object_offset_x,
    new_object_offset_y,
    object_width,
    object_height,
  )


def on_after_add_scale_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('scale_for_'):
    _set_sensitive_for_local_origin(
      procedure['arguments/object_to_scale'],
      procedure['arguments/local_origin'],
    )

    procedure['arguments/object_to_scale'].connect_event(
      'value-changed',
      _set_sensitive_for_local_origin,
      procedure['arguments/local_origin'])

    _set_sensitive_for_dimensions_given_aspect_ratio(
      procedure['arguments/aspect_ratio'],
      procedure['arguments/new_width'],
      procedure['arguments/new_height'],
    )

    procedure['arguments/aspect_ratio'].connect_event(
      'value-changed',
      _set_sensitive_for_dimensions_given_aspect_ratio,
      procedure['arguments/new_width'],
      procedure['arguments/new_height'],
    )

    procedure['arguments/padding_position'].connect_event(
      'value-changed',
      _set_visible_for_padding_custom_position,
      procedure['arguments/padding_position_custom'],
    )

    procedure['arguments/padding_position'].connect_event(
      'gui-visible-changed',
      _set_visible_for_padding_custom_position,
      procedure['arguments/padding_position_custom'],
    )

    _set_visible_for_padding_color_and_position(
      procedure['arguments/aspect_ratio'],
      procedure['arguments/padding_color'],
      procedure['arguments/padding_position'],
    )

    procedure['arguments/aspect_ratio'].connect_event(
      'value-changed',
      _set_visible_for_padding_color_and_position,
      procedure['arguments/padding_color'],
      procedure['arguments/padding_position'],
    )

    procedure['arguments/image_resolution'].connect_event(
      'after-set-gui',
      _set_left_margin_for_resolution,
    )

    _set_sensitive_for_resolution(
      procedure['arguments/set_image_resolution'],
      procedure['arguments/image_resolution'],
    )

    procedure['arguments/set_image_resolution'].connect_event(
      'value-changed',
      _set_sensitive_for_resolution,
      procedure['arguments/image_resolution'],
    )


def _set_sensitive_for_local_origin(object_to_scale_setting, local_origin_setting):
  local_origin_setting.gui.set_sensitive(object_to_scale_setting.value != 'current_image')


def _set_sensitive_for_dimensions_given_aspect_ratio(
      aspect_ratio_setting,
      new_width_setting,
      new_height_setting,
):
  adjust_width = aspect_ratio_setting.value == AspectRatios.KEEP_ADJUST_WIDTH
  adjust_height = aspect_ratio_setting.value == AspectRatios.KEEP_ADJUST_HEIGHT

  new_width_setting.gui.set_sensitive(not adjust_height)
  new_height_setting.gui.set_sensitive(not adjust_width)


def _set_visible_for_padding_custom_position(
      padding_position_setting,
      padding_position_custom_setting,
):
  padding_position_custom_setting.gui.set_visible(
    padding_position_setting.gui.get_visible()
    and padding_position_setting.value == builtin_procedures_utils.Positions.CUSTOM)


def _set_visible_for_padding_color_and_position(
      aspect_ratio_setting,
      padding_color_setting,
      padding_position_setting,
):
  padding_color_setting.gui.set_visible(
    aspect_ratio_setting.value == AspectRatios.FIT_WITH_PADDING)
  padding_position_setting.gui.set_visible(
    aspect_ratio_setting.value == AspectRatios.FIT_WITH_PADDING)


def _set_left_margin_for_resolution(image_resolution_setting):
  if not isinstance(image_resolution_setting.gui, pg.setting.NullPresenter):
    image_resolution_setting.gui.widget.set_margin_start(pg.constants.RELATED_WIDGETS_LEFT_MARGIN)


def _set_sensitive_for_resolution(set_image_resolution_setting, image_resolution_setting):
  image_resolution_setting.gui.set_sensitive(set_image_resolution_setting.value)


SCALE_FOR_IMAGES_DICT = {
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
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
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
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
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
      'type': 'enum',
      'enum_type': Gimp.InterpolationType,
      'name': 'interpolation',
      'default_value': Gimp.InterpolationType.NONE,
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
      'type': 'coordinates',
      'name': 'image_resolution',
      'default_value': {
        'x': 72.0,
        'y': 72.0,
      },
      'min_x': 0.0,
      'min_y': 0.0,
      'show_display_name': False,
      'gui_type_kwargs': {
        # FOR TRANSLATORS: "X" represents the X-axis.
        'label_x': _('X'),
        # FOR TRANSLATORS: "Y" represents the Y-axis.
        'label_y': _('Y'),
      },
    },
    {
      'type': 'color',
      'name': 'padding_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Padding color'),
    },
    {
      'type': 'choice',
      'name': 'padding_position',
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
      'name': 'padding_position_custom',
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
  ],
}

SCALE_FOR_LAYERS_DICT = utils.semi_deep_copy(SCALE_FOR_IMAGES_DICT)
SCALE_FOR_LAYERS_DICT.update({
  'name': 'scale_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
SCALE_FOR_LAYERS_DICT['arguments'][0]['default_value'] = 'current_layer'

_SCALE_DIMENSION_ARGUMENT_INDEXES = [
  index for index, dict_ in enumerate(SCALE_FOR_LAYERS_DICT['arguments'])
  if dict_['type'] == 'dimension']
for index in _SCALE_DIMENSION_ARGUMENT_INDEXES:
  SCALE_FOR_LAYERS_DICT['arguments'][index]['default_value']['percent_object'] = 'current_layer'
