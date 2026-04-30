import gi

gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config import CONFIG
from src import builtin_actions
from src import builtin_commands_common
from src import builtin_conditions
from src import directory as directory_
from src import setting as setting_
from src.gui import messages as messages_
from src.gui import utils as gui_utils_
from src.gui.commands import list as command_list_
from src.gui.main import export_settings as export_settings_


class CommandLists:

  _COMMAND_LABEL_BOX_SPACING = 5

  _CONDITIONS_TOP_MARGIN = 5

  def __init__(self, settings, dialog):
    self._settings = settings
    self._dialog = dialog

    self._actions_or_conditions_loaded = False

    self._action_list = command_list_.CommandList(
      self._settings['main/actions'],
      builtin_commands=builtin_commands_common.get_filtered_builtin_commands(
        builtin_actions.BUILTIN_ACTIONS,
        tags=[CONFIG.PROCEDURE_GROUP],
        availability_funcs=builtin_actions.BUILTIN_ACTIONS_AVAILABILITY_FUNCTIONS,
      ),
      add_command_text=_('Add _Action...'),
      allow_custom_commands=True,
      add_custom_command_text=_('Add Custom Action...'),
      command_browser_text=_('Add Custom Action'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._condition_list = command_list_.CommandList(
      self._settings['main/conditions'],
      builtin_commands=builtin_commands_common.get_filtered_builtin_commands(
        builtin_conditions.BUILTIN_CONDITIONS,
        tags=[CONFIG.PROCEDURE_GROUP],
        availability_funcs=builtin_conditions.BUILTIN_CONDITIONS_AVAILABILITY_FUNCTIONS,
      ),
      add_command_text=_('Add C_ondition...'),
      allow_custom_commands=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._init_gui()

    self._init_setting_gui()

  @property
  def action_list(self):
    return self._action_list

  @property
  def condition_list(self):
    return self._condition_list

  @property
  def vbox_actions(self):
    return self._vbox_actions

  @property
  def vbox_conditions(self):
    return self._vbox_conditions

  def display_command_status_and_tooltips_and_deactivate_failing_commands(
        self, batcher, clear_previous=True):
    self.set_command_status_and_deactivate_failed_commands(batcher, clear_previous=clear_previous)

  def set_command_status_and_deactivate_failed_commands(self, batcher, clear_previous=True):
    command_lists = [self._action_list, self._condition_list]
    failed_commands_dict = [batcher.failed_actions, batcher.failed_conditions]
    skipped_commands_dict = [batcher.skipped_actions, batcher.skipped_conditions]

    for command_list, failed_commands, skipped_commands in zip(
          command_lists, failed_commands_dict, skipped_commands_dict):
      for command_item in command_list.items:
        if command_item.command.name in failed_commands:
          command_item.set_info(False)
          command_item.set_warning(
            True,
            messages_.get_failing_message(
              (command_item.command, failed_commands[command_item.command.name][0][0])),
            failed_commands[command_item.command.name][0][1],
            failed_commands[command_item.command.name][0][2],
            parent=self._dialog,
          )
        elif command_item.command.name in skipped_commands:
          command_item.set_warning(False)
          command_item.set_info(
            True,
            _('Skipped: {}').format(skipped_commands[command_item.command.name][0][1])
          )
        else:
          if clear_previous and command_item.command['enabled'].value:
            command_item.set_warning(False)
            command_item.set_info(False)

  def reset_command_status(self):
    for command_list in [self._action_list, self._condition_list]:
      for command_item in command_list.items:
        command_item.set_warning(False)
        command_item.set_info(False)

  def close_command_edit_dialogs(self):
    for command_list in [self._action_list, self._condition_list]:
      for command_item in command_list.items:
        command_item.editor.hide()

  def _init_gui(self):
    self._label_actions = Gtk.Label(
      label='<b>{}</b>'.format(_('Actions')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_actions = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._COMMAND_LABEL_BOX_SPACING,
    )
    self._vbox_actions.pack_start(self._label_actions, False, False, 0)
    self._vbox_actions.pack_start(self._action_list, True, True, 0)

    self._label_conditions = Gtk.Label(
      label='<b>{}</b>'.format(_('Conditions')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_conditions = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._COMMAND_LABEL_BOX_SPACING,
      margin_top=self._CONDITIONS_TOP_MARGIN,
    )
    self._vbox_conditions.pack_start(self._label_conditions, False, False, 0)
    self._vbox_conditions.pack_start(self._condition_list, True, True, 0)

  def _init_setting_gui(self):
    self._settings['gui/action_browser/paned_position'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.paned_position,
      widget=self._action_list.browser.paned,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/action_browser/dialog_position'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.window_position,
      widget=self._action_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/action_browser/dialog_size'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.window_size,
      widget=self._action_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/action_browser/categories_collapsed_state'].set_gui(
      gui_type=setting_.SETTING_GUI_TYPES.command_browser_categories_collapsed_state,
      widget=self._action_list.browser,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

    self._action_list.connect(
      'command-list-item-added-interactive',
      _on_action_item_added,
      self._settings,
      self._condition_list,
    )

    _set_up_existing_export_actions(self._action_list)
    self._action_list.commands.connect_event(
      'after-load',
      lambda _actions: _set_up_existing_export_actions(self._action_list))

    _set_up_existing_insert_overlay_and_related_commands(
      self._action_list, self._condition_list)
    self._action_list.commands.connect_event(
      'after-load', self._set_up_existing_insert_overlay_and_related_commands_on_load)
    self._condition_list.commands.connect_event(
      'after-load', self._set_up_existing_insert_overlay_and_related_commands_on_load)

  def _set_up_existing_insert_overlay_and_related_commands_on_load(self, _commands):
    if self._actions_or_conditions_loaded:
      _set_up_existing_insert_overlay_and_related_commands(
        self._action_list, self._condition_list)

      # This allows setting up the commands again when loading again.
      self._actions_or_conditions_loaded = False

    self._actions_or_conditions_loaded = True


def _on_action_item_added(action_list, item, settings, condition_list):
  if item.command['orig_name'].value.startswith('export_for_'):
    _handle_export_action_item_added(item)

    if item.command['orig_name'].value not in [
          'export_for_edit_and_save_images', 'export_for_edit_layers']:
      _handle_export_action_item_added_for_export_mode(item, settings)

  if item.command['orig_name'].value != 'save':
    _reorder_action_before_first_save_action(action_list, item)

  if item.command['orig_name'].value.startswith('insert_overlay_for_'):
    _handle_insert_overlay_action_item_added(action_list, item, condition_list)


def _set_up_existing_export_actions(action_list: command_list_.CommandList):
  for item in action_list.items:
    if item.command['orig_name'].value.startswith('export_for_'):
      _handle_export_action_item_added(item)


def _handle_insert_overlay_action_item_added(action_list, item, condition_list):
  if item.command['orig_name'].value == 'insert_overlay_for_layers':
    if (item.command['arguments/insert_content'].value
        == builtin_actions.ContentType.LAYERS_WITH_COLOR_TAG):
      _add_and_set_up_without_color_tag_condition(item, action_list, condition_list)

    item.command['arguments/insert_content'].connect_event(
      'value-changed',
      _add_or_remove_without_color_tag_condition_when_insert_content_changes,
      item,
      action_list,
      condition_list,
    )


def _add_or_remove_without_color_tag_condition_when_insert_content_changes(
      insert_content_setting,
      item,
      action_list,
      condition_list,
):
  if insert_content_setting.value == builtin_actions.ContentType.LAYERS_WITH_COLOR_TAG:
    _add_and_set_up_without_color_tag_condition(item, action_list, condition_list)
  else:
    condition_name = item.command['arguments/condition_name'].value
    if condition_name in condition_list.commands:
      condition_item = next(
        iter(item_ for item_ in condition_list.items if
             item_.command.name == condition_name),
        None)

      if condition_item is not None and condition_item in condition_list.items:
        condition_list.remove_item(condition_item)
        item.command['arguments/condition_name'].set_value('')


def _add_and_set_up_without_color_tag_condition(item, action_list, condition_list):
  condition_item = _add_without_color_tag_condition(item, condition_list)

  if condition_item is not None:
    _set_up_without_color_tag_condition(condition_item)
    _set_up_insert_overlay_action(item, condition_item, action_list, condition_list)

    item.command['arguments/condition_name'].set_value(condition_item.command.name)


def _set_up_existing_insert_overlay_and_related_commands(
      action_list: command_list_.CommandList,
      condition_list: command_list_.CommandList,
):
  for item in action_list.items:
    if item.command['orig_name'].value != 'insert_overlay_for_layers':
      continue

    condition_name = item.command['arguments/condition_name'].value
    if condition_name in condition_list.commands:
      condition_item = next(
        iter(item_ for item_ in condition_list.items if item_.command.name == condition_name),
        None)
    else:
      condition_item = None

    if condition_item is not None:
      _set_up_without_color_tag_condition(condition_item)
      _set_up_insert_overlay_action(item, condition_item, action_list, condition_list)

    item.command['arguments/insert_content'].connect_event(
      'value-changed',
      _add_or_remove_without_color_tag_condition_when_insert_content_changes,
      item,
      action_list,
      condition_list,
    )


def _set_up_insert_overlay_action(
      item,
      condition_item,
      action_list: command_list_.CommandList,
      condition_list: command_list_.CommandList,
):
  action_list.connect(
    'command-list-item-removed',
    _on_insert_overlay_action_removed,
    item,
    condition_list,
    condition_item,
  )


def _add_without_color_tag_condition(item, condition_list):
  if item.command['orig_name'].value != 'insert_overlay_for_layers':
    return None

  if item.command['arguments/condition_name'].value:
    return None

  condition_item = condition_list.add_item(
    builtin_conditions.BUILTIN_CONDITIONS['without_color_tag'])

  return condition_item


def _set_up_without_color_tag_condition(condition_item):
  _set_buttons_for_command_item_sensitive(condition_item, False)


def _on_insert_overlay_action_removed(
      _action_list,
      removed_item,
      insert_overlay_item,
      condition_list,
      condition_item,
):
  if (removed_item == insert_overlay_item
      and condition_item is not None
      and condition_item in condition_list.items):
    condition_list.remove_item(condition_item)


def _handle_export_action_item_added(item):
  item.command['arguments/file_extension'].gui.widget.connect(
    'changed',
    lambda _entry, setting: export_settings_.apply_file_extension_gui_to_setting_if_valid(setting),
    item.command['arguments/file_extension'])

  export_settings_.revert_file_extension_gui_to_last_valid_value(
    item.command['arguments/file_extension'])

  item.command['arguments/file_extension'].gui.widget.connect(
    'focus-out-event',
    lambda _entry, _event, setting: (
      export_settings_.revert_file_extension_gui_to_last_valid_value(setting)),
    item.command['arguments/file_extension'])

  item.command['arguments/output_directory'].connect_event(
    'value-changed',
    _warn_about_output_directory_special_values)


def _handle_export_action_item_added_for_export_mode(item, settings):
  _copy_setting_values_from_default_export_action(settings['main'], item.command)


def _copy_setting_values_from_default_export_action(main_settings, export_action):
  if main_settings['output_directory'].value:
    export_action['arguments/output_directory'].set_value(main_settings['output_directory'].value)

  export_action['arguments/file_extension'].set_value(main_settings['file_extension'].value)

  for setting in main_settings['export']:
    export_action[f'arguments/{setting.name}'].set_value(setting.value)


def _warn_about_output_directory_special_values(output_directory_setting):
  if (output_directory_setting.value.type_ == directory_.DirectoryTypes.SPECIAL
      and output_directory_setting.value.value == 'match_input_folders'):
    gui_utils_.display_popover(
      output_directory_setting.gui.widget,
      _('Exporting to input folders can overwrite original images.\n'
        'Add and adjust a {} action before export to avoid losing data.').format(_('Rename')),
      icon_name=GimpUi.ICON_DIALOG_WARNING,
    )


def _reorder_action_before_first_save_action(
      action_list: command_list_.CommandList,
      item,
):
  first_save_action_position = next(
    iter(
      index for index, item_ in enumerate(action_list.items)
      if item_.command['orig_name'].value == 'save'),
    None)

  if first_save_action_position is not None:
    action_list.reorder_item(item, first_save_action_position)


def _set_buttons_for_command_item_sensitive(item, sensitive):
  item.button_remove.set_sensitive(sensitive)
