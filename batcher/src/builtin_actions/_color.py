"""Built-in actions related to adjusting colors."""

import re
import struct

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import constants
from src import exceptions
from src import utils_pdb
from src.procedure_groups import *
from src.pypdb import pdb


__all__ = [
  'brightness_contrast',
  'levels',
  'curves',
  'white_balance',
  'BrightnessContrastFilters',
  'on_after_add_brightness_contrast_action',
]


class BrightnessContrastFilters:
  BRIGHTNESS_CONTRAST_FILTERS = (
    GEGL,
    GIMP,
  ) = 'gegl', 'gimp'


class CurveData:

  def __init__(self, curve_type=None, channel=None, samples=None, points=None):
    self.curve_type = curve_type
    self.channel = channel
    self.samples = samples
    self.points = points


class LevelsData:

  def __init__(
        self,
        channel=None,
        low_input=0.0,
        high_input=1.0,
        clamp_input=False,
        gamma=1.0,
        low_output=0.0,
        high_output=1.0,
        clamp_output=False,
  ):
    self.channel = channel
    self.low_input = low_input
    self.high_input = high_input
    self.clamp_input = clamp_input
    self.gamma = gamma
    self.low_output = low_output
    self.high_output = high_output
    self.clamp_output = clamp_output

  def has_default_values(self):
    return (
      self.low_input == 0.0
      and self.high_input == 1.0
      and self.gamma == 1.0
      and self.low_output == 0.0
      and self.high_output == 1.0
    )


