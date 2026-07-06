from src import setting_additional

from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  actions_and_arguments_to_show_percent = {
    'crop_for_images': [
      'crop_from_position_width', 'crop_from_position_height',
      'crop_to_area_width', 'crop_to_area_height'],
    'crop_for_layers': [
      'crop_from_position_width', 'crop_from_position_height',
      'crop_to_area_width', 'crop_to_area_height'],
    'insert_overlay_for_images': ['size'],
    'insert_overlay_for_layers': ['size'],
    'resize_canvas': [
      'resize_from_position_width', 'resize_from_position_height',
      'resize_to_area_width', 'resize_to_area_height'],
    'scale_for_images': ['new_width', 'new_height'],
    'scale_for_layers': ['new_width', 'new_height'],
  }

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        action_name = orig_name_setting_dict['value']

        for argument_dict in arguments_list:
          if argument_dict['type'] == 'dimension':
            argument_dict.pop('percent_placeholder_names', None)

            for key in ['value', 'default_value']:
              if key in argument_dict:
                if 'unit' in argument_dict[key] and argument_dict[key]['unit'] in ['%', 'percent']:
                  argument_dict[key]['unit'] = (
                    setting_additional.DimensionSetting.CUSTOM_PERCENT_SYMBOL)

                if action_name in actions_and_arguments_to_show_percent:
                  if argument_dict['name'] in actions_and_arguments_to_show_percent[action_name]:
                    argument_dict['show_percent'] = True
