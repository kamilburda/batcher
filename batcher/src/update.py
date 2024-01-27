"""Updating the plug-in to the latest version."""

from typing import Dict, List, Optional, Tuple, Union

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import utils as utils_
from src import version as version_
from src.gui import messages

_UPDATE_STATUSES = FRESH_START, UPDATE, CLEAR_SETTINGS, NO_ACTION, TERMINATE = 0, 1, 2, 3, 4


def update(
      settings: pg.setting.Group,
      handle_invalid: str = 'ask_to_clear',
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
) -> Tuple[int, str]:
  """Updates settings and setting sources to the latest version of the plug-in.
  
  This includes renaming settings or replacing obsolete actions.
  
  ``handle_invalid`` is a string indicating how to handle a failed update:
    
    * ``'ask_to_clear'`` - a message is displayed asking the user whether to
      clear settings. If the user chose to clear the settings, `CLEAR_SETTINGS`
      is returned, `TERMINATE` otherwise.
    
    * ``'clear'`` - settings will be cleared unconditionally and
      `CLEAR_SETTINGS` is returned.
    
    * any other value - no action is taken and `TERMINATE` is returned.
  
  If ``sources`` is ``None``, default setting sources are updated. Otherwise,
  ``sources`` must be a dictionary of (key, source) pairs.
  
  Two values are returned - status and an accompanying message.
  
  Status can have one of the following integer values:
  
  * `FRESH_START` - The plug-in was never used before or has no settings stored.
  
  * `UPDATE` - The plug-in was successfully updated to the latest version.
  
  * `CLEAR_SETTINGS` - An old version of the plug-in (incompatible with the
    changes in later versions) was used that required clearing stored settings.
  
  * `NO_ACTION` - No update was performed as the plug-in version remains the
    same.
  
  * `TERMINATE` - No update was performed. This value is returned if the user
    cancelled clearing settings interactively.
  """
  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()

  if _is_fresh_start(sources):
    utils_.save_plugin_version(settings, sources)
    return FRESH_START, ''

  current_version = version_.Version.parse(pg.config.PLUGIN_VERSION)

  previous_version, load_status, load_message = _load_previous_version(settings)

  if load_status == pg.setting.Persistor.SUCCESS and previous_version is not None:
    if previous_version == current_version:
      return NO_ACTION, load_message
    else:
      settings['main/plugin_version'].reset()

      handle_update(
        settings,
        sources,
        _UPDATE_HANDLERS,
        previous_version,
        current_version)

      return UPDATE, load_message

  if handle_invalid == 'ask_to_clear':
    response = messages.display_message(
      _('Due to significant changes in the plug-in, settings need to be reset. Proceed?'),
      Gtk.MessageType.WARNING,
      buttons=Gtk.ButtonsType.YES_NO,
      button_response_id_to_focus=Gtk.ResponseType.NO)

    if response == Gtk.ResponseType.YES:
      utils_.clear_setting_sources(settings, sources)
      return CLEAR_SETTINGS, load_message
    else:
      return TERMINATE, load_message
  elif handle_invalid == 'clear':
    utils_.clear_setting_sources(settings, sources)
    return CLEAR_SETTINGS, load_message
  else:
    return TERMINATE, load_message


def _load_previous_version(settings):
  load_result = settings['main/plugin_version'].load()

  try:
    previous_version = version_.Version.parse(settings['main/plugin_version'].value)
  except (version_.InvalidVersionFormatError, TypeError):
    previous_version = None
    load_status = pg.setting.Persistor.FAIL
    load_message = ''
  else:
    if any(status == pg.setting.Persistor.SOURCE_NOT_FOUND
           for status in load_result.statuses_per_source.values()):
      # Ignore sources if missing
      load_status = pg.setting.Persistor.SUCCESS
      load_message = ''
    else:
      load_status = load_result.status
      load_message = utils_.format_message_from_persistor_statuses(load_result.statuses_per_source)

  return previous_version, load_status, load_message


def handle_update(
      settings,
      sources,
      update_handlers,
      previous_version,
      current_version):
  if not update_handlers:
    return

  for source in sources.values():
    source.clear()

  for version_str, update_handler in update_handlers.items():
    if previous_version < version_.Version.parse(version_str) <= current_version:
      update_handler(settings, sources)

  settings.save(sources)


def _is_fresh_start(sources):
  return all(not source.has_data() for source in sources.values())


_UPDATE_HANDLERS = {}
