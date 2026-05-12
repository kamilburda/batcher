from .. import _common as update_common_
from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    export_settings_list, _index = update_utils_.get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      _export_replace_merge_visible_layers_and_rasterize(export_settings_list)

    if actions_list is not None:
      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        update_common_.update_dimension_arguments(arguments_list)

        if (orig_name_setting_dict['value'].startswith('export_for_')
            and arguments_list is not None):
          _export_replace_merge_visible_layers_and_rasterize(arguments_list)

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_update_arguments(arguments_list)

        if (orig_name_setting_dict['value'].startswith('rotate_for_')
            and arguments_list is not None):
          _rotate_add_resize_to_image_size_argument(arguments_list)


def _export_replace_merge_visible_layers_and_rasterize(export_settings_list):
  setting_dict, merge_visible_layers_and_rasterize_index = update_utils_.get_child_setting(
    export_settings_list, 'merge_visible_layers_and_rasterize')

  # We can obtain this argument even now (i.e. before `pop()`) as it is
  # placed before `merge_visible_layers_and_rasterize` at this point.
  single_image_name_pattern_dict, single_image_name_pattern_index = update_utils_.get_child_setting(
    export_settings_list, 'single_image_name_pattern')

  if setting_dict is not None and single_image_name_pattern_dict is not None:
    export_settings_list.pop(merge_visible_layers_and_rasterize_index)

    new_index = single_image_name_pattern_index + 1

    export_settings_list.insert(
      new_index,
      {
        'type': 'color',
        'name': 'background_color_for_flatten',
        'default_value': [1.0, 1.0, 1.0, 1.0],
        'value': [1.0, 1.0, 1.0, 1.0],
        'has_alpha': False,
        'display_name': _('Background color'),
      },
    )
    export_settings_list.insert(
      new_index,
      {
        'type': 'choice',
        'name': 'layer_handling',
        'default_value': 'merge_and_add_alpha',
        'value': 'merge_and_add_alpha' if setting_dict['value'] else 'keep_layers',
        'items': [
          ('keep_layers', _('Keep layers')),
          ('merge_and_add_alpha', _('Merge and add alpha')),
          ('merge_and_remove_alpha', _('Merge and remove alpha')),
        ],
        'display_name': _('Layer handling'),
      },
    )


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
