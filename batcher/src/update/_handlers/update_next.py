from .. import _utils as update_utils_

from src import setting_additional


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    export_settings_list, _index = update_utils_.get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      _update_file_format_export_options_setting(export_settings_list)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_change_show_display_name_to_gui_kwargs(arguments_list)

        if (orig_name_setting_dict['value'].startswith('export_for_')
            and arguments_list is not None):
          _update_file_format_export_options_setting(arguments_list)

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  _change_gui_type_for_show_original_item_names(gui_settings_list)


def _update_export_procedure(export_settings_list):
  _update_file_format_export_options_setting(export_settings_list)
  _add_rotate_flip_image_based_on_exif_metadata_argument(export_settings_list)


def _update_file_format_export_options_setting(export_settings_list):
  file_format_export_options_dict, _index = update_utils_.get_child_setting(
    export_settings_list, 'file_format_export_options')

  if file_format_export_options_dict is not None:
    _change_active_file_format_to_dict(file_format_export_options_dict)
    _remove_initial_file_format_argument(file_format_export_options_dict)


def _add_rotate_flip_image_based_on_exif_metadata_argument(export_settings_list):
  setting_dict, _index = update_utils_.get_child_setting(
    export_settings_list, 'rotate_flip_image_based_on_exif_metadata')

  if setting_dict is not None:
    return

  export_settings_list.append({
    'type': 'bool',
    'name': 'rotate_flip_image_based_on_exif_metadata',
    'default_value': True,
    'value': True,
    'display_name': _('Rotate and flip image based on Exif metadata'),
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


def _scale_change_show_display_name_to_gui_kwargs(arguments_list):
  if 'show_display_name' in arguments_list[7]:
    del arguments_list[7]['show_display_name']
    arguments_list[7]['gui_kwargs'] = {'show_display_name': False}


def _change_gui_type_for_show_original_item_names(gui_settings_list):
  show_original_item_names_dict, _index = update_utils_.get_child_setting(
    gui_settings_list, 'show_original_item_names')

  if show_original_item_names_dict is not None:
    show_original_item_names_dict['gui_type'] = 'check_menu_item'
