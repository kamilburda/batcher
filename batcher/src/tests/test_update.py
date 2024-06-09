import unittest
import unittest.mock as mock

import parameterized

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import update
from src import version as version_


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('batcher.src.tests.test_update.update.handle_update')
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
    
    self.previous_version = '0.1.0'
    self.current_version = '1.0.0'
    
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
  
  def test_fresh_start_stores_current_version(self, *mocks):
    self.assertFalse(pg.setting.Persistor.get_default_setting_sources()['persistent'].has_data())

    status, _unused = update.load_and_update(self.settings)
    
    self.assertEqual(status, update.FRESH_START)
    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)
    
    load_result = self.settings['main/plugin_version'].load()

    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)
    self.assertEqual(load_result.status, pg.setting.Persistor.SUCCESS)

  @mock.patch('batcher.src.update.version_.Version.parse')
  @mock.patch('batcher.src.tests.test_update.update._get_previous_version')
  def test_minimum_version_or_later_is_overwritten_by_current_version(
        self, mock_get_previous_version, mock_version_parse, *mocks):
    mock_get_previous_version.return_value = self.previous_version
    mock_version_parse.return_value = self.current_version

    self.settings['main/plugin_version'].set_value(self.previous_version)
    self.settings['main/plugin_version'].save()
    
    status, _unused = update.load_and_update(self.settings)
    
    self.assertEqual(status, update.UPDATE)
    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)

  @mock.patch('batcher.src.update.version_.Version.parse')
  @mock.patch('batcher.src.tests.test_update.update._get_previous_version')
  def test_previous_version_is_not_valid_returns_terminate(
        self, mock_get_previous_version, mock_version_parse, *mocks):
    mock_get_previous_version.return_value = None
    mock_version_parse.return_value = self.current_version

    status, _unused = update.load_and_update(self.settings)

    self.assertEqual(status, update.TERMINATE)
    self.assertEqual(self.settings['main/plugin_version'].value, self.current_version)


class TestHandleUpdate(unittest.TestCase):
  
  def setUp(self):
    self.update_handlers = {
      '3.3.1': lambda *args, **kwargs: self._invoked_handlers.append('3.3.1'),
      '3.4': lambda *args, **kwargs: self._invoked_handlers.append('3.4'),
      '3.5': lambda *args, **kwargs: self._invoked_handlers.append('3.5'),
    }
    
    self._invoked_handlers = []
    
    self.settings = pg.setting.Group('settings')
  
  @parameterized.parameterized.expand([
    ['previous_version_earlier_than_all_handlers_invoke_one_handler',
     '3.3', '3.3.1', ['3.3.1']],
    ['previous_version_earlier_than_all_handlers_invoke_multiple_handlers',
     '3.3', '3.4', ['3.3.1', '3.4']],
    ['equal_previous_and_current_version_invoke_no_handler',
     '3.5', '3.5', []],
    ['equal_previous_and_current_version_and_globally_not_latest_invoke_no_handler',
     '3.3.1', '3.3.1', []],
    ['previous_version_equal_to_first_handler_invoke_one_handler',
     '3.3.1', '3.4', ['3.4']],
    ['previous_version_equal_to_latest_handler_invoke_no_handler',
     '3.5', '3.6', []],
    ['previous_greater_than_handlers_invoke_no_handler',
     '3.6', '3.6', []],
  ])
  def test_handle_update(
        self,
        test_case_suffix,
        previous_version_str,
        current_version_str,
        invoked_handlers):
    update.handle_update(
      self.settings,
      {},
      self.update_handlers,
      version_.Version.parse(previous_version_str),
      version_.Version.parse(current_version_str),
    )
    
    self.assertEqual(self._invoked_handlers, invoked_handlers)
