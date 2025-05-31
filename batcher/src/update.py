"""Updating the plug-in to the latest version."""

import re
import traceback
from typing import Dict, List, Optional, Tuple, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

import pygimplib as pg
from pygimplib import pdb

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures
from src import setting_classes as setting_classes_
from src import utils as utils_
from src import version as version_
from src.path import pattern as pattern_
from src.path import uniquify
from src.procedure_groups import *

_UPDATE_STATUSES = FRESH_START, UPDATE, TERMINATE = 0, 1, 2


def load_and_update(
      settings: pg.setting.Group,
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
      update_sources: bool = True,
      procedure_group: Optional[str] = None,
) -> Tuple[int, str]:
  """Loads and updates settings and setting sources to the latest version of the
  plug-in.
  
  Updating involves renaming settings or replacing/removing obsolete settings.
  
  If ``sources`` is ``None``, default setting sources are used. Otherwise,
  ``sources`` must be a dictionary of (key, source) pairs.
  
  Two values are returned - status and an accompanying message.
  
  Status can have one of the following integer values:
  
  * `FRESH_START` - The plug-in was never used before or has no settings stored.
  
  * `UPDATE` - The plug-in was successfully updated to the latest version, or no
    update was performed as the plug-in version remains the same.
  
  * `TERMINATE` - No update was performed. This value is returned if the update
    failed (e.g. because of a malformed setting source).

  If ``update_sources`` is ``True``, the contents of ``sources`` are updated
  (overwritten), otherwise they are kept intact.

  Some parts of the update may be skipped if the parts can only be applied to
  the setting sources whose name match ``procedure_group``. If
  ``procedure_group`` is ``None``, all parts of the update apply.
  """
  def _handle_update(data):
    nonlocal current_version, previous_version

    current_version = version_.Version.parse(pg.config.PLUGIN_VERSION)

    previous_version = _get_plugin_version(data)
    _update_plugin_version(data, current_version)

    if not _UPDATE_HANDLERS:
      return data

    if previous_version is None:
      raise pg.setting.SourceModifyDataError(_('Failed to obtain the previous plug-in version.'))

    for version_str, update_handler in _UPDATE_HANDLERS.items():
      if previous_version < version_.Version.parse(version_str) <= current_version:
        update_handler(data, settings, procedure_groups)

    return data

  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()

  if procedure_group is None:
    procedure_groups = PROCEDURE_GROUPS
  else:
    procedure_groups = [procedure_group]

  if _is_fresh_start(sources):
    if update_sources:
      _update_sources(settings, sources)

    return FRESH_START, ''

  current_version = None
  previous_version = None

  try:
    load_result = settings.load(sources, modify_data_func=_handle_update)
  except Exception:
    # Gracefully exit the update upon an exception not caught by
    # `setting.Persistor.load()`.
    # This should be handled as early as possible in the client code to avoid
    # disrupting the plug-in functionality. Ideally, settings should be reset
    # completely.
    return TERMINATE, traceback.format_exc()

  load_message = utils_.format_message_from_persistor_statuses(load_result)

  if any(status == pg.setting.Persistor.FAIL
         for status in load_result.statuses_per_source.values()):
    return TERMINATE, load_message

  if (update_sources
      and current_version is not None and previous_version is not None
      and previous_version < current_version):
    _update_sources(settings, sources)

  return UPDATE, load_message


def _get_plugin_version(data) -> Union[version_.Version, None]:
  plugin_version_dict = _get_plugin_version_dict(data)

  if plugin_version_dict is not None:
    if 'value' in plugin_version_dict:
      plugin_version = plugin_version_dict['value']
    elif 'default_value' in plugin_version_dict:
      plugin_version = plugin_version_dict['default_value']
    else:
      return None

    try:
      return version_.Version.parse(plugin_version)
    except (version_.InvalidVersionFormatError, TypeError):
      return None
  else:
    return None


def _update_plugin_version(data, new_version):
  plugin_version_dict = _get_plugin_version_dict(data)

  if plugin_version_dict is not None:
    plugin_version_dict['value'] = str(new_version)
    plugin_version_dict['default_value'] = str(new_version)


