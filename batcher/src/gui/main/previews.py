import gi

import src.gui.preview.base

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import core
from src import overwrite

from src.gui.preview import controller as previews_controller_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_


class Previews:

  _PREVIEWS_GLOBAL_KEY = 'previews_global'
  _PREVIEWS_SENSITIVE_KEY = 'previews_sensitive'
  _VPANED_PREVIEW_SENSITIVE_KEY = 'vpaned_preview_sensitive'

  _DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS = 500

  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0

  _PREVIEWS_LEFT_MARGIN = 4
  _PREVIEW_LABEL_BOTTOM_MARGIN = 4

  def __init__(
        self,
        settings,
        batcher_mode,
        initial_layer_tree,
        lock_previews=True,
        display_message_func=None,
  ):
    self._settings = settings
    self._batcher_mode = batcher_mode
    self._initial_layer_tree = initial_layer_tree
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._image = self._initial_layer_tree.image

    overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
      overwrite.OverwriteModes.RENAME_NEW)

    self._batcher_for_name_preview = core.LayerBatcher(
      input_image=self._image,
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=self._batcher_mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
      overwrite_chooser=overwrite_chooser,
      item_tree=self._initial_layer_tree)

    self._name_preview = preview_name_.NamePreview(
      self._batcher_for_name_preview,
      self._settings,
      self._initial_layer_tree,
      self._settings['gui/name_preview_items_collapsed_state'].value[self._image],
      self._settings['main/selected_layers'].value[self._image],
      'selected_in_preview')

    self._batcher_for_image_preview = core.LayerBatcher(
      input_image=self._image,
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=self._batcher_mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
      overwrite_chooser=overwrite_chooser,
      item_tree=self._initial_layer_tree)

    self._image_preview = preview_image_.ImagePreview(
      self._batcher_for_image_preview, self._settings)

    self._previews_controller = previews_controller_.PreviewsController(
      self._name_preview, self._image_preview, self._settings, self._image)

    self._paned_outside_previews_previous_position = (
      self._settings['gui/size/paned_outside_previews_position'].value)

    self._paned_between_previews_previous_position = (
      self._settings['gui/size/paned_between_previews_position'].value)

    if lock_previews:
      self.lock()

    self._init_gui()

    self._init_setting_gui()

  @property
  def name_preview(self):
    return self._name_preview

  @property
  def image_preview(self):
    return self._image_preview

  @property
  def controller(self):
    return self._previews_controller

  @property
  def vbox_previews(self):
    return self._vbox_previews

  def lock(self):
    self._previews_controller.lock_previews(self._PREVIEWS_GLOBAL_KEY)

  def unlock(self):
    self._previews_controller.unlock_and_update_previews(self._PREVIEWS_GLOBAL_KEY)

  def _init_gui(self):
    self._preview_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      margin_bottom=self._PREVIEW_LABEL_BOTTOM_MARGIN,
    )
    self._preview_label.set_markup('<b>{}</b>'.format(_('Preview')))

    self._vpaned_previews = Gtk.Paned(
      orientation=Gtk.Orientation.VERTICAL,
      wide_handle=True,
    )
    self._vpaned_previews.pack1(self._name_preview, True, True)
    self._vpaned_previews.pack2(self._image_preview, True, True)

    self._vbox_previews = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      margin_start=self._PREVIEWS_LEFT_MARGIN,
    )
    self._vbox_previews.pack_start(self._preview_label, False, False, 0)
    self._vbox_previews.pack_start(self._vpaned_previews, True, True, 0)

  def connect_events(self, action_lists, paned_outside_previews):
    self._vpaned_previews.connect(
      'notify::position',
      self._on_paned_between_previews_notify_position)

    paned_outside_previews.connect(
      'notify::position',
      self._on_paned_outside_previews_notify_position)

    self._image_preview.connect('preview-updated', self._on_image_preview_updated, action_lists)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated, action_lists)

    self._previews_controller.connect_setting_changes_to_previews()

  def _init_setting_gui(self):
    self._settings['gui/image_preview_automatic_update'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.check_menu_item,
      widget=self._image_preview.menu_item_update_automatically,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/size/paned_between_previews_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
      widget=self._vpaned_previews,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  def _on_paned_outside_previews_notify_position(self, paned, _property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property('max-position')

    if (current_position == max_position
        and self._paned_outside_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
      self._disable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
    elif (current_position != max_position
          and self._paned_outside_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
      self._enable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._PREVIEWS_SENSITIVE_KEY)
    elif current_position != self._paned_outside_previews_previous_position:
      if self._image_preview.is_larger_than_image():
        pg.invocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        pg.invocation.timeout_remove(self._image_preview.update)
        self._image_preview.resize()

    self._paned_outside_previews_previous_position = current_position

  def _on_paned_between_previews_notify_position(self, paned, _property_spec):
    current_position = paned.get_position()
    max_position = paned.get_property('max-position')
    min_position = paned.get_property('min-position')

    if (current_position == max_position
        and self._paned_between_previews_previous_position != max_position):
      self._disable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position != max_position
          and self._paned_between_previews_previous_position == max_position):
      self._enable_preview_on_paned_drag(
        self._image_preview,
        self._settings['gui/image_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position == min_position
          and self._paned_between_previews_previous_position != min_position):
      self._disable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif (current_position != min_position
          and self._paned_between_previews_previous_position == min_position):
      self._enable_preview_on_paned_drag(
        self._name_preview,
        self._settings['gui/name_preview_sensitive'],
        self._VPANED_PREVIEW_SENSITIVE_KEY)
    elif current_position != self._paned_between_previews_previous_position:
      if self._image_preview.is_larger_than_image():
        pg.invocation.timeout_add_strict(
          self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS,
          self._image_preview.update)
      else:
        pg.invocation.timeout_remove(self._image_preview.update)
        self._image_preview.resize()

    self._paned_between_previews_previous_position = current_position

  def _enable_preview_on_paned_drag(
        self,
        preview: src.gui.preview.base.Preview,
        preview_sensitive_setting: pg.setting.Setting,
        update_lock_key: str,
  ):
    preview.lock_update(False, update_lock_key)
    preview.add_function_at_update(preview.set_sensitive, True)
    # In case the image preview gets resized, the update would be canceled,
    # hence update always.
    GLib.timeout_add(self._DELAY_PREVIEWS_PANE_DRAG_UPDATE_MILLISECONDS, preview.update)
    preview_sensitive_setting.set_value(True)

  def _disable_preview_on_paned_drag(
        self,
        preview: src.gui.preview.base.Preview,
        preview_sensitive_setting: pg.setting.Setting,
        update_lock_key: str,
  ):
    preview.lock_update(True, update_lock_key)
    preview.set_sensitive(False)
    preview_sensitive_setting.set_value(False)

  def _on_image_preview_updated(self, _preview, _error, update_duration_seconds, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(self._batcher_for_image_preview)

    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)

      self._display_message_func(
        _('Disabling automatic preview update. The preview takes too long to update.'),
        Gtk.MessageType.INFO)

  def _on_name_preview_updated(self, _preview, _error, _reset_items, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(
      self._batcher_for_name_preview, clear_previous=False)
