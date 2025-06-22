from __future__ import annotations

from typing import Any, Dict, Optional, Union, Tuple, Type

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

from .. import meta as meta_
from . import _array as _array_
from . import _base
from . import _choice as _choice_
from . import _color as _color_
from . import _display as _display_
from . import _enum as _enum_
from . import _file as _file_
from . import _gimp_objects as _gimp_objects_
from . import _numeric as _numeric_
from . import _string as _string_
from . import _unit as _unit_

from src import pypdb


_SETTING_TYPES = meta_.SETTING_TYPES
_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'get_setting_type_and_kwargs',
  'get_array_setting_type_from_gimp_core_object_array',
  'array_as_pdb_compatible_type',
]


def get_setting_type_and_kwargs(
      gtype: GObject.GType,
      pdb_param_info: Optional[GObject.ParamSpec] = None,
      pdb_procedure: Optional[pypdb.PDBProcedure] = None,
) -> Union[Tuple[Type[_base.Setting], Dict[str, Any]], None]:
  """Given a GIMP PDB parameter type, returns the corresponding `Setting`
  subclass and keyword arguments passable to its ``__init__()`` method.

  Some of the keyword arguments passable may be positional arguments, such as
  ``enum_type`` for `EnumSetting`.

  If ``gtype`` does not match any `setting.Setting` subclass, ``None`` is
  returned.

  Args:
    gtype:
      `GObject.GType` instance representing a GIMP PDB parameter.
    pdb_param_info:
      Object representing PDB parameter information, obtainable via
      `pypdb.PDBProcedure.arguments`. This is used to infer additional arguments
      passed to the `__init__()` method of the corresponding `Setting` subclass,
      such as the element type of object array arguments (images, layers, etc.),
      or the list of choices for `ChoiceSetting`.
    pdb_procedure:
      If not ``None``, it is a `pypdb.PDBProcedure` instance used to infer
      additional arguments passed to the `__init__()` method of the
      corresponding `Setting` subclass, in particular for the `EnumSetting`
      subclass.

  Returns:
    Tuple of (`setting.Setting` subclass, dictionary of keyword arguments to be
    passed to ``__init__()`` for the returned `setting.Setting` subclass), or
    ``None`` if there is no matching `setting.Setting` subclass for ``gtype``.
  """
  if gtype in meta_.GTYPES_AND_SETTING_TYPES:
    if pdb_param_info is not None:
      if pdb_param_info.__gtype__ == Gimp.ParamChoice.__gtype__:
        return (
          _choice_.ChoiceSetting,
          _get_choice_setting_init_arguments(pdb_param_info, pdb_procedure))
      elif gtype == Gio.File.__gtype__:
        if pdb_param_info.__gtype__ == Gimp.ParamFile.__gtype__:
          file_action = _get_param_spec_attribute(
            Gimp.param_spec_file_get_action, pdb_param_info, Gimp.FileChooserAction.ANY)
          file_none_ok = _get_param_spec_attribute(
            Gimp.param_spec_file_none_allowed, pdb_param_info, True)
        else:
          file_action = Gimp.FileChooserAction.ANY
          file_none_ok = True

        return (
          _file_.FileSetting,
          dict(
            action=file_action,
            none_ok=file_none_ok))
      elif gtype == Gimp.Image.__gtype__:
        return (
          _gimp_objects_.ImageSetting,
          dict(none_ok=_get_param_spec_attribute(
            Gimp.param_spec_image_none_allowed, pdb_param_info, True)))
      elif gtype in [
            Gimp.Item.__gtype__,
            Gimp.Drawable.__gtype__,
            Gimp.Layer.__gtype__,
            Gimp.GroupLayer.__gtype__,
            Gimp.TextLayer.__gtype__,
            Gimp.Channel.__gtype__,
            Gimp.LayerMask.__gtype__,
            Gimp.Selection.__gtype__,
            Gimp.Path.__gtype__]:
        return (
          _get_setting_type_from_mapping(gtype),
          dict(none_ok=_get_param_spec_attribute(
            Gimp.param_spec_item_none_allowed, pdb_param_info, True)))
      elif gtype == Gimp.DrawableFilter.__gtype__:
        return (
          _gimp_objects_.DrawableFilterSetting,
          dict(none_ok=_get_param_spec_attribute(
            Gimp.param_spec_drawable_filter_none_allowed, pdb_param_info, True)))
      elif gtype == Gimp.Display.__gtype__:
        return (
          _display_.DisplaySetting,
          dict(none_ok=_get_param_spec_attribute(
            Gimp.param_spec_display_none_allowed, pdb_param_info, True)))
      elif gtype == Gegl.Color.__gtype__:
        if pdb_param_info.__gtype__ == Gimp.ParamColor.__gtype__:
          color_has_alpha = _get_param_spec_attribute(
            Gimp.param_spec_color_has_alpha, pdb_param_info, True)
        else:
          color_has_alpha = True

        return (
          _color_.ColorSetting,
          dict(has_alpha=color_has_alpha))
      elif gtype.parent == Gimp.Resource.__gtype__:
        return (
          _get_setting_type_from_mapping(gtype),
          dict(
            none_ok=_get_param_spec_attribute(
              Gimp.param_spec_resource_none_allowed, pdb_param_info, True),
            default_to_context=_get_param_spec_attribute(
              Gimp.param_spec_resource_defaults_to_context, pdb_param_info, True)))
      elif gtype == Gimp.Unit.__gtype__:
        return (
          _unit_.UnitSetting,
          dict(
            show_pixels=_get_param_spec_attribute(
              Gimp.param_spec_unit_pixel_allowed, pdb_param_info, True),
            show_percent=_get_param_spec_attribute(
              Gimp.param_spec_unit_percent_allowed, pdb_param_info, True)))

    # Explicitly pass `gtype` as a `pdb_type` so that e.g. an `IntSetting`
    # instance can have its minimum and maximum values properly adjusted.
    return _get_setting_type_from_mapping(gtype), dict(pdb_type=gtype)
  elif hasattr(gtype, 'parent') and gtype.parent == GObject.GEnum.__gtype__:
    if pdb_procedure is not None and pdb_param_info is not None:
      return _enum_.EnumSetting, dict(enum_type=(pdb_procedure, pdb_param_info))
    else:
      return _enum_.EnumSetting, dict(enum_type=gtype)
  elif gtype in _ARRAY_GTYPES_TO_SETTING_TYPES:
    return _ARRAY_GTYPES_TO_SETTING_TYPES[gtype]
  elif (hasattr(gtype, 'name')
        and gtype.name == 'GimpCoreObjectArray'
        and pdb_param_info is not None):
    return get_array_setting_type_from_gimp_core_object_array(pdb_param_info)
  else:
    return None


