from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    update_utils_.remove_setting(main_settings_list, 'selected_items')

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if orig_name_setting_dict['default_value'] == 'scale' and arguments_list is not None:
          orig_name_setting_dict['value'] = 'scale_for_layers'
          orig_name_setting_dict['default_value'] = 'scale_for_layers'

          arguments_list.insert(
            2,
            {
              'type': 'choice',
              'name': 'object_to_scale',
              'default_value': 'layer',
              'value': 'layer',
              'items': [
                ('image', 'Image'),
                ('layer', 'Layer'),
              ],
              'display_name': 'Object to scale',
            })

          arguments_list[4]['items'] = [
            ('percentage_of_image_width', '% of image width'),
            ('percentage_of_image_height', '% of image height'),
            ('percentage_of_layer_width', '% of layer width'),
            ('percentage_of_layer_height', '% of layer height'),
            ('pixels', 'Pixels'),
          ]

          arguments_list[6]['items'] = [
            ('percentage_of_image_width', '% of image width'),
            ('percentage_of_image_height', '% of image height'),
            ('percentage_of_layer_width', '% of layer width'),
            ('percentage_of_layer_height', '% of layer height'),
            ('pixels', 'Pixels'),
          ]

        if (orig_name_setting_dict['default_value'] == 'use_layer_size'
            and arguments_list is not None):
          orig_name_setting_dict['value'] = 'resize_to_layer_size'
          orig_name_setting_dict['default_value'] = 'resize_to_layer_size'

          arguments_list.append(
            {
              'type': 'placeholder_layer_array',
              'name': 'layers',
              'default_value': 'current_layer_for_array',
              'value': 'current_layer_for_array',
              'element_type': 'layer',
              'display_name': 'Layers',
            },
          )

        if (orig_name_setting_dict['default_value'] == 'insert_background'
            and arguments_list is not None):
          orig_name_setting_dict['value'] = 'insert_background_for_layers'
          orig_name_setting_dict['default_value'] = 'insert_background_for_layers'

        if (orig_name_setting_dict['default_value'] == 'insert_foreground'
            and arguments_list is not None):
          orig_name_setting_dict['value'] = 'insert_foreground_for_layers'
          orig_name_setting_dict['default_value'] = 'insert_foreground_for_layers'

        if (orig_name_setting_dict['default_value'] == 'rename_for_edit_layers'
            and arguments_list is not None):
          for argument_dict in arguments_list:
            if argument_dict['name'] == 'rename_group_layers':
              argument_dict['name'] = 'rename_folders'
