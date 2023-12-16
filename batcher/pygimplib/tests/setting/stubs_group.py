"""Stubs primarily to be used in the `test_group` module."""

from ...setting import group as group_


def create_test_settings():
  settings = group_.Group('main')
  settings.add([
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'bmp',
      'display_name': 'File extension',
    },
    {
      'type': 'bool',
      'name': 'flatten',
      'default_value': False,
      'display_name': 'Flatten',
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': [('replace', 'Replace'),
                ('skip', 'Skip'),
                ('rename_new', 'Rename new file'),
                ('rename_existing', 'Rename existing file')],
    },
  ])
  
  return settings


def create_test_settings_hierarchical():
  main_settings = group_.Group('main')
  main_settings.add([
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'bmp',
      'display_name': 'File extension',
    },
  ])
  
  advanced_settings = group_.Group('advanced')
  advanced_settings.add([
    {
      'type': 'bool',
      'name': 'flatten',
      'default_value': False,
      'display_name': 'Flatten',
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': [('replace', 'Replace'),
                ('skip', 'Skip'),
                ('rename_new', 'Rename new file'),
                ('rename_existing', 'Rename existing file')],
    },
  ])
  
  settings = group_.Group('settings')
  settings.add([main_settings, advanced_settings])
  
  return settings


def create_test_settings_for_persistor():
  main_settings = group_.Group(name='main')
  
  main_settings.add([
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
    },
  ])
  
  advanced_settings = group_.Group(name='advanced')
  
  advanced_settings.add([
    {
      'type': 'bool',
      'name': 'flatten',
      'default_value': False,
      'tags': ['ignore_load', 'ignore_save'],
    },
    {
      'type': 'bool',
      'name': 'use_layer_size',
      'default_value': False,
    },
  ])
  
  settings = group_.Group('settings')
  settings.add([main_settings, advanced_settings])
  
  return settings
