"""Built-in "Color correction" action."""

import re
import struct

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import constants
from src.procedure_groups import *
from src.pypdb import pdb


__all__ = [
  'color_correction',
]


def color_correction(
      _batcher,
      layer,
      brightness,
      contrast,
      levels_preset_file,
      curves_preset_file,
):
  pdb.gegl__brightness_contrast(layer, contrast=contrast, brightness=brightness, merge_filter_=True)

  image = layer.get_image()

  if (image.get_base_type() == Gimp.ImageBaseType.INDEXED
      and levels_preset_file is not None and levels_preset_file.get_path() is not None):
    raise ValueError('Levels cannot be applied to indexed images')

  _apply_correction(
    layer,
    levels_preset_file,
    _parse_gimp_levels_preset,
    _parse_photoshop_levels_preset,
    _apply_levels,
  )

  _apply_correction(
    layer,
    curves_preset_file,
    _parse_gimp_curves_preset,
    _parse_photoshop_curves_preset,
    _apply_curves,
  )


def _apply_correction(
      layer,
      preset_file,
      _parse_gimp_preset,
      _parse_photoshop_preset,
      _apply_func,
):
  if preset_file is None or preset_file.get_path() is None:
    return

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

  if trc is not None and curve_data is not None:
    _apply_func(layer, trc, curve_data)


def _apply_levels(layer, _trc, levels_data):
  for levels_data_for_channel in levels_data.values():
    if not levels_data_for_channel.has_default_values():
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


def _apply_curves(layer, _trc, curve_data):
  for curve_data_for_channel in curve_data.values():
    if curve_data_for_channel.samples is not None:
      layer.curves_explicit(curve_data_for_channel.channel, curve_data_for_channel.samples)
    elif curve_data_for_channel.points is not None:
      layer.curves_spline(curve_data_for_channel.channel, curve_data_for_channel.points)
    else:
      raise ValueError('failed to obtain curve points from file')


def _parse_gimp_levels_preset(data):
  trc = None
  clamp_input = None
  clamp_output = None

  levels_data = {}
  current_channel = None

  for line in data:
    if trc is None:
      trc = _parse_entry(line, 'trc')

    if clamp_input is None:
      clamp_input = _parse_clamp_value(line, 'clamp-input')

    if clamp_output is None:
      clamp_output = _parse_clamp_value(line, 'clamp-output')

    parsed_channel = _parse_entry(line, 'channel')
    if parsed_channel is not None:
      current_channel = _get_channel_from_str(parsed_channel)
      levels_data[current_channel] = LevelsData(
        channel=current_channel,
        clamp_input=clamp_input,
        clamp_output=clamp_output,
      )

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

  trc = 'non-linear'

  return trc, levels_data


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
  trc = None
  curve_data = {}
  current_channel = None

  for line in data:
    if trc is None:
      trc = _parse_entry(line, 'trc')

    parsed_channel = _parse_entry(line, 'channel')
    if parsed_channel is not None:
      current_channel = _get_channel_from_str(parsed_channel)

    match = re.match(r'\s*\(points +(.*?)\)+', line)
    if match and current_channel is not None:
      points = match.group(1)
      keep_channel_intact = re.match(r' *0 *', points) or re.match(r' *4 +0 +0 +1 +1 *', points)
      if not keep_channel_intact:
        curve_data[current_channel] = CurveData(channel=current_channel)

    match = re.match(r'\s*\(samples +[0-9]+ +(.*?)\)+', line)
    if match and current_channel in curve_data:
      samples = _parse_samples(match.group(1))
      if samples is not None:
        curve_data[current_channel].samples = samples

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


def _parse_samples(samples_str):
  sample_list_str = re.split(r' +', samples_str)

  try:
    return [float(sample) for sample in sample_list_str if sample]
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

  trc = 'non-linear'

  return trc, curve_data


def _read_points(file):
  curve_points = []
  n_points_in_curve, = struct.unpack('>H', file.read(2))

  for index in range(n_points_in_curve):
    output_value, input_value = struct.unpack('>HH', file.read(4))
    curve_points.append(input_value / 255.0)
    curve_points.append(output_value / 255.0)

  return curve_points


class CurveData:

  def __init__(self, channel=None, samples=None, points=None):
    self.channel = channel
    self.samples = samples
    self.points = points


class LevelsData:

  def __init__(
        self,
        channel,
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


_FAILED_TO_READ_DATA_MESSAGE = 'Failed to obtain data from file. File may be corrupt.'


_HISTOGRAM_CHANNELS = {
  'value': Gimp.HistogramChannel.VALUE,
  'red': Gimp.HistogramChannel.RED,
  'green': Gimp.HistogramChannel.GREEN,
  'blue': Gimp.HistogramChannel.BLUE,
  'alpha': Gimp.HistogramChannel.ALPHA,
}


COLOR_CORRECTION_DICT = {
  'name': 'color_correction',
  'function': color_correction,
  'display_name': _('Color correction'),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer',
      'name': 'layer',
      'display_name': _('Layer'),
    },
    {
      'type': 'double',
      'name': 'brightness',
      'default_value': 0.0,
      'display_name': _('Brightness'),
      'min_value': -3.0,
      'max_value': 3.0,
      'gui_type_kwargs': {
        'step_increment': 0.01,
      },
    },
    {
      'type': 'double',
      'name': 'contrast',
      'default_value': 1.0,
      'display_name': _('Contrast'),
      'min_value': -5.0,
      'max_value': 5.0,
      'gui_type_kwargs': {
        'step_increment': 0.01,
      },
    },
    {
      'type': 'file',
      'name': 'levels_preset_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Levels (preset file)'),
      'none_ok': True,
    },
    {
      'type': 'file',
      'name': 'curves_preset_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Curves (preset file)'),
      'none_ok': True,
    },
  ],
}
