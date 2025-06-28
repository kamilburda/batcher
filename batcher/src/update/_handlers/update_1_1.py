from src import utils as utils_

from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    update_utils_.rename_group(main_settings_list, 'procedures', 'actions')
    update_utils_.rename_group(main_settings_list, 'constraints', 'conditions')

    _add_new_attributes_to_output_directory(main_settings_list)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        _rename_command_attributes_1_1(action_dict)

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_1_1_merge_image_layer_object_to_scale(arguments_list, orig_name_setting_dict)
          _scale_1_1_merge_dimensions_and_units(arguments_list, orig_name_setting_dict)
          _scale_1_1_merge_scale_to_fit_keep_aspect_ratio_and_dimension_to_keep(arguments_list)
          _scale_1_1_add_image_resolution(arguments_list)
          _scale_1_1_add_padding_related_arguments(arguments_list, orig_name_setting_dict)

        if (orig_name_setting_dict['value'] == 'align_and_offset_layers'
            and arguments_list is not None):
          _align_1_1_merge_reference_object_and_layer(arguments_list)
          _align_1_1_merge_dimensions_and_units(arguments_list)

        if (orig_name_setting_dict['value'] == 'resize_to_layer_size'
            and arguments_list is not None):
          _resize_canvas_1_1_rename_action(orig_name_setting_dict)
          _resize_canvas_1_1_rename_layers_argument(arguments_list)
          _resize_canvas_1_1_add_new_arguments(arguments_list)

        if (orig_name_setting_dict['value'] == 'rename_for_export_images'
            and arguments_list is not None):
          _rename_for_export_images_1_1_remove_rename_images_argument(arguments_list)

        if (orig_name_setting_dict['value'].startswith('export_for_')
            and arguments_list is not None):
          _add_new_attributes_to_output_directory(arguments_list)

        if ((orig_name_setting_dict['value'].startswith('insert_background_for_')
             or orig_name_setting_dict['value'].startswith('insert_foreground_for_'))
            and arguments_list is not None):
          _insert_1_1_rename_arguments(arguments_list)

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'conditions')
    if conditions_list is not None:
      for condition_dict in conditions_list:
        condition_list = condition_dict['settings']

        _rename_command_attributes_1_1(condition_dict)

        orig_name_setting_dict, _index = update_utils_.get_child_setting(
          condition_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(condition_list, 'arguments')

        if (orig_name_setting_dict['value'] == 'matching_text'
            and arguments_list is not None):
          _matching_text_1_1_add_new_options(arguments_list)

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    update_utils_.rename_group(gui_settings_list, 'procedure_browser', 'action_browser')


def _rename_command_attributes_1_1(command_dict):
  if 'tags' in command_dict:
    _replace_item_in_list(command_dict, 'tags', 'action', 'command')
    _replace_item_in_list(command_dict, 'tags', 'procedure', 'action')
    _replace_item_in_list(command_dict, 'tags', 'constraint', 'condition')

  command_groups_setting_dict, _index = update_utils_.get_child_setting(
    command_dict['settings'], 'action_groups')
  if command_groups_setting_dict is not None:
    command_groups_setting_dict['name'] = 'command_groups'
    _replace_item_in_list(
      command_groups_setting_dict, 'default_value', 'default_procedures', 'default_actions')
    _replace_item_in_list(
      command_groups_setting_dict, 'value', 'default_procedures', 'default_actions')
    _replace_item_in_list(
      command_groups_setting_dict, 'default_value', 'default_constraints', 'default_conditions')
    _replace_item_in_list(
      command_groups_setting_dict, 'value', 'default_constraints', 'default_conditions')


def _replace_item_in_list(setting_dict, attribute_name, previous_value, new_value):
  if previous_value in setting_dict[attribute_name]:
    previous_value_index = setting_dict[attribute_name].index(previous_value)
    setting_dict[attribute_name].remove(previous_value)
    setting_dict[attribute_name].insert(previous_value_index, new_value)


def _scale_1_1_merge_image_layer_object_to_scale(arguments_list, orig_name_setting_dict):
  update_utils_.remove_setting(arguments_list, 'image')
  update_utils_.remove_setting(arguments_list, 'layer')
  update_utils_.remove_setting(arguments_list, 'object_to_scale')

  object_to_scale_default_value = 'current_image'
  if orig_name_setting_dict['value'] == 'scale_for_layers':
    object_to_scale_default_value = 'current_layer'

  arguments_list.insert(
    0,
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_scale',
      'default_value': object_to_scale_default_value,
      'value': object_to_scale_default_value,
      'display_name': _('Apply to (image or layer):'),
    })


