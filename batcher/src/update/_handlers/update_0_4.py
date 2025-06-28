from src import builtin_actions
from src import builtin_conditions
from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  if EXPORT_LAYERS_GROUP not in procedure_groups:
    return

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    update_utils_.remove_setting(main_settings_list, 'edit_mode')

    update_utils_.rename_setting(main_settings_list, 'layer_filename_pattern', 'name_pattern')
    update_utils_.set_setting_attribute_value(
      main_settings_list, 'name_pattern', 'type', 'name_pattern')

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')
    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'constraints')

    if actions_list is None or conditions_list is None:
      return

    _handle_background_foreground_commands(actions_list, conditions_list)

    for action_dict in actions_list:
      action_list = action_dict['settings']

      orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')

      arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

      if orig_name_setting_dict['default_value'] == 'export' and arguments_list is not None:
        arguments_list[3]['name'] = 'single_image_name_pattern'
        arguments_list[3]['type'] = 'name_pattern'
        arguments_list[3]['gui_type'] = 'name_pattern_entry'

      if orig_name_setting_dict['default_value'] == 'rename' and arguments_list is not None:
        orig_name_setting_dict['value'] = 'rename_for_export_layers'
        orig_name_setting_dict['default_value'] = 'rename_for_export_layers'

        arguments_list[0]['type'] = 'name_pattern'
        arguments_list[0]['gui_type'] = 'name_pattern_entry'

      if orig_name_setting_dict['default_value'] == 'remove_folder_structure':
        orig_name_setting_dict['value'] = 'remove_folder_structure_for_export_layers'
        orig_name_setting_dict['default_value'] = 'remove_folder_structure_for_export_layers'


def _handle_background_foreground_commands(actions_list, conditions_list):
  update_utils_.remove_command_by_orig_names(actions_list, ['merge_background', 'merge_foreground'])

  merge_action_mapping = {
    'insert_background': 'merge_background',
    'insert_foreground': 'merge_foreground',
  }
  action_names = {command_dict['name'] for command_dict in actions_list}
  action_display_names = {
    update_utils_.get_child_setting(command_dict['settings'], 'display_name')[0]['value']
    for command_dict in actions_list
    if update_utils_.get_child_setting(command_dict['settings'], 'display_name')[0] is not None
  }

  condition_mapping = {
    'insert_background': 'not_background',
    'insert_foreground': 'not_foreground',
  }
  condition_names = {command_dict['name'] for command_dict in conditions_list}
  condition_display_names = {
    update_utils_.get_child_setting(command_dict['settings'], 'display_name')[0]['value']
    for command_dict in conditions_list
    if update_utils_.get_child_setting(command_dict['settings'], 'display_name')[0] is not None
  }

  merge_group_dicts = []
  condition_group_dicts = []

  for action_dict in actions_list:
    action_list = action_dict['settings']
    orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')

    arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

    if (orig_name_setting_dict['default_value'] in ['insert_background', 'insert_foreground']
        and arguments_list is not None):
      arguments_list.append(
        {
          'type': 'string',
          'name': 'merge_action_name',
          'gui_type': None,
        })
      arguments_list.append(
        {
          'type': 'string',
          'name': 'constraint_name',
          'gui_type': None,
        })

      merge_action_name = merge_action_mapping[orig_name_setting_dict['default_value']]
      merge_group_dict = update_utils_.create_command_as_saved_dict(
        builtin_actions.BUILTIN_ACTIONS[merge_action_name])

      unique_merge_action_name = update_utils_.uniquify_command_name(
        merge_action_name, action_names)
      merge_group_dict['name'] = unique_merge_action_name
      arguments_list[-2]['value'] = unique_merge_action_name
      arguments_list[-2]['default_value'] = unique_merge_action_name

      merge_action_display_name_dict, _index = update_utils_.get_child_setting(
        merge_group_dict['settings'], 'display_name')
      if merge_action_display_name_dict is not None:
        unique_merge_action_display_name = update_utils_.uniquify_command_display_name(
          merge_action_display_name_dict['value'], action_display_names)
        merge_action_display_name_dict['value'] = unique_merge_action_display_name

      merge_group_dicts.append(merge_group_dict)

      condition_name = condition_mapping[orig_name_setting_dict['default_value']]
      condition_group_dict = update_utils_.create_command_as_saved_dict(
        builtin_conditions.BUILTIN_CONDITIONS[condition_name])

      unique_condition_name = update_utils_.uniquify_command_name(condition_name, condition_names)
      condition_group_dict['name'] = unique_condition_name
      arguments_list[-1]['value'] = unique_condition_name
      arguments_list[-1]['default_value'] = unique_condition_name

      condition_display_name_dict, _index = update_utils_.get_child_setting(
        condition_group_dict['settings'], 'display_name')
      if condition_display_name_dict is not None:
        unique_condition_display_name = update_utils_.uniquify_command_display_name(
          condition_display_name_dict['value'], condition_display_names)
        condition_display_name_dict['value'] = unique_condition_display_name

      condition_group_dicts.append(condition_group_dict)

  for merge_group_dict in merge_group_dicts:
    actions_list.append(merge_group_dict)

  for condition_group_dict in condition_group_dicts:
    conditions_list.append(condition_group_dict)
