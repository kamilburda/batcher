import unittest
import unittest.mock as mock

from ... import utils as pgutils

from ...setting import group as group_
from ...setting import persistor as persistor_
from ...setting import settings as settings_
from ...setting import sources as sources_

from .. import stubs_gimp
from . import stubs_group
from . import stubs_setting
from . import stubs_sources


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestPersistor(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.orig_default_setting_sources = persistor_.Persistor.get_default_setting_sources()
  
  @classmethod
  def tearDownClass(cls):
    persistor_.Persistor.set_default_setting_sources(cls.orig_default_setting_sources)

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp')
  def setUp(self, mock_gimp_module):
    mock_gimp_module.directory.return_value = 'gimp_directory'

    self.settings = stubs_group.create_test_settings()
    # FIXME: This is a temporary fix until a proper session source is implemented.
    self.session_source = sources_.GimpParasiteSource('plug-in-session', source_type='session')
    self.persistent_source = sources_.GimpParasiteSource('plug-in-persistent')
    
    self.sources_for_persistor = {
      'session': self.session_source,
      'persistent': self.persistent_source,
    }
    self.session_source_for_persistor = {'session': self.session_source}
    
    persistor_.Persistor.set_default_setting_sources(None)
    mock_gimp_module.parasites = {}
  
  def test_set_default_setting_sources_none(self, *mocks):
    persistor_.Persistor.set_default_setting_sources(None)
    self.assertFalse(persistor_.Persistor.get_default_setting_sources())
  
  def test_set_default_setting_sources_raises_error_on_invalid_input(self, *mocks):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      persistor_.Persistor.set_default_setting_sources(['persistent'])
  
  def test_get_default_setting_sources_returns_copy(self, *mocks):
    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    result = persistor_.Persistor.get_default_setting_sources()
    
    self.assertDictEqual(result, self.sources_for_persistor)
    self.assertNotEqual(id(result), id(self.sources_for_persistor))
  
  def test_load_save(self, *mocks):
    self._test_load_save(self.sources_for_persistor)
  
  def test_load_save_with_default_sources(self, *mocks):
    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    self._test_load_save(None)

  # noinspection PyUnresolvedReferences
  def test_load_save_with_default_sources_as_dict_of_lists(self, *mocks):
    session_source = stubs_sources.StubSource('session', 'session')
    
    self._spy_for_source(self.persistent_source)
    self._spy_for_source(self.session_source)
    self._spy_for_source(session_source)
    
    persistor_.Persistor.set_default_setting_sources({
      'session': [self.session_source, session_source],
      'persistent': self.persistent_source,
    })
    
    self._test_load_save(None)
    
    self.assertEqual(self.session_source.read.call_count, 1)
    self.assertEqual(self.session_source.write.call_count, 1)
    self.assertEqual(session_source.read.call_count, 0)
    self.assertEqual(session_source.write.call_count, 1)
    self.assertEqual(self.persistent_source.read.call_count, 0)
    self.assertEqual(self.persistent_source.write.call_count, 1)

  # noinspection PyUnresolvedReferences
  def test_load_save_with_default_sources_and_dict(self, *mocks):
    session_source = stubs_sources.StubSource('', 'session')
    
    self._spy_for_source(self.persistent_source)
    self._spy_for_source(self.session_source)
    self._spy_for_source(session_source)
    
    session_source_for_persistor = {'session': session_source}
    
    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    self._test_load_save(session_source_for_persistor)
    
    self.assertEqual(session_source.read.call_count, 1)
    self.assertEqual(session_source.write.call_count, 1)
    self.assertEqual(self.session_source.read.call_count, 0)
    self.assertEqual(self.session_source.write.call_count, 0)
    self.assertEqual(self.persistent_source.read.call_count, 0)
    self.assertEqual(self.persistent_source.write.call_count, 0)

  # noinspection PyUnresolvedReferences
  def test_load_save_with_default_sources_and_dict_of_lists(self, *mocks):
    session_source = stubs_sources.StubSource('', 'session')
    
    self._spy_for_source(self.persistent_source)
    self._spy_for_source(self.session_source)
    self._spy_for_source(session_source)
    
    session_source_for_persistor = {'session': [session_source, self.session_source]}
    
    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    self._test_load_save(session_source_for_persistor)
    
    self.assertEqual(session_source.read.call_count, 1)
    self.assertEqual(session_source.write.call_count, 1)
    self.assertEqual(self.session_source.read.call_count, 0)
    self.assertEqual(self.session_source.write.call_count, 1)
    self.assertEqual(self.persistent_source.read.call_count, 0)
    self.assertEqual(self.persistent_source.write.call_count, 0)

  # noinspection PyUnresolvedReferences
  def test_load_save_with_default_sources_and_list(self, *mocks):
    self._spy_for_source(self.persistent_source)
    self._spy_for_source(self.session_source)
    
    sources_for_persistor = ['session', 'persistent']
    default_sources = {
      'session': self.session_source,
      'persistent': self.persistent_source,
    }
    
    persistor_.Persistor.set_default_setting_sources(default_sources)
    
    self._test_load_save(sources_for_persistor)
    
    self.assertEqual(self.session_source.read.call_count, 1)
    self.assertEqual(self.session_source.write.call_count, 1)
    # `read` should not be called as all settings have been found in `self.session_source`.
    self.assertEqual(self.persistent_source.read.call_count, 0)
    self.assertEqual(self.persistent_source.write.call_count, 1)
  
  @staticmethod
  def _spy_for_source(source):
    source.read = mock.Mock(wraps=source.read)
    source.write = mock.Mock(wraps=source.write)
  
  def _test_load_save(self, sources_for_persistor):
    self.settings['file_extension'].set_value('png')
    self.settings['flatten'].set_value(True)
    
    result = persistor_.Persistor.save([self.settings], sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.SUCCESS)
    
    self.settings['file_extension'].set_value('jpg')
    self.settings['flatten'].set_value(False)
    
    result = persistor_.Persistor.load([self.settings], sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.SUCCESS)
    self.assertEqual(self.settings['file_extension'].value, 'png')
    self.assertEqual(self.settings['flatten'].value, True)
  
  def test_load_combine_settings_from_multiple_sources(self, *mocks):
    self.settings['file_extension'].set_value('png')
    self.settings['flatten'].set_value(True)
    self.session_source.write([self.settings['file_extension']])
    self.settings['file_extension'].set_value('jpg')
    self.persistent_source.write([self.settings['flatten'], self.settings['file_extension']])
    self.settings['file_extension'].set_value('gif')
    self.settings['flatten'].set_value(False)
    
    persistor_.Persistor.load([self.settings], self.sources_for_persistor)
    
    self.assertEqual(self.settings['file_extension'].value, 'png')
    self.assertEqual(self.settings['flatten'].value, True)
    
    for setting in self.settings:
      if setting not in [self.settings['file_extension'], self.settings['flatten']]:
        self.assertEqual(setting.value, setting.default_value)
  
  def test_load_multiple_setting_groups(self, *mocks):
    settings = stubs_group.create_test_settings_hierarchical()
    
    settings['main/file_extension'].set_value('png')
    settings['advanced/flatten'].set_value(True)
    self.session_source.write(settings.walk())
    settings['main/file_extension'].set_value('gif')
    settings['advanced/flatten'].set_value(False)
    
    persistor_.Persistor.load([settings], self.session_source_for_persistor)
    
    self.assertEqual(settings['main/file_extension'].value, 'png')
    self.assertEqual(settings['advanced/flatten'].value, True)
  
  def test_load_empty_settings(self, *mocks):
    result = persistor_.Persistor.load([], self.session_source_for_persistor)
    self.assertEqual(result.status, persistor_.Persistor.NO_SETTINGS)
  
  def test_load_no_default_source(self, *mocks):
    result = persistor_.Persistor.load([self.settings], None)
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
  
  def test_load_missing_default_source_from_list(self, *mocks):
    persistor_.Persistor.set_default_setting_sources(self.session_source_for_persistor)
    
    result = persistor_.Persistor.load([self.settings], ['persistent'])
    
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
  
  def test_load_settings_source_not_found(self, *mocks):
    result = persistor_.Persistor.load([self.settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['persistent']],
      persistor_.Persistor.SOURCE_NOT_FOUND)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['session']],
      persistor_.Persistor.SOURCE_NOT_FOUND)
    self.assertTrue(bool(result.settings_not_loaded))
  
  def test_load_settings_not_found(self, *mocks):
    self.session_source.write([self.settings['flatten']])
    self.persistent_source.write([self.settings['file_extension'], self.settings['flatten']])
    
    result = persistor_.Persistor.load(
      [self.settings['overwrite_mode']], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertTrue(bool(result.settings_not_loaded))
    self.assertListEqual(
      self.session_source.settings_not_loaded, [self.settings['overwrite_mode']])
    self.assertListEqual(
      self.persistent_source.settings_not_loaded, [self.settings['overwrite_mode']])
  
  def test_load_child_settings_not_found_in_first_but_subsequent_sources(self, *mocks):
    settings = stubs_group.create_test_settings_hierarchical()
    
    arguments_settings = group_.Group('arguments')
    arguments_settings.add([
      {
        'type': 'string',
        'name': 'tag',
        'default_value': 'background',
      }
    ])
    
    settings['advanced'].add([arguments_settings])
    
    self.persistent_source.write([settings])
    
    arguments_group = settings['advanced/arguments']
    overwrite_mode_setting = settings['advanced/overwrite_mode']
    
    settings['advanced'].remove(['overwrite_mode', 'arguments'])
    
    self.session_source.write([settings])
    
    settings['advanced'].add([overwrite_mode_setting, arguments_group])
    
    result = persistor_.Persistor.load([settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.SUCCESS)
    self.assertListEqual(
      self.session_source.settings_not_loaded,
      [settings['advanced/overwrite_mode'], settings['advanced/arguments/tag']])
    self.assertFalse(self.persistent_source.settings_not_loaded)
  
  def test_load_do_not_load_settings_with_source_name_not_matching_specified_sources(
        self, *mocks):
    settings = stubs_group.create_test_settings_with_specific_setting_sources()

    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    settings['main/file_extension'].set_value('jpg')
    settings['advanced/flatten'].set_value(True)
    settings['advanced/use_layer_size'].set_value(True)

    self.persistent_source.write([settings])
    self.session_source.write([settings])

    settings['main/file_extension'].reset()
    settings['advanced/use_layer_size'].reset()
    
    result = persistor_.Persistor.load([settings], ['session'])
    
    self.assertEqual(result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(result.settings_not_loaded, [settings['main/file_extension']])
    self.assertEqual(settings['main/file_extension'].value, 'png')
    self.assertEqual(settings['advanced/flatten'].value, True)
    self.assertEqual(settings['advanced/use_layer_size'].value, True)
  
  def test_load_fail_for_one_source(self, *mocks):
    persistor_.Persistor.save([self.settings], self.sources_for_persistor)
    
    self.session_source.read_data_from_source = mock.Mock(
      wraps=self.session_source.read_data_from_source)
    self.session_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    result = persistor_.Persistor.load([self.settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['persistent']],
      persistor_.Persistor.SUCCESS)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['session']],
      persistor_.Persistor.FAIL)
  
  def test_load_fail_for_all_sources(self, *mocks):
    persistor_.Persistor.save([self.settings], self.sources_for_persistor)
    
    self.session_source.read_data_from_source = mock.Mock(
      wraps=self.session_source.read_data_from_source)
    self.session_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    self.persistent_source.read_data_from_source = mock.Mock(
      wraps=self.persistent_source.read_data_from_source)
    self.persistent_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    result = persistor_.Persistor.load([self.settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['persistent']],
      persistor_.Persistor.FAIL)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['session']],
      persistor_.Persistor.FAIL)
  
  def test_save_empty_settings(self, *mocks):
    result = persistor_.Persistor.save([], self.session_source_for_persistor)
    self.assertEqual(result.status, persistor_.Persistor.NO_SETTINGS)
  
  def test_save_no_default_source(self, *mocks):
    result = persistor_.Persistor.save([self.settings], None)
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
  
  def test_save_missing_default_source_from_list(self, *mocks):
    persistor_.Persistor.set_default_setting_sources(self.session_source_for_persistor)
    
    result = persistor_.Persistor.save([self.settings], ['persistent'])
    
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
  
  def test_save_ignore_settings_with_source_name_not_matching_specified_sources(
        self, *mocks):
    settings = stubs_group.create_test_settings_with_specific_setting_sources()
    
    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    
    settings['main/file_extension'].set_value('jpg')
    settings['advanced/flatten'].set_value(True)
    settings['advanced/use_layer_size'].set_value(True)
    
    save_result = persistor_.Persistor.save([settings], ['session'])
    
    settings['main/file_extension'].reset()
    settings['advanced/flatten'].reset()
    settings['advanced/use_layer_size'].reset()
    
    load_result = persistor_.Persistor.load([settings], ['session'])
    
    self.assertEqual(save_result.status, persistor_.Persistor.SUCCESS)
    self.assertEqual(load_result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(load_result.settings_not_loaded, [settings['main/file_extension']])
    self.assertEqual(settings['main/file_extension'].value, 'png')
    # This setting is ignored
    self.assertEqual(settings['advanced/flatten'].value, False)
    self.assertEqual(settings['advanced/use_layer_size'].value, True)
    
    settings['main/file_extension'].set_value('jpg')
    
    save_result = persistor_.Persistor.save([settings], ['persistent'])
    
    settings['main/file_extension'].reset()
    settings['advanced/flatten'].reset()
    settings['advanced/use_layer_size'].reset()
    
    load_result = persistor_.Persistor.load([settings], ['persistent'])
    
    self.assertEqual(save_result.status, persistor_.Persistor.SUCCESS)
    self.assertEqual(load_result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(load_result.settings_not_loaded, [settings['advanced/use_layer_size']])
    self.assertEqual(settings['main/file_extension'].value, 'jpg')
    # This setting is ignored
    self.assertEqual(settings['advanced/flatten'].value, False)
    self.assertEqual(settings['advanced/use_layer_size'].value, False)
    
    self.assertFalse(settings['main/file_extension'].tags)
    self.assertSetEqual(settings['advanced/flatten'].tags, {'ignore_load', 'ignore_save'})
    self.assertFalse(settings['advanced/use_layer_size'].tags)
  
  def test_save_fail_for_one_source(self, *mocks):
    self.session_source.read_data_from_source = mock.Mock(
      wraps=self.session_source.read_data_from_source)
    self.session_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    result = persistor_.Persistor.save([self.settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.PARTIAL_SUCCESS)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['persistent']],
      persistor_.Persistor.SUCCESS)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['session']],
      persistor_.Persistor.FAIL)
  
  def test_save_fail_for_all_sources(self, *mocks):
    self.session_source.read_data_from_source = mock.Mock(
      wraps=self.session_source.read_data_from_source)
    self.session_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    self.persistent_source.read_data_from_source = mock.Mock(
      wraps=self.persistent_source.read_data_from_source)
    self.persistent_source.read_data_from_source.side_effect = sources_.SourceInvalidFormatError
    
    result = persistor_.Persistor.save([self.settings], self.sources_for_persistor)
    
    self.assertEqual(result.status, persistor_.Persistor.FAIL)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['persistent']],
      persistor_.Persistor.FAIL)
    self.assertEqual(
      result.statuses_per_source[self.sources_for_persistor['session']],
      persistor_.Persistor.FAIL)


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestLoadSaveFromSettingsAndGroups(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    cls.orig_default_setting_sources = persistor_.Persistor.get_default_setting_sources()
  
  @classmethod
  def tearDownClass(cls):
    persistor_.Persistor.set_default_setting_sources(cls.orig_default_setting_sources)

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp')
  def setUp(self, mock_gimp_module):
    mock_gimp_module.directory.return_value = 'gimp_directory'

    self.settings = stubs_group.create_test_settings_with_specific_setting_sources()
    # FIXME: This is a temporary fix until a proper session source is implemented.
    self.session_source = sources_.GimpParasiteSource('plug-in-session', source_type='session')
    self.persistent_source = sources_.GimpParasiteSource('plug-in-persistent')
    
    self.sources_for_persistor = {
      'session': self.session_source,
      'persistent': self.persistent_source,
    }

    persistor_.Persistor.set_default_setting_sources(self.sources_for_persistor)
    mock_gimp_module.parasites = {}
  
  def test_load_save_setting(self, *mocks):
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['advanced/flatten'].set_value(True)
    self.settings['advanced/use_layer_size'].set_value(True)
    
    self.settings['main/file_extension'].save()
    
    self.settings['main/file_extension'].reset()
    self.settings['advanced/flatten'].reset()
    self.settings['advanced/use_layer_size'].reset()
    
    self.settings['main/file_extension'].load()
    
    self.assertEqual(self.settings['main/file_extension'].value, 'jpg')
    self.assertEqual(self.settings['advanced/flatten'].value, False)
    self.assertEqual(self.settings['advanced/use_layer_size'].value, False)
  
  def test_load_setting_has_no_effect_if_setting_has_ignore_tag(self, *mocks):
    self.settings['main/file_extension'].tags.add('ignore_load')
    
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['advanced/flatten'].set_value(True)
    self.settings['advanced/use_layer_size'].set_value(True)
    
    self.settings['main/file_extension'].save()
    
    self.settings['main/file_extension'].reset()
    self.settings['advanced/flatten'].reset()
    self.settings['advanced/use_layer_size'].reset()
    
    self.settings['main/file_extension'].load()
    
    self.assertEqual(self.settings['main/file_extension'].value, 'png')
    self.assertEqual(self.settings['advanced/flatten'].value, False)
    self.assertEqual(self.settings['advanced/use_layer_size'].value, False)
  
  def test_load_save_group(self, *mocks):
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['advanced/flatten'].set_value(True)
    self.settings['advanced/use_layer_size'].set_value(True)
    
    self.settings['advanced'].save()

    self.settings['main/file_extension'].reset()
    self.settings['advanced/flatten'].reset()
    self.settings['advanced/use_layer_size'].reset()

    self.settings['advanced'].load()
    
    self.assertEqual(self.settings['main/file_extension'].value, 'png')
    # 'advanced/flatten' value must not be loaded
    self.assertEqual(self.settings['advanced/flatten'].value, False)
    self.assertEqual(self.settings['advanced/use_layer_size'].value, True)
  
  def test_load_group_has_no_effect_if_group_has_ignore_tag(self, *mocks):
    self.settings['advanced'].tags.add('ignore_load')
    
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['advanced/flatten'].set_value(True)
    self.settings['advanced/use_layer_size'].set_value(True)
    
    self.settings['advanced'].save()
    
    self.settings['main/file_extension'].reset()
    self.settings['advanced/flatten'].reset()
    self.settings['advanced/use_layer_size'].reset()
    
    self.settings['advanced'].load()
    
    self.assertEqual(self.settings['main/file_extension'].value, 'png')
    self.assertEqual(self.settings['advanced/flatten'].value, False)
    self.assertEqual(self.settings['advanced/use_layer_size'].value, False)


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp',
  new_callable=stubs_gimp.GimpModuleStub)
