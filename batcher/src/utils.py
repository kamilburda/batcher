"""Utility functions used in other modules."""

from typing import Any, Dict

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


def format_message_from_persistor_statuses(
      persistor_result: pg.setting.PersistorResult,
      separator: str = '\n',
) -> str:
  messages = get_messages_from_persistor_statuses(persistor_result).values()

  return separator.join(message for message in messages if message)


def get_messages_from_persistor_statuses(
      persistor_result: pg.setting.PersistorResult,
) -> Dict[pg.setting.Source, str]:
  messages = {}

  if not persistor_result.statuses_per_source:
    return messages

  if persistor_result.messages_per_source:
    messages_per_source = persistor_result.messages_per_source
  else:
    messages_per_source = {}

  for source, status in persistor_result.statuses_per_source.items():
    message = messages_per_source.get(source, '')

    if status == pg.setting.Persistor.FAIL:
      if hasattr(source, 'filepath'):
        formatted_message = _(
          'Settings stored in "{}" may be corrupt.'
          ' This could happen if the file was edited manually.'
          ' To fix this, save the settings again.').format(source.filepath)
        if message:
          formatted_message += _(' More information: {}').format(message)
        messages[source] = formatted_message
      else:
        formatted_message = _(
          'Settings for this plug-in may be corrupt.'
          ' To fix this, save the settings again or reset them.')
        if message:
          formatted_message += _('More information: {}').format(message)
        messages[source] = formatted_message
    elif status == pg.setting.Persistor.SOURCE_NOT_FOUND:
      if hasattr(source, 'filepath'):
        messages[source] = _('Count not locate settings in file "{}" in "{}".').format(
          source.filepath, source.name)
      else:
        messages[source] = _('Count not locate settings in "{}".').format(source.name)
    else:
      messages[source] = ''

  return messages
