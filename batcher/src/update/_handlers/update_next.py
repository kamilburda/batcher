from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if (orig_name_setting_dict['value'] == 'save'
            and arguments_list is not None):
          _fix_output_directory_for_new_images_argument(arguments_list)


def _fix_output_directory_for_new_images_argument(arguments_list):
  argument_dict, index = update_utils_.get_child_setting(
    arguments_list, 'output_directory_for_new_images')

  if argument_dict is not None:
    if argument_dict['default_value'] == 'special:///use_original_location':
      argument_dict['default_value'] = None

    if argument_dict['value'] == 'special:///use_original_location':
      argument_dict['value'] = None