def _scale_1_1_merge_dimensions_and_units(arguments_list, orig_name_setting_dict):
  dimension_default_value = {
    'pixel_value': 100.0,
    'percent_value': 100.0,
    'other_value': 1.0,
    'unit': 'percent',
    'percent_object': 'current_image',
    'percent_property': {
      ('current_image',): 'width',
      ('current_layer', 'background_layer', 'foreground_layer'): 'width',
    },
  }

  if orig_name_setting_dict['value'] == 'scale_for_images':
    dimension_default_value['percent_object'] = 'current_image'
  elif orig_name_setting_dict['value'] == 'scale_for_layers':
    dimension_default_value['percent_object'] = 'current_layer'

  width_unit_setting_dict, _index = update_utils_.remove_setting(arguments_list, 'width_unit')
  width_setting_dict, _index = update_utils_.get_child_setting(arguments_list, 'new_width')
  width_setting_dict['type'] = 'dimension'
  width_setting_dict['value'], width_setting_dict['default_value'] = _get_dimension(
    width_setting_dict['value'],
    width_unit_setting_dict['value'],
    'x',
    dimension_default_value,
  )
  width_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']
  width_setting_dict['min_value'] = 0.0

  height_unit_setting_dict, _index = update_utils_.remove_setting(arguments_list, 'height_unit')
  height_setting_dict, _index = update_utils_.get_child_setting(arguments_list, 'new_height')
  height_setting_dict['type'] = 'dimension'
  height_setting_dict['value'], height_setting_dict['default_value'] = _get_dimension(
    height_setting_dict['value'],
    height_unit_setting_dict['value'],
    'y',
    dimension_default_value,
  )
  height_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']
  height_setting_dict['min_value'] = 0.0


def _scale_1_1_merge_scale_to_fit_keep_aspect_ratio_and_dimension_to_keep(arguments_list):
  scale_to_fit_setting_dict, _index = update_utils_.remove_setting(arguments_list, 'scale_to_fit')
  keep_aspect_ratio_setting_dict, _index = update_utils_.remove_setting(
    arguments_list, 'keep_aspect_ratio')
  dimension_to_keep_setting_dict, _index = update_utils_.remove_setting(
    arguments_list, 'dimension_to_keep')

  value = 'stretch'

  if scale_to_fit_setting_dict['value']:
    value = 'fit'
  elif keep_aspect_ratio_setting_dict['value']:
    if dimension_to_keep_setting_dict['value'] == 'width':
      value = 'keep_adjust_width'
    else:
      value = 'keep_adjust_height'

  arguments_list.insert(
    3,
    {
      'type': 'choice',
      'name': 'aspect_ratio',
      'default_value': value,
      'value': value,
      'items': [
        ('stretch', _('None (Stretch)')),
        ('keep_adjust_width', _('Keep, adjust width')),
        ('keep_adjust_height', _('Keep, adjust height')),
        ('fit', _('Fit')),
        ('fit_with_padding', _('Fit with padding')),
      ],
      'display_name': _('Aspect ratio'),
    },
  )


def _scale_1_1_add_image_resolution(arguments_list):
  arguments_list.append(
    {
      'type': 'bool',
      'name': 'set_image_resolution',
      'default_value': False,
      'value': False,
      'display_name': _('Set image resolution in DPI'),
    },
  )
  arguments_list.append(
    {
      'type': 'coordinates',
      'name': 'image_resolution',
      'default_value': {
        'x': 72.0,
        'y': 72.0,
      },
      'value': {
        'x': 72.0,
        'y': 72.0,
      },
      'show_display_name': False,
      'gui_type_kwargs': {
        'label_x': _('X'),
        'label_y': _('Y'),
      },
    },
  )


def _scale_1_1_add_padding_related_arguments(arguments_list, orig_name_setting_dict):
  arguments_list.append(
    {
      'type': 'color',
      'name': 'padding_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Padding color'),
    },
  )
  arguments_list.append(
    {
      'type': 'choice',
      'name': 'padding_position',
      'default_value': 'center',
      'value': 'center',
      'items': [
        ('start', _('Start')),
        ('center', _('Center')),
        ('end', _('End')),
        ('custom', _('Custom')),
      ],
      'display_name': _('Position'),
    },
  )

  dimension_default_value = {
    'pixel_value': 0.0,
    'percent_value': 0.0,
    'other_value': 0.0,
    'unit': 'pixel',
    'percent_object': 'current_image',
    'percent_property': {
      ('current_image',): 'width',
      ('current_layer', 'background_layer', 'foreground_layer'): 'width',
    },
  }
  if orig_name_setting_dict['value'] == 'scale_for_images':
    dimension_default_value['percent_object'] = 'current_image'
  elif orig_name_setting_dict['value'] == 'scale_for_layers':
    dimension_default_value['percent_object'] = 'current_layer'
  arguments_list.append(
    {
      'type': 'dimension',
      'name': 'padding_position_custom',
      'default_value': dimension_default_value,
      'value': utils_.semi_deep_copy(dimension_default_value),
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Custom start position'),
    },
  )