def _get_param_spec_attribute(func, param_spec, default_value):
  """This is a compatibility wrapper for PyGObject < 3.50.0 where calls to
  ``Gimp.param_spec_*`` functions fail.

  The default value should not limit the choices of the parameter. For example,
  if the function is `Gimp.param_spec_item_none_allowed`, it should return
  ``True`` on failure even if the parameter does not support ``None`` as a valid
  value. The rationale is that there is no other way to determine whether the
  value is allowed or not, and we need to present the user with all options,
  even if some of them will not always be applicable.
  """
  try:
    return func(param_spec)
  except TypeError:
    return default_value


def _get_choice_setting_init_arguments(param_spec, procedure):
  try:
    choice = Gimp.param_spec_choice_get_choice(param_spec)
  except TypeError:
    return dict(
      items=None,
      procedure=procedure,
      gui_type='prop_choice_combo_box',
    )
  else:
    return dict(
      default_value=Gimp.param_spec_choice_get_default(param_spec),
      items=choice)


def get_array_setting_type_from_gimp_core_object_array(
      pdb_param_info: GObject.ParamSpec,
) -> Union[Tuple[Type[_array_.ArraySetting], Dict[str, Any]], None]:
  try:
    array_element_gtype = Gimp.param_spec_core_object_array_get_object_type(pdb_param_info)
  except TypeError:
    return _infer_array_setting_element_type_from_name(pdb_param_info.name)
  else:
    if array_element_gtype in meta_.GTYPES_AND_SETTING_TYPES:
      return _array_.ArraySetting, dict(element_type=_get_setting_type_from_mapping(array_element_gtype))
    else:
      return None


def _infer_array_setting_element_type_from_name(name):
  if name == 'images':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.ImageSetting)
  elif name == 'drawables':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.DrawableSetting)
  elif name == 'layers':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.LayerSetting)
  elif name == 'channels':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.ChannelSetting)
  elif name == 'paths':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.PathSetting)
  elif name == 'children':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.ItemSetting)
  elif name == 'filters':
    return _array_.ArraySetting, dict(element_type=_gimp_objects_.DrawableFilterSetting)
  else:
    return None


def _get_setting_type_from_mapping(gtype):
  # If multiple `GType`s map to the same `Setting` subclass, use the
  # `Setting` subclass registered (i.e. declared) the earliest.
  return meta_.GTYPES_AND_SETTING_TYPES[gtype][0]


def array_as_pdb_compatible_type(
      values: Tuple[Any, ...],
      element_setting_type: Optional[Type[_base.Setting]] = None,
) -> Union[Tuple[Any, ...], Gimp.Int32Array, Gimp.DoubleArray]:
  """Returns an array suitable to be passed to a GIMP PDB procedure."""
  if element_setting_type == _numeric_.IntSetting:
    array = GObject.Value(Gimp.Int32Array)
    Gimp.value_set_int32_array(array, values)
    return array.get_boxed()
  elif element_setting_type == _numeric_.DoubleSetting:
    array = GObject.Value(Gimp.DoubleArray)
    Gimp.value_set_double_array(array, values)
    return array.get_boxed()
  else:
    return values


_ARRAY_GTYPES_TO_SETTING_TYPES = {
  Gimp.Int32Array.__gtype__: (_array_.ArraySetting, dict(element_type=_numeric_.IntSetting)),
  Gimp.DoubleArray.__gtype__: (_array_.ArraySetting, dict(element_type=_numeric_.DoubleSetting)),
  GObject.TYPE_STRV: (_array_.ArraySetting, dict(element_type=_string_.StringSetting)),
}
