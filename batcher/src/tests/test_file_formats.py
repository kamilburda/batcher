import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import file_formats as file_formats_


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
      *self.common_options,
      {
        'name': 'interlaced',
        'type': pg.setting.BoolSetting,
        'display_name': 'interlaced',
        'default_value': False,
      },
      {
        'name': 'compression',
        'type': pg.setting.IntSetting,
        'display_name': 'compression',
        'default_value': 9,
      },
    ]

    self.jpg_options = [
      *self.common_options,
      {
        'name': 'quality',
        'type': pg.setting.DoubleSetting,
        'display_name': 'quality',
        'default_value': 0.9,
      },
    ]

  def test_fill_file_format_options(self, mock_get_setting_data_from_pdb_procedure):
    file_format_options = {}

    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-save', self.jpg_options

    file_formats_.fill_file_format_options(file_format_options, 'jpg', 'export')

    mock_get_setting_data_from_pdb_procedure.assert_called_once()
    self.assertIn('jpg', file_format_options)
    self.assertEqual(file_format_options['jpg']['quality'].value, 0.9)

  def test_fill_file_format_options_has_no_effect_after_already_filling_file_format(
        self, mock_get_setting_data_from_pdb_procedure):
    file_format_options = {}

    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-save', self.jpg_options

    file_formats_.fill_file_format_options(file_format_options, 'jpg', 'export')
    file_formats_.fill_file_format_options(file_format_options, 'jpg', 'export')

    mock_get_setting_data_from_pdb_procedure.assert_called_once()
    self.assertIn('jpg', file_format_options)
    self.assertEqual(file_format_options['jpg']['quality'].value, 0.9)

  def test_fill_file_format_options_with_alias(self, mock_get_setting_data_from_pdb_procedure):
    file_format_options = {}

    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-save', self.jpg_options

    file_formats_.fill_file_format_options(file_format_options, 'jpeg', 'export')

    mock_get_setting_data_from_pdb_procedure.assert_called_once()
    self.assertNotIn('jpeg', file_format_options)
    self.assertIn('jpg', file_format_options)
    self.assertEqual(file_format_options['jpg']['quality'].value, 0.9)

  def test_fill_file_format_options_unrecognized_format(
        self, mock_get_setting_data_from_pdb_procedure):
    file_format_options = {}

    file_formats_.fill_file_format_options(file_format_options, 'unknown', 'export')

    mock_get_setting_data_from_pdb_procedure.assert_not_called()
    self.assertFalse(file_format_options)
