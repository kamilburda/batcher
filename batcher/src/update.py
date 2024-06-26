"""Updating the plug-in to the latest version."""

from typing import Dict, List, Optional, Tuple, Union

import pygimplib as pg

from src import utils as utils_
from src import version as version_

_UPDATE_STATUSES = FRESH_START, UPDATE, TERMINATE = 0, 1, 2


def load_and_update(
      settings: pg.setting.Group,
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
      update_sources: bool = True,
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
        update_handler(data, settings)

    return data

  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()

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


def _is_fresh_start(sources):
  return all(not source.has_data() for source in sources.values())


def _update_sources(settings, sources):
  for source in sources.values():
    source.clear()
  settings.save(sources)


def _update_to_0_3(data, settings):
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

    setting_dict, _index = _get_child_setting(main_settings_list, 'layer_filename_pattern')
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


_UPDATE_HANDLERS = {
  '0.3': _update_to_0_3,
}
