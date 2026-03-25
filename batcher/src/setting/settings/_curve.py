from __future__ import annotations

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import utils_pdb

from .. import meta as meta_
from . import _base

_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = []

if utils_pdb.get_gimp_version() >= (3, 2):
  __all__.extend([
    'CurveSetting',
  ])


if utils_pdb.get_gimp_version() >= (3, 2):
  class CurveSetting(_base.Setting):
    """Class for settings holding `Gimp.Curve` instances.

    Allowed GIMP PDB types:
    * `Gimp.Curve`

    Default value:
      A `Gimp.Curve` instance containing (0, 0) and (1.0, 1.0) points.

    Message IDs for invalid values:
    * ``'invalid_value'``: The value is not a `Gimp.Curve` instance.
    """

    # According to the GIMP API documentation
    NUM_MINIMUM_SAMPLES = 256

    _ALLOWED_PDB_TYPES = [Gimp.Curve]

    _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.curve_editor]

    # Create default value dynamically to avoid potential errors on GIMP startup.
    _DEFAULT_DEFAULT_VALUE = lambda self: self._create_default_curve()

    def _copy_value(self, value):
      return value

    def _raw_to_value(self, raw_value):
      if isinstance(raw_value, dict):
        curve = Gimp.Curve.new()

        try:
          curve.set_curve_type(Gimp.CurveType(raw_value['type']))
        except Exception:
          return self._create_default_curve()

        if 'points' in raw_value and isinstance(raw_value['points'], (list, tuple)):
          for point_data in raw_value['points']:
            if len(point_data) >= 3:
              x, y, point_type = point_data[:3]
            else:
              continue

            point = curve.add_point(x, y)
            curve.set_point_type(point, Gimp.CurvePointType(point_type))
        elif 'samples' in raw_value and isinstance(raw_value['samples'], (list, tuple)):
          num_samples = len(raw_value['samples'])

          if num_samples >= self.NUM_MINIMUM_SAMPLES:
            curve.set_n_samples(num_samples)

          max_x = num_samples - 1
          for index, y in enumerate(raw_value['samples']):
            curve.set_sample(index / max_x, y)

        return curve

      return raw_value

    def _value_to_raw(self, value):
      curve_type = value.get_curve_type()

      raw_value = {
        'type': int(value.get_curve_type()),
      }

      if curve_type == Gimp.CurveType.SMOOTH:
        raw_value['points'] = [
          [*value.get_point(point), int(value.get_point_type(point))]
          for point in range(value.get_n_points())
        ]
      else:
        num_samples = value.get_n_samples()
        max_x = num_samples - 1

        raw_value['samples'] = [value.get_sample(index / max_x) for index in range(num_samples)]

      return raw_value

    def _validate(self, curve):
      if not isinstance(curve, Gimp.Curve):
        return 'invalid curve', 'invalid_value'

    @classmethod
    def _create_default_curve(cls):
      curve = Gimp.Curve.new()
      curve.set_curve_type(Gimp.CurveType.SMOOTH)

      curve.add_point(0.0, 0.0)
      curve.add_point(1.0, 1.0)

      return curve
