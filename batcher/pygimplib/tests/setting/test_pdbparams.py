import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from ...setting import pdbparams as pdbparams_
from ...setting import settings as settings_

from . import stubs_group


class TestCreateParams(unittest.TestCase):
  
  def setUp(self):
    self.string_setting = settings_.StringSetting(
      'file_extension', default_value='png', display_name='File extension')
    self.unregistrable_setting = settings_.GenericSetting(
      'exported_items', default_value=0, pdb_type=None)
    self.coordinates_setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='double',
      element_default_value=0.0)
    
    self.settings = stubs_group.create_test_settings_hierarchical()
  
  def test_create_params_single_param(self):
    params = pdbparams_.create_params(self.string_setting)
    param = params[0]

    self.assertEqual(len(params), 1)
    self.assertListEqual(
      param,
      [
        'string',
        'file-extension',
        'File extension',
        'File extension',
        'png',
        GObject.ParamFlags.READWRITE,
      ])
  
  def test_create_multiple_params(self):
    params = pdbparams_.create_params(
      self.string_setting, self.coordinates_setting, self.settings)

    self.assertEqual(len(params), 2)
    
    self.assertListEqual(
      params[0],
      [
        'string',
        'file-extension',
        'File extension',
        'File extension',
        'png',
        GObject.ParamFlags.READWRITE,
      ])
    
    self.assertEqual(
      params[1],
      [
        'double_array',
        'coordinates',
        'Coordinates',
        'Coordinates',
        GObject.ParamFlags.READWRITE,
      ])

  def test_create_multiple_params_recursive(self):
    params = pdbparams_.create_params(
      self.string_setting, self.coordinates_setting, self.settings, recursive=True)

    self.assertEqual(len(params), 5)

    self.assertListEqual(
      params[0],
      [
        'string',
        'file-extension',
        'File extension',
        'File extension',
        'png',
        GObject.ParamFlags.READWRITE,
      ])

    self.assertEqual(
      params[1],
      [
        'double_array',
        'coordinates',
        'Coordinates',
        'Coordinates',
        GObject.ParamFlags.READWRITE,
      ])

    self.assertEqual(
      params[2],
      [
        'string',
        'file-extension',
        'File extension',
        'File extension',
        'bmp',
        GObject.ParamFlags.READWRITE,
      ])

    self.assertEqual(
      params[3],
      [
        'boolean',
        'flatten',
        'Flatten',
        'Flatten',
        False,
        GObject.ParamFlags.READWRITE,
      ])

    # We omit the `Gimp.Choice` object and check its contents manually below.
    self.assertEqual(
      params[4][:4] + params[4][5:],
      [
        'choice',
        'overwrite-mode',
        'Overwrite mode',
        'Overwrite mode',
        'rename_new',
        GObject.ParamFlags.READWRITE,
      ])

    # TODO: Check for the contents of the `Gimp.Choice` instance

  def test_create_params_invalid_argument(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      pdbparams_.create_params([self.string_setting])
  
  def test_create_params_with_unregistrable_setting(self):
    params = pdbparams_.create_params(self.unregistrable_setting)
    self.assertEqual(params, [])
