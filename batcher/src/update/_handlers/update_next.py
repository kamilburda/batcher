from .. import _common as update_common_
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

        update_common_.update_dimension_arguments(arguments_list)

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_update_arguments(arguments_list)

        if (orig_name_setting_dict['value'].startswith('rotate_for_')
            and arguments_list is not None):
          _rotate_add_resize_to_image_size_argument(arguments_list)


def _scale_update_arguments(arguments_list):
  if arguments_list[3]['name'] == 'aspect_ratio':
    scale_mode_argument = arguments_list.pop(3)
    scale_mode_argument['name'] = 'scale_mode'

    arguments_list.insert(1, scale_mode_argument)


def _rotate_add_resize_to_image_size_argument(arguments_list):
  argument_dict, index = update_utils_.get_child_setting(
    arguments_list, 'resize_image_to_fit')

  if argument_dict is None:
    arguments_list.insert(
      3,
      {
        'type': 'bool',
        'name': 'resize_image_to_fit',
        'default_value': True,
        # This is to maintain the previous behavior to avoid surprises for
        # users.
        'value': False,
        'display_name': _('Resize image to fit'),
      },
    )
