import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

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

        if orig_name_setting_dict['value'] in ['brightness_contrast', 'levels', 'curves']:
          _add_filter_args_to_color_action(arguments_list)


def _add_filter_args_to_color_action(arguments_list):
  argument_dict, index = update_utils_.get_child_setting(
    arguments_list, 'apply_non_destructively')

  if argument_dict is None:
    arguments_list.append({
      'type': 'bool',
      'name': 'apply_non_destructively',
      'default_value': False,
      'value': False,
      'display_name': _('Apply non-destructively'),
    })

  argument_dict, index = update_utils_.get_child_setting(
    arguments_list, 'blend_mode')

  if argument_dict is None:
    arguments_list.append({
      'type': 'enum',
      'name': 'blend_mode',
      'enum_type': Gimp.LayerMode,
      'default_value': Gimp.LayerMode.REPLACE,
      'value': Gimp.LayerMode.REPLACE,
      'display_name': _('Blend mode'),
    })

  argument_dict, index = update_utils_.get_child_setting(
    arguments_list, 'opacity')

  if argument_dict is None:
    arguments_list.append({
      'type': 'double',
      'name': 'opacity',
      'default_value': 100.0,
      'value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    })
