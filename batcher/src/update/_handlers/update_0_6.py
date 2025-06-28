from src import builtin_actions
from src import builtin_conditions
from src.procedure_groups import *
from src.pypdb import pdb

from .. import _utils as update_utils_


def update(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  gui_settings_list, _index = update_utils_.get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    update_utils_.rename_setting(
      gui_settings_list,
      'name_preview_layers_collapsed_state',
      'name_preview_items_collapsed_state')
    update_utils_.rename_setting(
      gui_settings_list,
      'image_preview_displayed_layers',
      'image_preview_displayed_items')

    gui_size_list, _index = update_utils_.get_child_group_list(gui_settings_list, 'size')

    setting_dict, _index = update_utils_.get_child_setting(
      gui_size_list, 'paned_between_previews_position')
    if setting_dict is not None:
      setting_dict['type'] = 'integer'

  if EDIT_LAYERS_GROUP in procedure_groups:
    update_utils_.remove_setting(gui_settings_list, 'images_and_directories')

  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    overwrite_mode_dict, _index = update_utils_.get_child_setting(
      main_settings_list, 'overwrite_mode')
    if overwrite_mode_dict is not None:
      _update_choice_setting(overwrite_mode_dict)

    main_settings_list.insert(
      -2,
      {
        'type': 'tagged_items',
        'name': 'tagged_items',
        'default_value': [],
        'pdb_type': None,
        'gui_type': None,
        'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
        'value': [],
      },
    )

    export_settings_list, _index = update_utils_.get_child_group_list(gui_settings_list, 'export')
    if export_settings_list is not None:
      for setting_dict in export_settings_list:
        if 'settings' not in setting_dict and setting_dict['type'] == 'choice':
          _update_choice_setting(setting_dict)

    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'procedures')

    if actions_list is not None:
      for action_dict in actions_list:
        action_list = action_dict['settings']

        function_setting_dict, _index = update_utils_.get_child_setting(action_list, 'function')
        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        display_name_setting_dict, _index = update_utils_.get_child_setting(
          action_list, 'display_name')
        description_setting_dict, _index = update_utils_.get_child_setting(
          action_list, 'description')
        origin_setting_dict, _index = update_utils_.get_child_setting(action_list, 'origin')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')

        _update_origin_setting(origin_setting_dict)
        _update_arguments_list(arguments_list)
        _change_drawable_to_drawables_for_pdb_procedure(
          arguments_list, origin_setting_dict, function_setting_dict)

        if (orig_name_setting_dict['default_value'] in ['insert_background', 'insert_foreground']
            and arguments_list is not None):
          arguments_list.insert(
            1,
            {
              'type': 'tagged_items',
              'name': 'tagged_items',
              'default_value': [],
              'gui_type': None,
              'tags': ['ignore_reset'],
              'value': [],
            })

        if orig_name_setting_dict['default_value'] == 'apply_opacity_from_layer_groups':
          # We retain `name` and only modify `orig_name` as only the latter is
          # potentially used in the code.
          orig_name_setting_dict['value'] = 'apply_opacity_from_group_layers'
          orig_name_setting_dict['default_value'] = 'apply_opacity_from_group_layers'

          if display_name_setting_dict is not None:
            display_name_setting_dict['value'] = builtin_actions.BUILTIN_ACTIONS[
              'apply_opacity_from_group_layers']['display_name']
            display_name_setting_dict['default_value'] = builtin_actions.BUILTIN_ACTIONS[
              'apply_opacity_from_group_layers']['display_name']

          if description_setting_dict is not None:
            description_setting_dict['value'] = builtin_actions.BUILTIN_ACTIONS[
              'apply_opacity_from_group_layers']['description']
            description_setting_dict['default_value'] = builtin_actions.BUILTIN_ACTIONS[
              'apply_opacity_from_group_layers']['description']

        if (orig_name_setting_dict['default_value'] == 'rename_for_edit_layers'
            and arguments_list is not None):
          for argument_dict in arguments_list:
            if argument_dict['name'] == 'rename_layer_groups':
              argument_dict['name'] = 'rename_group_layers'
              argument_dict['display_name'] = builtin_actions.BUILTIN_ACTIONS[
                orig_name_setting_dict['default_value']]['arguments'][2]['display_name']

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'constraints')

    if conditions_list is not None:
      for condition_dict in conditions_list:
        condition_list = condition_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(condition_list, 'orig_name')
        display_name_setting_dict, _index = update_utils_.get_child_setting(condition_list, 'display_name')
        origin_setting_dict, _index = update_utils_.get_child_setting(condition_list, 'origin')
        arguments_list, _index = update_utils_.get_child_group_list(condition_list, 'arguments')

        _update_origin_setting(origin_setting_dict)
        _update_arguments_list(arguments_list)

        if orig_name_setting_dict['default_value'] == 'layer_groups':
          # We retain `name` and only modify `orig_name` as only the latter is
          # potentially used in the code.
          orig_name_setting_dict['value'] = 'group_layers'
          orig_name_setting_dict['default_value'] = 'group_layers'

          if display_name_setting_dict is not None:
            display_name_setting_dict['value'] = (
              builtin_conditions.BUILTIN_CONDITIONS['group_layers']['display_name'])
            display_name_setting_dict['default_value'] = (
              builtin_conditions.BUILTIN_CONDITIONS['group_layers']['display_name'])


