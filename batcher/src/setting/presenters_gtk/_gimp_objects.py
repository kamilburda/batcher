import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from src.gui import widgets as gui_widgets_
from src.pypdb import pdb

from . import _base
from . import _enum_choice


__all__ = [
  'GimpObjectComboBoxPresenter',
  'ImageComboBoxPresenter',
  'ItemComboBoxPresenter',
  'DrawableComboBoxPresenter',
  'LayerComboBoxPresenter',
  'GroupLayerComboBoxPresenter',
  'TextLayerComboBoxPresenter',
  'LayerMaskComboBoxPresenter',
  'ChannelComboBoxPresenter',
  'PathComboBoxPresenter',
  'DrawableFilterComboBoxPresenter',
]


class GimpObjectComboBoxPresenter(_enum_choice.GimpUiIntComboBoxPresenter):
  """Abstract `setting.Presenter` subclass for `GimpUi` combo boxes ued to
  select GIMP objects (images, layers, channels, ...).

  This presenter updates the underlying setting on initialization as these
  `GimpUi` combo boxes are set to a valid value when they are created.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.update_setting_value(force=True)


class ImageComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.ImageComboBox` widgets.

  Value: `Gimp.Image` selected in the combo box, or ``None`` if there is no
  image available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.ImageComboBox.new()

  def get_value(self):
    return Gimp.Image.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Image` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class ItemComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `gui.GimpItemComboBox` widgets.

  Value: `Gimp.Item` selected in the combo box, or ``None`` if there is no
  item available.
  """

  def _connect_value_changed_event(self):
    # This is a custom combo box rather than a `GimpUi` combo box. Therefore,
    # the GTK ``connect`` method is used.
    _base.GtkPresenter._connect_value_changed_event(self)

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.GimpItemComboBox()

  def get_value(self):
    return Gimp.Item.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Item` instance to be selected in the combo box.

    Passing ``None`` or a GIMP object that is not `Gimp.Item` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class DrawableComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.DrawableComboBox` widgets.

  Value: `Gimp.Drawable` selected in the combo box, or ``None`` if there is no
  drawable available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.DrawableComboBox.new()

  def get_value(self):
    return Gimp.Drawable.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Drawable` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class LayerComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.LayerComboBox` widgets.

  Value: `Gimp.Layer` selected in the combo box, or ``None`` if there is no
  layer available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.LayerComboBox.new()

  def get_value(self):
    return Gimp.Layer.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Layer` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class GroupLayerComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.LayerComboBox` widgets, limiting
  the choices to `Gimp.GroupLayer` instances.

  Value: `Gimp.GroupLayer` selected in the combo box, or ``None`` if there is no
  group layer available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.LayerComboBox.new(lambda image, item: item.is_group_layer())

  def get_value(self):
    return Gimp.GroupLayer.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.GroupLayer` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class TextLayerComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.LayerComboBox` widgets, limiting
  the choices to `Gimp.TextLayer` instances.

  Value: `Gimp.TextLayer` selected in the combo box, or ``None`` if there is no
  text layer available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.LayerComboBox.new(lambda image, item: item.is_text_layer())

  def get_value(self):
    return Gimp.TextLayer.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.TextLayer` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class LayerMaskComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.LayerComboBox` widgets, limiting
  the choices to `Gimp.Layer` instances having a layer mask.

  Value: `Gimp.LayerMask` from a `Gimp.Layer` selected in the combo box, or
  ``None`` if there is no layer with a mask available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.LayerComboBox.new(
      lambda image, item: item.is_layer() and item.get_mask() is not None)

  def get_value(self):
    layer = Gimp.Layer.get_by_id(self._widget.get_active().value)

    if layer is not None:
      return layer.get_mask()
    else:
      return None

  def _set_value(self, value):
    """Sets a `Gimp.Layer` instance having the specified `Gimp.LayerMask` to be
    selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None and value.is_layer_mask():
      layer = pdb.gimp_layer_from_mask(value)
      if layer is not None:
        self._widget.set_active(layer.get_id())


class ChannelComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.ChannelComboBox` widgets.

  Value: `Gimp.Channel` selected in the combo box, or ``None`` if there is no
  channel available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.ChannelComboBox.new()

  def get_value(self):
    return Gimp.Channel.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Channel` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class PathComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.PathComboBox` widgets.

  Value: `Gimp.Path` selected in the combo box, or ``None`` if there is no
  path available.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.PathComboBox.new()

  def get_value(self):
    return Gimp.Path.get_by_id(self._widget.get_active().value)

  def _set_value(self, value):
    """Sets a `Gimp.Path` instance to be selected in the combo box.

    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class DrawableFilterComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `gui.DrawableFilterComboBox` widgets.

  Value: `Gimp.DrawableFilter` selected in the combo box, or ``None`` if there
  is no drawable filter available.
  """

  def _connect_value_changed_event(self):
    # This is a custom combo box rather than a `GimpUi` combo box. Therefore,
    # the GTK ``connect`` method is used.
    _base.GtkPresenter._connect_value_changed_event(self)

  def _create_widget(self, setting, **kwargs):
    return gui_widgets_.GimpDrawableFilterComboBox()

  def get_value(self):
    self._setting.drawable = self._widget.get_active_drawable()

    return Gimp.DrawableFilter.get_by_id(self._widget.get_active())

  def _set_value(self, value):
    """Sets a `Gimp.DrawableFilter` instance to be selected in the combo box.

    Passing ``None`` or an ID that does not correspond to any
    `Gimp.DrawableFilter` object has no effect.
    """
    if value is not None and self._setting.drawable is not None:
      self._widget.set_active_drawable(self._setting.drawable)
      self._widget.set_active(value.get_id())