def _is_fresh_start(sources):
  return all(not source.has_data() for source in sources.values())


def _update_sources(settings, sources):
  for source in sources.values():
    source.clear()
  settings.save(sources)


def _get_plugin_version_dict(data) -> Union[dict, None]:
  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    return _get_child_setting(main_settings_list, 'plugin_version')[0]
  else:
    return None


def _get_top_level_group_list(data, name):
  for index, dict_ in enumerate(data[0]['settings']):
    if dict_['name'] == name:
      return dict_['settings'], index

  return None, None


def _get_child_group_list(group_list, name):
  for index, dict_ in enumerate(group_list):
    if 'settings' in dict_ and dict_['name'] == name:
      return dict_['settings'], index

  return None, None


def _get_child_setting(group_list, name):
  for index, dict_ in enumerate(group_list):
    if 'settings' not in dict_ and dict_['name'] == name:
      return dict_, index

  return None, None


def _rename_setting(group_list, previous_setting_name, new_setting_name):
  setting_dict, _index = _get_child_setting(group_list, previous_setting_name)
  if setting_dict is not None:
    setting_dict['name'] = new_setting_name


def _set_setting_attribute_value(group_list, setting_name, attrib_name, new_attrib_value):
  setting_dict, _index = _get_child_setting(group_list, setting_name)
  if setting_dict is not None:
    setting_dict[attrib_name] = new_attrib_value


def _remove_setting(group_list, setting_name):
  setting_dict, index = _get_child_setting(group_list, setting_name)
  if index is not None:
    del group_list[index]

  return setting_dict, index


def _update_to_0_3(data, settings, procedure_groups):
  if EXPORT_LAYERS_GROUP not in procedure_groups:
    return

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    _update_actions_to_0_3(main_settings_list, 'procedures')
    _update_actions_to_0_3(main_settings_list, 'constraints')

    setting_dict, _index = _get_child_setting(main_settings_list, 'file_extension')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

    setting_dict, _index = _get_child_setting(main_settings_list, 'output_directory')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

    setting_dict, _index = _get_child_setting(main_settings_list, 'layer_name_pattern')
    if setting_dict is not None:
      setting_dict['auto_update_gui_to_setting'] = False

  gui_settings_list, _index = _get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _setting, index = _get_child_setting(gui_settings_list, 'show_more_settings')
    if index is not None:
      gui_settings_list.pop(index)

    gui_size_setting_list, _index = _get_child_group_list(gui_settings_list, 'size')

    if gui_size_setting_list is not None:
      setting_dict, _index = _get_child_setting(gui_size_setting_list, 'dialog_size')
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/dialog_size'].default_value
        setting_dict['default_value'] = settings['gui/size/dialog_size'].default_value

      setting_dict, _index = (
        _get_child_setting(gui_size_setting_list, 'paned_outside_previews_position'))
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/paned_outside_previews_position'].default_value
        setting_dict['default_value'] = (
          settings['gui/size/paned_outside_previews_position'].default_value)

      setting_dict, _index = (
        _get_child_setting(gui_size_setting_list, 'paned_between_previews_position'))
      if setting_dict is not None:
        setting_dict['value'] = settings['gui/size/paned_between_previews_position'].default_value
        setting_dict['default_value'] = (
          settings['gui/size/paned_between_previews_position'].default_value)


