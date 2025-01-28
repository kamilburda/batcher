import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import parameterized

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import placeholders as placeholders_


class _BatcherStub:

  def __init__(self, current_image_name=None, current_layer_name=None):
    self.current_image = stubs_gimp.Image(name=current_image_name)
    self.current_layer = stubs_gimp.Layer(name=current_layer_name, image=current_image_name)


class TestGetReplacedArg(unittest.TestCase):

  def test_arg_matching_placeholder(self):
    batcher = _BatcherStub(current_image_name='image')
    setting = placeholders_.PlaceholderImageSetting('placeholder')

    result = placeholders_.get_replaced_value(setting, batcher)

    self.assertIsInstance(result, stubs_gimp.Image)

  def test_arg_matching_array_placeholder(self):
    batcher = _BatcherStub(current_image_name='image')
    setting = placeholders_.PlaceholderDrawableArraySetting('placeholder', element_type='layer')

    result = placeholders_.get_replaced_value(setting, batcher)

    self.assertEqual(len(result), 1)
    self.assertIsInstance(result[0], stubs_gimp.Layer)

  def test_arg_not_matching_placeholder(self):
    batcher = _BatcherStub(current_image_name='image')

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

  @mock.patch(
    f'{pg.utils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new_callable=stubs_gimp.GimpModuleStub)
  def test_with_layer_array(self, _mock_gimp):
    param = stubs_gimp.GParamStub(
      GObject.GType.from_name('GimpCoreObjectArray'), 'layers', object_type=Gimp.Layer.__gtype__)

    # noinspection PyTypeChecker
    self.assertEqual(
      placeholders_.get_placeholder_type_name_from_pdb_type(
        GObject.GType.from_name('GimpCoreObjectArray'), param),
      'placeholder_layer_array',
    )

  @mock.patch(
    f'{pg.utils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new_callable=stubs_gimp.GimpModuleStub)
  def test_image_array_is_unsupported(self, _mock_gimp):
    param = stubs_gimp.GParamStub(
      GObject.GType.from_name('GimpCoreObjectArray'), 'images', object_type=Gimp.Image.__gtype__)

    # noinspection PyTypeChecker
    self.assertIsNone(
      placeholders_.get_placeholder_type_name_from_pdb_type(
        GObject.GType.from_name('GimpCoreObjectArray'), param))


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
    setting = placeholders_.PlaceholderDrawableArraySetting('drawables', element_type='layer')

    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'drawables',
        'type': 'placeholder_drawable_array',
        'value': 'current_layer_for_array',
        'element_type': 'layer',
      }
    )
