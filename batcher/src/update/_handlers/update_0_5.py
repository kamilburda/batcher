from src import setting_additional as setting_additional_
from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    file_extension_dict, _index = update_utils_.get_child_setting(
      main_settings_list, 'file_extension')
    if file_extension_dict is not None:
      file_extension_dict['gui_type'] = None

    output_directory_dict, _index = update_utils_.get_child_setting(
      main_settings_list, 'output_directory')
    if output_directory_dict is not None:
      output_directory_dict['type'] = 'dirpath'
      output_directory_dict['gui_type'] = 'folder_chooser_button'
      if 'auto_update_gui_to_setting' in output_directory_dict:
        del output_directory_dict['auto_update_gui_to_setting']

    name_pattern_dict, _index = update_utils_.get_child_setting(main_settings_list, 'name_pattern')
    if name_pattern_dict is not None and 'auto_update_gui_to_setting' in name_pattern_dict:
      del name_pattern_dict['auto_update_gui_to_setting']

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')

    if actions_list is None:
      return

    for action_dict in actions_list:
      action_list = action_dict['settings']

      orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')

      arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

      if arguments_list is not None:
        for argument_dict in arguments_list:
          if 'gui_type' in argument_dict and argument_dict['gui_type'] == 'check_button_no_text':
            argument_dict['gui_type'] = 'check_button'

          if argument_dict['name'] == 'file_extension':
            argument_dict['auto_update_gui_to_setting'] = False

      if orig_name_setting_dict['default_value'] == 'export' and arguments_list is not None:
        # We retain `name` and only modify `orig_name` as only the latter is
        # used in the code to check if an action is an export action.
        if EXPORT_LAYERS_GROUP in procedure_groups:
          orig_name_setting_dict['value'] = 'export_for_export_layers'
          orig_name_setting_dict['default_value'] = 'export_for_export_layers'
        elif EDIT_LAYERS_GROUP in procedure_groups:
          orig_name_setting_dict['value'] = 'export_for_edit_layers'
          orig_name_setting_dict['default_value'] = 'export_for_edit_layers'

        del arguments_list[-1]

        arguments_list.insert(
          2,
          {
            'type': 'choice',
            'name': 'overwrite_mode',
            'default_value': 'ask',
            'value': 6,
            'items': [
              ('ask', 'Ask', 6),
              ('replace', 'Replace', 0),
              ('skip', 'Skip', 1),
              ('rename_new', 'Rename new file', 2),
              ('rename_existing', 'Rename existing file', 3)],
            'display_name': 'If a file already exists:',
          })

        arguments_list.insert(
          2,
          {
            'type': 'file_format_options',
            'name': 'file_format_export_options',
            'default_value': {
              setting_additional_.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY: 'png'},
            'value': {
              setting_additional_.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY: 'png'},
            'import_or_export': 'export',
            'initial_file_format': 'png',
            'gui_type': 'file_format_options',
            'display_name': 'File format options'
          })

        arguments_list.insert(
          2,
          {
            'type': 'choice',
            'name': 'file_format_mode',
            'default_value': 'use_explicit_values',
            'value': 1,
            'items': [
              ('use_native_plugin_values', 'Interactively', 0),
              ('use_explicit_values', 'Use options below', 1)],
            'display_name': 'How to adjust file format options:',
            'description': (
              'Native dialogs usually allow you to adjust more options such as image metadata,'
              ' while adjusting options in place is more convenient as no extra dialog is displayed'
              ' before the export.'),
            'gui_type': 'radio_button_box',
          })

      if (orig_name_setting_dict['default_value'] in ['insert_background', 'insert_foreground']
          and arguments_list is not None):
        for argument_dict in arguments_list:
          if argument_dict['type'] == 'color_tag':
            argument_dict['type'] = 'enum'
            argument_dict['enum_type'] = 'GimpColorTag'
            argument_dict['excluded_values'] = [0]

      if (orig_name_setting_dict['default_value'] in ['merge_background', 'merge_foreground']
          and arguments_list is not None):
        for argument_dict in arguments_list:
          if argument_dict['name'] == 'merge_type':
            argument_dict['excluded_values'] = [3]

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'constraints')

    if conditions_list is None:
      return

    for condition_dict in conditions_list:
      condition_list = condition_dict['settings']

      orig_name_setting_dict, _index = update_utils_.get_child_setting(condition_list, 'orig_name')

      arguments_list, _index = update_utils_.get_child_group_list(condition_list, 'arguments')

      if (orig_name_setting_dict['default_value'] in ['not_background', 'not_foreground']
          and arguments_list is not None):
        for argument_dict in arguments_list:
          if argument_dict['type'] == 'color_tag':
            argument_dict['type'] = 'enum'
            argument_dict['enum_type'] = 'GimpColorTag'
            argument_dict['excluded_values'] = [0]

      if (orig_name_setting_dict['default_value'] in ['with_color_tags', 'without_color_tags']
          and arguments_list is not None):
        for argument_dict in arguments_list:
          if argument_dict['element_type'] == 'color_tag':
            argument_dict['element_type'] = 'enum'
            argument_dict['element_enum_type'] = 'GimpColorTag'
            argument_dict['element_excluded_values'] = [0]
            argument_dict['element_default_value'] = [1]
