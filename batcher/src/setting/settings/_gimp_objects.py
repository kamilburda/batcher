from __future__ import annotations

from collections.abc import Iterable

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from .. import meta as meta_
from . import _base

from src import utils_pdb


_SETTING_GUI_TYPES = meta_.SETTING_GUI_TYPES

__all__ = [
  'ImageSetting',
  'GimpItemSetting',
  'ItemSetting',
  'DrawableSetting',
  'LayerSetting',
  'GroupLayerSetting',
  'TextLayerSetting',
  'LayerMaskSetting',
  'ChannelSetting',
  'SelectionSetting',
  'PathSetting',
  'DrawableFilterSetting',
]


class ImageSetting(_base.Setting):
  """Class for settings holding `Gimp.Image` objects.

  This class accepts as a value a file path to the image or image ID.
  If calling `to_dict()`, the image file path is returned or ``None`` if the
  image does not exist in the file system.

  Allowed GIMP PDB types:
  * `Gimp.Image`

  Message IDs for invalid values:
  * ``'invalid_value'``: The image assigned is invalid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Image]

  _REGISTRABLE_TYPE_NAME = 'image'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.image_combo_box]

  def __init__(
        self,
        name: str,
        none_ok: bool = True,
        **kwargs,
  ):
    self._none_ok = none_ok

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  def _copy_value(self, value):
    return value

  def _raw_to_value(self, raw_value):
    value = raw_value

    if isinstance(raw_value, int):
      value = Gimp.Image.get_by_id(raw_value)
    elif isinstance(raw_value, str):
      value = utils_pdb.find_image_by_filepath(raw_value)

    return value

  def _value_to_raw(self, value):
    if value is not None and value.get_file() is not None:
      raw_value = value.get_file().get_path()
    else:
      raw_value = None

    return raw_value

  def _validate(self, image):
    if not self._none_ok and image is None:
      return 'None is not allowed for this setting', 'invalid_value'

    if image is not None and not image.is_valid():
      return 'invalid image', 'invalid_value'

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      GObject.ParamFlags.READWRITE,
    ]


class GimpItemSetting(_base.Setting):
  """Abstract class for settings storing GIMP items - layers, channels, paths.

  This class accepts as a value one of the following:
  * a tuple (item type, item path components, image file path) where item
    type is the name of the item's GIMP class (e.g. ``'Layer'``).
  * a tuple (item type, item ID). Item ID is are assigned by GIMP.
  * a `Gimp.Item` instance.

  If calling `to_dict()`, a tuple (item path components, item type,
  image file path) is returned.
  """

  _ABSTRACT = True

  def __init__(
        self,
        name: str,
        none_ok: bool = True,
        **kwargs,
  ):
    self._none_ok = none_ok

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  def _raw_to_value(self, raw_value):
    value = raw_value

    if isinstance(raw_value, list):
      if len(raw_value) == 3:
        value = self._get_item_from_image_and_item_path(*raw_value)
      else:
        raise ValueError(
          ('lists as values for GIMP item settings must contain'
           f' exactly 3 elements (has {len(raw_value)})'))
    elif isinstance(raw_value, int):
      value = Gimp.Item.get_by_id(raw_value)

    return value

  def _value_to_raw(self, value):
    return self._item_to_path(value)

  def _get_item_from_image_and_item_path(
        self, item_type_name, item_path_components, image_filepath):
    image = utils_pdb.find_image_by_filepath(image_filepath)

    if image is None:
      return None

    return utils_pdb.get_item_from_image_and_item_path(item_type_name, item_path_components, image)

  def _item_to_path(self, item):
    return utils_pdb.get_item_as_path(item)

  def _get_pdb_param(self):
    return [
      self._REGISTRABLE_TYPE_NAME,
      self._pdb_name,
      self._display_name,
      self._description,
      self._none_ok,
      GObject.ParamFlags.READWRITE,
    ]


class ItemSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Item` instances.

  Allowed GIMP PDB types:
  * `Gimp.Item`

  Message IDs for invalid values:
  * ``'invalid_value'``: The item assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Item]

  _REGISTRABLE_TYPE_NAME = 'item'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.item_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, item):
    if item is not None and not isinstance(item, Gimp.Item):
      return 'invalid item', 'invalid_value'


class DrawableSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Drawable` instances.

  Allowed GIMP PDB types:
  * `Gimp.Drawable`

  Message IDs for invalid values:
  * ``'invalid_value'``: The drawable assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Drawable]

  _REGISTRABLE_TYPE_NAME = 'drawable'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.drawable_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, drawable):
    if drawable is not None and not drawable.is_drawable():
      return 'invalid drawable', 'invalid_value'


class LayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Layer` instances.

  Allowed GIMP PDB types:
  * `Gimp.Layer`

  Message IDs for invalid values:
  * ``'invalid_value'``: The layer assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Layer]

  _REGISTRABLE_TYPE_NAME = 'layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.layer_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, layer):
    if layer is not None and not layer.is_layer():
      return 'invalid layer', 'invalid_value'


class GroupLayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.GroupLayer` instances.

  Allowed GIMP PDB types:
  * `Gimp.GroupLayer`

  Message IDs for invalid values:
  * ``'invalid_value'``: The group layer assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.GroupLayer]

  _REGISTRABLE_TYPE_NAME = 'group_layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.group_layer_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, layer):
    if layer is not None and not layer.is_group_layer():
      return 'invalid group layer', 'invalid_value'


class TextLayerSetting(GimpItemSetting):
  """Class for settings holding `Gimp.TextLayer` instances.

  Allowed GIMP PDB types:
  * `Gimp.TextLayer`

  Message IDs for invalid values:
  * ``'invalid_value'``: The text layer assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.TextLayer]

  _REGISTRABLE_TYPE_NAME = 'text_layer'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.text_layer_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, layer):
    if layer is not None and not layer.is_text_layer():
      return 'invalid text layer', 'invalid_value'


