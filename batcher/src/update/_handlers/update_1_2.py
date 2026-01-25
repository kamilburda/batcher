from .. import _utils as update_utils_

from src import builtin_actions
from src import setting_additional


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    _update_output_directory_setting(main_settings_list)

    export_settings_list, _index = update_utils_.get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      _update_export_procedure(export_settings_list)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      indexes_of_apply_opacity_from_group_layers_dict = []
      data_for_color_correction_dict = []
      data_for_rotate_and_flip_dict = []

      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if orig_name_setting_dict['value'] == 'apply_opacity_from_group_layers':
          indexes_of_apply_opacity_from_group_layers_dict.append(index)

        if (orig_name_setting_dict['value'] == 'color_correction'
            and arguments_list is not None):
          data_for_color_correction_dict.append((arguments_list, index))

        if (orig_name_setting_dict['value'].startswith('rotate_and_flip_for_')
            and arguments_list is not None):
          data_for_rotate_and_flip_dict.append(
            (arguments_list, index, orig_name_setting_dict))

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_change_show_display_name_to_gui_kwargs(arguments_list)

        if (orig_name_setting_dict['value'].startswith('export_for_')
            and arguments_list is not None):
          _update_export_procedure(arguments_list)
          _update_output_directory_setting(arguments_list)

        if (orig_name_setting_dict['value'] == 'save'
            and arguments_list is not None):
          _update_output_directory_setting(arguments_list)
          _save_replace_save_existing_image_to_its_original_location_argument(arguments_list)

      for index in indexes_of_apply_opacity_from_group_layers_dict:
        _replace_apply_opacity_from_group_layers_with_apply_group_layer_appearance(
          actions_list, index)

      num_added_actions = 0
      for arguments_list, index in data_for_color_correction_dict:
        num_added_actions += _color_correction_split_to_separate_actions(
          actions_list, arguments_list, index + num_added_actions)

      num_added_actions = 0
      for arguments_list, index, orig_name_setting_dict in data_for_rotate_and_flip_dict:
        num_added_actions += _rotate_and_flip_split_to_separate_actions(
          actions_list, arguments_list, index + num_added_actions, orig_name_setting_dict)

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  _change_gui_type_for_show_original_item_names(gui_settings_list)


def _update_output_directory_setting(group_list):
  output_directory_dict, _index = update_utils_.get_child_setting(group_list, 'output_directory')

  if output_directory_dict is not None and output_directory_dict['type'] == 'file':
    output_directory_dict['type'] = 'directory'
    output_directory_dict['default_value'] = None
    output_directory_dict.pop('action', None)
    output_directory_dict.pop('gui_type', None)
    output_directory_dict.pop('gui_type_kwargs', None)
    output_directory_dict.pop('none_ok', None)
    output_directory_dict.pop('set_default_if_not_exists', None)


def _update_export_procedure(export_settings_list):
  _update_file_format_export_options_setting(export_settings_list)
  _add_rotate_flip_image_based_on_exif_metadata_argument(export_settings_list)
  _add_merge_visible_layers_and_rasterize_argument(export_settings_list)


def _update_file_format_export_options_setting(export_settings_list):
  file_format_export_options_dict, _index = update_utils_.get_child_setting(
    export_settings_list, 'file_format_export_options')

  if file_format_export_options_dict is not None:
    _change_active_file_format_to_dict(file_format_export_options_dict)
    _remove_initial_file_format_argument(file_format_export_options_dict)


def _add_rotate_flip_image_based_on_exif_metadata_argument(export_settings_list):
  setting_dict, _index = update_utils_.get_child_setting(
    export_settings_list, 'rotate_flip_image_based_on_exif_metadata')

  if setting_dict is None:
    export_settings_list.append({
      'type': 'bool',
      'name': 'rotate_flip_image_based_on_exif_metadata',
      'default_value': True,
      'value': True,
      'display_name': _('Rotate or flip image based on Exif metadata'),
    })


