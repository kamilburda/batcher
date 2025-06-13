import os
from typing import Dict, List

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import builtin_commands_common
from src import builtin_conditions
from src import builtin_procedures

from src.gui import messages as messages_
from src.gui.commands import list as command_list_
from src.gui.main import export_settings as export_settings_


class CommandLists:

  _COMMAND_LABEL_BOX_SPACING = 5

  _CONDITIONS_TOP_MARGIN = 5

  def __init__(self, settings, dialog):
    self._settings = settings
    self._dialog = dialog

    self._procedures_or_conditions_loaded = False

    self._procedure_list = command_list_.CommandList(
      self._settings['main/procedures'],
      builtin_commands=builtin_commands_common.get_filtered_builtin_commands(
        builtin_procedures.BUILTIN_PROCEDURES, [pg.config.PROCEDURE_GROUP]),
      add_command_text=_('Add P_rocedure...'),
      allow_custom_commands=True,
      add_custom_command_text=_('Add Custom Procedure...'),
      command_browser_text=_('Add Custom Procedure'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._condition_list = command_list_.CommandList(
      self._settings['main/conditions'],
      builtin_commands=builtin_commands_common.get_filtered_builtin_commands(
        builtin_conditions.BUILTIN_CONDITIONS, [pg.config.PROCEDURE_GROUP]),
      add_command_text=_('Add C_ondition...'),
      allow_custom_commands=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._init_gui()

    self._init_setting_gui()

  @property
  def procedure_list(self):
    return self._procedure_list

  @property
  def condition_list(self):
    return self._condition_list

  @property
  def vbox_procedures(self):
    return self._vbox_procedures

  @property
  def vbox_conditions(self):
    return self._vbox_conditions

  def display_warnings_and_tooltips_for_commands_and_deactivate_failing_commands(
        self, batcher, clear_previous=True):
    self.set_warnings_and_deactivate_failed_commands(batcher, clear_previous=clear_previous)

    self._set_command_skipped_tooltips(
      self._procedure_list,
      batcher.skipped_procedures,
      _('This procedure is skipped. Reason: {}'),
      clear_previous=clear_previous)

    self._set_command_skipped_tooltips(
      self._condition_list,
      batcher.skipped_conditions,
      _('This condition is skipped. Reason: {}'),
      clear_previous=clear_previous)

  def set_warnings_and_deactivate_failed_commands(self, batcher, clear_previous=True):
    command_lists = [self._procedure_list, self._condition_list]
    failed_commands_dict = [batcher.failed_procedures, batcher.failed_conditions]

    for command_list, failed_commands in zip(command_lists, failed_commands_dict):
      for command_item in command_list.items:
        if command_item.command.name in failed_commands:
          command_item.set_warning(
            True,
            messages_.get_failing_command_message(
              (command_item.command, failed_commands[command_item.command.name][0][0])),
            failed_commands[command_item.command.name][0][1],
            failed_commands[command_item.command.name][0][2],
            parent=self._dialog)

          command_item.command['enabled'].set_value(False)
        else:
          if clear_previous and command_item.command['enabled'].value:
            command_item.set_warning(False)

  def reset_command_tooltips_and_indicators(self):
    for command_list in [self._procedure_list, self._condition_list]:
      for command_item in command_list.items:
        command_item.reset_tooltip()
        command_item.set_warning(False)

  def close_command_edit_dialogs(self):
    for command_list in [self._procedure_list, self._condition_list]:
      for command_item in command_list.items:
        command_item.editor.hide()

  def _init_gui(self):
    self._label_procedures = Gtk.Label(
      label='<b>{}</b>'.format(_('Procedures')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_procedures = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._COMMAND_LABEL_BOX_SPACING,
    )
    self._vbox_procedures.pack_start(self._label_procedures, False, False, 0)
    self._vbox_procedures.pack_start(self._procedure_list, True, True, 0)

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
    self._settings['gui/procedure_browser/paned_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
      widget=self._procedure_list.browser.paned,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_position,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_size'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_size,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

    self._procedure_list.connect(
      'command-list-item-added-interactive',
      _on_procedure_item_added,
      self._settings,
      self._condition_list,
    )

    _set_up_existing_crop_procedures(self._procedure_list)
    self._procedure_list.commands.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_crop_procedures(self._procedure_list))

    _set_up_existing_resize_canvas_procedures(self._procedure_list)
    self._procedure_list.commands.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_resize_canvas_procedures(self._procedure_list))

    _set_up_existing_rename_procedures(self._procedure_list)
    self._procedure_list.commands.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_rename_procedures(self._procedure_list))

    _set_up_existing_export_procedures(self._procedure_list)
    self._procedure_list.commands.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_export_procedures(self._procedure_list))

    _set_up_existing_save_procedures(self._procedure_list)
    self._procedure_list.commands.connect_event(
      'after-load',
      lambda _procedures: _set_up_existing_save_procedures(self._procedure_list))

    _set_up_existing_insert_back_foreground_and_related_commands(
      self._procedure_list, self._condition_list)
    self._procedure_list.commands.connect_event(
      'after-load', self._set_up_existing_insert_back_foreground_and_related_commands_on_load)
    self._condition_list.commands.connect_event(
      'after-load', self._set_up_existing_insert_back_foreground_and_related_commands_on_load)

    self._condition_list.connect(
      'command-list-item-added-interactive',
      _on_condition_item_added,
      self._settings,
    )

    _set_up_existing_matching_text_conditions(self._condition_list)
    self._condition_list.commands.connect_event(
      'after-load',
      lambda _conditions: _set_up_existing_matching_text_conditions(self._condition_list))

  def _set_up_existing_insert_back_foreground_and_related_commands_on_load(self, _commands):
    if self._procedures_or_conditions_loaded:
      _set_up_existing_insert_back_foreground_and_related_commands(
        self._procedure_list, self._condition_list)

      # This allows setting up the commands again when loading again.
      self._procedures_or_conditions_loaded = False

    self._procedures_or_conditions_loaded = True

  @staticmethod
  def _set_command_skipped_tooltips(
        command_list: command_list_.CommandList,
        skipped_commands: Dict[str, List],
        message: str,
        clear_previous: bool = True,
  ):
    for command_item in command_list.items:
      if not command_item.has_warning():
        if command_item.command.name in skipped_commands:
          skipped_message = skipped_commands[command_item.command.name][0][1]
          command_item.set_tooltip(message.format(skipped_message))
        else:
          if clear_previous:
            command_item.reset_tooltip()


def _on_procedure_item_added(procedure_list, item, settings, condition_list):
  if item.command['orig_name'].value.startswith('crop_for_'):
    _handle_crop_procedure_item_added(item)

  if item.command['orig_name'].value == 'resize_canvas':
    _handle_resize_canvas_procedure_item_added(item)

  if item.command['orig_name'].value.startswith('rename_for_'):
    _handle_rename_procedure_item_added(item)

  if item.command['orig_name'].value.startswith('export_for_'):
    _handle_export_procedure_item_added(item)

    if item.command['orig_name'].value not in [
          'export_for_edit_and_save_images', 'export_for_edit_layers']:
      _handle_export_procedure_item_added_for_export_mode(item, settings)

  if item.command['orig_name'].value == 'save':
    _handle_save_procedure_item_added(item)

  if item.command['orig_name'].value != 'save':
    _reorder_procedure_before_first_save_procedure(procedure_list, item)

  if any(item.command['orig_name'].value.startswith(prefix) for prefix in [
       'insert_background_for_', 'insert_foreground_for_']):
    _handle_insert_background_foreground_procedure_item_added(procedure_list, item, condition_list)


def _set_up_existing_crop_procedures(procedure_list: command_list_.CommandList):
  for item in procedure_list.items:
    if item.command['orig_name'].value.startswith('crop_for_'):
      _handle_crop_procedure_item_added(item)


def _set_up_existing_resize_canvas_procedures(procedure_list: command_list_.CommandList):
  for item in procedure_list.items:
    if item.command['orig_name'].value == 'resize_canvas':
      _handle_resize_canvas_procedure_item_added(item)


def _set_up_existing_rename_procedures(procedure_list: command_list_.CommandList):
  for item in procedure_list.items:
    if item.command['orig_name'].value.startswith('rename_for_'):
      _handle_rename_procedure_item_added(item)


def _set_up_existing_export_procedures(procedure_list: command_list_.CommandList):
  for item in procedure_list.items:
    if item.command['orig_name'].value.startswith('export_for_'):
      _handle_export_procedure_item_added(item)


def _set_up_existing_save_procedures(procedure_list: command_list_.CommandList):
  for item in procedure_list.items:
    if item.command['orig_name'].value == 'save':
      _handle_save_procedure_item_added(item)


def _handle_insert_background_foreground_procedure_item_added(
      procedure_list, item, condition_list):
  procedure_list.reorder_item(item, 0)

  merge_item = _add_merge_background_foreground_procedure(procedure_list, item)

  condition_item = _add_not_background_foreground_condition(item, condition_list)

  _hide_internal_arguments_for_insert_background_foreground_procedure(item)
  _set_up_merge_background_foreground_procedure(merge_item)
  _set_up_not_background_foreground_condition(item, condition_item)

  if merge_item is not None or condition_item is not None:
    _set_up_insert_background_foreground_procedure(
      item, merge_item, condition_item, procedure_list, condition_list)

  if merge_item is not None:
    item.command['arguments/merge_procedure_name'].set_value(merge_item.command.name)
  if condition_item is not None:
    item.command['arguments/condition_name'].set_value(condition_item.command.name)


def _set_up_existing_insert_back_foreground_and_related_commands(
      procedure_list: command_list_.CommandList,
      condition_list: command_list_.CommandList,
):
  for item in procedure_list.items:
    if any(item.command['orig_name'].value.startswith(prefix) for prefix in [
         'insert_background_for_', 'insert_foreground_for_']):
      merge_procedure_name = (
        item.command['arguments/merge_procedure_name'].value
        if 'merge_procedure_name' in item.command['arguments'] else None)
      if merge_procedure_name is not None and merge_procedure_name in procedure_list.commands:
        merge_item = next(
          iter(
            item_ for item_ in procedure_list.items if item_.command.name == merge_procedure_name),
          None)
      else:
        merge_item = None

      condition_name = (
        item.command['arguments/condition_name'].value
        if 'condition_name' in item.command['arguments'] else None)
      if condition_name is not None and condition_name in condition_list.commands:
        condition_item = next(
          iter(item_ for item_ in condition_list.items if item_.command.name == condition_name),
          None)
      else:
        condition_item = None

      _hide_internal_arguments_for_insert_background_foreground_procedure(item)
      _set_up_merge_background_foreground_procedure(merge_item)
      _set_up_not_background_foreground_condition(item, condition_item)

      if merge_item is not None or condition_item is not None:
        _set_up_insert_background_foreground_procedure(
          item, merge_item, condition_item, procedure_list, condition_list)


def _hide_internal_arguments_for_insert_background_foreground_procedure(item):
  if 'merge_procedure_name' in item.command['arguments']:
    item.command['arguments/merge_procedure_name'].gui.set_visible(False)
  if 'condition_name' in item.command['arguments']:
    item.command['arguments/condition_name'].gui.set_visible(False)


def _set_up_insert_background_foreground_procedure(
      item,
      merge_item,
      condition_item,
      procedure_list: command_list_.CommandList,
      condition_list: command_list_.CommandList,
):
  item.command['enabled'].connect_event(
    'value-changed',
    _on_insert_background_foreground_procedure_enabled_changed,
    merge_item.command if merge_item is not None else None,
    condition_item.command if condition_item is not None else None,
  )

  procedure_list.connect(
    'command-list-item-removed',
    _on_insert_background_foreground_procedure_removed,
    item,
    merge_item,
    condition_list,
    condition_item,
  )


def _add_merge_background_foreground_procedure(procedure_list, item):
  merge_procedure_orig_name_mapping = {
    'insert_background_for_images': 'merge_background',
    'insert_background_for_layers': 'merge_background',
    'insert_foreground_for_images': 'merge_foreground',
    'insert_foreground_for_layers': 'merge_foreground',
  }

  if item.command['orig_name'].value not in merge_procedure_orig_name_mapping:
    return None

  merge_procedure_name = merge_procedure_orig_name_mapping[item.command['orig_name'].value]

  merge_item = procedure_list.add_item(builtin_procedures.BUILTIN_PROCEDURES[merge_procedure_name])

  export_procedure_index = next(
    iter(index for index, item in enumerate(procedure_list.items)
         if item.command['orig_name'].value.startswith('export_for_')),
    None)
  if export_procedure_index is not None:
    procedure_list.reorder_item(merge_item, export_procedure_index)

  return merge_item


def _set_up_merge_background_foreground_procedure(merge_item):
  if merge_item is not None:
    _set_buttons_for_command_item_sensitive(merge_item, False)

    merge_item.command['arguments/last_enabled_value'].gui.set_visible(False)


def _add_not_background_foreground_condition(item, condition_list):
  condition_orig_name_mapping = {
    'insert_background_for_layers': 'not_background',
    'insert_foreground_for_layers': 'not_foreground',
  }

  if item.command['orig_name'].value not in condition_orig_name_mapping:
    return None

  condition_name = condition_orig_name_mapping[item.command['orig_name'].value]

  condition_item = condition_list.add_item(
    builtin_conditions.BUILTIN_CONDITIONS[condition_name])

  return condition_item


def _set_up_not_background_foreground_condition(item, condition_item):
  if condition_item is None:
    return

  def _on_insert_background_foreground_color_tag_changed(color_tag_setting):
    condition_item.command['arguments/color_tag'].set_value(color_tag_setting.value)

  if condition_item is not None:
    _set_buttons_for_command_item_sensitive(condition_item, False)

  condition_item.command['arguments/color_tag'].gui.set_visible(False)
  condition_item.command['arguments/last_enabled_value'].gui.set_visible(False)

  item.command['arguments/color_tag'].connect_event(
    'value-changed', _on_insert_background_foreground_color_tag_changed)
  _on_insert_background_foreground_color_tag_changed(item.command['arguments/color_tag'])


def _on_insert_background_foreground_procedure_enabled_changed(
      enabled_setting,
      merge_procedure,
      condition,
):
  if not enabled_setting.value:
    if merge_procedure is not None:
      merge_procedure['arguments/last_enabled_value'].set_value(merge_procedure['enabled'].value)
      merge_procedure['enabled'].set_value(False)

    if condition is not None:
      condition['arguments/last_enabled_value'].set_value(condition['enabled'].value)
      condition['enabled'].set_value(False)
  else:
    if merge_procedure is not None:
      merge_procedure['enabled'].set_value(merge_procedure['arguments/last_enabled_value'].value)
    if condition is not None:
      condition['enabled'].set_value(condition['arguments/last_enabled_value'].value)

  if merge_procedure is not None:
    merge_procedure['enabled'].gui.set_sensitive(enabled_setting.value)
  if condition is not None:
    condition['enabled'].gui.set_sensitive(enabled_setting.value)


def _on_insert_background_foreground_procedure_removed(
      procedure_list,
      removed_item,
      insert_back_foreground_item,
      merge_item,
      condition_list,
      condition_item):
  if removed_item == insert_back_foreground_item:
    if merge_item is not None and merge_item in procedure_list.items:
      procedure_list.remove_item(merge_item)
    if condition_item is not None and condition_item in condition_list.items:
      condition_list.remove_item(condition_item)


def _handle_crop_procedure_item_added(item):
  _set_display_name_for_crop_procedure(
    item.command['arguments/crop_mode'],
    item.command)

  item.command['arguments/crop_mode'].connect_event(
    'value-changed',
    _set_display_name_for_crop_procedure,
    item.command)


def _set_display_name_for_crop_procedure(crop_mode_setting, crop_procedure):
  if crop_mode_setting.value == builtin_procedures.CropModes.REMOVE_EMPTY_BORDERS:
    crop_procedure['display_name'].set_value(_('Crop to remove empty borders'))
  else:
    if crop_mode_setting.value in crop_mode_setting.items_display_names:
      crop_procedure['display_name'].set_value(
        crop_mode_setting.items_display_names[crop_mode_setting.value])


def _handle_resize_canvas_procedure_item_added(item):
  _set_display_name_for_resize_canvas_procedure(
    item.command['arguments/resize_mode'],
    item.command)

  item.command['arguments/resize_mode'].connect_event(
    'value-changed',
    _set_display_name_for_resize_canvas_procedure,
    item.command)


def _set_display_name_for_resize_canvas_procedure(
      resize_mode_setting, resize_canvas_procedure):
  if resize_mode_setting.value in resize_mode_setting.items_display_names:
    resize_canvas_procedure['display_name'].set_value(
      resize_mode_setting.items_display_names[resize_mode_setting.value])


def _handle_rename_procedure_item_added(item):
  _set_display_name_for_rename_procedure(
    item.command['arguments/pattern'],
    item.command)

  item.command['arguments/pattern'].connect_event(
    'value-changed',
    _set_display_name_for_rename_procedure,
    item.command)

  if item.command['orig_name'].value == 'rename_for_edit_and_save_images':
    item.command['arguments/rename_only_new_images'].connect_event(
      'value-changed',
      _set_display_name_for_rename_procedure_for_rename_only_new_images,
      item.command['arguments/pattern'],
      item.command)


def _set_display_name_for_rename_procedure(pattern_setting, rename_procedure):
  if rename_procedure['orig_name'].value != 'rename_for_edit_and_save_images':
    rename_procedure['display_name'].set_value(_('Rename to "{}"').format(pattern_setting.value))
  else:
    if rename_procedure['arguments/rename_only_new_images'].value:
      rename_procedure['display_name'].set_value(
        _('Rename new images to "{}"').format(pattern_setting.value))
    else:
      rename_procedure['display_name'].set_value(_('Rename to "{}"').format(pattern_setting.value))


def _set_display_name_for_rename_procedure_for_rename_only_new_images(
      _rename_only_new_images_setting,
      pattern_setting,
      rename_procedure,
):
  _set_display_name_for_rename_procedure(pattern_setting, rename_procedure)


def _handle_export_procedure_item_added(item):
  pg.config.SETTINGS_FOR_WHICH_TO_SUPPRESS_WARNINGS_ON_INVALID_VALUE.add(
    item.command['arguments/file_extension'])

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

  _set_display_name_for_export_procedure(
    item.command['arguments/file_extension'],
    item.command)

  item.command['arguments/file_extension'].connect_event(
    'value-changed',
    _set_display_name_for_export_procedure,
    item.command)


def _set_display_name_for_export_procedure(file_extension_setting, export_procedure):
  file_extension = file_extension_setting.value.upper() if file_extension_setting.value else ''

  export_procedure_name = None
  if export_procedure['orig_name'].value in [
        'export_for_edit_and_save_images', 'export_for_edit_layers']:
    export_procedure_name = _('Export as {}')
  elif export_procedure['orig_name'].value.startswith('export_for_'):
    export_procedure_name = _('Also export as {}')

  if export_procedure_name is not None:
    export_procedure['display_name'].set_value(export_procedure_name.format(file_extension))


def _handle_export_procedure_item_added_for_export_mode(item, settings):
  _copy_setting_values_from_default_export_procedure(settings['main'], item.command)


def _copy_setting_values_from_default_export_procedure(main_settings, export_procedure):
  if main_settings['output_directory'].value:
    export_procedure['arguments/output_directory'].set_value(
      main_settings['output_directory'].value)

  export_procedure['arguments/file_extension'].set_value(main_settings['file_extension'].value)

  for setting in main_settings['export']:
    export_procedure[f'arguments/{setting.name}'].set_value(setting.value)


def _set_buttons_for_command_item_sensitive(item, sensitive):
  item.button_remove.set_sensitive(sensitive)


def _handle_save_procedure_item_added(item):
  _set_display_name_for_save_procedure(
    item.command['arguments/save_existing_image_to_its_original_location'],
    item.command['arguments/output_directory'],
    item.command,
  )

  item.command['arguments/save_existing_image_to_its_original_location'].connect_event(
    'value-changed',
    _set_display_name_for_save_procedure,
    item.command['arguments/output_directory'],
    item.command,
  )

  item.command['arguments/output_directory'].connect_event(
    'value-changed',
    _set_display_name_for_save_procedure_for_output_directory,
    item.command['arguments/save_existing_image_to_its_original_location'],
    item.command,
  )


def _set_display_name_for_save_procedure(
      save_existing_image_to_its_original_location_setting,
      output_directory_setting,
      save_procedure,
):
  if (output_directory_setting.value is not None
      and output_directory_setting.value.get_path() is not None):
    output_dirname = os.path.basename(output_directory_setting.value.get_path())

    if save_existing_image_to_its_original_location_setting.value:
      save_procedure['display_name'].set_value(
        _('Save (imported images to "{}")').format(output_dirname))
    else:
      save_procedure['display_name'].set_value(_('Save to "{}"').format(output_dirname))
  else:
      save_procedure['display_name'].set_value(_('Save'))


def _set_display_name_for_save_procedure_for_output_directory(
      output_directory_setting,
      save_existing_image_to_its_original_location_setting,
      save_procedure,
):
  _set_display_name_for_save_procedure(
    save_existing_image_to_its_original_location_setting,
    output_directory_setting,
    save_procedure,
  )


def _reorder_procedure_before_first_save_procedure(
      procedure_list: command_list_.CommandList,
      item,
):
  first_save_procedure_position = next(
    iter(
      index for index, item_ in enumerate(procedure_list.items)
      if item_.command['orig_name'].value == 'save'),
    None)

  if first_save_procedure_position is not None:
    procedure_list.reorder_item(item, first_save_procedure_position)


def _on_condition_item_added(_condition_list, item, _settings):
  if item.command['orig_name'].value == 'matching_text':
    _handle_matching_text_condition_item_added(item)


def _set_up_existing_matching_text_conditions(condition_list: command_list_.CommandList):
  for item in condition_list.items:
    if item.command['orig_name'].value == 'matching_text':
      _handle_matching_text_condition_item_added(item)


def _handle_matching_text_condition_item_added(item):
  _set_display_name_for_matching_text_condition(
    item.command['arguments/match_mode'],
    item.command['arguments/text'],
    item.command['arguments/ignore_case_sensitivity'],
    item.command)

  item.command['arguments/match_mode'].connect_event(
    'value-changed',
    _set_display_name_for_matching_text_condition,
    item.command['arguments/text'],
    item.command['arguments/ignore_case_sensitivity'],
    item.command)

  item.command['arguments/text'].connect_event(
    'value-changed',
    lambda text_setting, match_mode_setting, ignore_case_sensitivity_setting, condition: (
      _set_display_name_for_matching_text_condition(
        match_mode_setting, text_setting, ignore_case_sensitivity_setting, condition)),
    item.command['arguments/match_mode'],
    item.command['arguments/ignore_case_sensitivity'],
    item.command)

  item.command['arguments/ignore_case_sensitivity'].connect_event(
    'value-changed',
    lambda ignore_case_sensitivity_setting, match_mode_setting, text_setting, condition: (
      _set_display_name_for_matching_text_condition(
        match_mode_setting, text_setting, ignore_case_sensitivity_setting, condition)),
    item.command['arguments/match_mode'],
    item.command['arguments/text'],
    item.command)


def _set_display_name_for_matching_text_condition(
      match_mode_setting, text_setting, ignore_case_sensitivity_setting, condition):
  display_name = None

  if match_mode_setting.value == builtin_conditions.MatchModes.STARTS_WITH:
    if text_setting.value:
      display_name = _('Starting with "{}"').format(text_setting.value)
    else:
      display_name = _('Starting with any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.DOES_NOT_START_WITH:
    if text_setting.value:
      display_name = _('Not starting with "{}"').format(text_setting.value)
    else:
      display_name = _('Not starting with any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.CONTAINS:
    if text_setting.value:
      display_name = _('Containing "{}"').format(text_setting.value)
    else:
      display_name = _('Containing any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.DOES_NOT_CONTAIN:
    if text_setting.value:
      display_name = _('Not containing "{}"').format(text_setting.value)
    else:
      display_name = _('Not containing any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.ENDS_WITH:
    if text_setting.value:
      display_name = _('Ending with "{}"').format(text_setting.value)
    else:
      display_name = _('Ending with any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.DOES_NOT_END_WITH:
    if text_setting.value:
      display_name = _('Not ending with "{}"').format(text_setting.value)
    else:
      display_name = _('Not ending with any text')
  elif match_mode_setting.value == builtin_conditions.MatchModes.REGEX:
    display_name = _('Matching pattern "{}"').format(text_setting.value)

  if display_name is not None:
    if ignore_case_sensitivity_setting.value:
      # FOR TRANSLATORS: Think of "case-insensitive matching" when translating this
      display_name += _(' (case-insensitive)')

    condition['display_name'].set_value(display_name)
