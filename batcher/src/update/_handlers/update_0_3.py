from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, settings, procedure_groups):
  if EXPORT_LAYERS_GROUP not in procedure_groups:
    return

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    _update_commands_to_0_3(main_settings_list, 'procedures')
    _update_commands_to_0_3(main_settings_list, 'constraints')

    setting_dict, _index = update_utils_.get_child_setting(main_settings_list, 'file_extension')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

    setting_dict, _index = update_utils_.get_child_setting(main_settings_list, 'output_directory')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

    setting_dict, _index = update_utils_.get_child_setting(main_settings_list, 'layer_name_pattern')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _setting, index = update_utils_.get_child_setting(gui_settings_list, 'show_more_settings')
    if index is not None:
      gui_settings_list.pop(index)

    gui_size_setting_list, _index = update_utils_.get_child_group_list(gui_settings_list, 'size')

    if gui_size_setting_list is not None:
      setting_dict, _index = update_utils_.get_child_setting(gui_size_setting_list, 'dialog_size')
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/dialog_size'].default_value
        setting_dict['default_value'] = settings['gui/size/dialog_size'].default_value

      setting_dict, _index = (
        update_utils_.get_child_setting(gui_size_setting_list, 'paned_outside_previews_position'))
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/paned_outside_previews_position'].default_value
        setting_dict['default_value'] = (
          settings['gui/size/paned_outside_previews_position'].default_value)

      setting_dict, _index = (
        update_utils_.get_child_setting(gui_size_setting_list, 'paned_between_previews_position'))
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/paned_between_previews_position'].default_value
        setting_dict['default_value'] = (
          settings['gui/size/paned_between_previews_position'].default_value)


def _update_commands_to_0_3(main_settings_list, command_type):
  commands_list, _index = update_utils_.get_child_group_list(main_settings_list, command_type)

  if commands_list is None:
    return

  for command_dict in commands_list:
    command_list = command_dict['settings']

    display_options_on_create_dict, _index = (
      update_utils_.get_child_setting(command_list, 'display_options_on_create'))
    if display_options_on_create_dict:
      display_options_on_create_dict['value'] = False
      display_options_on_create_dict['default_value'] = False

    more_options_list, _index = update_utils_.get_child_group_list(command_list, 'more_options')

    if more_options_list is None:
      more_options_dict = {
        'name': 'more_options',
        'setting_attributes': {
          'pdb_type': None,
        },
        'settings': [],
      }
      command_list.insert(-2, more_options_dict)

      more_options_list = more_options_dict['settings']

    enabled_for_previews_in_more_options_dict, _index = (
      update_utils_.get_child_setting(more_options_list, 'enabled_for_previews'))
    if enabled_for_previews_in_more_options_dict is None:
      enabled_for_previews_dict, index = update_utils_.get_child_setting(
        command_list, 'enabled_for_previews')
      if enabled_for_previews_dict is not None:
        command_list.pop(index)
        more_options_list.append(enabled_for_previews_dict)

    also_apply_to_parent_folders_in_more_options_dict, _index = (
      update_utils_.get_child_setting(more_options_list, 'also_apply_to_parent_folders'))
    if also_apply_to_parent_folders_in_more_options_dict is None:
      also_apply_to_parent_folders_dict, index = (
        update_utils_.get_child_setting(command_list, 'also_apply_to_parent_folders'))
      if also_apply_to_parent_folders_dict is not None:
        command_list.pop(index)
        more_options_list.append(also_apply_to_parent_folders_dict)
