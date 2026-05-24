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

        if (orig_name_setting_dict['value'].startswith('insert_overlay_for_')
            and arguments_list is not None):
          _insert_overlay_add_tags(arguments_list)

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'conditions')
    if conditions_list is not None:
      for condition_dict in conditions_list:
        condition_list = condition_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(
          condition_list, 'orig_name')

        if orig_name_setting_dict['value'] == 'without_color_tag':
          _without_color_tag_add_tags(condition_dict)


def _insert_overlay_add_tags(arguments_list):
  for argument_name in ['tagged_items', 'condition_name']:
    setting_dict, _index = update_utils_.get_child_setting(arguments_list, argument_name)

    if setting_dict is not None:
      if 'tags' not in setting_dict:
        setting_dict['tags'] = []

      if 'use_default_on_duplicate' not in setting_dict['tags']:
        setting_dict['tags'].append('use_default_on_duplicate')


def _without_color_tag_add_tags(condition_dict):
  if 'tags' not in condition_dict:
    condition_dict['tags'] = []

  if 'do_not_duplicate' not in condition_dict['tags']:
    condition_dict['tags'].append('do_not_duplicate')

  if 'do_not_remove' not in condition_dict['tags']:
    condition_dict['tags'].append('do_not_remove')
