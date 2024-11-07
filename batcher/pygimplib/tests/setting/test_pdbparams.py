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
      dict(
        name='file-extension',
        type=GObject.TYPE_STRING,
        default='png',
        nick='File extension',
        blurb='File extension',
      ))
  
  def test_create_multiple_params(self):
    params = pdbparams_.create_params(
      self.string_setting, self.coordinates_setting, self.settings)

    self.assertEqual(len(params), 3)
    
    self.assertListEqual(
      params[0],
      dict(
        name='file-extension',
        type=GObject.TYPE_STRING,
        default='png',
        nick='File extension',
        blurb='File extension',
      ))
    
    self.assertEqual(
      params[1],
      dict(
        name='coordinates',
        type=Gimp.DoubleArray,
        nick='Coordinates',
        blurb='Coordinates',
      ))

  def test_create_multiple_params_recursive(self):
    params = pdbparams_.create_params(
      self.string_setting, self.coordinates_setting, self.settings, recursive=True)

    self.assertEqual(len(params), 6)

    self.assertListEqual(
      params[0],
      dict(
        name='file-extension',
        type=GObject.TYPE_STRING,
        default='png',
        nick='File extension',
        blurb='File extension',
      ))

    self.assertEqual(
      params[1],
      dict(
        name='coordinates',
        type=Gimp.DoubleArray,
        nick='Coordinates',
        blurb='Coordinates',
      ))
    
    for param, setting in zip(params[3:], self.settings.walk()):
      self.assertListEqual(
        param,
        dict(
          name=setting.pdb_name,
          type=setting.pdb_type,
          default=setting.default_value,
          nick=setting.display_name,
          blurb=setting.description,
        ))

  def test_create_params_invalid_argument(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      pdbparams_.create_params([self.string_setting])
  
  def test_create_params_with_unregistrable_setting(self):
    params = pdbparams_.create_params(self.unregistrable_setting)
    self.assertEqual(params, [])
