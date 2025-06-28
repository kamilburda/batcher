import re

from src import itemtree
from src.path import pattern as pattern_
from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _update_items_setting(
      gui_settings_list, 'image_preview_displayed_items', 'gimp_item_tree_items')
    _update_items_setting(
      gui_settings_list, 'name_preview_items_collapsed_state', 'gimp_item_tree_items')

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    # 'selected_items' may exist as a new setting. We need to remove that one
    # and instead rename the original so that the value of the original setting
    # is preserved on update.
    update_utils_.remove_setting(main_settings_list, 'selected_items')
    update_utils_.rename_setting(main_settings_list, 'selected_layers', 'selected_items')

    _update_items_setting(main_settings_list, 'selected_items', 'gimp_item_tree_items')

    _replace_layer_related_options_in_attributes_field_in_pattern(
      main_settings_list, 'name_pattern')

    export_settings_list, _index = update_utils_.get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      _update_export_mode_setting(export_settings_list)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        _replace_command_tags_with_plug_in_procedure_groups(action_dict)

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        gimp_item_setting_types = [
          'item', 'drawable', 'layer', 'group_layer', 'text_layer',
          'layer_mask', 'channel', 'selection', 'path']

        if orig_name_setting_dict['default_value'] == 'remove_folder_structure_for_export_layers':
          orig_name_setting_dict['value'] = 'remove_folder_structure'
          orig_name_setting_dict['default_value'] = 'remove_folder_structure'

        if (orig_name_setting_dict['default_value']
              in ['rename_for_export_layers', 'rename_for_edit_layers']
            and arguments_list is not None):
          _replace_layer_related_options_in_attributes_field_in_pattern(
            arguments_list, 'pattern')

        if (orig_name_setting_dict['default_value']
              in ['export_for_export_layers', 'export_for_edit_layers']
            and arguments_list is not None):
          _update_export_mode_setting(arguments_list)
          _replace_layer_related_options_in_attributes_field_in_pattern(
            arguments_list, 'single_image_name_pattern')

        if arguments_list is not None:
          for argument_dict in arguments_list:
            if argument_dict['type'] in gimp_item_setting_types:
              if argument_dict['value'] and len(argument_dict['value']) == 3:
                argument_dict['value'][1] = argument_dict['value'][1].split('/')
                argument_dict['value'].append(argument_dict['value'].pop(0))

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'constraints')
    if conditions_list is not None:
      update_utils_.remove_command_by_orig_names(conditions_list, ['selected_in_preview'])
      for condition_dict in conditions_list:
        _replace_command_tags_with_plug_in_procedure_groups(condition_dict)


def _replace_command_tags_with_plug_in_procedure_groups(command_dict):
  tags_new_name_mapping = {
    'convert': 'plug-in-batch-convert',
    'export_layers': 'plug-in-batch-export-layers',
    'edit_layers': 'plug-in-batch-edit-layers',
  }

  if 'tags' in command_dict:
    command_dict['tags'] = [
      tags_new_name_mapping[tag] if tag in tags_new_name_mapping else tag
      for tag in command_dict['tags']]


def _update_items_setting(settings_list, setting_name, new_type_name):
  setting_dict, _index = update_utils_.get_child_setting(settings_list, setting_name)

  setting_dict['type'] = new_type_name

  setting_dict.pop('default_value', None)

  new_value = []
  for image_filepath, items in setting_dict['value'].items():
    for item_data in items:
      if len(item_data) >= 2:
        new_value.append([
          item_data[0],
          item_data[1].split('/'),
          itemtree.FOLDER_KEY if len(item_data) >= 3 else '',
          image_filepath,
        ])

  setting_dict['value'] = new_value


def _update_export_mode_setting(settings_list):
  export_mode_dict, _index = update_utils_.get_child_setting(settings_list, 'export_mode')
  if export_mode_dict is not None:
    export_mode_dict['items'][0][0] = 'each_item'
    export_mode_dict['items'][1][0] = 'each_top_level_item_or_folder'
    export_mode_dict['items'][2][0] = 'single_image'

    export_mode_dict['default_value'] = 'each_item'
    if export_mode_dict['value'] == 'each_layer':
      export_mode_dict['value'] = 'each_item'
    elif export_mode_dict['value'] == 'each_top_level_layer_or_group':
      export_mode_dict['value'] = 'each_top_level_item_or_folder'
    elif export_mode_dict['value'] == 'entire_image_at_once':
      export_mode_dict['value'] = 'single_image'


def _replace_layer_related_options_in_attributes_field_in_pattern(settings_list, setting_name):
  setting_dict, _index = update_utils_.get_child_setting(settings_list, setting_name)
  if setting_dict is not None:
    setting_dict['value'] = _replace_field_arguments_in_pattern(
      setting_dict['value'],
      [
        ['attributes', '%w', '%lw'],
        ['attributes', '%h', '%lh'],
        ['attributes', '%x', '%lx'],
        ['attributes', '%y', '%ly'],
      ])


def _replace_field_arguments_in_pattern(
      pattern, field_regexes_arguments_and_replacements, as_lists=False):
  string_pattern = pattern_.StringPattern(
    pattern,
    fields={item[0]: lambda *args: None for item in field_regexes_arguments_and_replacements})

  processed_pattern_parts = []

  for part in string_pattern.pattern_parts:
    if isinstance(part, str):
      processed_pattern_parts.append(part)
    else:
      field_regex = part[0]
      new_arguments = []

      if len(part) > 1:
        if not as_lists:
          for argument in part[1]:
            new_argument = argument
            for item in field_regexes_arguments_and_replacements:
              if field_regex != item[0]:
                continue

              new_argument = re.sub(item[1], item[2], new_argument)

            new_arguments.append(new_argument)
        else:
          new_arguments = list(part[1])

          for item in field_regexes_arguments_and_replacements:
            if field_regex != item[0]:
              continue

            if len(item[1]) != len(part[1]):
              continue

            for i in range(len(item[1])):
              new_arguments[i] = re.sub(item[1][i], item[2][i], new_arguments[i])

            for i in range(len(item[1]), len(item[2])):
              new_arguments.append(item[2][i])

      processed_pattern_parts.append((field_regex, new_arguments))

  return pattern_.StringPattern.reconstruct_pattern(processed_pattern_parts)
