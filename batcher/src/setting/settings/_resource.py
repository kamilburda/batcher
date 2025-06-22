from __future__ import annotations

from typing import Union, Type

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from .. import meta as meta_
from . import _base


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'GimpResourceSetting',
  'BrushSetting',
  'FontSetting',
  'GradientSetting',
  'PaletteSetting',
  'PatternSetting',
]


class GimpResourceSetting(_base.Setting):
  """Abstract class for settings storing `Gimp.Resource` instances (brushes,
  fonts, etc.).

  Default value:
    If ``default_to_context`` is ``False``, the default value is ``None``.
    If ``default_to_context`` is ``True``, it is the currently active resource
    obtainable via `Gimp.context_get_<resource_type>()`.

  Message IDs for invalid values:
  * ``'invalid_value'``: The resource is not valid.
  """

  _ABSTRACT = True

  _DEFAULT_DEFAULT_VALUE = None

  def __init__(
        self,
        name: str,
        resource_type: Union[GObject.GType, Type[GObject.GObject]],
        none_ok: bool = True,
        default_to_context: bool = True,
        **kwargs,
  ):
    self._resource_type = resource_type
    self._none_ok = none_ok
    self._default_to_context = default_to_context

    if not self._none_ok or self._default_to_context:
      kwargs['default_value'] = self._get_default_value_from_gimp_context()

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  @property
  def default_to_context(self):
    """If ``True``, `the default setting value is inferred from the GIMP
    context (the currently active resource) and the ``default_value`` parameter
    in `__init__()` is ignored.
    """
    return self._default_to_context

  def _get_default_value_from_gimp_context(self):
    return None

  def _raw_to_value(self, raw_value):
    if isinstance(raw_value, dict):
      raw_value_copy = dict(raw_value)

      name = raw_value_copy.pop('name', None)

      if name is None:
        return None

      resource = self._resource_type.get_by_name(name)

      if resource is None:
        return None

      for key, value in raw_value_copy.items():
        set_property_func = getattr(resource, f'set_{key}', None)
        if set_property_func is not None:
          set_property_func(value)

      return resource
    else:
      return raw_value

  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
      }
    else:
      return None

  def _validate(self, resource):
    if not self._none_ok and resource is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if resource is not None and not resource.is_valid():
      return 'invalid resource', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      self._default_value,
      self._default_to_context,
      GObject.ParamFlags.READWRITE,
    ]


class BrushSetting(GimpResourceSetting):
  """Class for settings storing brushes.

  Allowed GIMP PDB types:
  * `Gimp.Brush`

  Default value: ``None``
  """

  _ALLOWED_PDB_TYPES = [Gimp.Brush]

  _REGISTRABLE_TYPE_NAME = 'brush'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.brush_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Brush, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_brush()

  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
        'angle': resource.get_angle().angle,
        'aspect_ratio': resource.get_aspect_ratio().aspect_ratio,
        'hardness': resource.get_hardness().hardness,
        'radius': resource.get_radius().radius,
        'shape': int(resource.get_shape().shape),
        'spacing': resource.get_spacing(),
        'spikes': resource.get_spikes().spikes,
      }
    else:
      return None


class FontSetting(GimpResourceSetting):
  """Class for settings storing fonts.

  Allowed GIMP PDB types:
  * `Gimp.Font`

  Default value: ``None``
  """

  _ALLOWED_PDB_TYPES = [Gimp.Font]

  _REGISTRABLE_TYPE_NAME = 'font'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.font_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Font, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_font()


class GradientSetting(GimpResourceSetting):
  """Class for settings storing gradients.

  Allowed GIMP PDB types:
  * `Gimp.Gradient`

  Default value: ``None``
  """

  _ALLOWED_PDB_TYPES = [Gimp.Gradient]

  _REGISTRABLE_TYPE_NAME = 'gradient'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.gradient_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Gradient, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_gradient()


class PaletteSetting(GimpResourceSetting):
  """Class for settings storing color palettes.

  Allowed GIMP PDB types:
  * `Gimp.Palette`

  Default value: ``None``
  """

  _ALLOWED_PDB_TYPES = [Gimp.Palette]

  _REGISTRABLE_TYPE_NAME = 'palette'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.palette_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Palette, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_palette()

  def _value_to_raw(self, resource):
    if resource is not None:
      return {
        'name': resource.get_name(),
        'columns': resource.get_columns(),
      }
    else:
      return None


class PatternSetting(GimpResourceSetting):
  """Class for settings storing patterns.

  Allowed GIMP PDB types:
  * `Gimp.Pattern`

  Default value: ``None``
  """

  _ALLOWED_PDB_TYPES = [Gimp.Pattern]

  _REGISTRABLE_TYPE_NAME = 'pattern'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.pattern_chooser]

  def __init__(self, name, **kwargs):
    super().__init__(name, Gimp.Pattern, **kwargs)

  def _get_default_value_from_gimp_context(self):
    return Gimp.context_get_pattern()