def _align_1_1_merge_reference_object_and_layer(arguments_list):
  reference_object_setting_dict, _index = update_utils_.remove_setting(
    arguments_list, 'reference_object')
  reference_layer_setting_dict, _index = update_utils_.remove_setting(
    arguments_list, 'reference_layer')

  if reference_object_setting_dict['value'] == 'image':
    reference_object_value = 'current_image'
  else:
    reference_object_value = reference_layer_setting_dict['value']

  arguments_list.insert(
    1,
    {
      'type': 'placeholder_image_or_layer',
      'name': 'reference_object',
      'default_value': 'current_image',
      'value': reference_object_value,
      'display_name': _('Object to align layers with'),
    },
  )


def _align_1_1_merge_dimensions_and_units(arguments_list):
  dimension_default_value = {
    'pixel_value': 0.0,
    'percent_value': 0.0,
    'other_value': 0.0,
    'unit': 'pixel',
    'percent_object': 'current_layer',
    'percent_property': {
      ('current_image',): 'width',
      ('current_layer', 'background_layer', 'foreground_layer'): 'width',
    },
  }

  x_offset_unit_setting_dict, _index = update_utils_.remove_setting(arguments_list, 'x_offset_unit')
  x_offset_setting_dict, _index = update_utils_.get_child_setting(arguments_list, 'x_offset')
  x_offset_setting_dict['type'] = 'dimension'
  x_offset_setting_dict['value'], x_offset_setting_dict['default_value'] = _get_dimension(
    x_offset_setting_dict['value'],
    x_offset_unit_setting_dict['value'],
    'x',
    dimension_default_value,
  )
  x_offset_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']

  y_offset_unit_setting_dict, _index = update_utils_.remove_setting(arguments_list, 'y_offset_unit')
  y_offset_setting_dict, _index = update_utils_.get_child_setting(arguments_list, 'y_offset')
  y_offset_setting_dict['type'] = 'dimension'
  y_offset_setting_dict['value'], y_offset_setting_dict['default_value'] = _get_dimension(
    y_offset_setting_dict['value'],
    y_offset_unit_setting_dict['value'],
    'y',
    dimension_default_value,
  )
  y_offset_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']


def _resize_canvas_1_1_rename_action(orig_name_setting_dict):
  orig_name_setting_dict['value'] = 'resize_canvas'
  orig_name_setting_dict['default_value'] = 'resize_canvas'


def _resize_canvas_1_1_rename_layers_argument(arguments_list):
  update_utils_.rename_setting(arguments_list, 'layers', 'resize_to_layer_size_layers')