def _update_arguments_list(arguments_list):
  if arguments_list is None:
    return

  for argument_dict in arguments_list:
    if argument_dict['type'] == 'vectors':
      argument_dict['type'] = 'path'
      if 'gui_type' in argument_dict and argument_dict['gui_type'] == 'vectors_combo_box':
        argument_dict['gui_type'] = 'path_combo_box'
      if argument_dict.get('pdb_type', None) is not None:
          argument_dict['pdb_type'] = 'GimpPath'

    if argument_dict['type'] == 'int':
      if 'pdb_type' in argument_dict:
        if argument_dict['pdb_type'] in ['gint64', 'glong', 'gchar']:
          argument_dict['pdb_type'] = 'gint'
        elif argument_dict['pdb_type'] in ['guint', 'guint64', 'gulong', 'guchar']:
          argument_dict['type'] = 'uint'
          argument_dict['pdb_type'] = 'guint'

    if argument_dict['type'] == 'float':
      argument_dict['type'] = 'double'
      if 'gui_type' in argument_dict and argument_dict['gui_type'] == 'float_spin_button':
        argument_dict['gui_type'] = 'double_spin_button'
      if argument_dict.get('pdb_type', None) == 'gfloat':
        argument_dict['pdb_type'] = 'gdouble'

    if argument_dict['type'] == 'choice':
      _update_choice_setting(argument_dict)

    if argument_dict['type'] == 'rgb':
      argument_dict['type'] = 'color'
      if 'gui_type' in argument_dict and argument_dict['gui_type'] == 'rgb_button':
        argument_dict['gui_type'] = 'color_button'
      if argument_dict.get('pdb_type', None) == 'GimpRGB':
        argument_dict['pdb_type'] = 'GeglColor'

    if argument_dict['type'] == 'unit':
      argument_dict['value'] = 'pixel'
      argument_dict['default_value'] = 'pixel'
      if argument_dict.get('pdb_type', None) is not None:
        argument_dict['pdb_type'] = 'GimpUnit'
      if 'gui_type' in argument_dict:
        argument_dict['gui_type'] = 'unit_combo_box'

    if argument_dict['type'] == 'array':
      argument_dict.pop('length_name', None)

    if argument_dict['type'] == 'array' and argument_dict['element_type'] == 'float':
      argument_dict['element_type'] = 'double'
      if argument_dict.get('element_gui_type', None) == 'float_spin_button':
        argument_dict['element_gui_type'] = 'double_spin_button'


def _update_origin_setting(origin_setting_dict):
  if origin_setting_dict is not None:
    _update_choice_setting(origin_setting_dict)


def _update_choice_setting(setting_dict):
  for index, item_tuple in enumerate(setting_dict['items']):
    if len(item_tuple) >= 3:
      item_value = item_tuple[2]
    else:
      item_value = index

    if setting_dict['value'] == item_value:
      setting_dict['value'] = item_tuple[0]
      break
  else:
    setting_dict['value'] = setting_dict['default_value']


def _change_drawable_to_drawables_for_pdb_procedure(
      arguments_list, origin_setting_dict, function_setting_dict):
  if any(list_or_dict is None
         for list_or_dict in [arguments_list, origin_setting_dict, function_setting_dict]):
    return

  if not (origin_setting_dict['value'] == 'gimp_pdb'
      and len(arguments_list) >= 3
      and (arguments_list[0]['type'] == 'enum' and arguments_list[0]['enum_type'] == 'GimpRunMode')
      and arguments_list[1]['type'] == 'placeholder_image'
      and arguments_list[2]['type'] == 'placeholder_drawable'):
    return

  pdb_proc_name = function_setting_dict['value']

  if pdb_proc_name not in pdb:
    return

  pdb_proc_args = pdb[pdb_proc_name].arguments

  if len(pdb_proc_args) < 3:
    return

  drawables_arg = pdb_proc_args[2]
  if drawables_arg.value_type.name == 'GimpCoreObjectArray':
    arguments_list[2] = {
      'type': 'placeholder_drawable_array',
      'name': drawables_arg.name,
      'element_type': 'drawable',
      'display_name': drawables_arg.blurb,
      'pdb_type': None,
      'value': 'current_layer_for_array',
    }
