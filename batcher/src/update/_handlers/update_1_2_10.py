from src import builtin_actions
from src import placeholders as placeholders_
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
    _update_main_settings_moved_to_preferences(main_settings_list)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        origin_setting_dict, _index = update_utils_.get_child_setting(action_list, 'origin')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        _update_dimension_arguments(
          arguments_list, orig_name_setting_dict['value'], actions_and_arguments_to_show_percent)

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_update_arguments(arguments_list)

        if (orig_name_setting_dict['value'].startswith('insert_overlay_for_')
            and arguments_list is not None):
          _update_opacity_argument(arguments_list)

        if (orig_name_setting_dict['value'] in ['brightness_contrast', 'levels', 'curves']
            and arguments_list is not None):
          _update_opacity_argument(arguments_list)

        if origin_setting_dict['value'] == 'gegl' and arguments_list is not None:
          _update_opacity_argument(arguments_list, opacity_argument_name='opacity-')

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _update_gui_settings_moved_to_preferences(gui_settings_list)


def _update_main_settings_moved_to_preferences(group_list):
  setting_dict, _index = update_utils_.get_child_setting(group_list, 'continue_on_error')

  if setting_dict is not None:
    setting_dict['display_name'] = _('Continue on Error')
    if 'gui_type' in setting_dict:
      del setting_dict['gui_type']


def _update_gui_settings_moved_to_preferences(group_list):
  setting_dict, _index = update_utils_.get_child_setting(group_list, 'auto_close')

  if setting_dict is not None:
    setting_dict['display_name'] = _('Close when done')
    if 'gui_type' in setting_dict:
      del setting_dict['gui_type']

  setting_dict, _index = update_utils_.get_child_setting(group_list, 'keep_inputs')

  if setting_dict is not None:
    setting_dict['display_name'] = _('Keep input images')
    if 'gui_type' in setting_dict:
      del setting_dict['gui_type']

  setting_dict, _index = update_utils_.get_child_setting(group_list, 'show_quick_settings')

  if setting_dict is not None:
    setting_dict['display_name'] = _('Display dialog for quick export')
    if 'gui_type' in setting_dict:
      del setting_dict['gui_type']


def _update_dimension_arguments(arguments_list, action_name, actions_and_arguments_to_show_percent):
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


def _scale_update_arguments(arguments_list):
  argument_dict, _index = update_utils_.get_child_setting(arguments_list, 'scale_condition')

  if argument_dict is None:
    arguments_list.append(
      {
        'type': 'choice',
        'name': 'scale_condition',
        'value': builtin_actions.ScaleConditions.ALWAYS,
        'default_value': builtin_actions.ScaleConditions.ALWAYS,
        'items': [
          (builtin_actions.ScaleConditions.ALWAYS, _('Always')),
          (builtin_actions.ScaleConditions.SMALLER, _('Smaller than new dimensions')),
          (builtin_actions.ScaleConditions.LARGER, _('Larger than new dimensions')),
          (builtin_actions.ScaleConditions.SMALLER_THAN_CUSTOM, _('Only if smaller than...')),
          (builtin_actions.ScaleConditions.LARGER_THAN_CUSTOM, _('Only if larger than...')),
        ],
        'display_name': _('When to scale'),
      },
    )

  argument_dict, _index = update_utils_.get_child_setting(arguments_list, 'scale_condition_width')

  if argument_dict is None:
    arguments_list.append(
      {
        'type': 'dimension',
        'name': 'scale_condition_width',
        'value': {
          'pixel_value': 1920.0,
          'unit': 'px',
          'percent_object': 'current_image',
          'percent_property': {
            placeholders_.ALL_IMAGE_PLACEHOLDERS: 'width',
            placeholders_.ALL_LAYER_PLACEHOLDERS: 'width',
          },
        },
        'default_value': {
          'pixel_value': 1920.0,
          'unit': 'px',
          'percent_object': 'current_image',
          'percent_property': {
            placeholders_.ALL_IMAGE_PLACEHOLDERS: 'width',
            placeholders_.ALL_LAYER_PLACEHOLDERS: 'width',
          },
        },
        'min_value': 0.0,
        'display_name': _('Custom width'),
      },
    )

  argument_dict, _index = update_utils_.get_child_setting(arguments_list, 'scale_condition_height')

  if argument_dict is None:
    arguments_list.append(
      {
        'type': 'dimension',
        'name': 'scale_condition_height',
        'value': {
          'pixel_value': 1080.0,
          'unit': 'px',
          'percent_object': 'current_image',
          'percent_property': {
            placeholders_.ALL_IMAGE_PLACEHOLDERS: 'height',
            placeholders_.ALL_LAYER_PLACEHOLDERS: 'height',
          },
        },
        'default_value': {
          'pixel_value': 1080.0,
          'unit': 'px',
          'percent_object': 'current_image',
          'percent_property': {
            placeholders_.ALL_IMAGE_PLACEHOLDERS: 'height',
            placeholders_.ALL_LAYER_PLACEHOLDERS: 'height',
          },
        },
        'min_value': 0.0,
        'display_name': _('Custom height'),
      },
    )


def _update_opacity_argument(arguments_list, opacity_argument_name='opacity'):
  argument_dict, _index = update_utils_.get_child_setting(arguments_list, opacity_argument_name)

  if argument_dict is None:
    return

  if argument_dict['max_value'] == 100.0:
    if 'value' in argument_dict:
      argument_dict['value'] = argument_dict['value'] / 100.0

    argument_dict['default_value'] = 1.0
    argument_dict['min_value'] = 0.0
    argument_dict['max_value'] = 1.0
    argument_dict['gui_type_kwargs'] = {
      'factor': 100.0,
      'digits': 1,
    }
  else:
    argument_dict['gui_type_kwargs'] = {
      'factor': 100.0,
      'digits': 1,
    }
