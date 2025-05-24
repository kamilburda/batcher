"""Preview widget displaying a scaled-down image to be processed."""

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

from . import base as preview_base_

from src import builtin_procedures
from src import exceptions
from src import utils as utils_
from src.gui import messages as messages_


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
      GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_DOUBLE)),
  }
  
  _MANUAL_UPDATE_LOCK = '_manual_update'
  
  _WIDGET_SPACING = 5
  _HBOX_SPACING = 4
  _ARROW_ICON_PIXEL_SIZE = 12
  
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

    self._set_update_duration_action_id = None
    self._update_duration_seconds = 0.0
    
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

    if self.item.raw is not None and not self.item.raw.is_valid():
      self.clear()
      return

    if self.item.type != pg.itemtree.TYPE_FOLDER:
      self._is_updating = True

      self.set_item_name_label(self.item)
      
      if self._is_preview_image_allocated_size:
        self._set_contents()
    else:
      self._set_pixbuf(self._folder_icon)
      self.set_item_name_label(self.item)
  
  def clear(self, use_item_name=False, error=None):
    self.item = None

    self._set_pixbuf(self._no_selection_icon)

    if not use_item_name:
      if error is None:
        self._set_no_selection_label()
      else:
        self._set_label(str(error), sensitive=False)
  
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

  def set_item_name_label(self, item: pg.itemtree.Item):
    if not self._batcher.edit_mode:
      item_state = item.get_named_state(builtin_procedures.EXPORT_NAME_ITEM_STATE)
      item_name = item_state['name'] if item_state is not None else item.name
    else:
      item_name = item.name

    self._label_item_name.set_sensitive(True)
    self._label_item_name.set_markup(f'<i>{GLib.markup_escape_text(item_name)}</i>')

  def _set_no_selection_label(self):
    self._label_item_name.set_markup('<i>{}</i>'.format(_('No selection')))
    self._label_item_name.set_sensitive(False)

  def _set_label(self, text, sensitive=True):
    self._label_item_name.set_markup(f'<i>{text}</i>')
    self._label_item_name.set_sensitive(sensitive)

  def _set_contents(self):
    # Sanity check in case `item` changes before 'size-allocate' is emitted.
    if self.item is None:
      return

    self._update_duration_seconds = 0.0

    with pg.pdbutils.redirect_messages():
      self._preview_pixbuf, error, display_error_message_as_label = self._get_in_memory_preview()
    
    if self._preview_pixbuf is not None:
      self._preview_pixbuf_to_draw = self._preview_pixbuf
      self._preview_image.queue_draw()
    else:
      if error is None or not display_error_message_as_label:
        self.clear(use_item_name=True)
      else:
        self.clear(use_item_name=False, error=error)
    
    self._is_updating = False

    self.emit('preview-updated', error, self._update_duration_seconds)
  
  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.VERTICAL)

    self._preview_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
    )
    self._preview_label.set_markup('<b>{}</b>'.format(_('Preview')))

    self._image_arrow = Gtk.Image.new_from_icon_name('go-down', Gtk.IconSize.BUTTON)
    self._image_arrow.set_pixel_size(self._ARROW_ICON_PIXEL_SIZE)

    self._button_menu = Gtk.Button(
      image=self._image_arrow,
      relief=Gtk.ReliefStyle.NONE,
    )

    self._menu_item_update_automatically = Gtk.CheckMenuItem(
      label=_('Update Automatically'),
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
    
    self._hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_SPACING,
    )
    self._hbox.pack_start(self._preview_label, False, False, 0)
    self._hbox.pack_start(self._button_menu, False, False, 0)
    self._hbox.pack_start(self._button_refresh, False, False, 0)

    self._preview_image = Gtk.DrawingArea(
      hexpand=True,
      vexpand=True,
    )

    self._no_selection_icon = pg.gui.utils.get_icon_pixbuf(
      GimpUi.ICON_IMAGE, self, Gtk.IconSize.DIALOG)

    self._folder_icon = pg.gui.utils.get_icon_pixbuf('folder', self, Gtk.IconSize.DIALOG)
    
    self._label_item_name = Gtk.Label(ellipsize=Pango.EllipsizeMode.MIDDLE)
    
    self.set_spacing(self._WIDGET_SPACING)
    
    self.pack_start(self._hbox, False, False, 0)
    self.pack_start(self._preview_image, True, True, 0)
    self.pack_start(self._label_item_name, False, False, 0)

    self._set_pixbuf(self._no_selection_icon)
    self._set_no_selection_label()
  
  def _get_in_memory_preview(self):
    start_update_time = time.time()

    self._batcher.remove_action(
      self._set_update_duration_action_id, groups='all', ignore_if_not_exists=True)
    self._set_update_duration_action_id = self._batcher.add_procedure(
      self._set_update_duration, ['cleanup_contents'], [start_update_time], ignore_if_exists=True)

    image_copies, error, display_error_message_as_label = self._get_image_preview()

    if not image_copies:
      return None, error, display_error_message_as_label

    image_preview = image_copies[0]

    if image_preview is None or not image_preview.is_valid():
      return None, error, display_error_message_as_label

    image_layers = image_preview.get_layers()

    if not image_layers:
      pg.pdbutils.try_delete_image(image_preview)
      return None, error, display_error_message_as_label

    preview_width, preview_height = self._get_preview_size(
      image_preview.get_width(), image_preview.get_height())

    preview_pixbuf = self._get_preview_pixbuf(image_preview, preview_width, preview_height)

    for image in image_copies:
      pg.pdbutils.try_delete_image(image)
    
    return preview_pixbuf, error, display_error_message_as_label

  def _set_update_duration(self, _batcher, start_update_time):
    self._update_duration_seconds = time.time() - start_update_time

  def _get_image_preview(self):
    # We use a separate `pygimplib.ItemTree` with just the item to be previewed.
    # A new item wrapping the original object is created to avoid introducing
    # any changes to the item from other sources (e.g. the item could be
    # renamed via the name preview).
    tree_for_preview = type(self._batcher.item_tree)()
    tree_for_preview.add([self.item.id], with_folders=False)

    error = None
    display_error_message_as_label = False

    try:
      self._batcher.run(
        item_tree=tree_for_preview,
        refresh_item_tree=False,
        keep_image_copies=True,
        is_preview=True,
        process_contents=True,
        process_names=False,
        process_export=False,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.BatcherFileLoadError as e:
      error = e
      display_error_message_as_label = True
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

    return self._batcher.image_copies, error, display_error_message_as_label

  @staticmethod
  def _get_preview_pixbuf(image, preview_width, preview_height):
    return image.get_thumbnail(preview_width, preview_height, Gimp.PixbufTransparency.SMALL_CHECKS)
  
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