class LayerMaskSetting(GimpItemSetting):
  """Class for settings holding `Gimp.LayerMask` instances.

  When serializing to a source, the setting value as returned by
  `Setting.to_dict()` corresponds to the layer path the layer mask is
  attached to.

  Allowed GIMP PDB types:
  * `Gimp.LayerMask`

  Message IDs for invalid values:
  * ``'invalid_value'``: The layer mask assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.LayerMask]

  _REGISTRABLE_TYPE_NAME = 'layer_mask'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.layer_mask_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, drawable):
    if drawable is not None and not drawable.is_layer_mask():
      return 'invalid layer mask', 'invalid_value'

  def _get_item_from_image_and_item_path(
        self, item_type_name, item_path_components, image_filepath):
    layer = super()._get_item_from_image_and_item_path(
      item_type_name, item_path_components, image_filepath)

    if layer is not None:
      return layer.get_mask()
    else:
      return None

  def _item_to_path(self, item):
    if item is None:
      return None

    layer = Gimp.Layer.from_mask(item)
    if layer is not None:
      return super()._item_to_path(layer)
    else:
      return None


class ChannelSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Channel` instances.

  Allowed GIMP PDB types:
  * `Gimp.Channel`

  Message IDs for invalid values:
  * ``'invalid_value'``: The channel assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Channel]

  _REGISTRABLE_TYPE_NAME = 'channel'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.channel_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, channel):
    if channel is not None and not channel.is_channel():
      return 'invalid channel', 'invalid_value'


class SelectionSetting(ChannelSetting):
  """Class for settings holding the current selection.

  A selection in GIMP is internally represented as a `Gimp.Channel` instance.
  Unlike `ChannelSetting`, this setting does not support GUI (there is no need
  for GUI).

  Allowed GIMP PDB types:
  * `Gimp.Selection`

  Message IDs for invalid values:
  * ``'invalid_value'``: The channel assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Selection]

  _REGISTRABLE_TYPE_NAME = 'selection'

  _ALLOWED_GUI_TYPES = []


class PathSetting(GimpItemSetting):
  """Class for settings holding `Gimp.Path` instances.

  Allowed GIMP PDB types:
  * `Gimp.Path`

  Message IDs for invalid values:
  * ``'invalid_value'``: The path assigned is not valid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.Path]

  _REGISTRABLE_TYPE_NAME = 'path'

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.path_combo_box]

  def _copy_value(self, value):
    return value

  def _validate(self, path):
    if path is not None and not path.is_path():
      return 'invalid path', 'invalid_value'


class DrawableFilterSetting(_base.Setting):
  """Class for settings holding `Gimp.DrawableFilter` objects.

  This class accepts as a value one of the following:
  * a tuple (drawable type, drawable path components, image file path, position
     of the filter in the drawable, filter name) where drawable type is the name
     of the drawable's GIMP class (e.g. ``'Layer'``) holding the filter.
  * an ID (assigned by GIMP) representing a `Gimp.DrawableFilter` instance.
  * a `Gimp.DrawableFilter` instance.

  Allowed GIMP PDB types:
  * `Gimp.DrawableFilter`

  Message IDs for invalid values:
  * ``'invalid_value'``: The drawable filter assigned is invalid.
  """

  _ALLOWED_PDB_TYPES = [Gimp.DrawableFilter]

  _ALLOWED_GUI_TYPES = [_SETTING_GUI_TYPES.drawable_filter_combo_box]

  def __init__(self, name: str, none_ok: bool = True, **kwargs):
    self.drawable = None
    """The drawable holding the filter (the setting value)."""

    self._none_ok = none_ok

    super().__init__(name, **kwargs)

  @property
  def none_ok(self):
    """If ``True``, ``None`` is allowed as a valid value for this setting."""
    return self._none_ok

  def _copy_value(self, value):
    return value

  def _raw_to_value(self, raw_value):
    value = raw_value

    if isinstance(raw_value, int):
      value = Gimp.DrawableFilter.get_by_id(raw_value)
    elif isinstance(raw_value, Iterable):
      self.drawable, value = self._get_drawable_and_drawable_filter_by_path(raw_value)

    return value

  def _value_to_raw(self, value):
    if self.drawable is None:
      return None

    try:
      drawable_filter_order = self.drawable.get_filters().index(value)
    except ValueError:
      return None

    drawable_as_path = utils_pdb.get_item_as_path(self.drawable)

    if drawable_as_path is None:
      return None

    return [*drawable_as_path, drawable_filter_order, value.get_name()]

  def _validate(self, drawable_filter):
    if drawable_filter is not None and not drawable_filter.is_valid():
      return 'invalid drawable filter', 'invalid_value'

  @staticmethod
  def _get_drawable_and_drawable_filter_by_path(path):
    path_list = list(path)

    drawable_type_name, drawable_path_components, image_filepath = path_list[:-2]
    drawable_filter_position = path_list[-2]
    drawable_filter_name = path_list[-1]

    image = utils_pdb.find_image_by_filepath(image_filepath)

    if image is None:
      return None, None

    drawable = utils_pdb.get_item_from_image_and_item_path(
      drawable_type_name, drawable_path_components, image)

    if drawable is None:
      return None, None

    drawable_filters = drawable.get_filters()

    if drawable_filter_position >= len(drawable_filters):
      return None, None

    drawable_filter = drawable_filters[drawable_filter_position]

    if drawable_filter.get_name() != drawable_filter_name:
      return None, None

    return drawable, drawable_filter
