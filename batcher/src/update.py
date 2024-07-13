"""Updating the plug-in to the latest version."""

from typing import Dict, List, Optional, Tuple, Union

import pygimplib as pg

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures
from src import utils as utils_
from src import version as version_
from src.path import uniquify
from src.setting_source_names import *

_UPDATE_STATUSES = FRESH_START, UPDATE, TERMINATE = 0, 1, 2


def load_and_update(
      settings: pg.setting.Group,
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
      update_sources: bool = True,
      source_name: Optional[str] = None,
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
  the setting sources whose name match ``source_name``. If ``source_name`` is
  ``None``, all parts of the update apply.
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
        update_handler(data, settings, source_names)

    return data

  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()

  if source_name is None:
    source_names = SOURCE_NAMES
  else:
    source_names = [source_name]

  if _is_fresh_start(sources):
    if update_sources:
      _update_sources(settings, sources)

    return FRESH_START, ''

  current_version = None
  previous_version = None

  load_result = settings.load(sources, modify_data_func=_handle_update)
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
  _setting_dict, index = _get_child_setting(group_list, setting_name)
  if index is not None:
    del group_list[index]


def _update_to_0_3(data, settings, source_names):
  if EXPORT_LAYERS_SOURCE_NAME not in source_names:
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


def _update_to_0_4(data, _settings, source_names):
  if EXPORT_LAYERS_SOURCE_NAME not in source_names:
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
        procedure_dict['name'] = 'rename_for_export_layers'
        orig_name_setting_dict['default_value'] = 'rename_for_export_layers'
        orig_name_setting_dict['value'] = 'rename_for_export_layers'

        arguments_list[0]['type'] = 'name_pattern'
        arguments_list[0]['gui_type'] = 'name_pattern_entry'

      if orig_name_setting_dict['default_value'] == 'remove_folder_structure':
        procedure_dict['name'] = 'remove_folder_structure_for_export_layers'
        orig_name_setting_dict['default_value'] = 'remove_folder_structure_for_export_layers'
        orig_name_setting_dict['value'] = 'remove_folder_structure_for_export_layers'


def _handle_background_foreground_actions(procedures_list, constraints_list):
  _remove_merge_background_foreground_procedures(procedures_list)

  merge_procedure_mapping = {
    'insert_background': 'merge_background',
    'insert_foreground': 'merge_foreground',
  }
  procedure_names = {action_dict['name'] for action_dict in procedures_list}

  constraint_mapping = {
    'insert_background': 'not_background',
    'insert_foreground': 'not_foreground',
  }
  constraint_names = {action_dict['name'] for action_dict in constraints_list}

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
          'default_value': '',
          'gui_type': None,
        })
      arguments_list.append(
        {
          'type': 'string',
          'name': 'constraint_name',
          'default_value': '',
          'gui_type': None,
        })

      merge_procedure_name = merge_procedure_mapping[orig_name_setting_dict['default_value']]
      merge_procedure_name = _uniquify_action_name(merge_procedure_name, procedure_names)

      merge_group_dict = _create_action_as_saved_dict(
        builtin_procedures.BUILTIN_PROCEDURES[merge_procedure_name])

      procedure_list.append(merge_group_dict)

      arguments_list[-2]['default_value'] = merge_procedure_name

      constraint_name = constraint_mapping[orig_name_setting_dict['default_value']]
      constraint_name = _uniquify_action_name(constraint_name, constraint_names)

      constraint_group_dict = _create_action_as_saved_dict(
        builtin_constraints.BUILTIN_CONSTRAINTS[constraint_name])

      constraints_list.append(constraint_group_dict)

      arguments_list[-1]['default_value'] = constraint_name


def _remove_merge_background_foreground_procedures(procedures_list):
  merge_procedure_indexes = []
  for index, procedure_dict in enumerate(procedures_list):
    orig_name_setting_dict, _index = _get_child_setting(
      procedure_dict['settings'], 'orig_name')
    if orig_name_setting_dict['default_value'] in ['merge_background', 'merge_foreground']:
      merge_procedure_indexes.append(index)

  for index in reversed(merge_procedure_indexes):
    procedures_list.pop(index)


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

  uniquified_name = (
    uniquify.uniquify_string(name, existing_names, generator=_generate_unique_action_name()))

  existing_names.add(uniquified_name)

  return uniquified_name


_UPDATE_HANDLERS = {
  '0.3': _update_to_0_3,
  '0.4': _update_to_0_4,
}
