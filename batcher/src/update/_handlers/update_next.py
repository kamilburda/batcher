from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_change_show_display_name_to_gui_kwargs(arguments_list)


def _scale_change_show_display_name_to_gui_kwargs(arguments_list):
  del arguments_list[7]['show_display_name']
  arguments_list[7]['gui_kwargs'] = {'show_display_name': False}
