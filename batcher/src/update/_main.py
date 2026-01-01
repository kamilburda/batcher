"""Main logic of updating settings to the latest version."""

import os
import sys
import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union


from config import CONFIG
from src import setting as setting_
from src import utils
from src import utils_setting as utils_setting_
from src import version as version_
from src.procedure_groups import *
from src.pypdb import pdb

from . import _utils as update_utils_
from .. import utils_update


__all__ = [
  'load_and_update',
  'UpdateStatuses',
]


class UpdateStatuses:

  UPDATE_STATUSES = (
    FRESH_START,
    UPDATE,
    UPDATE_WITH_REMOVED_COMMANDS,
    TERMINATE,
  ) = (
    'fresh_start',
    'update',
    'update_with_removed_commands',
    'terminate',
  )


def load_and_update(
      settings: setting_.Group,
      sources: Optional[Dict[str, Union[setting_.Source, List[setting_.Source]]]] = None,
      update_sources: bool = True,
      procedure_group: Optional[str] = None,
      update_handlers: Optional[Dict[str, Callable]] = None,
) -> Tuple[int, str]:
  """Loads and updates settings and setting sources to the latest version of the
  plug-in.
  
  Updating involves renaming settings or replacing/removing obsolete settings.
  
  If ``sources`` is ``None``, default setting sources are used. Otherwise,
  ``sources`` must be a dictionary of (key, source) pairs.
  
  Two values are returned - status and an accompanying message.
  
  Status can have one of the following integer values:
  
  * `UpdateStatuses.FRESH_START`:
      The plug-in was never used before or has no settings stored.
  
  * `UpdateStatuses.UPDATE`:
      The plug-in was successfully updated to the latest version, or no
      update was performed as the plug-in version remains the same.

  * `UpdateStatuses.UPDATE_WITH_REMOVED_COMMANDS`:
      The plug-in was successfully updated to the latest version, or no
      update was performed as the plug-in version remains the same. However,
      some actions or conditions were removed due to no longer being available
      in GIMP.

  * `UpdateStatuses.TERMINATE`:
      No update was performed. This value is returned if the update
      failed (e.g. because of a malformed setting source).

  If ``update_sources`` is ``True``, the contents of ``sources`` are updated
  (overwritten), otherwise they are kept intact.

  Some parts of the update may be skipped if the parts can only be applied to
  the setting sources whose name match ``procedure_group``. If
  ``procedure_group`` is ``None``, all parts of the update apply.

  If ``update_handlers`` is ``None`` (the default), update will be performed
  from the earliest version to the latest version. You can override
  ``update_handlers`` to specify a custom dictionary of (version, function)
  pairs. This is usually utilized for testing purposes.
  """

  def _handle_update(data):
    nonlocal current_version, previous_version, commands_no_longer_available

    current_version = version_.Version.parse(CONFIG.PLUGIN_VERSION)

    previous_version = _get_plugin_version(data)
    _update_plugin_version(data, current_version)

    if previous_version is None:
      raise setting_.SourceModifyDataError(_('Failed to obtain the previous plug-in version.'))

    if update_handlers is None:
      processed_update_handlers = _get_update_handlers(previous_version, current_version)
    else:
      processed_update_handlers = [
        handler for version_str, handler in update_handlers.items()
        if previous_version < version_.Version.parse(version_str) <= current_version
      ]

    for update_handler in processed_update_handlers:
      update_handler(data, settings, procedure_groups)

    commands_no_longer_available = _remove_no_longer_available_commands(data)

    return data

  if sources is None:
    sources = setting_.Persistor.get_default_setting_sources()

  if procedure_group is None:
    procedure_groups = ALL_PROCEDURE_GROUPS
  else:
    procedure_groups = [procedure_group]

  if _is_fresh_start(sources):
    if update_sources:
      _update_sources(settings, sources)

    return UpdateStatuses.FRESH_START, ''

  current_version = None
  previous_version = None
  commands_no_longer_available = []

  try:
    load_result = settings.load(sources, modify_data_func=_handle_update)
  except Exception:
    # Gracefully exit the update upon an exception not caught by
    # `setting.Persistor.load()`.
    # This should be handled as early as possible in the client code to avoid
    # disrupting the plug-in functionality. Ideally, settings should be reset
    # completely.
    return UpdateStatuses.TERMINATE, traceback.format_exc()

  load_message = utils_setting_.format_message_from_persistor_statuses(load_result)

  if any(status == setting_.Persistor.FAIL
         for status in load_result.statuses_per_source.values()):
    return UpdateStatuses.TERMINATE, load_message

  if (update_sources
      and current_version is not None and previous_version is not None
      and previous_version < current_version):
    _update_sources(settings, sources)

  if not commands_no_longer_available:
    return UpdateStatuses.UPDATE, load_message
  else:
    message = _format_commands_no_longer_available_message(commands_no_longer_available)
    return UpdateStatuses.UPDATE_WITH_REMOVED_COMMANDS, message


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
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    return update_utils_.get_child_setting(main_settings_list, 'plugin_version')[0]
  else:
    return None


