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


def load_and_update(
      settings: pg.setting.Group,
      handle_invalid: str = 'ask_to_clear',
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
      update_sources: bool = True,
) -> Tuple[int, str]:
  """Loads and updates settings and setting sources to the latest version of the
  plug-in.
  
  Updating includes renaming settings or replacing obsolete settings.
  
  ``handle_invalid`` is a string indicating how to handle a failed update:

    * ``'ask_to_clear'`` - a message is displayed asking the user whether to
      clear settings. If the user chose to clear the settings, `CLEAR_SETTINGS`
      is returned, `TERMINATE` otherwise.
    
    * ``'clear'`` - settings will be cleared unconditionally and
      `CLEAR_SETTINGS` is returned.
    
    * any other value - no action is taken and `TERMINATE` is returned.
  
  If ``sources`` is ``None``, default setting sources are used. Otherwise,
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
    cancelled clearing settings interactively, or if the update failed (e.g.
    because of a malformed setting source).

  If ``update_sources`` is ``True``, the contents of ``sources`` are updated
  (overwritten), otherwise they are kept intact.
  """
  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()

  load_result = settings.load(sources)
  load_message = utils_.format_message_from_persistor_statuses(load_result.statuses_per_source)

  if any(status == pg.setting.Persistor.FAIL
         for status in load_result.statuses_per_source.values()):
    return TERMINATE, load_message

  if _is_fresh_start(sources):
    utils_.update_plugin_version(settings, sources, save_to_sources=update_sources)
    return FRESH_START, ''

  current_version = version_.Version.parse(pg.config.PLUGIN_VERSION)

  previous_version = _get_previous_version(settings)

  if previous_version is not None:
    if previous_version == current_version:
      return NO_ACTION, load_message
    else:
      utils_.update_plugin_version(settings, sources, save_to_sources=update_sources)

      handle_update(
        settings,
        sources,
        _UPDATE_HANDLERS,
        previous_version,
        current_version,
        update_sources=update_sources,
      )

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


def _get_previous_version(settings):
  try:
    return version_.Version.parse(settings['main/plugin_version'].value)
  except (version_.InvalidVersionFormatError, TypeError):
    return None


def handle_update(
      settings,
      sources,
      handlers,
      previous_version,
      current_version,
      update_sources=True,
):
  if not handlers:
    return

  if update_sources:
    for source in sources.values():
      source.clear()

  for version_str, update_handler in handlers.items():
    if previous_version < version_.Version.parse(version_str) <= current_version:
      update_handler(settings, sources)

  if update_sources:
    settings.save(sources)


def _is_fresh_start(sources):
  return all(not source.has_data() for source in sources.values())


def _update_to_0_3(settings, sources):
  _update_actions_to_0_3(settings, 'procedures')
  _update_actions_to_0_3(settings, 'constraints')

  if 'file_extension' in settings['main']:
    settings['main/file_extension'].gui.auto_update_gui_to_setting(False)

  if 'output_directory' in settings['main']:
    settings['main/output_directory'].gui.auto_update_gui_to_setting(False)

  if 'layer_filename_pattern' in settings['main']:
    settings['main/layer_filename_pattern'].gui.auto_update_gui_to_setting(False)

  if 'show_more_settings' in settings['gui']:
    settings['gui'].remove(['show_more_settings'])

  if 'dialog_size' in settings['gui/size']:
    settings['gui/size/dialog_size'].reset()

  if 'paned_outside_previews_position' in settings['gui/size']:
    settings['gui/size/paned_outside_previews_position'].reset()

  if 'paned_between_previews_position' in settings['gui/size']:
    settings['gui/size/paned_between_previews_position'].reset()


def _update_actions_to_0_3(settings, action_type):
  for action in settings[f'main/{action_type}']:
    action['display_options_on_create'].set_value(False)

    if 'more_options' not in action:
      more_options_group = pg.setting.Group(
        'more_options',
        setting_attributes={
          'pdb_type': None,
        })
      action.add([more_options_group])
      action.reorder('more_options', -2)

    if 'enabled_for_previews' in action and 'enabled_for_previews' not in action['more_options']:
      enabled_for_previews_setting = action['enabled_for_previews']
      action.remove(['enabled_for_previews'])
      action['more_options'].add([enabled_for_previews_setting])

    if ('also_apply_to_parent_folders' in action
        and 'also_apply_to_parent_folders' not in action['more_options']):
      also_apply_to_parent_folders_setting = action['also_apply_to_parent_folders']
      action.remove(['also_apply_to_parent_folders'])
      action['more_options'].add([also_apply_to_parent_folders_setting])


_UPDATE_HANDLERS = {
  '0.3': _update_to_0_3,
}
