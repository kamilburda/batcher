from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if orig_name_setting_dict['default_value'] == 'scale' and arguments_list is not None:
          arguments_list.extend([
            {
              'type': 'bool',
              'name': 'scale_to_fit',
              'default_value': False,
              'display_name': 'Scale to fit',
              'gui_type': 'check_button',
              'value': False,
            },
            {
              'type': 'bool',
              'name': 'keep_aspect_ratio',
              'default_value': False,
              'display_name': 'Keep aspect ratio',
              'gui_type': 'check_button',
              'value': False,
            },
            {
              'type': 'choice',
              'default_value': 'width',
              'name': 'dimension_to_keep',
              'items': [
                ('width', 'Width'),
                ('height', 'Height'),
              ],
              'display_name': 'Dimension to keep',
              'value': 'width',
            },
          ])
