import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib import pdb
from pygimplib.tests import stubs_gimp

from src import export as export_


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp', new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
class TestFileFormatOptionsSetting(unittest.TestCase):

  @mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
  def setUp(self, mock_get_setting_data_from_pdb_procedure):
    self.common_options = [
      {
        'name': 'run-mode',
        'type': pg.setting.EnumSetting,
        'default_value': Gimp.RunMode.NONINTERACTIVE,
        'enum_type': Gimp.RunMode.__gtype__,
        'display_name': 'run-mode',
      },
      {
        'name': 'image',
        'type': pg.setting.ImageSetting,
        'default_value': None,
        'display_name': 'image',
      },
      {
        'name': 'drawables',
        'type': pg.setting.ArraySetting,
        'element_type': pg.setting.DrawableSetting,
        'display_name': 'drawables',
      },
      {
        'name': 'file',
        'type': pg.setting.FileSetting,
      },
    ]

    self.png_options = [
      {
        'name': 'offsets',
        'type': pg.setting.ArraySetting,
        'element_type': pg.setting.IntSetting,
        'display_name': 'Offsets',
        'default_value': (7, 11),
      },
      {
        'name': 'is-interlaced',
        'type': pg.setting.BoolSetting,
        'display_name': 'interlaced',
        'default_value': False,
      },
    ]

    self.file_format_options = [
      *self.common_options,
      *self.png_options,
    ]

  def test_get_export_function(self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_get_setting_data_from_pdb_procedure.return_value = (
      None, 'file-png-export', self.file_format_options)
    mock_gimp.get_pdb().add_procedure(stubs_gimp.PdbProcedureStub('file-png-export'))

    file_format_options = {}

    proc, kwargs = export_.get_export_function(
      'png', export_.FileFormatModes.USE_EXPLICIT_VALUES, file_format_options)

    self.assertIs(proc, pdb.file_png_export)
    mock_get_setting_data_from_pdb_procedure.assert_called_once()
    self.assertEqual(len(file_format_options['png']), 2)
    self.assertEqual(file_format_options['png']['is-interlaced'].value, False)
    self.assertEqual(file_format_options['png']['offsets'].value, (7, 11))

    self.assertEqual(len(kwargs), 3)
    self.assertFalse(kwargs['is_interlaced'])
    self.assertIsInstance(kwargs['offsets'], Gimp.Int32Array)

  def test_get_default_export_function_if_file_format_mode_is_not_use_explicit_values(
        self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_gimp.get_pdb().add_procedure(stubs_gimp.PdbProcedureStub('gimp-file-export'))

    file_format_options = {}

    proc, kwargs = export_.get_export_function(
      'unknown', export_.FileFormatModes.USE_NATIVE_PLUGIN_VALUES, file_format_options)

    self.assertIs(proc, pdb.gimp_file_save)
    mock_get_setting_data_from_pdb_procedure.assert_not_called()
    self.assertFalse(file_format_options)

  def test_get_default_export_function_if_file_format_is_not_recognized(
        self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_gimp.get_pdb().add_procedure(stubs_gimp.PdbProcedureStub('gimp-file-export'))

    file_format_options = {}

    proc, kwargs = export_.get_export_function(
      'unknown', export_.FileFormatModes.USE_EXPLICIT_VALUES, file_format_options)

    self.assertIs(proc, pdb.gimp_file_save)
    mock_get_setting_data_from_pdb_procedure.assert_not_called()
    self.assertFalse(file_format_options)