class TestLoadSaveEvents(unittest.TestCase):

  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.setting.sources.Gimp')
  def setUp(self, mock_gimp_module):
    mock_gimp_module.directory.return_value = 'gimp_directory'

    self.setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='png')
    self.flatten = settings_.BoolSetting('flatten', default_value=False)
    # FIXME: This is a temporary fix until a proper session source is implemented.
    self.session_source = sources_.GimpParasiteSource('plug-in-session', source_type='session')
    
    self.session_source_dict = {'session': self.session_source}

    mock_gimp_module.parasites = {}
  
  def test_before_load_event(self, *mocks):
    persistor_.Persistor.save([self.setting, self.flatten], self.session_source_dict)
    self.setting.set_value('gif')
    
    self.setting.connect_event(
      'before-load', stubs_setting.on_file_extension_changed, self.flatten)
    persistor_.Persistor.load([self.setting], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'png')
    self.assertEqual(self.flatten.value, True)
  
  def test_after_load_event(self, *mocks):
    self.flatten.set_value(True)
    persistor_.Persistor.save([self.setting, self.flatten], self.session_source_dict)
    
    self.setting.connect_event(
      'after-load', stubs_setting.on_file_extension_changed, self.flatten)
    persistor_.Persistor.load([self.setting], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'png')
    self.assertEqual(self.flatten.value, False)
  
  def test_after_load_event_not_all_settings_found_invoke_for_all_settings(self, *mocks):
    self.setting.set_value('gif')
    persistor_.Persistor.save([self.setting], self.session_source_dict)
    
    self.setting.connect_event(
      'after-load', stubs_setting.on_file_extension_changed, self.flatten)
    persistor_.Persistor.load([self.setting, self.flatten], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, True)
  
  def test_after_load_event_is_triggered_even_after_fail(self, *mocks):
    self.flatten.set_value(True)
    persistor_.Persistor.save([self.setting, self.flatten], self.session_source_dict)
    
    self.setting.connect_event(
      'after-load', stubs_setting.on_file_extension_changed, self.flatten)

    # FIXME: This is a temporary fix until a proper session source is implemented.
    with mock.patch(
           pgutils.get_pygimplib_module_path()
           + '.setting.sources.GimpParasiteSource') as temp_mock_session_source:
      temp_mock_session_source.read_data_from_source.side_effect = sources_.SourceReadError

      persistor_.Persistor.load([self.setting], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'png')
    self.assertEqual(self.flatten.value, False)
  
  def test_load_trigger_set_value_events_multiple_times_if_setting_is_specified_multiple_times(
        self, *mocks):
    spy_event = mock.Mock(wraps=stubs_setting.on_file_extension_changed)
    
    self.setting.set_value('gif')
    persistor_.Persistor.save([self.setting], self.session_source_dict)
    
    self.setting.connect_event('value-changed', spy_event, self.flatten)
    
    persistor_.Persistor.load([self.setting, self.setting], self.session_source_dict)

    self.assertEqual(spy_event.call_count, 2)
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, True)
  
  def test_before_save_event(self, *mocks):
    self.setting.set_value('gif')
    
    self.setting.connect_event(
      'before-save', stubs_setting.on_file_extension_changed, self.flatten)
    persistor_.Persistor.save([self.setting, self.flatten], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, True)
    
    persistor_.Persistor.load([self.setting, self.flatten], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, True)
  
  def test_after_save_event(self, *mocks):
    self.setting.set_value('gif')
    
    self.setting.connect_event(
      'after-save', stubs_setting.on_file_extension_changed, self.flatten)
    persistor_.Persistor.save([self.setting, self.flatten], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, True)
    
    persistor_.Persistor.load([self.setting, self.flatten], self.session_source_dict)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, False)
  
  def test_after_save_event_is_triggered_even_after_fail(self, *mocks):
    self.setting.set_value('gif')
    self.setting.connect_event(
      'after-save', stubs_setting.on_file_extension_changed, self.flatten)

    # FIXME: This is a temporary fix until a proper session source is implemented.
    with mock.patch(
           pgutils.get_pygimplib_module_path()
           + '.setting.sources.GimpParasiteSource') as temp_mock_session_source:
      temp_mock_session_source.read_data_from_source.side_effect = sources_.SourceReadError

      persistor_.Persistor.save([self.setting], self.session_source_dict)
    
    self.assertEqual(self.flatten.value, True)
  
  def test_events_are_triggered_for_groups_including_top_group(self, *mocks):
    settings = stubs_group.create_test_settings_hierarchical()
    
    test_list = []
    
    settings.connect_event('before-save', lambda group: test_list.append(2))
    settings['main'].connect_event('before-save', lambda group: test_list.append(4))
    
    persistor_.Persistor.save([settings])
    
    self.assertEqual(test_list, [2, 4])
  
  def test_event_triggering_is_not_enabled(self, *mocks):
    self.setting.set_value('gif')
    
    self.setting.connect_event(
      'before-save', stubs_setting.on_file_extension_changed, self.flatten)
    
    self.setting.connect_event(
      'before-load', stubs_setting.on_file_extension_changed, self.flatten)
    
    persistor_.Persistor.save(
      [self.setting, self.flatten], self.session_source_dict, trigger_events=False)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, False)
    
    persistor_.Persistor.load(
      [self.setting, self.flatten], self.session_source_dict, trigger_events=False)
    
    self.assertEqual(self.setting.value, 'gif')
    self.assertEqual(self.flatten.value, False)
