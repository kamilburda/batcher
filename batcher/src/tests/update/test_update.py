import unittest
import unittest.mock as mock

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import update


def _update_to_0_3(data, _settings, _procedure_groups):
  return data


def _update_to_0_4(data, _settings, _procedure_groups):
  return data


def _update_to_0_3_with_error(_data, _settings, _procedure_groups):
  raise ValueError


_UPDATE_HANDLERS = {
  '0.3': _update_to_0_3,
  '0.4': _update_to_0_4,
}


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
@mock.patch(
  'batcher.src.tests.update.test_update.update._UPDATE_HANDLERS',
  new_callable=lambda: dict(_UPDATE_HANDLERS))
class TestUpdate(unittest.TestCase):
  
  def setUp(self):
    self.settings = pg.setting.create_groups({
      'name': 'all_settings',
      'groups': [
        {
          'name': 'main',
        }
      ]
    })

    self.orig_config_version = pg.config.PLUGIN_VERSION

    self.current_version = '1.0'
    
    self.settings['main'].add([
      {
        'type': 'string',
        'name': 'plugin_version',
        'default_value': self.current_version,
        'pdb_type': None,
        'gui_type': None,
      },
      {
        'type': 'string',
        'name': 'test_setting',
        'default_value': 'test',
        'pdb_type': None,
        'gui_type': None,
      },
    ])

    self.source = pg.setting.SimpleInMemorySource('test_settings')

    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [
          {
            'name': 'main',
            'settings': [
              {
                'type': 'string',
                'name': 'plugin_version',
                'value': self.current_version,
                'default_value': self.current_version,
                'gui_type': None,
                'pdb_type': None,
              },
              {
                'type': 'string',
                'name': 'test_setting',
                'value': 'test',
                'default_value': 'test',
                'gui_type': None,
                'pdb_type': None,
              },
            ],
          },
        ],
      },
    ]

    self._spy_on_source(self.source)

  def tearDown(self):
    pg.config.PLUGIN_VERSION = self.orig_config_version
  
  def test_fresh_start_saves_all_settings(self, *mocks):
    source = pg.setting.Persistor.get_default_setting_sources()['persistent']

    self.assertFalse(source.has_data())

    self._spy_on_source(source)

    status, _message = update.load_and_update(self.settings)
    
    self.assertEqual(status, update.FRESH_START)

    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)

    source.write.assert_called_once()
    source.clear.assert_called_once()

  def test_fresh_start_without_updating_sources(self, *mocks):
    source = pg.setting.Persistor.get_default_setting_sources()['persistent']

    self.assertFalse(source.has_data())

    self._spy_on_source(source)

    status, _message = update.load_and_update(self.settings, update_sources=False)

    self.assertEqual(status, update.FRESH_START)

    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)

    source.write.assert_not_called()
    source.clear.assert_not_called()

  def test_update_unchanged_plugin_version_does_not_trigger_update(self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.1')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.1')

    self.source.read.assert_called_once()
    # Sources should not be updated for the same version.
    self.source.write.assert_not_called()
    self.source.clear.assert_not_called()

  def test_update_changed_plugin_version_with_no_handler_does_not_trigger_update_and_updates_source(
        self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.2')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.2')

    self.source.read.assert_called_once()
    # Sources should be updated to write the new version.
    self.source.write.assert_called_once()
    self.source.clear.assert_called_once()

    update_handlers['0.3'].assert_not_called()
    update_handlers['0.4'].assert_not_called()

  def test_update_plugin_version_with_no_handler_does_not_trigger_update(
        self, update_handlers, *mocks):
    update_handlers.clear()

    self.set_previous_version('0.1')
    self.set_current_version('0.2')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.2')

    self.source.read.assert_called_once()
    # Sources should be updated to write the new version.
    self.source.write.assert_called_once()
    self.source.clear.assert_called_once()

  def test_update_with_one_handler(self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.3')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.3')

    self.source.read.assert_called_once()
    self.source.write.assert_called_once()
    self.source.clear.assert_called_once()

    update_handlers['0.3'].assert_called_once()
    update_handlers['0.4'].assert_not_called()

  def test_update_with_multiple_handlers(self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.4')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.4')

    self.source.read.assert_called_once()
    self.source.write.assert_called_once()
    self.source.clear.assert_called_once()

    update_handlers['0.3'].assert_called_once()
    update_handlers['0.4'].assert_called_once()

  def test_update_without_updating_sources(self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.4')

    status, _message = update.load_and_update(
      self.settings, sources={'persistent': self.source}, update_sources=False)

    self.assertEqual(status, update.UPDATE)

    self.assertEqual(self.settings['main/plugin_version'].value, '0.4')

    self.source.read.assert_called_once()
    self.source.write.assert_not_called()
    self.source.clear.assert_not_called()

    update_handlers['0.3'].assert_called_once()
    update_handlers['0.4'].assert_called_once()

  def test_update_failing_to_parse_previous_version_returns_terminate(
        self, update_handlers, *mocks):
    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('invalid_version')
    self.set_current_version('0.4')

    status, _message = update.load_and_update(self.settings, sources={'persistent': self.source})

    self.assertEqual(status, update.TERMINATE)

    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)

    self.source.read.assert_called_once()
    self.source.write.assert_not_called()
    self.source.clear.assert_not_called()

    update_handlers['0.3'].assert_not_called()
    update_handlers['0.4'].assert_not_called()

  def test_update_any_failure_in_update_handling_returns_terminate(self, update_handlers, *mocks):
    update_handlers['0.3'] = _update_to_0_3_with_error

    self._spy_on_update_handlers(update_handlers)

    self.set_previous_version('0.1')
    self.set_current_version('0.4')

    status, _message = update.load_and_update(
      self.settings, sources={'persistent': self.source}, update_sources=False)

    self.assertEqual(status, update.TERMINATE)

    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)

    self.source.read.assert_called_once()
    self.source.write.assert_not_called()
    self.source.clear.assert_not_called()

    update_handlers['0.3'].assert_called_once()
    update_handlers['0.4'].assert_not_called()

  @staticmethod
  def _spy_on_source(source):
    source.read = mock.Mock(wraps=source.read)
    source.write = mock.Mock(wraps=source.write)
    source.clear = mock.Mock(wraps=source.clear)

  @staticmethod
  def _spy_on_update_handlers(update_handlers):
    for key, function in update_handlers.items():
      update_handlers[key] = mock.Mock(wraps=function)

  def set_previous_version(self, version):
    previous_version_dict = self.source.data[0]['settings'][0]['settings'][0]
    previous_version_dict['value'] = version
    previous_version_dict['default_value'] = version

  @staticmethod
  def set_current_version(version):
    pg.config.PLUGIN_VERSION = version