def _update_actions_to_0_3(main_settings_list, action_type):
  actions_list, _index = _get_child_group_list(main_settings_list, action_type)

  if actions_list is None:
    return

  for action_dict in actions_list:
    action_list = action_dict['settings']

    display_options_on_create_dict, _index = (
      _get_child_setting(action_list, 'display_options_on_create'))
    if display_options_on_create_dict:
      display_options_on_create_dict['value'] = False
      display_options_on_create_dict['default_value'] = False

    more_options_list, _index = _get_child_group_list(action_list, 'more_options')

    if more_options_list is None:
      more_options_dict = {
        'name': 'more_options',
        'setting_attributes': {
          'pdb_type': None,
        },
        'settings': [],
      }
      action_list.insert(-2, more_options_dict)

      more_options_list = more_options_dict['settings']

    enabled_for_previews_in_more_options_dict, _index = (
      _get_child_setting(more_options_list, 'enabled_for_previews'))
    if enabled_for_previews_in_more_options_dict is None:
      enabled_for_previews_dict, index = _get_child_setting(action_list, 'enabled_for_previews')
      if enabled_for_previews_dict is not None:
        action_list.pop(index)
        more_options_list.append(enabled_for_previews_dict)

    also_apply_to_parent_folders_in_more_options_dict, _index = (
      _get_child_setting(more_options_list, 'also_apply_to_parent_folders'))
    if also_apply_to_parent_folders_in_more_options_dict is None:
      also_apply_to_parent_folders_dict, index = (
        _get_child_setting(action_list, 'also_apply_to_parent_folders'))
      if also_apply_to_parent_folders_dict is not None:
        action_list.pop(index)
        more_options_list.append(also_apply_to_parent_folders_dict)


def _update_to_0_4(data, _settings, procedure_groups):
  if EXPORT_LAYERS_GROUP not in procedure_groups:
    return

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    _remove_setting(main_settings_list, 'edit_mode')

    _rename_setting(main_settings_list, 'layer_filename_pattern', 'name_pattern')
    _set_setting_attribute_value(main_settings_list, 'filename_pattern', 'type', 'name_pattern')

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')
    constraints_list, _index = _get_child_group_list(main_settings_list, 'constraints')

    if procedures_list is None or constraints_list is None:
      return

    _handle_background_foreground_actions(procedures_list, constraints_list)

    for procedure_dict in procedures_list:
      procedure_list = procedure_dict['settings']

      orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')

      arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

      if orig_name_setting_dict['default_value'] == 'export' and arguments_list is not None:
        arguments_list[3]['name'] = 'single_image_name_pattern'
        arguments_list[3]['type'] = 'name_pattern'
        arguments_list[3]['gui_type'] = 'name_pattern_entry'

      if orig_name_setting_dict['default_value'] == 'rename' and arguments_list is not None:
        orig_name_setting_dict['value'] = 'rename_for_export_layers'
        orig_name_setting_dict['default_value'] = 'rename_for_export_layers'

        arguments_list[0]['type'] = 'name_pattern'
        arguments_list[0]['gui_type'] = 'name_pattern_entry'

      if orig_name_setting_dict['default_value'] == 'remove_folder_structure':
        orig_name_setting_dict['value'] = 'remove_folder_structure_for_export_layers'
        orig_name_setting_dict['default_value'] = 'remove_folder_structure_for_export_layers'