def _resize_canvas_1_1_add_new_arguments(arguments_list):
  arguments_list[0:0] = [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_resize',
      'default_value': 'current_image',
      'value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'choice',
      'name': 'resize_mode',
      'default_value': 'resize_from_edges',
      'value': 'resize_to_layer_size',
      'items': [
        ('resize_from_edges', _('Resize from edges')),
        ('resize_from_position', _('Resize from position')),
        ('resize_to_aspect_ratio', _('Resize to aspect ratio')),
        ('resize_to_area', _('Resize to area')),
        ('resize_to_layer_size', _('Resize to layer size')),
      ],
      'display_name': _('How to resize'),
    },
    {
      'type': 'bool',
      'name': 'set_fill_color',
      'default_value': False,
      'value': False,
      'display_name': _('Fill added space with color'),
    },
    {
      'type': 'color',
      'name': 'fill_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Color for added space'),
    },
    {
      'type': 'bool',
      'name': 'resize_from_edges_same_amount_for_each_side',
      'default_value': False,
      'value': False,
      'display_name': _('Resize by the same amount from each side'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_amount',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Amount'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_top',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Top'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_bottom',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Bottom'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_left',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Left'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_edges_right',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Right'),
    },
    {
      'type': 'anchor',
      'name': 'resize_from_position_anchor',
      'default_value': 'center',
      'value': 'center',
      'items': [
        ('top_left', _('Top left')),
        ('top', _('Top')),
        ('top_right', _('Top right')),
        ('left', _('Left')),
        ('center', _('Center')),
        ('right', _('Right')),
        ('bottom_left', _('Bottom left')),
        ('bottom', _('Bottom')),
        ('bottom_right', _('Bottom right')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_position_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'resize_from_position_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
    {
      'type': 'coordinates',
      'name': 'resize_to_aspect_ratio_ratio',
      'default_value': {
        'x': 1.0,
        'y': 1.0,
      },
      'value': {
        'x': 1.0,
        'y': 1.0,
      },
      'min_x': 1.0,
      'min_y': 1.0,
      'display_name': _('Aspect ratio (width:height)'),
    },
    {
      'type': 'choice',
      'name': 'resize_to_aspect_ratio_position',
      'default_value': 'center',
      'value': 'center',
      'items': [
        ('start', _('Start')),
        ('center', _('Center')),
        ('end', _('End')),
        ('custom', _('Custom')),
      ],
      'display_name': _('Position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_aspect_ratio_position_custom',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Custom start position'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_x',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Offset X'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_y',
      'default_value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'value': {
        'pixel_value': 0.0,
        'percent_value': 0.0,
        'other_value': 0.0,
        'unit': 'pixel',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Offset Y'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Width'),
    },
    {
      'type': 'dimension',
      'name': 'resize_to_area_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': 'percent',
        'percent_object': 'current_image',
        'percent_property': {
          ('current_image',): 'height',
          ('current_layer', 'background_layer', 'foreground_layer'): 'height',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('Height'),
    },
  ]
  arguments_list.append(
    {
      'type': 'placeholder_image',
      'name': 'resize_to_image_size_image',
      'element_type': 'image',
      'default_value': 'current_image',
      'value': 'current_image',
      'display_name': _('Image'),
    },
  )


def _rename_for_export_images_1_1_remove_rename_images_argument(arguments_list):
  update_utils_.remove_setting(arguments_list, 'rename_images')


def _add_new_attributes_to_output_directory(group_list):
  output_directory_dict, _index = update_utils_.get_child_setting(group_list, 'output_directory')

  if output_directory_dict is not None:
    output_directory_dict['set_default_if_not_exists'] = True
    output_directory_dict['gui_type_kwargs'] = {
      'show_clear_button': False,
    }


def _insert_1_1_rename_arguments(arguments_list):
  update_utils_.rename_setting(arguments_list, 'merge_procedure_name', 'merge_action_name')
  update_utils_.rename_setting(arguments_list, 'constraint_name', 'condition_name')


def _matching_text_1_1_add_new_options(arguments_list):
  arguments_list[0]['items'] = [
    ('starts_with', _('Starts with text')),
    ('does_not_start_with', _('Does not start with text')),
    ('contains', _('Contains text')),
    ('does_not_contain', _('Does not contain text')),
    ('ends_with', _('Ends with text')),
    ('does_not_end_with', _('Does not end with text')),
    ('regex', _('Matches regular expression')),
  ]


def _get_dimension(orig_value, orig_unit, axis, dimension_default_value):
  dimension_value = utils_.semi_deep_copy(dimension_default_value)

  if orig_unit == 'pixels':
    dimension_value['unit'] = 'pixel'
    dimension_value['pixel_value'] = orig_value

    if axis == 'x':
      dimension_value['percent_property'][('current_image',)] = 'width'
      dimension_value['percent_property'][
        ('current_layer', 'background_layer', 'foreground_layer')] = 'width'
    else:
      dimension_value['percent_property'][('current_image',)] = 'height'
      dimension_value['percent_property'][
        ('current_layer', 'background_layer', 'foreground_layer')] = 'height'

  elif orig_unit.startswith('percentage_of_'):
    dimension_value['unit'] = 'percent'
    dimension_value['percent_value'] = orig_value
    if orig_unit.startswith('percentage_of_image_'):
      dimension_value['percent_object'] = 'current_image'
    elif orig_unit.startswith('percentage_of_layer_'):
      dimension_value['percent_object'] = 'current_layer'

    if orig_unit.endswith('_width'):
      dimension_value['percent_property'][('current_image',)] = 'width'
      dimension_value['percent_property'][
        ('current_layer', 'background_layer', 'foreground_layer')] = 'width'
    else:
      dimension_value['percent_property'][('current_image',)] = 'height'
      dimension_value['percent_property'][
        ('current_layer', 'background_layer', 'foreground_layer')] = 'height'

  return dimension_value, dimension_default_value