def _add_merge_visible_layers_and_rasterize_argument(export_settings_list):
  setting_dict, _index = update_utils_.get_child_setting(
    export_settings_list, 'merge_visible_layers_and_rasterize')

  if setting_dict is None:
    export_settings_list.append({
      'type': 'bool',
      'name': 'merge_visible_layers_and_rasterize',
      'default_value': True,
      'value': True,
      'display_name': _('Merge visible layers and rasterize'),
    })


def _change_active_file_format_to_dict(file_format_export_options_dict):
  active_key = setting_additional.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY

  if ('value' in file_format_export_options_dict
      and file_format_export_options_dict['value']
      and active_key in file_format_export_options_dict['value']
      and not isinstance(file_format_export_options_dict['value'][active_key], (list, tuple))):
    file_format_export_options_dict['value'][active_key] = [
      file_format_export_options_dict['value'][active_key]]


def _remove_initial_file_format_argument(file_format_export_options_dict):
  if 'initial_file_format' in file_format_export_options_dict:
    del file_format_export_options_dict['initial_file_format']


def _replace_apply_opacity_from_group_layers_with_apply_group_layer_appearance(
      actions_list, index):
  update_utils_.remove_command_by_orig_names(actions_list, ['apply_opacity_from_group_layers'])

  apply_group_layer_appearance_group_dict = update_utils_.create_and_add_command(
    'apply_group_layer_appearance', actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  arguments_list, _index = update_utils_.get_child_group_list(
    apply_group_layer_appearance_group_dict['settings'], 'arguments')
  if arguments_list is not None:
    for argument_dict in arguments_list:
      if argument_dict['name'] in [
        'apply_filters',
        'apply_layer_modes',
        'apply_layer_masks',
        'apply_blend_space',
        'apply_composite_mode',
        'apply_composite_space',
      ]:
        argument_dict['value'] = False


def _color_correction_split_to_separate_actions(actions_list, arguments_list, index):
  update_utils_.remove_command_by_orig_names(actions_list, ['color_correction'])

  processed_index = index

  _add_brightness_contrast_action(actions_list, arguments_list, processed_index)

  if arguments_list[3]['value']:
    processed_index += 1
    _add_levels_action(actions_list, arguments_list, processed_index)

  if arguments_list[4]['value']:
    processed_index += 1
    _add_curves_action(actions_list, arguments_list, processed_index)

  return processed_index


def _add_brightness_contrast_action(actions_list, arguments_list, index):
  brightness_contrast_group_dict = update_utils_.create_and_add_command(
    'brightness_contrast', actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    brightness_contrast_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']

    new_brightness_dict = new_arguments_list[1]
    value = arguments_list[1]['value']
    processed_value = round(
      value * (new_brightness_dict['max_value'] - new_brightness_dict['min_value'])
      / 2
    )
    processed_value = max(processed_value, new_brightness_dict['min_value'])
    processed_value = min(processed_value, new_brightness_dict['max_value'])
    new_brightness_dict['value'] = processed_value

    new_contrast_dict = new_arguments_list[2]
    value = arguments_list[2]['value']
    processed_value = value - 1.0
    processed_value = round(
      processed_value * (new_contrast_dict['max_value'] - new_contrast_dict['min_value'])
      / 2
    )
    processed_value = max(processed_value, new_contrast_dict['min_value'])
    processed_value = min(processed_value, new_contrast_dict['max_value'])
    new_contrast_dict['value'] = processed_value

    new_arguments_list[3]['value'] = builtin_actions.BrightnessContrastFilters.GEGL


def _add_levels_action(actions_list, arguments_list, index):
  levels_group_dict = update_utils_.create_and_add_command(
    'levels', actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    levels_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']
    new_arguments_list[1]['value'] = arguments_list[3]['value']


def _add_curves_action(actions_list, arguments_list, index):
  levels_group_dict = update_utils_.create_and_add_command(
    'curves', actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    levels_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']
    new_arguments_list[1]['value'] = arguments_list[4]['value']


def _rotate_and_flip_split_to_separate_actions(
      actions_list,
      arguments_list,
      index,
      orig_name_setting_dict,
):
  update_utils_.remove_command_by_orig_names(
    actions_list, ['rotate_and_flip_for_images', 'rotate_and_flip_for_layers'])

  processed_index = index

  _add_rotate_action(actions_list, arguments_list, processed_index, orig_name_setting_dict)

  if arguments_list[8]['value']:
    processed_index += 1
    _add_flip_horizontally_action(
      actions_list, arguments_list, processed_index, orig_name_setting_dict)

  if arguments_list[9]['value']:
    processed_index += 1
    _add_flip_vertically_action(
      actions_list, arguments_list, processed_index, orig_name_setting_dict)

  return processed_index


def _add_rotate_action(actions_list, arguments_list, index, orig_name_setting_dict):
  if orig_name_setting_dict['value'].endswith('_for_images'):
    action_name = 'rotate_for_images'
  else:
    action_name = 'rotate_for_layers'

  rotate_group_dict = update_utils_.create_and_add_command(
    action_name, actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    rotate_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']

    if arguments_list[1]['value'] != 'none':
      new_arguments_list[1]['value'] = arguments_list[1]['value']
      new_arguments_list[2]['value'] = arguments_list[2]['value']
    else:
      new_arguments_list[1]['value'] = 'custom'
      new_arguments_list[2]['value'] = {
        'value': 0.0,
        'unit': 'degree',
      }

    new_arguments_list[3]['value'] = arguments_list[3]['value']
    new_arguments_list[4]['value'] = arguments_list[4]['value']
    new_arguments_list[5]['value'] = arguments_list[5]['value']
    new_arguments_list[6]['value'] = arguments_list[6]['value']
    new_arguments_list[7]['value'] = arguments_list[7]['value']


def _add_flip_horizontally_action(
      actions_list,
      arguments_list,
      index,
      orig_name_setting_dict,
):
  if orig_name_setting_dict['value'].endswith('_for_images'):
    action_name = 'flip_horizontally_for_images'
  else:
    action_name = 'flip_horizontally_for_layers'

  flip_group_dict = update_utils_.create_and_add_command(
    action_name, actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    flip_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']


def _add_flip_vertically_action(
      actions_list,
      arguments_list,
      index,
      orig_name_setting_dict,
):
  if orig_name_setting_dict['value'].endswith('_for_images'):
    action_name = 'flip_vertically_for_images'
  else:
    action_name = 'flip_vertically_for_layers'

  flip_group_dict = update_utils_.create_and_add_command(
    action_name, actions_list, builtin_actions.BUILTIN_ACTIONS, index,
  )

  new_arguments_list, _index = update_utils_.get_child_group_list(
    flip_group_dict['settings'], 'arguments')
  if new_arguments_list is not None:
    new_arguments_list[0]['value'] = arguments_list[0]['value']


def _scale_change_show_display_name_to_gui_kwargs(arguments_list):
  if 'show_display_name' in arguments_list[7]:
    del arguments_list[7]['show_display_name']
    arguments_list[7]['gui_kwargs'] = {'show_display_name': False}


def _change_gui_type_for_show_original_item_names(gui_settings_list):
  show_original_item_names_dict, _index = update_utils_.get_child_setting(
    gui_settings_list, 'show_original_item_names')

  if show_original_item_names_dict is not None:
    show_original_item_names_dict['gui_type'] = 'check_menu_item'


def _save_replace_save_existing_image_to_its_original_location_argument(argument_list):
  argument_dict, index = update_utils_.get_child_setting(
    argument_list, 'save_existing_image_to_its_original_location')

  if argument_dict is not None:
    argument_list.pop(index)

  argument_dict, index = update_utils_.get_child_setting(
    argument_list, 'output_directory_for_new_images')

  if argument_dict is None:
    argument_list.append({
      'type': 'directory',
      'name': 'output_directory_for_new_images',
      'default_value': 'special:///use_original_location',
      'value': 'special:///use_original_location',
      'display_name': _('Output folder for new images'),
      'procedure_groups': [],
    })