def _handle_background_foreground_actions(procedures_list, constraints_list):
  _remove_action_by_orig_names(procedures_list, ['merge_background', 'merge_foreground'])

  merge_procedure_mapping = {
    'insert_background': 'merge_background',
    'insert_foreground': 'merge_foreground',
  }
  procedure_names = {action_dict['name'] for action_dict in procedures_list}
  procedure_display_names = {
    _get_child_setting(action_dict['settings'], 'display_name')[0]['value']
    for action_dict in procedures_list
    if _get_child_setting(action_dict['settings'], 'display_name')[0] is not None
  }

  constraint_mapping = {
    'insert_background': 'not_background',
    'insert_foreground': 'not_foreground',
  }
  constraint_names = {action_dict['name'] for action_dict in constraints_list}
  constraint_display_names = {
    _get_child_setting(action_dict['settings'], 'display_name')[0]['value']
    for action_dict in constraints_list
    if _get_child_setting(action_dict['settings'], 'display_name')[0] is not None
  }

  merge_group_dicts = []
  constraint_group_dicts = []

  for procedure_dict in procedures_list:
    procedure_list = procedure_dict['settings']
    orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')

    arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

    if (orig_name_setting_dict['default_value'] in ['insert_background', 'insert_foreground']
        and arguments_list is not None):
      arguments_list.append(
        {
          'type': 'string',
          'name': 'merge_procedure_name',
          'gui_type': None,
        })
      arguments_list.append(
        {
          'type': 'string',
          'name': 'constraint_name',
          'gui_type': None,
        })

      merge_procedure_name = merge_procedure_mapping[orig_name_setting_dict['default_value']]
      merge_group_dict = _create_action_as_saved_dict(
        builtin_procedures.BUILTIN_PROCEDURES[merge_procedure_name])

      unique_merge_procedure_name = _uniquify_action_name(merge_procedure_name, procedure_names)
      merge_group_dict['name'] = unique_merge_procedure_name
      arguments_list[-2]['value'] = unique_merge_procedure_name
      arguments_list[-2]['default_value'] = unique_merge_procedure_name

      merge_procedure_display_name_dict, _index = _get_child_setting(
        merge_group_dict['settings'], 'display_name')
      if merge_procedure_display_name_dict is not None:
        unique_merge_procedure_display_name = _uniquify_action_display_name(
          merge_procedure_display_name_dict['value'], procedure_display_names)
        merge_procedure_display_name_dict['value'] = unique_merge_procedure_display_name

      merge_group_dicts.append(merge_group_dict)

      constraint_name = constraint_mapping[orig_name_setting_dict['default_value']]
      constraint_group_dict = _create_action_as_saved_dict(
        builtin_constraints.BUILTIN_CONSTRAINTS[constraint_name])

      unique_constraint_name = _uniquify_action_name(constraint_name, constraint_names)
      constraint_group_dict['name'] = unique_constraint_name
      arguments_list[-1]['value'] = unique_constraint_name
      arguments_list[-1]['default_value'] = unique_constraint_name

      constraint_display_name_dict, _index = _get_child_setting(
        constraint_group_dict['settings'], 'display_name')
      if constraint_display_name_dict is not None:
        unique_constraint_display_name = _uniquify_action_display_name(
          constraint_display_name_dict['value'], constraint_display_names)
        constraint_display_name_dict['value'] = unique_constraint_display_name

      constraint_group_dicts.append(constraint_group_dict)

  for merge_group_dict in merge_group_dicts:
    procedures_list.append(merge_group_dict)

  for constraint_group_dict in constraint_group_dicts:
    constraints_list.append(constraint_group_dict)


def _remove_action_by_orig_names(actions_list, action_orig_names):
  indexes = []
  for index, action_dict in enumerate(actions_list):
    orig_name_setting_dict, _index = _get_child_setting(action_dict['settings'], 'orig_name')
    if orig_name_setting_dict['default_value'] in action_orig_names:
      indexes.append(index)

  for index in reversed(indexes):
    actions_list.pop(index)


def _create_action_as_saved_dict(action_dict):
  action = actions_.create_action(action_dict)

  source = pg.setting.SimpleInMemorySource('')
  source.write(action)

  return source.data[0]


def _uniquify_action_name(name, existing_names):
  """Returns ``name`` modified to be unique, i.e. to not match the name of any
  existing action in ``actions``.
  """

  def _generate_unique_action_name():
    i = 2
    while True:
      yield f'_{i}'
      i += 1

  uniquified_name = uniquify.uniquify_string(
    name, existing_names, generator=_generate_unique_action_name())

  existing_names.add(uniquified_name)

  return uniquified_name


def _uniquify_action_display_name(display_name, existing_display_names):
  """Returns ``display_name`` modified to be unique, i.e. to not match the
  display name of any existing action in ``actions``.
  """

  def _generate_unique_action_display_name():
    i = 2
    while True:
      yield f' ({i})'
      i += 1

  uniquified_display_name = uniquify.uniquify_string(
    display_name, existing_display_names, generator=_generate_unique_action_display_name())

  existing_display_names.add(uniquified_display_name)

  return uniquified_display_name