def _get_update_handlers(
      minimum_version: version_.Version,
      maximum_version: version_.Version,
) -> List[Callable]:
  update_package_dirpath = os.path.dirname(utils.get_current_module_filepath())
  handlers_package_dirpath = os.path.join(
    update_package_dirpath, utils_update.HANDLERS_PACKAGE_NAME)
  handlers_package_path = (
    f'{sys.modules[__name__].__package__}.{utils_update.HANDLERS_PACKAGE_NAME}')

  return utils_update.get_versions_and_functions(
    minimum_version,
    maximum_version,
    handlers_package_dirpath,
    handlers_package_path,
    utils_update.UPDATE_HANDLER_MODULE_PREFIX,
    utils_update.UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX,
    utils_update.UPDATE_HANDLER_FUNC_NAME,
    include_next=True,
  )


def _remove_no_longer_available_commands(data):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_no_longer_available = _remove_no_longer_available_commands_for_group(
      main_settings_list, 'actions')
    conditions_no_longer_available = _remove_no_longer_available_commands_for_group(
      main_settings_list, 'conditions')

    return actions_no_longer_available + conditions_no_longer_available
  else:
    return []


def _remove_no_longer_available_commands_for_group(main_settings_list, command_group_name):
  commands_no_longer_available = []

  commands_list, _index = update_utils_.get_child_group_list(main_settings_list, command_group_name)

  if commands_list is not None:
    for command_dict in commands_list:
      command_list = command_dict['settings']

      orig_name_setting_dict, _index = update_utils_.get_child_setting(command_list, 'orig_name')
      origin_setting_dict, _index = update_utils_.get_child_setting(command_list, 'origin')

      orig_name = orig_name_setting_dict['value']

      if origin_setting_dict['value'] in ['gimp_pdb', 'gegl'] and orig_name not in pdb:
        commands_no_longer_available.append(orig_name)

    for orig_name in commands_no_longer_available:
      update_utils_.remove_command_by_orig_names(commands_list, orig_name)

  return commands_no_longer_available


def _format_commands_no_longer_available_message(commands_no_longer_available):
  alternative_commands = {
    'gegl:gray': 'gimp:desaturate',
    'gegl:posterize': 'gimp:desaturate',
    'gegl:threshold': 'gimp:threshold',
    'gegl:wavelet-blur': 'plug-in-wavelet-decompose',
  }

  processed_commands_no_longer_available = []
  for name in commands_no_longer_available:
    if name in alternative_commands:
      processed_commands_no_longer_available.append(
        _('{} (you may use "{}")').format(name, alternative_commands[name]))
    else:
      processed_commands_no_longer_available.append(name)

  return _(
    'The following actions or conditions are no longer available and have been removed:\n\n{}'
  ).format('\n'.join(processed_commands_no_longer_available))
