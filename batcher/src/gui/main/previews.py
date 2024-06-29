import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import core
from src import overwrite

from src.gui.preview import controller as previews_controller_
from src.gui.preview import image as preview_image_
from src.gui.preview import name as preview_name_


class Previews:

  _PREVIEWS_KEY = 'previews'

  _PREVIEWS_LEFT_MARGIN = 4
  _PREVIEW_LABEL_BOTTOM_MARGIN = 4

  _MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS = 1.0

  def __init__(
        self,
        settings,
        initial_layer_tree,
        lock_previews=True,
        display_message_func=None,
  ):
    self._settings = settings
    self._initial_layer_tree = initial_layer_tree
    self._display_message_func = (
      display_message_func if display_message_func is not None else pg.utils.empty_func)

    self._image = self._initial_layer_tree.image

    self._batcher_for_previews = core.Batcher(
      Gimp.RunMode.NONINTERACTIVE,
      self._image,
      self._settings['main/procedures'],
      self._settings['main/constraints'],
      overwrite_chooser=overwrite.NoninteractiveOverwriteChooser(
        self._settings['main/overwrite_mode'].items['replace']),
      item_tree=self._initial_layer_tree)

    self._name_preview = preview_name_.NamePreview(
      self._batcher_for_previews,
      self._settings,
      self._initial_layer_tree,
      self._settings['gui/name_preview_layers_collapsed_state'].value[self._image],
      self._settings['main/selected_layers'].value[self._image],
      'selected_in_preview')

    self._image_preview = preview_image_.ImagePreview(self._batcher_for_previews, self._settings)

    self._previews_controller = previews_controller_.PreviewsController(
      self._name_preview, self._image_preview, self._settings, self._image)

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
    self._previews_controller.lock_previews(self._PREVIEWS_KEY)

  def unlock(self):
    self._previews_controller.unlock_and_update_previews(self._PREVIEWS_KEY)

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
      self._previews_controller.on_paned_between_previews_notify_position)

    self._image_preview.connect('preview-updated', self._on_image_preview_updated, action_lists)
    self._name_preview.connect('preview-updated', self._on_name_preview_updated, action_lists)

    paned_outside_previews.connect(
      'notify::position',
      self._previews_controller.on_paned_outside_previews_notify_position)

    self._previews_controller.connect_setting_changes_to_previews(
      action_lists.procedure_list,
      action_lists.constraint_list,
    )
    self._previews_controller.connect_name_preview_events()

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

  def _on_image_preview_updated(self, _preview, _error, update_duration_seconds, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(self._batcher_for_previews)

    if (self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'].value
        and (update_duration_seconds
             >= self._MAXIMUM_IMAGE_PREVIEW_AUTOMATIC_UPDATE_DURATION_SECONDS)):
      self._settings['gui/image_preview_automatic_update'].set_value(False)

      self._display_message_func(
        _('Disabling automatic preview update. The preview takes too long to update.'),
        Gtk.MessageType.INFO)

  def _on_name_preview_updated(self, _preview, _error, action_lists):
    action_lists.display_warnings_and_tooltips_for_actions(
      self._batcher_for_previews, clear_previous=False)