def brightness_contrast(
      _batcher,
      layer,
      brightness,
      contrast,
      filter_,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  value_range = _MAX_BRIGHTNESS_CONTRAST_VALUE - _MIN_BRIGHTNESS_CONTRAST_VALUE

  if filter_ == BrightnessContrastFilters.GEGL:
    processed_brightness = (brightness / value_range) * 2
    processed_contrast = (contrast / value_range) * 2 + 1.0

    pdb.gegl__brightness_contrast(
      layer,
      contrast=processed_contrast,
      brightness=processed_brightness,
      merge_filter_=not apply_non_destructively,
      blend_mode_=blend_mode,
      opacity_=opacity / 100.0,
    )
  elif filter_ == BrightnessContrastFilters.GIMP:
    if utils_pdb.get_gimp_version() < (3, 1, 4):
      return

    processed_brightness = (brightness / value_range) * 2
    processed_contrast = (contrast / value_range) * 2

    pdb.gimp__brightness_contrast(
      layer,
      brightness=processed_brightness,
      contrast=processed_contrast,
      merge_filter_=not apply_non_destructively,
      blend_mode_=blend_mode,
      opacity_=opacity / 100.0,
    )


def levels(
      _batcher,
      layer,
      preset_file,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  image = layer.get_image()

  if (image.get_base_type() == Gimp.ImageBaseType.INDEXED
      and preset_file is not None and preset_file.get_path() is not None):
    raise ValueError('Levels cannot be applied to indexed images')

  _apply_levels_curves(
    layer,
    preset_file,
    _parse_gimp_levels_preset,
    _parse_photoshop_levels_preset,
    _apply_levels,
    apply_non_destructively,
    blend_mode,
    opacity,
  )


def curves(
      _batcher,
      layer,
      preset_file,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  _apply_levels_curves(
    layer,
    preset_file,
    _parse_gimp_curves_preset,
    _parse_photoshop_curves_preset,
    _apply_curves,
    apply_non_destructively,
    blend_mode,
    opacity,
  )


def _apply_levels_curves(
      layer,
      preset_file,
      _parse_gimp_preset,
      _parse_photoshop_preset,
      _apply_func,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  if preset_file is None or preset_file.get_path() is None:
    raise exceptions.SkipCommand(_('Preset file not specified.'))

  try:
    with open(preset_file.get_path(), 'r', encoding=constants.TEXT_FILE_ENCODING) as f:
      preset_data = f.readlines()
  except Exception:
    file_successfully_read = False
  else:
    file_successfully_read = True

  trc = None
  curve_data = None

  if file_successfully_read:
    try:
      trc, curve_data = _parse_gimp_preset(preset_data)
    except Exception as e:
      raise ValueError(_FAILED_TO_READ_DATA_MESSAGE) from e
  else:
    with open(preset_file.get_path(), 'rb') as f:
      try:
        trc, curve_data = _parse_photoshop_preset(f)
      except Exception as e:
        raise ValueError(_FAILED_TO_READ_DATA_MESSAGE) from e

  if utils_pdb.get_gimp_version() < (3, 2) and trc != _TRC_TYPES['linear']:
    raise ValueError(
      _('Only presets with the linear mode are supported for GIMP versions earlier than 3.2.'
        ' Upgrade to GIMP 3.2 or later if you need to use presets with modes other than linear.'))

  if trc is not None and curve_data is not None:
    _apply_func(
      layer,
      trc,
      curve_data,
      apply_non_destructively,
      blend_mode,
      opacity,
    )


def _apply_levels(
      layer,
      trc,
      levels_data,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  for levels_data_for_channel in levels_data.values():
    if not levels_data_for_channel.has_default_values():
      if utils_pdb.get_gimp_version() >= (3, 2):
        pdb.gimp__levels(
          layer,
          trc=trc,
          channel=levels_data_for_channel.channel,
          low_input=levels_data_for_channel.low_input,
          high_input=levels_data_for_channel.high_input,
          clamp_input=levels_data_for_channel.clamp_input,
          gamma=levels_data_for_channel.gamma,
          low_output=levels_data_for_channel.low_output,
          high_output=levels_data_for_channel.high_output,
          clamp_output=levels_data_for_channel.clamp_output,
          merge_filter_=not apply_non_destructively,
          blend_mode_=blend_mode,
          opacity_=opacity / 100.0,
        )
      else:
        layer.levels(
          levels_data_for_channel.channel,
          levels_data_for_channel.low_input,
          levels_data_for_channel.high_input,
          levels_data_for_channel.clamp_input,
          levels_data_for_channel.gamma,
          levels_data_for_channel.low_output,
          levels_data_for_channel.high_output,
          levels_data_for_channel.clamp_output,
        )


def _apply_curves(
      layer,
      trc,
      curve_data,
      apply_non_destructively,
      blend_mode,
      opacity,
):
  for curve_data_for_channel in curve_data.values():
    if curve_data_for_channel.channel is None:
      continue

    if utils_pdb.get_gimp_version() >= (3, 2):
      curve = Gimp.Curve.new()

      if curve_data_for_channel.curve_type is not None:
        curve.set_curve_type(Gimp.CurveType.FREE)

      max_index = len(curve_data_for_channel.samples) - 1
      for index, sample in enumerate(curve_data_for_channel.samples):
        curve.set_sample(index / max_index, sample)

      pdb.gimp__curves(
        layer,
        trc=trc,
        channel=curve_data_for_channel.channel,
        curve=curve,
        merge_filter_=not apply_non_destructively,
        blend_mode_=blend_mode,
        opacity_=opacity / 100.0,
      )
    else:
      if curve_data_for_channel.samples is not None:
        layer.curves_explicit(curve_data_for_channel.channel, curve_data_for_channel.samples)
      elif curve_data_for_channel.points is not None:
        layer.curves_spline(curve_data_for_channel.channel, curve_data_for_channel.points)
      else:
        raise ValueError('failed to obtain curve points from file')


def _parse_gimp_levels_preset(data):
  # We create empty levels data with a fixed order of channels. When levels are
  # applied as filters, they are appended. A filter using the VALUE channel
  # must be appended after other channels so that we obtain a result identical
  # to the Levels tool in GIMP. Hence, the VALUE channel is created here as the
  # last channel.
  levels_data = {
    channel: LevelsData()
    for channel in reversed(_HISTOGRAM_CHANNELS.values())
  }

  trc = None
  clamp_input = None
  clamp_output = None

  current_channel = None

  for line in data:
    if trc is None:
      trc = _get_trc_from_str(_parse_entry(line, 'trc'))

    if clamp_input is None:
      clamp_input = _parse_clamp_value(line, 'clamp-input')

    if clamp_output is None:
      clamp_output = _parse_clamp_value(line, 'clamp-output')

    parsed_channel = _parse_entry(line, 'channel')
    if parsed_channel is not None:
      current_channel = _get_channel_from_str(parsed_channel)
      levels_data[current_channel].channel = current_channel
      levels_data[current_channel].clamp_input = clamp_input
      levels_data[current_channel].clamp_output = clamp_output

    for entry in [
      'low-input',
      'high-input',
      'gamma',
      'low-output',
      'high-output',
    ]:
      parsed_entry = _parse_entry(line, entry)
      if parsed_entry is not None:
        setattr(levels_data[current_channel], entry.replace('-', '_'), float(parsed_entry))

  if trc is None:
    trc = _TRC_TYPES['linear']

  return trc, levels_data


def _parse_photoshop_levels_preset(file):
  _version = struct.unpack('>H', file.read(2))

  # We ignore other channels provided in the .alv file as there is no support
  # for them in GIMP at the time of writing this comment.
  levels_data = {}
  for channel in _HISTOGRAM_CHANNELS.values():
    levels_parameters = _read_levels_parameters(file)
    levels_data[channel] = LevelsData(
      channel=channel,
      **levels_parameters,
      clamp_input=True,
      clamp_output=True,
    )

  return _TRC_TYPES['linear'], levels_data


def _read_levels_parameters(file):
  return {
    # The range for low_input is 0..253:
    # https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/#50577411_pgfId-1057086
    'low_input': struct.unpack('>H', file.read(2))[0] / 253.0,
    'high_input': struct.unpack('>H', file.read(2))[0] / 255.0,
    'low_output': struct.unpack('>H', file.read(2))[0] / 255.0,
    'high_output': struct.unpack('>H', file.read(2))[0] / 255.0,
    'gamma': struct.unpack('>H', file.read(2))[0] / 100.0,
  }


def _parse_gimp_curves_preset(data):
  # We create empty curve data with a fixed order of channels. When curves are
  # applied as filters, they are appended. A filter using the VALUE channel
  # must be appended after other channels so that we obtain a result identical
  # to the Curves tool in GIMP. Hence, the VALUE channel is created here as the
  # last channel.
  curve_data = {
    channel: CurveData()
    for channel in reversed(_HISTOGRAM_CHANNELS.values())
  }
  trc = None
  current_channel = None
  current_curve_type_str = None

  for line in data:
    if trc is None:
      trc = _get_trc_from_str(_parse_entry(line, 'trc'))

    parsed_channel = _parse_entry(line, 'channel')
    if parsed_channel is not None:
      current_channel = _get_channel_from_str(parsed_channel)

    match = re.match(r'\s*\(curve-type +(.*?)\)+', line)
    if match and current_channel is not None:
      current_curve_type_str = match.group(1)
      if utils_pdb.get_gimp_version() >= (3, 2):
        curve_data[current_channel].curve_type = _get_curve_type_from_str(current_curve_type_str)

    match = re.match(r'\s*\(points +(.*?)\)+', line)
    if match and current_channel is not None:
      points = match.group(1)

      keep_channel_intact = (
        (re.match(r' *0 *', points) or re.match(r' *4 +0 +0 +1 +1 *', points))
        and current_curve_type_str != 'free')

      if not keep_channel_intact:
        curve_data[current_channel].channel = current_channel

    match = re.match(r'\s*\(samples +[0-9]+ +(.*?)\)+', line)
    if match and current_channel in curve_data:
      samples = _parse_samples_or_points(match.group(1))
      if samples is not None:
        curve_data[current_channel].samples = samples

  if trc is None:
    trc = _TRC_TYPES['linear']

  return trc, curve_data


def _parse_entry(line, name):
  match = re.match(r'\s*\(' + re.escape(name) + r' +(.*?)\)+', line)
  if match:
    return match.group(1)
  else:
    return None


def _parse_clamp_value(line, name):
  clamp_value_str = _parse_entry(line, name)
  if clamp_value_str is not None:
    return clamp_value_str.lower() == 'yes'
  else:
    return None


def _get_channel_from_str(channel_str):
  return _HISTOGRAM_CHANNELS.get(channel_str, None)


def _get_curve_type_from_str(curve_type_str):
  return _CURVE_TYPES.get(curve_type_str, None)


def _get_trc_from_str(trc_str):
  return _TRC_TYPES.get(trc_str, None)


def _parse_samples_or_points(str_):
  number_list_str = re.split(r' +', str_)

  try:
    return [float(number) for number in number_list_str if number]
  except ValueError:
    return None


def _parse_photoshop_curves_preset(file):
  # The code is based on: https://gist.github.com/fish2000/5641c3697fa4407fcfd59099575d6938

  version, n_curves = struct.unpack('>HH', file.read(4))

  if version not in [1, 4]:
    raise ValueError('version for the Photoshop curves format (.acv) must be 1 or 4')

  points_per_channel = []
  for i in range(n_curves):
    points_per_channel.append(_read_points(file))

  curve_data = {}
  for channel, points in zip(_HISTOGRAM_CHANNELS.values(), points_per_channel):
    curve_data[channel] = CurveData(channel=channel, points=points)

  return _TRC_TYPES['linear'], curve_data


def _read_points(file):
  curve_points = []
  n_points_in_curve, = struct.unpack('>H', file.read(2))

  for index in range(n_points_in_curve):
    output_value, input_value = struct.unpack('>HH', file.read(4))
    curve_points.append(input_value / 255.0)
    curve_points.append(output_value / 255.0)

  return curve_points


def white_balance(_batcher, layer):
  layer.levels_stretch()


def on_after_add_brightness_contrast_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value == 'brightness_contrast':
    if utils_pdb.get_gimp_version() < (3, 1, 4):
      action['arguments/filter_'].gui.set_visible(False)

  if action['orig_name'].value in ['brightness_contrast', 'levels', 'curves']:
    if utils_pdb.get_gimp_version() < (3, 2):
      action['arguments/apply_non_destructively'].gui.set_visible(False)
      action['arguments/blend_mode'].gui.set_visible(False)
      action['arguments/opacity'].gui.set_visible(False)


_MIN_BRIGHTNESS_CONTRAST_VALUE = -127
_MAX_BRIGHTNESS_CONTRAST_VALUE = 127

_FAILED_TO_READ_DATA_MESSAGE = 'Failed to obtain data from file. File may be corrupt.'

_HISTOGRAM_CHANNELS = {
  'value': Gimp.HistogramChannel.VALUE,
  'red': Gimp.HistogramChannel.RED,
  'green': Gimp.HistogramChannel.GREEN,
  'blue': Gimp.HistogramChannel.BLUE,
  'alpha': Gimp.HistogramChannel.ALPHA,
}

if utils_pdb.get_gimp_version() >= (3, 2):
  _CURVE_TYPES = {
    'smooth': Gimp.CurveType.SMOOTH,
    'free': Gimp.CurveType.FREE,
  }
else:
  _CURVE_TYPES = {
    'smooth': 0,
    'free': 1,
  }

if utils_pdb.get_gimp_version() >= (3, 2):
  _TRC_TYPES = {
    'linear': Gimp.TRCType.LINEAR,
    'non-linear': Gimp.TRCType.NON_LINEAR,
    'perceptual': Gimp.TRCType.PERCEPTUAL,
  }
else:
  _TRC_TYPES = {
    'linear': 0,
    'non-linear': 1,
    'perceptual': 2,
  }

BRIGHTNESS_CONTRAST_DICT = {
  'name': 'brightness_contrast',
  'function': brightness_contrast,
  'display_name': _('Brightness-Contrast'),
  'menu_path': _('Color'),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
    {
      'type': 'int',
      'name': 'brightness',
      'default_value': 0,
      'display_name': _('Brightness'),
      'min_value': _MIN_BRIGHTNESS_CONTRAST_VALUE,
      'max_value': _MAX_BRIGHTNESS_CONTRAST_VALUE,
    },
    {
      'type': 'int',
      'name': 'contrast',
      'default_value': 0,
      'display_name': _('Contrast'),
      'min_value': _MIN_BRIGHTNESS_CONTRAST_VALUE,
      'max_value': _MAX_BRIGHTNESS_CONTRAST_VALUE,
    },
    {
      'type': 'choice',
      'name': 'filter_',
      'default_value': (
        BrightnessContrastFilters.GEGL
        if utils_pdb.get_gimp_version() < (3, 1, 4)
        else BrightnessContrastFilters.GIMP),
      'items': [
        (BrightnessContrastFilters.GEGL, _('GEGL')),
        (BrightnessContrastFilters.GIMP, _('GIMP')),
      ],
      'display_name': _('Filter'),
    },
    {
      'type': 'bool',
      'name': 'apply_non_destructively',
      'default_value': False,
      'display_name': _('Apply non-destructively'),
    },
    {
      'type': 'enum',
      'name': 'blend_mode',
      'enum_type': Gimp.LayerMode,
      'default_value': Gimp.LayerMode.REPLACE,
      'display_name': _('Blend mode'),
    },
    {
      'type': 'double',
      'name': 'opacity',
      'default_value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    },
  ],
}

LEVELS_DICT = {
  'name': 'levels',
  'function': levels,
  'display_name': _('Levels'),
  'menu_path': _('Color'),
  'description': _(
    'Applies levels using a preset file saved in GIMP or Photoshop (.alv file).'
    '\n\nTo obtain a preset file in GIMP, go to Colors → Levels and export the settings.'
  ),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
    {
      'type': 'file',
      'name': 'preset_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Preset file'),
      'none_ok': True,
    },
    {
      'type': 'bool',
      'name': 'apply_non_destructively',
      'default_value': False,
      'display_name': _('Apply non-destructively'),
    },
    {
      'type': 'enum',
      'name': 'blend_mode',
      'enum_type': Gimp.LayerMode,
      'default_value': Gimp.LayerMode.REPLACE,
      'display_name': _('Blend mode'),
    },
    {
      'type': 'double',
      'name': 'opacity',
      'default_value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    },
  ],
}

CURVES_DICT = {
  'name': 'curves',
  'function': curves,
  'display_name': _('Curves'),
  'menu_path': _('Color'),
  'description': _(
    'Applies curves using a preset file saved in GIMP or Photoshop (.acv file).'
    '\n\nTo obtain a preset file in GIMP, go to Colors → Curves and export the settings.'
  ),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
    {
      'type': 'file',
      'name': 'preset_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Preset file'),
      'none_ok': True,
    },
    {
      'type': 'bool',
      'name': 'apply_non_destructively',
      'default_value': False,
      'display_name': _('Apply non-destructively'),
    },
    {
      'type': 'enum',
      'name': 'blend_mode',
      'enum_type': Gimp.LayerMode,
      'default_value': Gimp.LayerMode.REPLACE,
      'display_name': _('Blend mode'),
    },
    {
      'type': 'double',
      'name': 'opacity',
      'default_value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    },
  ],
}

WHITE_BALANCE_DICT = {
  'name': 'white_balance',
  'function': white_balance,
  'display_name': _('White Balance'),
  'menu_path': _('Color'),
  'display_options_on_create': False,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
  ],
}
