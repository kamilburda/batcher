import os
import sys
from typing import Callable, List

import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from config import CONFIG
from src import plugin_settings
from src import setting as setting_
from src import update
from src import utils
from src import utils_update
from src import version as version_

from src.tests import stubs_gimp


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))

_SETTINGS_MODULE_PATH = 'src.setting.settings'

_MOCK_PNG_CHOICE = Gimp.Choice.new()
_MOCK_PNG_CHOICE.add('auto', 0, 'Automatic', '')
_MOCK_PNG_CHOICE_DEFAULT_VALUE = 'auto'


def _get_assert_update_handlers(
      minimum_version: version_.Version,
      maximum_version: version_.Version,
      include_next: bool,
      match_minimum_version: bool = False,
) -> List[Callable]:
  test_update_package_dirpath = os.path.dirname(utils.get_current_module_filepath())
  handlers_package_dirpath = os.path.join(
    test_update_package_dirpath, utils_update.HANDLERS_PACKAGE_NAME)
  handlers_package_path = (
    f'{sys.modules[__name__].__package__}.{utils_update.HANDLERS_PACKAGE_NAME}')

  return utils_update.get_versions_and_functions(
    minimum_version,
    maximum_version,
    handlers_package_dirpath,
    handlers_package_path,
    utils_update.ASSERT_UPDATE_HANDLER_MODULE_PREFIX,
    utils_update.UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX,
    'assert_contents',
    include_next=include_next,
    match_minimum_version=match_minimum_version,
  )


@mock.patch('src.setting.sources.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestUpdateHandlers(unittest.TestCase):

  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
  def test_update_export_layers(self, *_mocks):
    settings = plugin_settings.create_settings_for_export_layers()
    source_name = 'plug-in-batch-export-layers'

    source = setting_.sources.JsonFileSource(
      source_name, os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_0-2.json'))

    orig_setting_values = self._get_orig_setting_values(settings)

    status, message = update.load_and_update(
      settings,
      sources={'persistent': source},
      update_sources=False,
    )

    self.assertEqual(status, update.UpdateStatuses.UPDATE, msg=message)

    assert_handlers = _get_assert_update_handlers(
      version_.Version.parse('0.2'),
      version_.Version.parse('1.0-RC4'),
      include_next=False,
    )

    for assert_handler in assert_handlers:
      assert_handler(self, settings, orig_setting_values)

  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_default',
    return_value=_MOCK_PNG_CHOICE_DEFAULT_VALUE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_choice_get_choice',
    return_value=_MOCK_PNG_CHOICE)
  @mock.patch(
    f'{_SETTINGS_MODULE_PATH}._functions.Gimp.param_spec_core_object_array_get_object_type',
    return_value=Gimp.Drawable.__gtype__)
  def test_update_batch_convert(self, *_mocks):
    settings = plugin_settings.create_settings_for_convert()
    source_name = 'plug-in-batch-convert'

    source = setting_.sources.JsonFileSource(
      source_name, os.path.join(_CURRENT_MODULE_DIRPATH, 'settings_1-0.json'))

    orig_setting_values = self._get_orig_setting_values(settings)

    status, message = update.load_and_update(
      settings,
      sources={'persistent': source},
      update_sources=False,
      procedure_group=source_name,
    )

    self.assertEqual(status, update.UpdateStatuses.UPDATE, msg=message)

    assert_handlers = _get_assert_update_handlers(
      version_.Version.parse('1.1'),
      version_.Version.parse(CONFIG.PLUGIN_VERSION),
      include_next=True,
      match_minimum_version=True,
    )

    for assert_handler in assert_handlers:
      assert_handler(self, settings, orig_setting_values)

  @staticmethod
  def _get_orig_setting_values(settings):
    return {
      setting.get_path(relative_path_group='root'): setting.value
      for setting in settings.walk()
    }
