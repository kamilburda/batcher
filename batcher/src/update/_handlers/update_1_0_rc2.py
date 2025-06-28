import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    output_directory_dict, _index = update_utils_.get_child_setting(
      main_settings_list, 'output_directory')
    if output_directory_dict is not None:
      _update_filepath_or_dirpath_setting(output_directory_dict)

    export_settings_list, _index = update_utils_.get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      file_format_export_options_dict, _index = update_utils_.get_child_setting(
        export_settings_list, 'file_format_export_options')
      if file_format_export_options_dict is not None:
        for name, format_options in file_format_export_options_dict['value'].items():
          if name != '_active':
            _update_choice_arguments(format_options)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')
    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if (orig_name_setting_dict['default_value'] == 'insert_background_for_images'
            and arguments_list is not None):
          update_utils_.rename_setting(arguments_list, 'image_filepath', 'image_file')

        if (orig_name_setting_dict['default_value'] == 'insert_foreground_for_images'
            and arguments_list is not None):
          update_utils_.rename_setting(arguments_list, 'image_filepath', 'image_file')

        _update_choice_arguments(arguments_list)

        _update_file_arguments(arguments_list)

        _update_filepath_and_dirpath_arguments(arguments_list)

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'constraints')
    if conditions_list is not None:
      for condition_dict in conditions_list:
        condition_list = condition_dict['settings']

        arguments_list, _index = update_utils_.get_child_group_list(condition_list, 'arguments')

        _update_choice_arguments(arguments_list)

        _update_file_arguments(arguments_list)

        _update_filepath_and_dirpath_arguments(arguments_list)


def _update_choice_arguments(arguments_list):
  for argument_dict in arguments_list:
    if argument_dict['type'] == 'choice':
      _update_choice_setting(argument_dict)


def _update_choice_setting(setting_dict):
  if 'gui_type' in setting_dict and setting_dict['gui_type'] == 'choice_combo_box':
    setting_dict['gui_type'] = 'prop_choice_combo_box'


def _update_file_arguments(arguments_list):
  for argument_dict in arguments_list:
    if argument_dict['type'] == 'file':
      _update_file_setting(argument_dict)


def _update_file_setting(setting_dict):
  if 'gui_type' in setting_dict:
    setting_dict['gui_type'] = 'file_chooser'

  setting_dict['action'] = int(Gimp.FileChooserAction.ANY)

  raw_value = setting_dict['value']
  if isinstance(raw_value, str):
    new_raw_value = Gio.file_new_for_path(raw_value).get_uri()
  elif raw_value is None:
    new_raw_value = None
  else:
    new_raw_value = raw_value

  setting_dict['value'] = new_raw_value

  raw_default_value = setting_dict['default_value']
  if isinstance(raw_default_value, str):
    new_raw_default_value = Gio.file_new_for_path(raw_default_value).get_uri()
  elif raw_default_value is None:
    new_raw_default_value = None
  else:
    new_raw_default_value = raw_default_value

  setting_dict['default_value'] = new_raw_default_value


def _update_filepath_and_dirpath_arguments(arguments_list):
  for argument_dict in arguments_list:
    if argument_dict['type'] in ['filepath', 'dirpath']:
      _update_filepath_or_dirpath_setting(argument_dict)


def _update_filepath_or_dirpath_setting(setting_dict):
  setting_dict['type'] = 'file'

  if 'gui_type' in setting_dict:
    setting_dict['gui_type'] = 'file_chooser'

  if setting_dict['value'] is not None:
    setting_dict['value'] = Gio.file_new_for_path(setting_dict['value']).get_uri()

  if setting_dict['default_value'] is not None:
    setting_dict['default_value'] = Gio.file_new_for_path(setting_dict['default_value']).get_uri()

  if setting_dict['type'] == 'filepath':
    setting_dict['action'] = int(Gimp.FileChooserAction.OPEN)
  elif setting_dict['type'] == 'dirpath':
    setting_dict['action'] = int(Gimp.FileChooserAction.SELECT_FOLDER)
  else:
    setting_dict['action'] = int(Gimp.FileChooserAction.ANY)

  if 'nullable' in setting_dict:
    setting_dict['none_ok'] = setting_dict.pop('nullable')
