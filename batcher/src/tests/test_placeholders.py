import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import parameterized

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import placeholders as placeholders_


class _BatcherStub:

  def __init__(self, current_image=None, current_raw_item=None):
    self.current_image = current_image
    self.current_raw_item = current_raw_item


class TestGetReplacedArg(unittest.TestCase):

  def test_arg_matching_placeholder(self):
    batcher = _BatcherStub(current_image='image')
    setting = placeholders_.PlaceholderImageSetting('placeholder')

    self.assertEqual(placeholders_.get_replaced_value(setting, batcher), 'image')

  def test_arg_matching_array_placeholder(self):
    batcher = _BatcherStub(current_image='image')
    setting = placeholders_.PlaceholderDrawableArraySetting('placeholder', element_type='layer')

    self.assertTupleEqual(
      placeholders_.get_replaced_value(setting, batcher), (None,))

  def test_arg_not_matching_placeholder(self):
    batcher = _BatcherStub(current_image='image')

    with self.assertRaises(ValueError):
      # noinspection PyTypeChecker
      placeholders_.get_replaced_value(
        pg.setting.StringSetting('placeholder', default_value='invalid_placeholder'), batcher)


class TestGetPlaceholderNameFromPdbType(unittest.TestCase):

  def test_with_gobject_subclass(self):
    self.assertEqual(
      placeholders_.get_placeholder_type_name_from_pdb_type(Gimp.Image),
      'placeholder_image')

  def test_with_gtype(self):
    self.assertEqual(
      placeholders_.get_placeholder_type_name_from_pdb_type(Gimp.Image.__gtype__),
      'placeholder_image')

  def test_with_non_matching_gtype(self):
    self.assertIsNone(placeholders_.get_placeholder_type_name_from_pdb_type(GObject.GObject))

  def test_with_invalid_object_type(self):
    self.assertIsNone(placeholders_.get_placeholder_type_name_from_pdb_type(object))

  def test_with_layer_array(self):
    param = stubs_gimp.GParamStub(Gimp.ObjectArray, 'layers')

    # noinspection PyTypeChecker
    self.assertEqual(
      placeholders_.get_placeholder_type_name_from_pdb_type(Gimp.ObjectArray, param),
      'placeholder_layer_array',
    )

  def test_image_array_is_unsupported(self):
    param = stubs_gimp.GParamStub(Gimp.ObjectArray, 'images')

    # noinspection PyTypeChecker
    self.assertIsNone(
      placeholders_.get_placeholder_type_name_from_pdb_type(Gimp.ObjectArray, param))


class TestPlaceholderSetting(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('placeholder', placeholders_.PlaceholderSetting, []),
    ('image_placeholder', placeholders_.PlaceholderImageSetting, ['current_image']),
  ])
  def test_get_allowed_placeholder_names(
        self, test_case_suffix, placeholder_setting_type, expected_result):
    self.assertListEqual(
      placeholder_setting_type.get_allowed_placeholder_names(), expected_result)
  
  @parameterized.parameterized.expand([
    ('placeholder', placeholders_.PlaceholderSetting, 0),
    ('image_placeholder', placeholders_.PlaceholderImageSetting, 1),
  ])
  def test_get_allowed_placeholders(
        self, test_case_suffix, placeholder_setting_type, expected_length):
    self.assertEqual(len(placeholder_setting_type.get_allowed_placeholders()), expected_length)


class TestPlaceholderArraySetting(unittest.TestCase):

  def test_to_dict(self):
    setting = placeholders_.PlaceholderDrawableArraySetting(
      'drawables', element_type='layer')

    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'drawables',
        'type': 'placeholder_drawable_array',
        'value': 'current_layer_for_array',
        'element_type': 'layer',
      }
    )
