"""Class interconnecting preview widgets for item names and images."""

import collections

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg


class PreviewsController:
  
  _DELAY_PREVIEWS_SETTING_UPDATE_MILLISECONDS = 100
  _DELAY_IMAGE_PREVIEW_SELECTION_CHANGED_UPDATE_MILLISECONDS = 30
  
  _PREVIEW_ERROR_KEY = 'preview_error'
  
  def __init__(self, name_preview, image_preview, settings, current_image=None):
    self._name_preview = name_preview
    self._image_preview = image_preview
    self._settings = settings
    self._current_image = current_image
    self._is_initial_selection_set = False

    self._previously_focused_on_related_window = False

  def lock_previews(self, key):
    self._name_preview.lock_update(True, key)
    self._image_preview.lock_update(True, key)

  def unlock_previews(
        self,
        key,
        update=True,
        name_preview_update_args=None,
        name_preview_update_kwargs=None,
        image_preview_update_args=None,
        image_preview_update_kwargs=None,
  ):
    self._name_preview.lock_update(False, key)
    self._image_preview.lock_update(False, key)

    if update:
      if name_preview_update_args is None:
        name_preview_update_args = ()

      if name_preview_update_kwargs is None:
        name_preview_update_kwargs = {}

      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEWS_SETTING_UPDATE_MILLISECONDS,
        self._name_preview.update,
        *name_preview_update_args,
        **name_preview_update_kwargs,
      )

      if image_preview_update_args is None:
        image_preview_update_args = ()

      if image_preview_update_kwargs is None:
        image_preview_update_kwargs = {}

      pg.invocation.timeout_add_strict(
        self._DELAY_PREVIEWS_SETTING_UPDATE_MILLISECONDS,
        self._update_image_preview,
        *image_preview_update_args,
        **image_preview_update_kwargs,
      )

  def connect_setting_changes_to_previews(self):
    self._connect_actions_changed(self._settings['main/procedures'])
    self._connect_actions_changed(self._settings['main/constraints'])
    
    self._connect_setting_after_reset_collapsed_items_in_name_preview()
    self._connect_setting_after_reset_selected_items_in_name_preview()
    self._connect_setting_after_reset_displayed_items_in_image_preview()

    self._connect_name_preview_events()

    self._connect_image_preview_menu_setting_changes()

    self._connect_focus_changes_for_plugin_windows()

  def _connect_actions_changed(self, actions):
    # We store event IDs in lists in case the same action is added multiple times.
    settings_and_event_ids = collections.defaultdict(lambda: collections.defaultdict(list))

    def _on_after_add_action(_actions, action_, _action_dict):
      self._update_previews_on_setting_change_if_enabled(action_['enabled'], action_)

      settings_and_event_ids[action_]['enabled'].append(
        action_['enabled'].connect_event(
          'value-changed', self._update_previews_on_setting_change, action_))

      for setting in action_['arguments']:
        settings_and_event_ids[action_][f'arguments/{setting.name}'].append(
          setting.connect_event(
            'value-changed', self._update_previews_on_setting_change_if_enabled, action_))

      for setting in action_['more_options']:
        settings_and_event_ids[action_][f'more_options/{setting.name}'].append(
          setting.connect_event(
            'value-changed', self._update_previews_on_setting_change_if_enabled, action_))
    
    def _on_after_reorder_action(_actions, action_, *_args, **_kwargs):
      self._update_previews_on_setting_change_if_enabled(action_['enabled'], action_)
    
    def _on_before_remove_action(_actions, action_, *_args, **_kwargs):
      self._update_previews_on_setting_change_if_enabled(action_['enabled'], action_)

      should_remove_action_from_event_ids = False

      for setting_path, event_ids in settings_and_event_ids[action_].items():
        if event_ids:
          action_[setting_path].remove_event(event_ids[-1])
          event_ids.pop()
          # We do not have to separately check if each list is empty as they are all updated at
          # once.
          should_remove_action_from_event_ids = True

      if should_remove_action_from_event_ids:
        del settings_and_event_ids[action_]
    
    actions.connect_event('after-add-action', _on_after_add_action)

    # Activate event for existing actions
    for action in actions:
      _on_after_add_action(actions, action, None)

    actions.connect_event('after-reorder-action', _on_after_reorder_action)
    actions.connect_event('before-remove-action', _on_before_remove_action)

  def _update_previews_on_setting_change_if_enabled(self, setting, action):
    if action['enabled'].value:
      self._update_previews_on_setting_change(setting, action)

  def _update_previews_on_setting_change(self, setting, action):
    if (not action['more_options/enabled_for_previews'].value
        and setting.name != 'enabled_for_previews'):
      return

    self.unlock_previews(self._PREVIEW_ERROR_KEY)

  def _connect_setting_after_reset_collapsed_items_in_name_preview(self):
    self._settings['gui/name_preview_items_collapsed_state'].connect_event(
      'after-load',
      lambda setting: self._name_preview.set_collapsed_items(set(setting.active_items)))

    self._settings['gui/name_preview_items_collapsed_state'].connect_event(
      'after-reset',
      lambda setting: self._name_preview.set_collapsed_items(set(setting.active_items)))
  
  def _connect_setting_after_reset_selected_items_in_name_preview(self):
    self._settings['gui/selected_items'].connect_event(
      'after-load',
      lambda setting: self._name_preview.set_selected_items(setting.active_items))

    self._settings['gui/selected_items'].connect_event(
      'after-reset',
      lambda setting: self._name_preview.set_selected_items(setting.active_items))
  
  def _connect_setting_after_reset_displayed_items_in_image_preview(self):
    def _clear_image_preview(_setting):
      self._image_preview.clear()
    
    self._settings['gui/image_preview_displayed_items'].connect_event(
      'after-reset', _clear_image_preview)
  
  def _connect_image_preview_menu_setting_changes(self):
    self._settings['gui/image_preview_automatic_update'].connect_event(
      'value-changed',
      lambda setting, update_if_below_setting: update_if_below_setting.set_value(False),
      self._settings['gui/image_preview_automatic_update_if_below_maximum_duration'])

  def _connect_focus_changes_for_plugin_windows(self):
    GObject.add_emission_hook(
      Gtk.Window,
      'window-state-event',
      self._on_related_window_window_state_event)

  def _on_related_window_window_state_event(self, widget, event):
    if not isinstance(widget, Gtk.Window):
      # This handles widgets such as `Gtk.Menu` that display menu popups.
      window = pg.gui.get_toplevel_window(widget)
    else:
      window = widget

    if (event.type != Gdk.EventType.WINDOW_STATE   # Safeguard, should not happen
        or window.get_window_type() != Gtk.WindowType.TOPLEVEL   # Popup windows
        or not (event.window_state.new_window_state & Gdk.WindowState.FOCUSED)):
      if pg.gui.has_any_window_focus(windows_to_ignore=[window]):
        self._previously_focused_on_related_window = True
      else:
        self._previously_focused_on_related_window = False

      return True

    if ((event.window_state.new_window_state & Gdk.WindowState.FOCUSED)
        and not self._previously_focused_on_related_window):
      self._perform_full_preview_update()

      return True

    return True

  def _perform_full_preview_update(self):
    pg.invocation.timeout_remove(self._name_preview.update)

    pg.invocation.timeout_remove(self._update_image_preview)
    pg.invocation.timeout_remove(self._image_preview.update)

    self._name_preview.update(full_update=True)

    self._update_tagged_items()

    if not self._is_initial_selection_set:
      self._set_initial_selection_and_update_image_preview()
    else:
      self._update_image_preview()

  def _connect_name_preview_events(self):
    self._name_preview.connect('preview-updated', self._on_name_preview_updated)
    self._name_preview.connect('preview-selection-changed', self._on_name_preview_selection_changed)
    self._name_preview.connect(
      'preview-collapsed-items-changed', self._on_name_preview_collapsed_items_changed)

  def _on_name_preview_updated(self, _preview, error):
    if error:
      self.lock_previews(self._PREVIEW_ERROR_KEY)

    if self._image_preview.item is not None:
      selected_item = self._get_item_selected_in_name_preview()
      if selected_item is not None and selected_item.key == self._image_preview.item.key:
        self._image_preview.item = selected_item
        self._image_preview.set_item_name_label(selected_item)

  def _get_item_selected_in_name_preview(self):
    item_from_cursor = self._name_preview.get_item_from_cursor()

    if item_from_cursor is not None:
      return item_from_cursor
    else:
      items_from_selected_rows = self._name_preview.get_items_from_selected_rows()
      if items_from_selected_rows:
        return items_from_selected_rows[0]
      else:
        return None

  def _on_name_preview_selection_changed(self, _preview):
    self._settings['gui/selected_items'].set_active_items(
      self._name_preview.selected_items)

    # There could be a rapid sequence of 'preview-selection-changed' signals
    # invoked if a selected item and preceding items are removed from the name
    # preview due to not matching constraints. Therefore, we delay the image
    # preview update when the selection changes.
    pg.invocation.timeout_add_strict(
      self._DELAY_IMAGE_PREVIEW_SELECTION_CHANGED_UPDATE_MILLISECONDS,
      self._update_image_preview,
      **dict(update_on_identical_item=False),
    )

  def _on_name_preview_collapsed_items_changed(self, _preview):
    self._settings['gui/name_preview_items_collapsed_state'].set_active_items(
      self._name_preview.collapsed_items)

  def _set_initial_selection_and_update_image_preview(self):
    displayed_items_setting = self._settings['gui/image_preview_displayed_items']
    if self._current_image is not None:
      item_key_to_display = next(
        iter(
          item_key for item_key, image in displayed_items_setting.active_items.items()
          if image == self._current_image),
        None)
    else:
      item_key_to_display = next(
        iter(item_key for item_key in displayed_items_setting.active_items),
        None,
      )

    if self._current_image is not None:
      selected_layers_in_current_image = [
        image.get_id() for image in self._current_image.get_selected_layers()]
    else:
      selected_layers_in_current_image = []

    if (item_key_to_display is None
        and not self._settings['gui/selected_items'].active_items
        and selected_layers_in_current_image):
      self._name_preview.set_selected_items(selected_layers_in_current_image)

      # `NamePreview.set_selected_items` triggers the
      # 'preview-selection-changed' event that also updates the image preview
      # with a delay. We need to update the image preview immediately to
      # avoid a "glitch" when there is a very short time period displaying a
      # placeholder icon.
      pg.invocation.timeout_remove(self._update_image_preview)
      self._update_image_preview()
    else:
      batcher = self._name_preview.batcher
      if item_key_to_display in batcher.item_tree:
        item = batcher.item_tree[item_key_to_display]
        if ((batcher.matching_items is not None and item in batcher.matching_items)
            or item.type == pg.itemtree.TYPE_FOLDER):
          self._image_preview.item = item

      self._image_preview.update()

    self._is_initial_selection_set = True

  def _update_tagged_items(self):
    if 'tagged_items' not in self._settings['main']:
      return

    tagged_items = [
      item
      for item in self._name_preview.batcher.item_tree.iter(with_folders=True, filtered=False)
      if (item.raw is not None
          and item.raw.is_valid()
          and item.raw.get_color_tag() != Gimp.ColorTag.NONE)
    ]
    # Remove folders to avoid inserting tagged group items twice.
    self._settings['main/tagged_items'].set_value(
      [item for item in tagged_items if item.type != pg.itemtree.TYPE_FOLDER])

    self._name_preview.set_tagged_items(set(item.key for item in tagged_items))

  def _update_image_preview(self, update_on_identical_item=True):
    item_from_cursor = self._name_preview.get_item_from_cursor()

    if item_from_cursor is not None:
      if (update_on_identical_item
          or self._image_preview.item is None
          or item_from_cursor.key != self._image_preview.item.key):
        self._image_preview.item = item_from_cursor
        self._image_preview.update()
    else:
      items_from_selected_rows = self._name_preview.get_items_from_selected_rows()
      if items_from_selected_rows:
        self._image_preview.item = items_from_selected_rows[0]
        self._image_preview.update()
      else:
        self._image_preview.clear()

    if self._image_preview.item is not None:
      self._settings['gui/image_preview_displayed_items'].set_value([self._image_preview.item.key])
    else:
      self._settings['gui/image_preview_displayed_items'].set_value([])
