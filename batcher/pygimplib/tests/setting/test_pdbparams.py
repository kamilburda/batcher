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
    self.file_ext_setting = settings_.FileExtensionSetting(
      'file_extension', default_value='png', display_name='File extension')
    self.unregistrable_setting = settings_.IntSetting(
      'num_exported_items', default_value=0, pdb_type=None)
    self.coordinates_setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_default_value=0.0)
    
    self.settings = stubs_group.create_test_settings_hierarchical()
  
  def test_create_params_single_param(self):
    params = pdbparams_.create_params(self.file_ext_setting)
    param = params[0]

    self.assertEqual(len(params), 1)
    self.assertDictEqual(
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
      self.file_ext_setting, self.coordinates_setting, self.settings)
    
    self.assertEqual(len(params), 6)
    
    self.assertDictEqual(
      params[0],
      dict(
        name='file-extension',
        type=GObject.TYPE_STRING,
        default='png',
        nick='File extension',
        blurb='File extension',
      ))

    self.assertDictEqual(
      params[1],
      dict(
        name='num-coordinates',
        type=GObject.TYPE_INT,
        default=0,
        minimum=0,
        nick='Number of elements in "coordinates"',
        blurb='Number of elements in "coordinates"',
      ))
    
    self.assertEqual(
      params[2],
      dict(
        name='coordinates',
        type=Gimp.FloatArray,
        nick='Coordinates',
        blurb='Coordinates',
      ))
    
    for param, setting in zip(params[3:], self.settings.walk()):
      self.assertDictEqual(
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
      pdbparams_.create_params([self.file_ext_setting])
  
  def test_create_params_with_unregistrable_setting(self):
    params = pdbparams_.create_params(self.unregistrable_setting)
    self.assertEqual(params, [])


class TestIterArgs(unittest.TestCase):
  
  def setUp(self):
    self.settings = stubs_group.create_test_settings_hierarchical()
    self.args = ['png', False, 'replace']
  
  def test_iter_args_number_of_args_equals_number_of_settings(self):
    self.assertListEqual(
      list(pdbparams_.iter_args(self.args, list(self.settings.walk()))),
      self.args)
  
  def test_iter_args_number_of_args_is_less_than_number_of_settings(self):
    self.assertListEqual(
      list(pdbparams_.iter_args(self.args[:-1], list(self.settings.walk()))),
      self.args[:-1])
  
  def test_iter_args_number_of_args_is_more_than_number_of_settings(self):
    self.assertListEqual(
      list(pdbparams_.iter_args(self.args, list(self.settings.walk())[:-1])),
      self.args[:-1])
  
  def test_iter_args_with_array_setting(self):
    coordinates_setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_default_value=0.0)
    
    self.settings.add([coordinates_setting])
    self.args.extend([3, (20.0, 50.0, 40.0)])
    
    self.assertListEqual(
      list(pdbparams_.iter_args(self.args, list(self.settings.walk()))),
      self.args[:-2] + [self.args[-1]])


class TestListParamValues(unittest.TestCase):
  
  def setUp(self):
    self.settings = stubs_group.create_test_settings_hierarchical()
  
  def test_list_param_values(self):
    param_values = pdbparams_.list_param_values([self.settings])
    self.assertEqual(param_values[0], self.settings['main/file_extension'].value)
    self.assertEqual(param_values[1], self.settings['advanced/flatten'].value)
    self.assertEqual(param_values[2], self.settings['advanced/overwrite_mode'].value)

  def test_list_param_values_ignore_run_mode(self):
    param_values = pdbparams_.list_param_values([settings_.IntSetting('run_mode'), self.settings])
    self.assertEqual(len(param_values), len(list(self.settings.walk())))
