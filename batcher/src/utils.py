"""Utility functions used in other modules."""

from typing import Any, Dict, List, Optional, Union

import pygimplib as pg


def get_settings_for_batcher(main_settings: pg.setting.Group) -> Dict[str, Any]:
  return {
    'procedures': main_settings['procedures'],
    'constraints': main_settings['constraints'],
    'edit_mode': main_settings['edit_mode'].value,
    'output_directory': main_settings['output_directory'].value,
    'layer_filename_pattern': main_settings['layer_filename_pattern'].value,
    'file_extension': main_settings['file_extension'].value,
    'overwrite_mode': main_settings['overwrite_mode'].value,
  }


def clear_setting_sources(
      settings: pg.setting.Group,
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
):
  if sources is None:
    sources = pg.setting.Persistor.get_default_setting_sources()
  
  pg.setting.Persistor.clear(sources)
  
  update_plugin_version(settings, sources)


def format_message_from_persistor_statuses(
      statuses_per_source: Dict[pg.setting.Source, int],
      separator: str = '\n',
) -> str:
  return separator.join(
    message for message in get_messages_from_persistor_statuses(statuses_per_source).values()
    if message)


def get_messages_from_persistor_statuses(
      statuses_per_source: Dict[pg.setting.Source, int]
) -> Dict[pg.setting.Source, str]:
  messages_per_source = {}

  for source, status in statuses_per_source.items():
    if status == pg.setting.Persistor.FAIL:
      if hasattr(source, 'filepath'):
        message = _(
          'Settings for this plug-in stored in "{}" may be corrupt.'
          ' This could happen if the file was edited manually.'
          '\nTo fix this, save the settings again or reset them.').format(source.filepath)
      else:
        message = _(
          'Settings for this plug-in may be corrupt.'
          '\nTo fix this, save the settings again or reset them.')

      messages_per_source[source] = message
    elif status == pg.setting.Persistor.SOURCE_NOT_FOUND:
      if hasattr(source, 'filepath'):
        messages_per_source[source] = _('Count not locate settings in file "{}" in "{}".').format(
          source.filepath, source.name)
      else:
        messages_per_source[source] = _('Count not locate settings in "{}".').format(
          source.name)
    else:
      messages_per_source[source] = ''

  return messages_per_source


def update_plugin_version(
      settings: pg.setting.Group,
      sources: Optional[Dict[str, Union[pg.setting.Source, List[pg.setting.Source]]]] = None,
      save_to_sources: bool = True,
):
  settings['main/plugin_version'].reset()
  if save_to_sources:
    settings['main/plugin_version'].save(sources)
