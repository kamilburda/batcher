"""Preview widget displaying a scaled-down image to be processed."""

from typing import List, Optional, Union

import time
import traceback

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import actions
from src import builtin_constraints
from src import exceptions
from src import utils as utils_

from src.gui import messages as messages_
from src.gui import preview_base as preview_base_


class ImagePreview(preview_base_.Preview):
  """Widget displaying a preview of an image to be processed, including its
  name.
  
  Signals:
  
  * ``'preview-updated'`` - The preview was updated by calling `update()`. This
    signal is not emitted if the update is locked.
    
    Arguments:
    
    * error: If ``None``, the preview was updated successfully. Otherwise,
      this is an `Exception` instance describing the error that occurred during
      the update.
    * update_duration_seconds: Duration of the update in seconds as a float.
      The duration only considers the update of the image contents (i.e. does
      not consider the duration of updating the label of the image name).
  """
  
  __gsignals__ = {
    'preview-updated': (
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_FLOAT)),
  }
  
  _MANUAL_UPDATE_LOCK = '_manual_update'
  
  _WIDGET_SPACING = 5
  
  def __init__(self, batcher, settings):
    super().__init__()
    
    self._batcher = batcher
    self._settings = settings
    
    self._item = None
    
    self._preview_pixbuf = None
    self._preview_pixbuf_to_draw = None
    self._previous_preview_pixbuf_width = None
    self._previous_preview_pixbuf_height = None
    
    self._is_updating = False
    self._is_preview_image_allocated_size = False
    
    self._preview_width = None
    self._preview_height = None
    self._preview_scaling_factor = None
    
    self._resize_image_action_id = None
    self._merge_items_action_id = None
    self._scale_item_action_id = None
    self._resize_item_action_id = None
    
    self.prepare_image_for_rendering()
    
    self._init_gui()

    self._preview_image.connect('draw', self._on_preview_image_draw)
    self._preview_image.connect('size-allocate', self._on_preview_image_size_allocate)
    
    self._button_menu.connect('clicked', self._on_button_menu_clicked)
    self._menu_item_update_automatically.connect(
      'toggled', self._on_menu_item_update_automatically_toggled)
    self._button_refresh.connect('clicked', self._on_button_refresh_clicked)
  
  @property
  def item(self):
    return self._item
  
  @item.setter
  def item(self, value):
    self._item = value

    if value is None:
      self._preview_pixbuf = None
      self._preview_pixbuf_to_draw = None
      self._previous_preview_pixbuf_width = None
      self._previous_preview_pixbuf_height = None
  
  @property
  def menu_item_update_automatically(self):
    return self._menu_item_update_automatically
  
  def update(self):
    update_locked = super().update()
    if update_locked:
      return
    
    if self.item is None:
      return
    
    if not self.item.raw.is_valid():
      self.clear()
      return
    
    if self.item.type != pg.itemtree.TYPE_FOLDER:
      self._is_updating = True

      self._set_item_name_label(self.item.name)
      
      if self._is_preview_image_allocated_size:
        self._set_contents()
    else:
      self._set_pixbuf(self._folder_icon)
      self._set_item_name_label(self.item.name)
  
  def clear(self, use_item_name=False):
    self.item = None

    self._set_pixbuf(self._no_selection_icon)

    if not use_item_name:
      self._set_no_selection_label()
  
  def resize(self):
    """Resizes the preview if the widget is smaller than the previewed image so
    that the image fits the widget.
    """
    if not self._is_updating and self._preview_image.get_mapped():
      self._resize_preview(self._preview_image.get_allocation(), self._preview_pixbuf)
  
  def is_larger_than_image(self) -> bool:
    """Returns ``True`` if the preview widget is larger than the image.

    ``False`` is returned if the preview widget is smaller than the image or no
    image is previewed.
    """
    allocation = self._preview_image.get_allocation()
    return (
      self._preview_pixbuf is not None
      and allocation.width > self._preview_pixbuf.get_width()
      and allocation.height > self._preview_pixbuf.get_height())
  
  def update_item(self, raw_item: Optional[Gimp.Item] = None):
    if raw_item is not None and raw_item.is_valid():
      should_update = raw_item in self._batcher.item_tree
    else:
      if (self.item is not None
          and self._batcher.item_tree is not None
          and self.item.raw in self._batcher.item_tree):
        raw_item = self.item.raw
        should_update = True
      else:
        should_update = False
    
    if should_update:
      item = self._batcher.item_tree[raw_item]
      if self._batcher.item_tree.filter.is_match(item):
        self.item = item
        self._set_item_name_label(self.item.name)
  
  def prepare_image_for_rendering(
        self,
        resize_image_action_groups: Union[str, List[str], None] = None,
        scale_item_action_groups: Union[str, List[str], None] = None,
  ):
    """Adds procedures that prepare an image for rendering in the preview.
    
    Specifically, the image to be previewed is resized, scaled and later merged
    into a single layer.
    
    Subsequent calls to this method will remove the previously added procedures.
    
    The optional action groups allow to customize at which point during
    processing the resize and scale procedures are applied. By default, these
    procedures are applied before applying other procedures added by the user.
    """
    if resize_image_action_groups is None:
      resize_image_action_groups = ['before_process_items_contents']
    
    if scale_item_action_groups is None:
      scale_item_action_groups = ['before_process_item_contents']
    
    self._batcher.remove_action(
      self._resize_image_action_id, groups='all', ignore_if_not_exists=True)
    self._resize_image_action_id = self._batcher.add_procedure(
      self._resize_image_for_batcher, resize_image_action_groups, ignore_if_exists=True)
    
    self._batcher.remove_action(
      self._merge_items_action_id, groups='all', ignore_if_not_exists=True)
    self._merge_items_action_id = self._batcher.add_procedure(
      self._merge_items_for_batcher, ['after_process_item_contents'], ignore_if_exists=True)
    
    self._batcher.remove_action(
      self._scale_item_action_id, groups='all', ignore_if_not_exists=True)
    self._scale_item_action_id = self._batcher.add_procedure(
      self._scale_item_for_batcher, scale_item_action_groups, ignore_if_exists=True)
    
    self._batcher.remove_action(
      self._resize_item_action_id, groups='all', ignore_if_not_exists=True)
    self._resize_item_action_id = self._batcher.add_procedure(
      self._resize_item_for_batcher, ['after_process_item_contents'], ignore_if_exists=True)
  
  def _set_contents(self):
    # Sanity check in case `item` changes before 'size-allocate' is emitted.
    if self.item is None:
      return
    
    start_update_time = time.time()
    
    with pg.pdbutils.redirect_messages():
      self._preview_pixbuf, error = self._get_in_memory_preview(self.item.raw)
    
    if self._preview_pixbuf is not None:
      self._preview_pixbuf_to_draw = self._preview_pixbuf
      self._preview_image.queue_draw()
    else:
      self.clear(use_item_name=True)
    
    self._is_updating = False
    
    update_duration_seconds = time.time() - start_update_time
    
    self.emit('preview-updated', error, update_duration_seconds)
  
  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.VERTICAL)

    self._button_menu = Gtk.Button(relief=Gtk.ReliefStyle.NONE)

    arrow = Gtk.Arrow(
      arrow_type=Gtk.ArrowType.DOWN,
      shadow_type=Gtk.ShadowType.IN,
    )
    self._button_menu.add(arrow)
    
    self._menu_item_update_automatically = Gtk.CheckMenuItem(
      label=_('Update Image Preview Automatically'),
      active=True,
    )
    
    self._menu_settings = Gtk.Menu()
    self._menu_settings.append(self._menu_item_update_automatically)
    self._menu_settings.show_all()
    
    self._button_refresh = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
    self._button_refresh.set_image(
      Gtk.Image.new_from_icon_name('view-refresh', Gtk.IconSize.BUTTON))
    self._button_refresh.set_tooltip_text(_('Update Preview'))
    self._button_refresh.show_all()
    self._button_refresh.hide()
    self._button_refresh.set_no_show_all(True)
    
    self._hbox_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    self._hbox_buttons.pack_start(self._button_menu, False, False, 0)
    self._hbox_buttons.pack_start(self._button_refresh, False, False, 0)

    self._preview_image = Gtk.DrawingArea(
      hexpand=True,
      vexpand=True,
    )

    self._no_selection_icon = pg.gui.utils.get_icon_pixbuf(
      GimpUi.ICON_DIALOG_QUESTION, self, Gtk.IconSize.DIALOG)

    self._folder_icon = pg.gui.utils.get_icon_pixbuf('folder', self, Gtk.IconSize.DIALOG)
    
    self._label_item_name = Gtk.Label(ellipsize=Pango.EllipsizeMode.MIDDLE)
    
    self.set_spacing(self._WIDGET_SPACING)
    
    self.pack_start(self._hbox_buttons, False, False, 0)
    self.pack_start(self._preview_image, True, True, 0)
    self.pack_start(self._label_item_name, False, False, 0)

    self._set_pixbuf(self._no_selection_icon)
    self._set_no_selection_label()
  
  def _get_in_memory_preview(self, raw_item):
    self._preview_width, self._preview_height = self._get_preview_size(
      raw_item.get_width(), raw_item.get_height())
    self._preview_scaling_factor = self._preview_width / raw_item.get_width()
    
    image_preview, error = self._get_image_preview()
    
    if image_preview is None or not image_preview.is_valid():
      return None, error

    image_layers = image_preview.list_layers()

    if not image_layers:
      pg.pdbutils.try_delete_image(image_preview)
      return None, error
    
    if image_preview.get_base_type() != Gimp.ImageBaseType.RGB:
      image_preview.convert_rgb()
    
    raw_item_preview = image_layers[0]
    
    if raw_item_preview.get_mask() is not None:
      raw_item_preview.remove_mask(Gimp.MaskApplyMode.APPLY)
    
    # Recompute the size as the item may have been resized during processing.
    self._preview_width, self._preview_height = self._get_preview_size(
      raw_item_preview.get_width(), raw_item_preview.get_height())

    preview_pixbuf = self._get_preview_pixbuf(
      raw_item_preview, self._preview_width, self._preview_height)
    
    image_preview.delete()
    
    return preview_pixbuf, error
  
  def _get_image_preview(self):
    # The processing requires items in their original state as some procedures
    # might depend on their values, which would otherwise produce an image that
    # would not correspond to the real output. We therefore reset items.
    # Also, we need to restore the items' state once the processing is finished
    # so that proper names are displayed in the image preview - the same ones as
    # produced by the name preview, since we assume here that the image preview
    # is updated after the name preview.
    if self._batcher.item_tree is not None:
      for item in self._batcher.item_tree.iter_all():
        item.push_state()
        item.reset()
    
    only_selected_item_constraint_id = self._batcher.add_constraint(
      builtin_constraints.is_item_in_items_selected_in_preview,
      groups=[actions.DEFAULT_CONSTRAINTS_GROUP],
      args=[{self.item.raw.get_image(): {self.item.raw}}])
    
    error = None
    image_preview = None
    
    try:
      image_preview = self._batcher.run(
        keep_image_copy=True,
        item_tree=self._batcher.item_tree,
        is_preview=True,
        process_contents=True,
        process_names=False,
        process_export=False,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError as e:
      pass
    except exceptions.ActionError as e:
      messages_.display_failure_message(
        messages_.get_failing_action_message(e),
        failure_message=str(e),
        details=e.traceback,
        parent=pg.gui.get_toplevel_window(self))
      
      error = e
    except Exception as e:
      messages_.display_failure_message(
        _('There was a problem with updating the image preview:'),
        failure_message=str(e),
        details=traceback.format_exc(),
        parent=pg.gui.get_toplevel_window(self))
      
      error = e
    
    self._batcher.remove_action(
      only_selected_item_constraint_id, [actions.DEFAULT_CONSTRAINTS_GROUP])
    
    if self._batcher.item_tree is not None:
      for item in self._batcher.item_tree.iter_all():
        item.pop_state()
    
    return image_preview, error
  
  def _resize_image_for_batcher(self, batcher, *args, **kwargs):
    image = batcher.current_image
    
    image.resize(
      max(1, int(round(image.get_width() * self._preview_scaling_factor))),
      max(1, int(round(image.get_height() * self._preview_scaling_factor))),
      0,
      0)
    
    Gimp.context_set_interpolation(Gimp.InterpolationType.LINEAR)
  
  @staticmethod
  def _merge_items_for_batcher(batcher, item=None, raw_item=None):
    raw_item_merged = batcher.current_image.merge_visible_layers(
      Gimp.MergeType.EXPAND_AS_NECESSARY)
    
    batcher.current_image.set_selected_layers([raw_item_merged])
    batcher.current_raw_item = raw_item_merged
    
  def _scale_item_for_batcher(self, batcher, item=None, raw_item=None):
    if raw_item is None or not raw_item.is_valid():
      raw_item = batcher.current_raw_item
    
    raw_item.transform_scale(
      raw_item.get_offsets().offset_x * self._preview_scaling_factor,
      raw_item.get_offsets().offset_y * self._preview_scaling_factor,
      (raw_item.get_offsets().offset_x + raw_item.get_width()) * self._preview_scaling_factor,
      (raw_item.get_offsets().offset_y + raw_item.get_height()) * self._preview_scaling_factor)
  
  @staticmethod
  def _resize_item_for_batcher(batcher, item=None, raw_item=None):
    batcher.current_raw_item.resize_to_image_size()
  
  @staticmethod
  def _get_preview_pixbuf(raw_item, preview_width, preview_height):
    return raw_item.get_thumbnail(
      preview_width, preview_height, Gimp.PixbufTransparency.SMALL_CHECKS)
  
  def _get_preview_size(self, width, height):
    preview_widget_allocation = self._preview_image.get_allocation()
    preview_widget_width = preview_widget_allocation.width
    preview_widget_height = preview_widget_allocation.height
    
    if preview_widget_width > preview_widget_height:
      preview_height = min(preview_widget_height, height)
      preview_width = int(round((preview_height / height) * width))
      
      if preview_width > preview_widget_width:
        preview_width = preview_widget_width
        preview_height = int(round((preview_width / width) * height))
    else:
      preview_width = min(preview_widget_width, width)
      preview_height = int(round((preview_width / width) * height))
      
      if preview_height > preview_widget_height:
        preview_height = preview_widget_height
        preview_width = int(round((preview_height / height) * width))
    
    if preview_width == 0:
      preview_width = 1
    if preview_height == 0:
      preview_height = 1
    
    return preview_width, preview_height
  
  def _resize_preview(self, preview_allocation, preview_pixbuf):
    if preview_pixbuf is None:
      return

    if (preview_allocation.width >= preview_pixbuf.get_width()
        and preview_allocation.height >= preview_pixbuf.get_height()):
      return

    scaled_preview_width, scaled_preview_height = self._get_preview_size(
      preview_pixbuf.get_width(), preview_pixbuf.get_height())
    
    if (self._previous_preview_pixbuf_width == scaled_preview_width
        and self._previous_preview_pixbuf_height == scaled_preview_height):
      return

    scaled_preview_pixbuf = self._scale_pixbuf(
      preview_pixbuf, scaled_preview_width, scaled_preview_height)
    
    self._preview_pixbuf_to_draw = scaled_preview_pixbuf
    self._preview_image.queue_draw()
    
    self._previous_preview_pixbuf_width = scaled_preview_width
    self._previous_preview_pixbuf_height = scaled_preview_height

  def _on_preview_image_draw(self, image, cairo_context):
    if self._preview_pixbuf_to_draw is None:
      return

    image_allocation = image.get_allocation()
    x = (image_allocation.width - self._preview_pixbuf_to_draw.get_width()) / 2
    y = (image_allocation.height - self._preview_pixbuf_to_draw.get_height()) / 2

    Gdk.cairo_set_source_pixbuf(cairo_context, self._preview_pixbuf_to_draw, x, y)
    cairo_context.paint()

  def _on_preview_image_size_allocate(self, image, allocation):
    if not self._is_preview_image_allocated_size:
      self._set_contents()
      self._is_preview_image_allocated_size = True

  def _set_pixbuf(self, pixbuf):
    if self._preview_image.get_mapped():
      pixbuf_width, pixbuf_height = self._get_preview_size(pixbuf.get_width(), pixbuf.get_height())
    else:
      pixbuf_width = pixbuf.get_width()
      pixbuf_height = pixbuf.get_height()

    self._preview_pixbuf = pixbuf
    self._preview_pixbuf_to_draw = self._scale_pixbuf(pixbuf, pixbuf_width, pixbuf_height)
    self._previous_preview_pixbuf_width = None
    self._previous_preview_pixbuf_height = None

    self._preview_image.queue_draw()

  @staticmethod
  def _scale_pixbuf(pixbuf, width, height):
    return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

  def _set_item_name_label(self, item_name):
    self._label_item_name.set_markup(f'<i>{GLib.markup_escape_text(item_name)}</i>')

  def _set_no_selection_label(self):
    self._set_item_name_label(_('No selection'))

  def _on_button_menu_clicked(self, button):
    pg.gui.menu_popup_below_widget(self._menu_settings, button)
  
  def _on_menu_item_update_automatically_toggled(self, menu_item):
    if self._menu_item_update_automatically.get_active():
      self._button_refresh.hide()
      self.lock_update(False, self._MANUAL_UPDATE_LOCK)
      self.update()
    else:
      self._button_refresh.show()
      self.lock_update(True, self._MANUAL_UPDATE_LOCK)
  
  def _on_button_refresh_clicked(self, button):
    if self._MANUAL_UPDATE_LOCK in self._lock_keys:
      self.lock_update(False, self._MANUAL_UPDATE_LOCK)
      self.update()
      self.lock_update(True, self._MANUAL_UPDATE_LOCK)
    else:
      self.update()


GObject.type_register(ImagePreview)