def _update_to_0_5(data, _settings, procedure_groups):
  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    file_extension_dict, _index = _get_child_setting(main_settings_list, 'file_extension')
    if file_extension_dict is not None:
      file_extension_dict['gui_type'] = None

    output_directory_dict, _index = _get_child_setting(main_settings_list, 'output_directory')
    if output_directory_dict is not None:
      output_directory_dict['type'] = 'dirpath'
      output_directory_dict['gui_type'] = 'folder_chooser_button'
      if 'auto_update_gui_to_setting' in output_directory_dict:
        del output_directory_dict['auto_update_gui_to_setting']

    name_pattern_dict, _index = _get_child_setting(main_settings_list, 'name_pattern')
    if name_pattern_dict is not None and 'auto_update_gui_to_setting' in name_pattern_dict:
      del name_pattern_dict['auto_update_gui_to_setting']

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is None:
      return

    for procedure_dict in procedures_list:
      procedure_list = procedure_dict['settings']

      orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')

      arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

      if arguments_list is not None:
        for argument_dict in arguments_list:
          if 'gui_type' in argument_dict and argument_dict['gui_type'] == 'check_button_no_text':
            argument_dict['gui_type'] = 'check_button'

          if argument_dict['name'] == 'file_extension':
            argument_dict['auto_update_gui_to_setting'] = False

      if orig_name_setting_dict['default_value'] == 'export' and arguments_list is not None:
        # We retain `name` and only modify `orig_name` as only the latter is
        # used in the code to check if a procedure is an export procedure.
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
              setting_classes_.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY: 'png'},
            'value': {
              setting_classes_.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY: 'png'},
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

    constraints_list, _index = _get_child_group_list(main_settings_list, 'constraints')

    if constraints_list is None:
      return

    for constraint_dict in constraints_list:
      constraint_list = constraint_dict['settings']

      orig_name_setting_dict, _index = _get_child_setting(constraint_list, 'orig_name')

      arguments_list, _index = _get_child_group_list(constraint_list, 'arguments')

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


