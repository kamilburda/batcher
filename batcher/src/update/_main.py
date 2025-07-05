"""Main logic of updating settings to the latest version."""

import importlib
import os
import pkgutil
import sys
import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union


from config import CONFIG
from src import setting as setting_
from src import utils_setting as utils_setting_
from src import utils
from src import version as version_
from src.procedure_groups import *

from . import _utils as update_utils_


__all__ = [
  'load_and_update',
  'UpdateStatuses',
  'get_versions_and_functions',
  'HANDLERS_PACKAGE_NAME',
  'UPDATE_HANDLER_MODULE_PREFIX',
  'UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX',
]


class UpdateStatuses:

  UPDATE_STATUSES = (
    FRESH_START,
    UPDATE,
    TERMINATE,
  ) = (
    'fresh_start',
    'update',
    'terminate',
  )


HANDLERS_PACKAGE_NAME = '_handlers'
UPDATE_HANDLER_MODULE_PREFIX = 'update_'
UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX = '_next'


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
    nonlocal current_version, previous_version

    current_version = version_.Version.parse(CONFIG.PLUGIN_VERSION)

    previous_version = _get_plugin_version(data)
    _update_plugin_version(data, current_version)

    if update_handlers is None:
      processed_update_handlers = _get_update_handlers(previous_version, current_version)
    else:
      processed_update_handlers = [
        handler for version_str, handler in update_handlers.items()
        if previous_version < version_.Version.parse(version_str) <= current_version
      ]

    if previous_version is None:
      raise setting_.SourceModifyDataError(_('Failed to obtain the previous plug-in version.'))

    if not processed_update_handlers:
      return data

    for update_handler in processed_update_handlers:
      update_handler(data, settings, procedure_groups)

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

  return UpdateStatuses.UPDATE, load_message


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
  module_filepath = utils.get_current_module_filepath()
  handlers_package_dirpath = os.path.join(os.path.dirname(module_filepath), HANDLERS_PACKAGE_NAME)
  handlers_package_path = f'{sys.modules[__name__].__package__}.{HANDLERS_PACKAGE_NAME}'

  return get_versions_and_functions(
    minimum_version,
    maximum_version,
    handlers_package_dirpath,
    handlers_package_path,
    UPDATE_HANDLER_MODULE_PREFIX,
    UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX,
    'update',
    include_next=True,
  )


def get_versions_and_functions(
      minimum_version: version_.Version,
      maximum_version: version_.Version,
      package_dirpath: str,
      package_path: str,
      module_prefix: str,
      next_version_suffix: str,
      function_name: str,
      include_next: bool,
      match_minimum_version: bool = False,
):
  functions_and_versions = []
  next_function = None

  for _module_info, module_name, is_package in pkgutil.walk_packages(path=[package_dirpath]):
    if is_package:
      continue

    if module_name.startswith(module_prefix):
      module_path = f'{package_path}.{module_name}'

      if module_name.endswith(next_version_suffix):
        if include_next:
          next_module = importlib.import_module(module_path)
          next_function = getattr(next_module, function_name)
      else:
        try:
          version_from_module = _get_version_from_module_name(module_name, module_prefix)
        except Exception as e:
          print(f'could not parse version from module {module_name}; reason: {e}', file=sys.stderr)
        else:
          if match_minimum_version:
            matches_version = minimum_version <= version_from_module <= maximum_version
          else:
            matches_version = minimum_version < version_from_module <= maximum_version

          if matches_version:
            module = importlib.import_module(module_path)

            functions_and_versions.append((getattr(module, function_name), version_from_module))

  functions_and_versions.sort(key=lambda item: item[1])
  functions = [item[0] for item in functions_and_versions]

  if next_function is not None:
    functions.append(next_function)

  return functions


def _get_version_from_module_name(
      module_name: str,
      module_prefix: str,
) -> version_.Version:
  version_str = module_name[len(module_prefix):]

  version_numbers_and_prerelease_components = version_str.split('__')
  if len(version_numbers_and_prerelease_components) > 1:
    version_numbers_str, prerelease_str = version_numbers_and_prerelease_components[:2]
  else:
    version_numbers_str = version_numbers_and_prerelease_components[0]
    prerelease_str = None

  version_number_components_str = version_numbers_str.split('_')
  major_number = int(version_number_components_str[0])
  minor_number = None
  patch_number = None
  prerelease = None
  prerelease_patch_number = None

  if len(version_number_components_str) == 2:
    minor_number = int(version_number_components_str[1])
  elif len(version_number_components_str) > 2:
    minor_number = int(version_number_components_str[1])
    patch_number = int(version_number_components_str[2])

  if prerelease_str is not None:
    prerelease_components_str = prerelease_str.split('_')
    prerelease = prerelease_components_str[0]

    if len(prerelease_components_str) > 1:
      prerelease_patch_number = int(prerelease_components_str[1])

  return version_.Version(
    major=major_number,
    minor=minor_number,
    patch=patch_number,
    prerelease=prerelease,
    prerelease_patch=prerelease_patch_number,
  )
