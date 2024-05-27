"""`setting.Presenter` subclasses for GTK GUI widgets."""

import inspect
import math
import sys

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from .. import gui as pggui
from ..pypdb import pdb
from .. import utils as pgutils

from . import presenter as presenter_


class GtkPresenter(presenter_.Presenter):
  """Abstract `setting.Presenter` subclass for GTK GUI widgets."""
  
  _ABSTRACT = True
  
  def __init__(self, *args, **kwargs):
    self._event_handler_id = None
    
    super().__init__(*args, **kwargs)
  
  def get_sensitive(self):
    return self._widget.get_sensitive()
  
  def set_sensitive(self, sensitive):
    self._widget.set_sensitive(sensitive)
  
  def get_visible(self):
    return self._widget.get_visible()
  
  def set_visible(self, visible):
    self._widget.set_visible(visible)
  
  def _connect_value_changed_event(self):
    self._event_handler_id = self._widget.connect(
      self._VALUE_CHANGED_SIGNAL, self._on_value_changed)
  
  def _disconnect_value_changed_event(self):
    self._widget.disconnect(self._event_handler_id)
    self._event_handler_id = None


class IntSpinButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.
  
  Value: Integer value of the spin button.
  """
  
  _VALUE_CHANGED_SIGNAL = 'value-changed'
  
  def _create_widget(self, setting, **kwargs):
    return _create_spin_button(setting, digits=0)
  
  def get_value(self):
    return self._widget.get_value_as_int()
  
  def _set_value(self, value):
    self._widget.set_value(value)


class FloatSpinButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.
  
  Value: Floating point value of the spin button.
  """
  
  _VALUE_CHANGED_SIGNAL = 'value-changed'
  
  def _create_widget(self, setting, digits=None, **kwargs):
    return _create_spin_button(setting, digits=digits)
  
  def get_value(self):
    return self._widget.get_value()
  
  def _set_value(self, value):
    self._widget.set_value(value)


class CheckButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckButton` widgets.
  
  Value: Checked state of the check button (checked/unchecked).
  """
  
  _VALUE_CHANGED_SIGNAL = 'clicked'
  
  def _create_widget(self, setting, **kwargs):
    return Gtk.CheckButton(label=setting.display_name, use_underline=False)
  
  def get_value(self):
    return self._widget.get_active()
  
  def _set_value(self, value):
    self._widget.set_active(value)


class CheckButtonNoTextPresenter(CheckButtonPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckButton` widgets without text
  next to the checkbox.
  
  Value: Checked state of the check button (checked/unchecked).
  """
  
  def _create_widget(self, setting, **kwargs):
    return Gtk.CheckButton(label=None, use_underline=False)


class CheckButtonLabelPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckButton` widgets.
  
  Value: Label of the check button.
  """

  _VALUE_CHANGED_SIGNAL = 'notify::text'
  
  def get_value(self):
    return self._widget.get_child().get_text()
  
  def _set_value(self, value):
    self._widget.get_child().set_text(value if value is not None else '')


class CheckMenuItemPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckMenuItem` widgets.
  
  Value: Checked state of the menu item (checked/unchecked).
  """
  
  _VALUE_CHANGED_SIGNAL = 'toggled'
  
  def _create_widget(self, setting, **kwargs):
    return Gtk.CheckMenuItem(label=setting.display_name)
  
  def get_value(self):
    return self._widget.get_active()
  
  def _set_value(self, value):
    self._widget.set_active(value)


class ExpanderPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Expander` widgets.
  
  Value: ``True`` if the expander is expanded, ``False`` if collapsed.
  """
  
  _VALUE_CHANGED_SIGNAL = 'notify::expanded'
  
  def _create_widget(self, setting, **kwargs):
    return Gtk.Expander(label=setting.display_name, use_underline=True)
  
  def get_value(self):
    return self._widget.get_expanded()
  
  def _set_value(self, value):
    self._widget.set_expanded(value)


class EntryPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Entry` widgets.

  Value: Text in the entry.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    return Gtk.Entry()

  def get_value(self):
    return self._widget.get_text()

  def _set_value(self, value):
    self._widget.set_text(value if value is not None else '')
    # Place the cursor at the end of the text entry.
    self._widget.set_position(-1)


class LabelPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Label` widgets.

  Value: Label text.
  """

  _VALUE_CHANGED_SIGNAL = 'notify::text'

  def _create_widget(
        self,
        setting,
        use_markup=True,
        xalign=0.0,
        yalign=0.5,
        max_width_chars=50,
        ellipsize=Pango.EllipsizeMode.END,
        **kwargs,
  ):
    label = Gtk.Label(
      use_markup=use_markup,
      max_width_chars=max_width_chars,
      xalign=xalign,
      yalign=yalign,
      ellipsize=ellipsize,
      **kwargs,
    )
    label.set_markup(GLib.markup_escape_text(setting.display_name))
    return label

  def get_value(self):
    return self._widget.get_label()

  def _set_value(self, value):
    self._widget.set_markup(value if value is not None else '')


class ComboBoxPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.ComboBox` widgets.

  The combo boxes contain two columns - displayed text and a numeric value
  associated with the text.

  Value: Item selected in the combo box.
  """
  
  _VALUE_CHANGED_SIGNAL = 'changed'
  
  def _create_widget(self, setting, **kwargs):
    model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_INT)

    for label, value in setting.get_item_display_names_and_values():
      model.append((label if label is not None else '', value))

    combo_box = Gtk.ComboBox(model=model, active=setting.default_value)

    renderer_text = Gtk.CellRendererText()
    combo_box.pack_start(renderer_text, True)
    combo_box.add_attribute(renderer_text, 'text', 0)
    
    return combo_box
  
  def get_value(self):
    return self._widget.get_active()
  
  def _set_value(self, value):
    self._widget.set_active(value)


class GimpUiIntComboBoxPresenter(GtkPresenter):
  """Abstract `setting.Presenter` subclass for widget classes inheriting from
  `GimpUi.IntComboBox` .

  These classes have a modified ``connect()`` method with different interface
  and the signal handler being triggered even when setting the initial value,
  which is undesired.
  """

  _ABSTRACT = True

  def _connect_value_changed_event(self):
    self._event_handler_id = Gtk.ComboBox.connect(
      self._widget, self._VALUE_CHANGED_SIGNAL, self._on_value_changed)


class EnumComboBoxPresenter(GimpUiIntComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.EnumComboBox` widgets.

  Value: Item selected in the enum combo box.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    combo_box = GimpUi.EnumComboBox.new_with_model(GimpUi.EnumStore.new(setting.enum_type))

    # If the default value is not valid, `set_active` returns `False`,
    # but otherwise does not result in errors.
    combo_box.set_active(int(setting.default_value))

    return combo_box

  def get_value(self):
    return self._widget.get_active().value

  def _set_value(self, value):
    self._widget.set_active(value)


class GimpObjectComboBoxPresenter(GimpUiIntComboBoxPresenter):
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
    GtkPresenter._connect_value_changed_event(self)
  
  def _create_widget(self, setting, **kwargs):
    return pggui.GimpItemComboBox()
  
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


class VectorsComboBoxPresenter(GimpObjectComboBoxPresenter):
  """`setting.Presenter` subclass for `GimpUi.VectorsComboBox` widgets.
  
  Value: `Gimp.Vectors` selected in the combo box, or ``None`` if there are no
  vectors available.
  """
  
  def _create_widget(self, setting, **kwargs):
    return GimpUi.VectorsComboBox.new()
  
  def get_value(self):
    return Gimp.Vectors.get_by_id(self._widget.get_active().value)
  
  def _set_value(self, value):
    """Sets a `Gimp.Vectors` instance to be selected in the combo box.
    
    Passing ``None`` has no effect.
    """
    if value is not None:
      self._widget.set_active(value.get_id())


class ColorButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `GimpUi.ColorButton` widgets.
  
  Value: `Gegl.Color` instance representing color in RGBA.
  """
  
  _VALUE_CHANGED_SIGNAL = 'color-changed'
  
  def _create_widget(self, setting, width=100, height=20):
    return GimpUi.ColorButton.new(
      setting.display_name, width, height, setting.value, GimpUi.ColorAreaType.SMALL_CHECKS)
  
  def get_value(self):
    return self._widget.get_color()
  
  def _set_value(self, value):
    self._widget.set_color(value)


class RgbButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `GimpUi.ColorButton` widgets.

  Value: `Gimp.RGB` instance representing color in RGBA.
  """

  _VALUE_CHANGED_SIGNAL = 'color-changed'

  def _create_widget(self, setting, width=100, height=20):
    color = Gegl.Color()
    color.set_rgba(setting.value.r, setting.value.g, setting.value.b, setting.value.a)

    return GimpUi.ColorButton.new(
      setting.display_name, width, height, color, GimpUi.ColorAreaType.SMALL_CHECKS)

  def get_value(self):
    color = self._widget.get_color().get_rgba()

    rgb = Gimp.RGB()
    rgb.set(color.red, color.green, color.blue)
    rgb.set_alpha(color.alpha)

    return rgb

  def _set_value(self, value):
    color = Gegl.Color()
    color.set_rgba(value.r, value.g, value.b, value.a)

    self._widget.set_color(color)


class ParasiteBoxPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `gui.ParasiteBox` widgets.
  
  Value: `Gimp.Parasite` instance.
  """
  
  _VALUE_CHANGED_SIGNAL = 'parasite-changed'
  
  def _create_widget(self, setting, **kwargs):
    return pggui.ParasiteBox(setting.value)
  
  def get_value(self):
    return self._widget.get_parasite()
  
  def _set_value(self, value):
    self._widget.set_parasite(value)


class DisplaySpinButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.SpinButton` widgets.
  
  Value: `Gimp.Display` instance, represented by its integer ID in the spin
  button.
  """
  
  _VALUE_CHANGED_SIGNAL = 'value-changed'
  
  def _create_widget(self, setting, **kwargs):
    return Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=setting.value.get_id() if setting.value is not None else 0,
        lower=0,
        upper=GLib.MAXINT,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
    )
  
  def get_value(self):
    return Gimp.Display.get_by_id(self._widget.get_value_as_int())
  
  def _set_value(self, value):
    if value is not None:
      self._widget.set_value(value.get_id())


class GFileEntryPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Entry` widgets used to store file or
  folder paths returning a `Gio.File` instance on output.

  Value: Current file or folder path as a `Gio.File` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    value = setting.value

    widget = Gtk.Entry(
      text=value.get_path() if value is not None and value.get_path() is not None else '')
    widget.set_position(-1)

    return widget

  def get_value(self):
    return Gio.file_new_for_path(self._widget.get_text())

  def _set_value(self, value):
    self._widget.set_text(
      value.get_path() if value is not None and value.get_path() is not None else '')
    # Place the cursor at the end of the text entry.
    self._widget.set_position(-1)


class GBytesEntryPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Entry` widgets used to store raw
  bytes.

  Value: Raw bytes as a `GLib.Bytes` instance.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    widget = Gtk.Entry(text=pgutils.bytes_to_escaped_string(setting.value.get_data()))
    widget.set_position(-1)

    return widget

  def get_value(self):
    return GLib.Bytes.new(
      pgutils.escaped_string_to_bytes(self._widget.get_text(), remove_overflow=True))

  def _set_value(self, value):
    self._widget.set_text(pgutils.bytes_to_escaped_string(value.get_data()))
    # Place the cursor at the end of the text entry.
    self._widget.set_position(-1)


class FolderChooserButtonPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.FileChooserButton` widgets used as
  folder choosers.
  
  Value: Current folder.
  """

  _VALUE_CHANGED_SIGNAL = 'file-set'

  def _create_widget(self, setting, **kwargs):
    button = Gtk.FileChooserButton(
      title=setting.display_name,
      action=Gtk.FileChooserAction.SELECT_FOLDER,
    )

    if setting.value is not None:
      button.set_filename(setting.value)

    return button
  
  def get_value(self):
    folder = self._widget.get_filename()

    if folder is not None:
      return folder
    else:
      return GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
  
  def _set_value(self, dirpath):
    self._widget.set_filename(dirpath if dirpath is not None else '')


class GimpResourceChooserPresenter(GtkPresenter):
  """Abstract `setting.Presenter` subclass for widgets allowing to select and
  modify a `Gimp.Resource` instance via a specialized button.
  """

  _ABSTRACT = True
  
  _VALUE_CHANGED_SIGNAL = 'resource-set'

  def get_value(self):
    return self._widget.get_resource()
  
  def _set_value(self, value):
    if value is not None:
      self._widget.set_resource(value)


class BrushChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.BrushChooser` widgets.

  Value: A `Gimp.Brush` instance.
  """

  def _create_widget(self, setting, **kwargs):
    return GimpUi.BrushChooser.new(setting.display_name, setting.value)


class FontChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.FontChooser` widgets.
  
  Value: A `Gimp.Font` instance.
  """
  
  def _create_widget(self, setting, **kwargs):
    return GimpUi.FontChooser.new(setting.display_name, setting.value)


class GradientChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.GradientChooser` widgets.
  
  Value: A `Gimp.Gradient` instance.
  """
  
  def _create_widget(self, setting, **kwargs):
    return GimpUi.GradientChooser.new(setting.display_name, setting.value)


class PaletteChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.PaletteChooser` widgets.
  
  Value: A `Gimp.Palette` instance.
  """
  
  def _create_widget(self, setting, **kwargs):
    return GimpUi.PaletteChooser.new(setting.display_name, setting.value)


class PatternChooserPresenter(GimpResourceChooserPresenter):
  """`setting.Presenter` subclass for `GimpUi.PatternChooser` widgets.
  
  Value: String representing a pattern.
  """
  
  def _create_widget(self, setting, **kwargs):
    return GimpUi.PatternChooser.new(setting.display_name, setting.value)


class ArrayBoxPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `gui.ArrayBox` widgets.
  
  Value: Tuple of values of type ``element_type`` specified in the
  `setting.ArraySetting` instance.
  """
  
  _VALUE_CHANGED_SIGNAL = 'array-box-changed'
  _ITEM_CHANGED_SIGNAL = 'array-box-item-changed'
  
  def __init__(self, *args, **kwargs):
    self._item_changed_event_handler_id = None
    self._array_elements_with_events = set()
    
    super().__init__(*args, **kwargs)
  
  def update_setting_value(self, force=False):
    super().update_setting_value(force=force)
    
    for array_element in self._setting.get_elements():
      array_element.gui.update_setting_value(force=force)
  
  def _connect_value_changed_event(self):
    super()._connect_value_changed_event()
    
    self._item_changed_event_handler_id = self._widget.connect(
      self._ITEM_CHANGED_SIGNAL, self._on_item_changed)
  
  def _disconnect_value_changed_event(self):
    super()._disconnect_value_changed_event()
    
    self._widget.disconnect(self._item_changed_event_handler_id)
    self._item_changed_event_handler_id = None
  
  def _create_widget(self, setting, **kwargs):
    def _add_existing_element(array_element_value, index):
      return self._add_array_element(setting[index], array_box)
    
    def _add_new_element(array_element_value, index):
      array_element = setting.add_element(value=array_element_value)
      return self._add_array_element(array_element, array_box)
    
    def _reorder_element(orig_position, new_position):
      setting.reorder_element(orig_position, new_position)
    
    def _remove_element(position):
      self._array_elements_with_events.remove(setting[position])
      del setting[position]

    array_box = pggui.ArrayBox(
      setting.element_default_value,
      setting.min_size,
      setting.max_size,
      propagate_natural_width=True,
      propagate_natural_height=True,
      **kwargs,
    )
    
    array_box.on_add_item = _add_existing_element
    
    for element_index in range(len(setting)):
      array_box.add_item(setting[element_index].value, element_index)
    
    array_box.on_add_item = _add_new_element
    array_box.on_reorder_item = _reorder_element
    array_box.on_remove_item = _remove_element
    
    return array_box
  
  def get_value(self):
    return tuple(array_element.value for array_element in self._setting.get_elements())
  
  def _set_value(self, value):
    def _add_existing_element(array_element_value, index):
      return self._add_array_element(self._setting[index], self._widget)
    
    orig_on_add_item = self._widget.on_add_item
    self._widget.on_add_item = _add_existing_element
    
    self._widget.set_values(value)
    
    self._widget.on_add_item = orig_on_add_item
  
  def _on_item_changed(self, *args):
    self._setting_value_synchronizer.apply_gui_value_to_setting(self.get_value())
  
  def _add_array_element(self, array_element, array_box):
    def _on_array_box_item_changed(array_element):
      array_box.emit('array-box-item-changed')
    
    array_element.set_gui()
    
    if array_element not in self._array_elements_with_events:
      array_element.connect_event('value-changed', _on_array_box_item_changed)
      self._array_elements_with_events.add(array_element)
    
    return array_element.gui.widget


class WindowPositionPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Window` widgets to get/set position.
  
  Value: Current position of the window as a tuple of 2 integers.
  """
  
  def get_value(self):
    return self._widget.get_position()
  
  def _set_value(self, value):
    """Sets a new position of the window (i.e. moves the window).
    
    The window is not moved if ``value`` is ``None`` or empty.
    """
    if value:
      self._widget.move(*value)


class WindowSizePresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Window` widgets to get/set size.
  
  Value: Current size of the window as a tuple of 2 integers.
  """
  
  def get_value(self):
    return self._widget.get_size()
  
  def _set_value(self, value):
    """Sets a new size of the window.
    
    The window is not resized if ``value`` is ``None`` or empty.
    """
    if value:
      self._widget.resize(*value)


class PanedPositionPresenter(GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Paned` widgets.
  
  Value: Position of the divider between the two panes.
  """
  
  def get_value(self):
    return self._widget.get_position()
  
  def _set_value(self, value):
    self._widget.set_position(value)


def _create_spin_button(setting, digits=None):
  if hasattr(setting, 'min_value') and setting.min_value is not None:
    min_value = setting.min_value
  elif hasattr(setting, 'pdb_min_value') and setting.pdb_min_value is not None:
    min_value = setting.pdb_min_value
  else:
    min_value = GLib.MININT
  
  if hasattr(setting, 'max_value') and setting.max_value is not None:
    max_value = setting.max_value
  elif hasattr(setting, 'pdb_max_value') and setting.pdb_max_value is not None:
    max_value = setting.pdb_max_value
  else:
    max_value = GLib.MAXINT

  value_range = abs(max_value - min_value)

  if value_range <= GLib.MAXUINT16:
    spin_button_class = GimpUi.SpinScale
  else:
    spin_button_class = Gtk.SpinButton

  step_increment = 1
  page_increment = 10

  if digits is None:
    digits = 2

    if 0 < value_range <= 1:
      digits_in_value_range = -math.floor(math.log10(value_range))

      digits = digits_in_value_range + 1
      step_increment = 10 ** -digits
      page_increment = 10 ** -(digits - 1)

  return spin_button_class(
    adjustment=Gtk.Adjustment(
      value=setting.value,
      lower=min_value,
      upper=max_value,
      step_increment=step_increment,
      page_increment=page_increment,
    ),
    digits=digits,
    numeric=True,
  )


__all__ = []

for name, class_ in inspect.getmembers(sys.modules[__name__], inspect.isclass):
  if issubclass(class_, GtkPresenter):
    __all__.append(name)
