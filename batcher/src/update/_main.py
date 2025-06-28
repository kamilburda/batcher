"""Main logic of updating settings to the latest version."""

import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union


from config import CONFIG
from src import setting as setting_
from src import utils_setting as utils_setting_
from src import version as version_
from src.procedure_groups import *

from . import _utils as update_utils_
from ._handlers import update_0_3
from ._handlers import update_0_4
from ._handlers import update_0_5
from ._handlers import update_0_6
from ._handlers import update_0_7
from ._handlers import update_0_8
from ._handlers import update_1_0_rc1
from ._handlers import update_1_0_rc2
from ._handlers import update_1_1
from ._handlers import update_1_2


__all__ = [
  'load_and_update',
  'UpdateStatuses',
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
      processed_update_handlers = _get_update_handlers()
    else:
      processed_update_handlers = update_handlers

    if not processed_update_handlers:
      return data

    if previous_version is None:
      raise setting_.SourceModifyDataError(_('Failed to obtain the previous plug-in version.'))

    for version_str, update_handler in processed_update_handlers.items():
      if previous_version < version_.Version.parse(version_str) <= current_version:
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


def _get_update_handlers() -> Dict[str, Callable]:
  return _UPDATE_HANDLERS


_UPDATE_HANDLERS = {
  '0.3': update_0_3.update,
  '0.4': update_0_4.update,
  '0.5': update_0_5.update,
  '0.6': update_0_6.update,
  '0.7': update_0_7.update,
  '0.8': update_0_8.update,
  '1.0-RC1': update_1_0_rc1.update,
  '1.0-RC2': update_1_0_rc2.update,
  '1.1': update_1_1.update,
  '1.2': update_1_2.update,
}
