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

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_update_arguments(arguments_list)


def _scale_update_arguments(arguments_list):
  if arguments_list[3]['name'] == 'aspect_ratio':
    scale_mode_argument = arguments_list.pop(3)
    scale_mode_argument['name'] = 'scale_mode'

    arguments_list.insert(1, scale_mode_argument)