def _update_to_0_6(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  gui_settings_list, _index = _get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _rename_setting(
      gui_settings_list,
      'name_preview_layers_collapsed_state',
      'name_preview_items_collapsed_state')
    _rename_setting(
      gui_settings_list,
      'image_preview_displayed_layers',
      'image_preview_displayed_items')

    gui_size_list, _index = _get_child_group_list(gui_settings_list, 'size')

    setting_dict, _index = _get_child_setting(gui_size_list, 'paned_between_previews_position')
    if setting_dict is not None:
      setting_dict['type'] = 'integer'

  if EDIT_LAYERS_GROUP in procedure_groups:
    _remove_setting(gui_settings_list, 'images_and_directories')

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    overwrite_mode_dict, _index = _get_child_setting(main_settings_list, 'overwrite_mode')
    if overwrite_mode_dict is not None:
      _update_choice_setting_for_0_6(overwrite_mode_dict)

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

    export_settings_list, _index = _get_child_group_list(gui_settings_list, 'export')
    if export_settings_list is not None:
      for setting_dict in export_settings_list:
        if 'settings' not in setting_dict and setting_dict['type'] == 'choice':
          _update_choice_setting_for_0_6(setting_dict)

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        function_setting_dict, _index = _get_child_setting(procedure_list, 'function')
        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        display_name_setting_dict, _index = _get_child_setting(procedure_list, 'display_name')
        description_setting_dict, _index = _get_child_setting(procedure_list, 'description')
        origin_setting_dict, _index = _get_child_setting(procedure_list, 'origin')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

        _update_origin_setting_for_0_6(origin_setting_dict)
        _update_arguments_list_for_0_6(arguments_list)
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
            display_name_setting_dict['value'] = builtin_procedures.BUILTIN_PROCEDURES[
              'apply_opacity_from_group_layers']['display_name']
            display_name_setting_dict['default_value'] = builtin_procedures.BUILTIN_PROCEDURES[
              'apply_opacity_from_group_layers']['display_name']

          if description_setting_dict is not None:
            description_setting_dict['value'] = builtin_procedures.BUILTIN_PROCEDURES[
              'apply_opacity_from_group_layers']['description']
            description_setting_dict['default_value'] = builtin_procedures.BUILTIN_PROCEDURES[
              'apply_opacity_from_group_layers']['description']

        if (orig_name_setting_dict['default_value'] == 'rename_for_edit_layers'
            and arguments_list is not None):
          for argument_dict in arguments_list:
            if argument_dict['name'] == 'rename_layer_groups':
              argument_dict['name'] = 'rename_group_layers'
              argument_dict['display_name'] = builtin_procedures.BUILTIN_PROCEDURES[
                orig_name_setting_dict['default_value']]['arguments'][2]['display_name']

    constraints_list, _index = _get_child_group_list(main_settings_list, 'constraints')

    if constraints_list is not None:
      for constraint_dict in constraints_list:
        constraint_list = constraint_dict['settings']

        orig_name_setting_dict, _index = _get_child_setting(constraint_list, 'orig_name')
        display_name_setting_dict, _index = _get_child_setting(constraint_list, 'display_name')
        origin_setting_dict, _index = _get_child_setting(constraint_list, 'origin')
        arguments_list, _index = _get_child_group_list(constraint_list, 'arguments')

        _update_origin_setting_for_0_6(origin_setting_dict)
        _update_arguments_list_for_0_6(arguments_list)

        if orig_name_setting_dict['default_value'] == 'layer_groups':
          # We retain `name` and only modify `orig_name` as only the latter is
          # potentially used in the code.
          orig_name_setting_dict['value'] = 'group_layers'
          orig_name_setting_dict['default_value'] = 'group_layers'

          if display_name_setting_dict is not None:
            display_name_setting_dict['value'] = (
              builtin_constraints.BUILTIN_CONSTRAINTS['group_layers']['display_name'])
            display_name_setting_dict['default_value'] = (
              builtin_constraints.BUILTIN_CONSTRAINTS['group_layers']['display_name'])


def _update_arguments_list_for_0_6(arguments_list):
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
      _update_choice_setting_for_0_6(argument_dict)

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


def _update_origin_setting_for_0_6(origin_setting_dict):
  if origin_setting_dict is not None:
    _update_choice_setting_for_0_6(origin_setting_dict)


def _update_choice_setting_for_0_6(setting_dict):
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


def _update_to_0_7(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

        if orig_name_setting_dict['default_value'] == 'scale' and arguments_list is not None:
          arguments_list.extend([
            {
              'type': 'bool',
              'name': 'scale_to_fit',
              'default_value': False,
              'display_name': 'Scale to fit',
              'gui_type': 'check_button',
              'value': False,
            },
            {
              'type': 'bool',
              'name': 'keep_aspect_ratio',
              'default_value': False,
              'display_name': 'Keep aspect ratio',
              'gui_type': 'check_button',
              'value': False,
            },
            {
              'type': 'choice',
              'default_value': 'width',
              'name': 'dimension_to_keep',
              'items': [
                ('width', 'Width'),
                ('height', 'Height'),
              ],
              'display_name': 'Dimension to keep',
              'value': 'width',
            },
          ])


def _update_to_0_8(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  gui_settings_list, _index = _get_top_level_group_list(data, 'gui')

  if gui_settings_list is not None:
    _update_items_setting_for_0_8(
      gui_settings_list, 'image_preview_displayed_items', 'gimp_item_tree_items')
    _update_items_setting_for_0_8(
      gui_settings_list, 'name_preview_items_collapsed_state', 'gimp_item_tree_items')

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    # 'selected_items' may exist as a new setting. We need to remove that one
    # and instead rename the original so that the value of the original setting
    # is preserved on update.
    _remove_setting(main_settings_list, 'selected_items')
    _rename_setting(main_settings_list, 'selected_layers', 'selected_items')

    _update_items_setting_for_0_8(main_settings_list, 'selected_items', 'gimp_item_tree_items')

    _replace_layer_related_options_in_attributes_field_in_pattern(
      main_settings_list, 'name_pattern')

    export_settings_list, _index = _get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      _update_export_mode_setting(export_settings_list)

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        _replace_action_tags_with_plug_in_procedure_groups(procedure_dict)

        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

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

    constraints_list, _index = _get_child_group_list(main_settings_list, 'constraints')
    if constraints_list is not None:
      _remove_action_by_orig_names(constraints_list, ['selected_in_preview'])
      for constraint_dict in constraints_list:
        _replace_action_tags_with_plug_in_procedure_groups(constraint_dict)


def _replace_action_tags_with_plug_in_procedure_groups(action_dict):
  tags_new_name_mapping = {
    'convert': 'plug-in-batch-convert',
    'export_layers': 'plug-in-batch-export-layers',
    'edit_layers': 'plug-in-batch-edit-layers',
  }

  if 'tags' in action_dict:
    action_dict['tags'] = [
      tags_new_name_mapping[tag] if tag in tags_new_name_mapping else tag
      for tag in action_dict['tags']]


def _update_items_setting_for_0_8(settings_list, setting_name, new_type_name):
  setting_dict, _index = _get_child_setting(settings_list, setting_name)

  setting_dict['type'] = new_type_name

  setting_dict.pop('default_value', None)

  new_value = []
  for image_filepath, items in setting_dict['value'].items():
    for item_data in items:
      if len(item_data) >= 2:
        new_value.append([
          item_data[0],
          item_data[1].split('/'),
          pg.itemtree.FOLDER_KEY if len(item_data) >= 3 else '',
          image_filepath,
        ])

  setting_dict['value'] = new_value


def _update_export_mode_setting(settings_list):
  export_mode_dict, _index = _get_child_setting(settings_list, 'export_mode')
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
  setting_dict, _index = _get_child_setting(settings_list, setting_name)
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


def _update_to_1_0_rc1(data, _settings, procedure_groups):
  if not (EXPORT_LAYERS_GROUP in procedure_groups or EDIT_LAYERS_GROUP in procedure_groups):
    return

  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    _remove_setting(main_settings_list, 'selected_items')

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

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


def _update_to_1_0_rc2(data, _settings, _procedure_groups):
  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    output_directory_dict, _index = _get_child_setting(main_settings_list, 'output_directory')
    if output_directory_dict is not None:
      _update_filepath_or_dirpath_setting(output_directory_dict)

    export_settings_list, _index = _get_child_group_list(main_settings_list, 'export')
    if export_settings_list is not None:
      file_format_export_options_dict, _index = _get_child_setting(
        export_settings_list, 'file_format_export_options')
      if file_format_export_options_dict is not None:
        for name, format_options in file_format_export_options_dict['value'].items():
          if name != '_active':
            _update_choice_arguments_for_1_0_rc2(format_options)

    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')
    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

        if (orig_name_setting_dict['default_value'] == 'insert_background_for_images'
            and arguments_list is not None):
          _rename_setting(arguments_list, 'image_filepath', 'image_file')

        if (orig_name_setting_dict['default_value'] == 'insert_foreground_for_images'
            and arguments_list is not None):
          _rename_setting(arguments_list, 'image_filepath', 'image_file')

        _update_choice_arguments_for_1_0_rc2(arguments_list)

        _update_file_arguments_for_1_0_rc2(arguments_list)

        _update_filepath_and_dirpath_arguments_for_1_0_rc2(arguments_list)

    constraints_list, _index = _get_child_group_list(main_settings_list, 'constraints')
    if constraints_list is not None:
      for constraint_dict in constraints_list:
        constraint_list = constraint_dict['settings']

        arguments_list, _index = _get_child_group_list(constraint_list, 'arguments')

        _update_choice_arguments_for_1_0_rc2(arguments_list)

        _update_file_arguments_for_1_0_rc2(arguments_list)

        _update_filepath_and_dirpath_arguments_for_1_0_rc2(arguments_list)


def _update_choice_arguments_for_1_0_rc2(arguments_list):
  for argument_dict in arguments_list:
    if argument_dict['type'] == 'choice':
      _update_choice_setting_for_1_0_rc2(argument_dict)


def _update_choice_setting_for_1_0_rc2(setting_dict):
  if 'gui_type' in setting_dict and setting_dict['gui_type'] == 'choice_combo_box':
    setting_dict['gui_type'] = 'prop_choice_combo_box'


def _update_file_arguments_for_1_0_rc2(arguments_list):
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


def _update_filepath_and_dirpath_arguments_for_1_0_rc2(arguments_list):
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


def _update_to_1_1(data, _settings, _procedure_groups):
  main_settings_list, _index = _get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    procedures_list, _index = _get_child_group_list(main_settings_list, 'procedures')

    if procedures_list is not None:
      for procedure_dict in procedures_list:
        procedure_list = procedure_dict['settings']

        orig_name_setting_dict, _index = _get_child_setting(procedure_list, 'orig_name')
        arguments_list, _index = _get_child_group_list(procedure_list, 'arguments')

        if (orig_name_setting_dict['value'].startswith('scale_for_')
            and arguments_list is not None):
          _scale_1_1_merge_image_layer_object_to_scale(arguments_list, orig_name_setting_dict)
          _scale_1_1_merge_dimensions_and_units(arguments_list, orig_name_setting_dict)
          _scale_1_1_merge_scale_to_fit_keep_aspect_ratio_and_dimension_to_keep(arguments_list)
          _scale_1_1_add_padding_color_argument(arguments_list)
          _scale_1_1_add_image_resolution(arguments_list)

        if (orig_name_setting_dict['value'].startswith('align_and_offset_layers')
            and arguments_list is not None):
          _align_1_1_merge_reference_object_and_layer(arguments_list)
          _align_1_1_merge_dimensions_and_units(arguments_list)


def _scale_1_1_merge_image_layer_object_to_scale(arguments_list, orig_name_setting_dict):
  _remove_setting(arguments_list, 'image')
  _remove_setting(arguments_list, 'layer')
  _remove_setting(arguments_list, 'object_to_scale')

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

  width_unit_setting_dict, _index = _remove_setting(arguments_list, 'width_unit')
  width_setting_dict, _index = _get_child_setting(arguments_list, 'new_width')
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

  height_unit_setting_dict, _index = _remove_setting(arguments_list, 'height_unit')
  height_setting_dict, _index = _get_child_setting(arguments_list, 'new_height')
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
  scale_to_fit_setting_dict, _index = _remove_setting(arguments_list, 'scale_to_fit')
  keep_aspect_ratio_setting_dict, _index = _remove_setting(arguments_list, 'keep_aspect_ratio')
  dimension_to_keep_setting_dict, _index = _remove_setting(arguments_list, 'dimension_to_keep')

  value = 'stretch'

  if scale_to_fit_setting_dict['value']:
    value = 'fit'
  elif keep_aspect_ratio_setting_dict['value']:
    if dimension_to_keep_setting_dict['value'] == 'width':
      value = 'keep_adjust_width'
    else:
      value = 'keep_adjust_height'

  arguments_list.insert(
    -2,
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


def _scale_1_1_add_padding_color_argument(arguments_list):
  arguments_list.insert(
    -2,
    {
      'type': 'color',
      'name': 'padding_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Padding color'),
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
    },
  )


def _align_1_1_merge_reference_object_and_layer(arguments_list):
  reference_object_setting_dict, _index = _remove_setting(arguments_list, 'reference_object')
  reference_layer_setting_dict, _index = _remove_setting(arguments_list, 'reference_layer')

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

  x_offset_unit_setting_dict, _index = _remove_setting(arguments_list, 'x_offset_unit')
  x_offset_setting_dict, _index = _get_child_setting(arguments_list, 'x_offset')
  x_offset_setting_dict['type'] = 'dimension'
  x_offset_setting_dict['value'], x_offset_setting_dict['default_value'] = _get_dimension(
    x_offset_setting_dict['value'],
    x_offset_unit_setting_dict['value'],
    'x',
    dimension_default_value,
  )
  x_offset_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']

  y_offset_unit_setting_dict, _index = _remove_setting(arguments_list, 'y_offset_unit')
  y_offset_setting_dict, _index = _get_child_setting(arguments_list, 'y_offset')
  y_offset_setting_dict['type'] = 'dimension'
  y_offset_setting_dict['value'], y_offset_setting_dict['default_value'] = _get_dimension(
    y_offset_setting_dict['value'],
    y_offset_unit_setting_dict['value'],
    'y',
    dimension_default_value,
  )
  y_offset_setting_dict['percent_placeholder_names'] = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']


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


_UPDATE_HANDLERS = {
  '0.3': _update_to_0_3,
  '0.4': _update_to_0_4,
  '0.5': _update_to_0_5,
  '0.6': _update_to_0_6,
  '0.7': _update_to_0_7,
  '0.8': _update_to_0_8,
  '1.0-RC1': _update_to_1_0_rc1,
  '1.0-RC2': _update_to_1_0_rc2,
  '1.1': _update_to_1_1,
}
