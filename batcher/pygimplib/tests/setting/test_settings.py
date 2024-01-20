"""Tests for the `setting.setting` and `setting.presenter` modules."""

import collections
import os
import unittest
import unittest.mock as mock

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import GObject

import parameterized

from ... import utils as pgutils

from ...setting import presenter as presenter_
from ...setting import settings as settings_

from .. import stubs_gimp
from . import stubs_setting


class TestSetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = stubs_setting.StubSetting('file_extension', default_value='png')
  
  def test_str(self):
    self.assertEqual(str(self.setting), '<StubSetting "file_extension">')

  def test_value_for_pdb_is_equal_to_value(self):
    self.assertEqual(self.setting.value_for_pdb, self.setting.value)
  
  def test_invalid_setting_name(self):
    with self.assertRaises(ValueError):
      stubs_setting.StubSetting('file/extension', default_value='png')
    
    with self.assertRaises(ValueError):
      stubs_setting.StubSetting('file.extension', default_value='png')
  
  def test_default_default_value(self):
    self.assertEqual(stubs_setting.StubSetting('setting').default_value, 0)
  
  def test_callable_default_default_value(self):
    self.assertEqual(
      stubs_setting.StubWithCallableDefaultDefaultValueSetting('setting').default_value,
      '_setting')
  
  def test_explicit_default_value(self):
    self.assertEqual(
      stubs_setting.StubSetting('file_extension', default_value='png').default_value, 'png')
  
  def test_assign_empty_value_not_allowed(self):
    self.setting.set_value('')

    self.assertFalse(self.setting.is_valid)
  
  def test_assign_empty_value_allowed(self):
    setting = stubs_setting.StubSetting('setting', default_value='', allow_empty_values=True)
    setting.set_value('')
    
    self.assertEqual(setting.value, '')
  
  def test_get_generated_display_name(self):
    self.assertEqual(self.setting.display_name, 'File extension')
  
  def test_get_generated_description(self):
    setting = stubs_setting.StubSetting(
      'setting', default_value='default value', display_name='_Setting')
    
    self.assertEqual(setting.display_name, '_Setting')
    self.assertEqual(setting.description, 'Setting')
  
  def test_get_custom_display_name_and_description(self):
    setting = stubs_setting.StubSetting(
      'setting',
      default_value='default value', display_name='_Setting', description='My description')
    
    self.assertEqual(setting.display_name, '_Setting')
    self.assertEqual(setting.description, 'My description')

  def test_pdb_type_automatic_is_not_registrable(self):
    self.assertIsNone(self.setting.pdb_type)
    self.assertFalse(self.setting.can_be_registered_to_pdb())
  
  def test_pdb_type_automatic_is_registrable(self):
    setting = stubs_setting.StubRegistrableToPdbSetting('file_extension', default_value='png')

    self.assertEqual(setting.pdb_type, GObject.TYPE_STRING)
    self.assertTrue(setting.can_be_registered_to_pdb())

  def test_pdb_type_as_none(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type=None)

    self.assertIsNone(setting.pdb_type)
    self.assertFalse(setting.can_be_registered_to_pdb())

  def test_pdb_type_as_gobject_subclass(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type=Gimp.RunMode)

    self.assertEqual(setting.pdb_type, Gimp.RunMode)
    self.assertTrue(setting.can_be_registered_to_pdb())

  def test_pdb_type_as_gtype(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type=Gimp.RunMode.__gtype__)

    self.assertEqual(setting.pdb_type, Gimp.RunMode.__gtype__)
    self.assertTrue(setting.can_be_registered_to_pdb())

  def test_pdb_type_as_gtype_name(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type='gchararray')

    self.assertEqual(setting.pdb_type, GObject.TYPE_STRING)
    self.assertTrue(setting.can_be_registered_to_pdb())
  
  def test_invalid_pdb_type(self):
    with self.assertRaises(ValueError):
      stubs_setting.StubRegistrableToPdbSetting(
        'file_extension', default_value='png', pdb_type=GObject.TYPE_INT)
  
  def test_get_pdb_param_for_registrable_setting(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', display_name='_Run mode')
    self.assertEqual(
      setting.get_pdb_param(),
      [
        dict(
          name='file-extension',
          type=GObject.TYPE_STRING,
          default='png',
          nick='_Run mode',
          blurb='Run mode',
        )])
  
  def test_get_pdb_param_for_nonregistrable_setting(self):
    self.assertIsNone(self.setting.get_pdb_param())
  
  def test_reset(self):
    self.setting.set_value('jpg')
    self.setting.reset()
    self.assertEqual(self.setting.value, 'png')
  
  def test_reset_with_container_as_default_value(self):
    setting = stubs_setting.StubSetting('images_and_directories', default_value={})
    setting.value[1] = 'image_directory'
    
    setting.reset()
    self.assertEqual(setting.value, {})
    
    setting.value[2] = 'another_image_directory'
    
    setting.reset()
    self.assertEqual(setting.value, {})
  
  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 'png',
        'type': 'stub',
        'default_value': 'png',
      })
  
  def test_to_dict_when_default_value_object_is_passed_to_init(self):
    setting = stubs_setting.StubSetting(
      'file_extension', default_value=settings_.Setting.DEFAULT_VALUE)
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 0,
        'type': 'stub',
        'default_value': 0,
      })
  
  def test_to_dict_with_gui_type_as_object(self):
    setting = stubs_setting.StubWithGuiSetting(
      'file_extension',
      default_value='png',
      gui_type=stubs_setting.StubPresenter)
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 'png',
        'type': 'stub_with_gui',
        'default_value': 'png',
        'gui_type': 'stub',
      })
  
  def test_to_dict_with_tags(self):
    tags = {'ignore_reset', 'ignore_load'}
    expected_tags = list(tags)
    
    setting = stubs_setting.StubSetting(
      'file_extension', default_value='png', tags=tags)
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 'png',
        'type': 'stub',
        'default_value': 'png',
        'tags': expected_tags,
      })

  def test_to_dict_with_pdb_type_as_gtype(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type=GObject.TYPE_STRING)

    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 'png',
        'type': 'stub_registrable_to_pdb',
        'default_value': 'png',
        'pdb_type': 'gchararray',
      })

  def test_to_dict_with_pdb_type_as_gobject_subclass(self):
    setting = stubs_setting.StubRegistrableToPdbSetting(
      'file_extension', default_value='png', pdb_type=Gimp.RunMode)

    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'file_extension',
        'value': 'png',
        'type': 'stub_registrable_to_pdb',
        'default_value': 'png',
        'pdb_type': 'GimpRunMode',
      })


class TestSettingEvents(unittest.TestCase):
  
  def setUp(self):
    self.setting = stubs_setting.StubSetting('file_extension', default_value='png')
    self.flatten = settings_.BoolSetting('flatten', default_value=False)
  
  def test_connect_value_changed_event(self):
    self.setting.connect_event(
      'value-changed', stubs_setting.on_file_extension_changed, self.flatten)
    
    self.setting.set_value('jpg')
    self.assertEqual(self.flatten.value, True)
    self.assertFalse(self.flatten.gui.get_sensitive())
  
  def test_connect_value_changed_event_nested(self):
    self.setting.connect_event(
      'value-changed', stubs_setting.on_file_extension_changed, self.flatten)
    
    use_layer_size = settings_.BoolSetting('use_layer_size', default_value=False)
    use_layer_size.connect_event(
      'value-changed', stubs_setting.on_use_layer_size_changed, self.setting)
    
    use_layer_size.set_value(True)
    
    self.assertEqual(self.setting.value, 'jpg')
    self.assertEqual(self.flatten.value, True)
    self.assertFalse(self.flatten.gui.get_sensitive())
  
  def test_reset_triggers_value_changed_event(self):
    self.setting.connect_event(
      'value-changed', stubs_setting.on_file_extension_changed, self.flatten)
    
    self.setting.set_value('jpg')
    self.setting.reset()
    self.assertEqual(self.flatten.value, self.flatten.default_value)
    self.assertTrue(self.flatten.gui.get_sensitive())


class TestSettingGui(unittest.TestCase):
  
  def setUp(self):
    self.setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='png')
    self.widget = stubs_setting.GuiWidgetStub('')
  
  def test_set_gui_updates_gui_value(self):
    self.setting.set_gui(stubs_setting.StubPresenter, self.widget)
    self.assertEqual(self.widget.value, 'png')
  
  def test_setting_set_value_updates_gui(self):
    self.setting.set_gui(stubs_setting.StubPresenter, self.widget)
    self.setting.set_value('gif')
    self.assertEqual(self.widget.value, 'gif')
  
  def test_set_gui_preserves_gui_state(self):
    self.setting.gui.set_sensitive(False)
    self.setting.gui.set_visible(False)
    self.setting.set_value('gif')
    
    self.setting.set_gui(stubs_setting.StubPresenter, self.widget)
    
    self.assertFalse(self.setting.gui.get_sensitive())
    self.assertFalse(self.setting.gui.get_visible())
    self.assertEqual(self.widget.value, 'gif')
  
  def test_setting_gui_type(self):
    setting = stubs_setting.StubWithGuiSetting(
      'flatten', default_value=False, gui_type=stubs_setting.CheckButtonStubPresenter)
    setting.set_gui()
    self.assertIs(type(setting.gui), stubs_setting.CheckButtonStubPresenter)
    self.assertIs(type(setting.gui.widget), stubs_setting.CheckButtonStub)
  
  def test_setting_different_gui_type(self):
    setting = stubs_setting.StubWithGuiSetting(
      'flatten', default_value=False, gui_type=stubs_setting.StubPresenter)
    setting.set_gui()
    self.assertIs(type(setting.gui), stubs_setting.StubPresenter)
    self.assertIs(type(setting.gui.widget), stubs_setting.GuiWidgetStub)
  
  def test_setting_invalid_gui_type_raises_error(self):
    with self.assertRaises(ValueError):
      stubs_setting.StubWithGuiSetting(
        'flatten',
        default_value=False,
        gui_type=stubs_setting.YesNoToggleButtonStubPresenter)
  
  def test_setting_null_gui_type(self):
    setting = stubs_setting.StubWithGuiSetting('flatten', default_value=False, gui_type='null')
    setting.set_gui()
    self.assertIs(type(setting.gui), presenter_.NullPresenter)
  
  def test_set_gui_gui_type_is_specified_widget_is_none_raises_error(self):
    setting = stubs_setting.StubWithGuiSetting('flatten', default_value=False)
    with self.assertRaises(ValueError):
      setting.set_gui(gui_type=stubs_setting.CheckButtonStubPresenter)
  
  def test_set_gui_gui_type_is_none_widget_is_specified_raises_error(self):
    setting = stubs_setting.StubWithGuiSetting('flatten', default_value=False)
    with self.assertRaises(ValueError):
      setting.set_gui(widget=stubs_setting.GuiWidgetStub)
  
  def test_set_gui_manual_gui_type(self):
    setting = stubs_setting.StubWithGuiSetting('flatten', default_value=False)
    setting.set_gui(
      gui_type=stubs_setting.YesNoToggleButtonStubPresenter,
      widget=stubs_setting.GuiWidgetStub(None))
    self.assertIs(type(setting.gui), stubs_setting.YesNoToggleButtonStubPresenter)
    self.assertIs(type(setting.gui.widget), stubs_setting.GuiWidgetStub)
  
  def test_set_gui_widget_is_none_presenter_has_no_wrapper_raises_error(self):
    setting = stubs_setting.StubWithGuiSetting(
      'flatten',
      default_value=False,
      gui_type=stubs_setting.StubWithoutGuiWidgetCreationPresenter)
    with self.assertRaises(ValueError):
      setting.set_gui()

  def test_create_gui_with_gui_type_kwargs_on_init(self):
    setting = stubs_setting.StubWithGuiSetting(
      'flatten',
      default_value=False,
      gui_type=stubs_setting.StubWithCustomKwargsInCreateWidgetPresenter,
      gui_type_kwargs=dict(width=200, height=15))

    setting.set_gui()

    self.assertEqual(setting.gui.widget.width, 200)
    self.assertEqual(setting.gui.widget.height, 15)
  
  def test_update_setting_value_manually(self):
    self.setting.set_gui(stubs_setting.StubPresenter, self.widget)
    self.widget.set_value('jpg')
    self.assertEqual(self.setting.value, 'png')
    
    self.setting.gui.update_setting_value()
    self.assertEqual(self.setting.value, 'jpg')
  
  def test_update_setting_value_automatically(self):
    self.setting.set_gui(
      stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    self.widget.set_value('jpg')
    self.assertEqual(self.setting.value, 'jpg')
  
  def test_update_setting_value_triggers_value_changed_event(self):
    self.setting.set_gui(
      stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    
    flatten = settings_.BoolSetting('flatten', default_value=False)
    self.setting.connect_event(
      'value-changed', stubs_setting.on_file_extension_changed, flatten)
    
    self.widget.set_value('jpg')
    self.assertEqual(self.setting.value, 'jpg')
    self.assertEqual(flatten.value, True)
    self.assertFalse(flatten.gui.get_sensitive())
  
  def test_reset_updates_gui(self):
    self.setting.set_gui(stubs_setting.StubPresenter, self.widget)
    self.setting.set_value('jpg')
    self.setting.reset()
    self.assertEqual(self.widget.value, 'png')
  
  def test_update_setting_value_after_resetting_to_disallowed_empty_value(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')

    setting.set_gui(stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    setting.set_value('jpg')
    setting.reset()

    # Raise error because setting is reset to an empty value, while empty
    # values are disallowed (`allow_empty_values` is False).
    setting.gui.update_setting_value()

    self.assertFalse(setting.is_valid)

  def test_null_presenter_has_automatic_gui(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')
    self.assertTrue(setting.gui.gui_update_enabled)
  
  def test_manual_gui_update_enabled_is_false(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')
    setting.set_gui(stubs_setting.StubPresenter, self.widget)
    self.assertFalse(setting.gui.gui_update_enabled)
  
  def test_automatic_gui_update_enabled_is_true(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')
    setting.set_gui(stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    self.assertTrue(setting.gui.gui_update_enabled)
    
    self.widget.set_value('png')
    self.assertEqual(setting.value, 'png')
  
  def test_automatic_gui_update_enabled_is_false(self):
    setting = stubs_setting.StubWithGuiSetting(
      'file_extension', default_value='', auto_update_gui_to_setting=False)
    setting.set_gui(stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    self.assertFalse(setting.gui.gui_update_enabled)
    
    self.widget.set_value('png')
    self.assertEqual(setting.value, '')
  
  def test_set_gui_disable_automatic_setting_value_update(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')
    setting.set_gui(
      stubs_setting.StubWithValueChangedSignalPresenter,
      self.widget, auto_update_gui_to_setting=False)
    self.assertFalse(setting.gui.gui_update_enabled)
    
    self.widget.set_value('png')
    self.assertEqual(setting.value, '')
  
  def test_automatic_gui_update_after_being_disabled(self):
    setting = stubs_setting.StubWithGuiSetting(
      'file_extension', default_value='', auto_update_gui_to_setting=False)
    setting.set_gui(stubs_setting.StubWithValueChangedSignalPresenter, self.widget)
    setting.gui.auto_update_gui_to_setting(True)
    
    self.widget.set_value('png')
    self.assertEqual(setting.value, 'png')
  
  def test_automatic_gui_update_for_manual_gui_raises_value_error(self):
    setting = stubs_setting.StubWithGuiSetting('file_extension', default_value='')
    setting.set_gui(stubs_setting.StubPresenter, self.widget)
    
    self.assertFalse(setting.gui.gui_update_enabled)
    
    with self.assertRaises(ValueError):
      setting.gui.auto_update_gui_to_setting(True)


class TestGenericSetting(unittest.TestCase):
  
  def test_value_functions_with_one_parameter(self):
    setting = settings_.GenericSetting(
      'selected_layers',
      value_set=lambda value: tuple(value),
      value_save=lambda value: list(value))

    setting.set_value([4, 6, 2])
    
    self.assertEqual(setting.value, (4, 6, 2))
    self.assertDictEqual(
      setting.to_dict(), {'name': setting.name, 'value': [4, 6, 2], 'type': 'generic'})
  
  def test_value_functions_as_none(self):
    setting = settings_.GenericSetting('selected_layers')
    
    setting.set_value([4, 6, 2])
    
    self.assertEqual(setting.value, [4, 6, 2])
    self.assertDictEqual(
      setting.to_dict(), {'name': setting.name, 'value': repr([4, 6, 2]), 'type': 'generic'})
  
  def test_value_functions_with_two_parameters(self):
    setting = settings_.GenericSetting(
      'selected_layers',
      value_set=lambda value, setting_: tuple(f'{setting_.name}_{str(item)}' for item in value),
      value_save=lambda value, setting_: list(value))
    
    setting.set_value([4, 6, 2])
    
    self.assertEqual(
      setting.value, ('selected_layers_4', 'selected_layers_6', 'selected_layers_2'))
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': setting.name,
        'value': ['selected_layers_4', 'selected_layers_6', 'selected_layers_2'],
        'type': 'generic',
      })
  
  def test_value_set_with_invalid_number_of_parameters_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.GenericSetting(
        'selected_layers',
        value_set=lambda value, setting, redundant: tuple(value),
        value_save=lambda value, setting: list(value))
  
  def test_value_set_not_being_callable_raises_error(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      settings_.GenericSetting(
        'selected_layers',
        value_set='not_a_callable',
        value_save=lambda value, setting: list(value))
  
  def test_value_save_with_invalid_number_of_parameters_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.GenericSetting(
        'selected_layers',
        value_set=lambda value, setting: tuple(value),
        value_save=lambda value, setting, redundant: list(value))
  
  def test_value_save_not_being_callable_raises_error(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      settings_.GenericSetting(
        'selected_layers',
        value_set=lambda value, setting: tuple(value),
        value_save='not_a_callable')


class TestBoolSetting(unittest.TestCase):

  def test_set_value_value_is_converted_to_bool(self):
    setting = settings_.BoolSetting('flatten', default_value=False)

    setting.set_value(['nonempty_list'])

    self.assertEqual(setting.value, True)


class TestIntSetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_.IntSetting('count', default_value=0, min_value=0, max_value=100)

  def test_value_not_valid_event_is_triggered_upon_invalid_value(self):
    counter = 0

    def increment_counter():
      nonlocal counter
      counter += 1

    self.setting.connect_event('value-not-valid', lambda *args: increment_counter())

    self.setting.set_value(-5)

    self.assertEqual(counter, 1)

  def test_value_below_min_is_not_valid(self):
    self.setting.set_value(-5)
    self.assertFalse(self.setting.is_valid)

  def test_value_below_pdb_min_is_not_valid(self):
    setting = settings_.IntSetting('count')

    setting.set_value(GLib.MININT - 1)

    self.assertFalse(setting.is_valid)

  def test_min_value_below_pdb_min_is_not_valid(self):
    with self.assertRaises(ValueError):
      settings_.IntSetting('count', min_value=GLib.MININT - 1)
  
  def test_min_value_is_valid(self):
    self.setting.set_value(0)

    self.assertTrue(self.setting.is_valid)
  
  def test_value_above_max_is_not_valid(self):
    self.setting.set_value(200)

    self.assertFalse(self.setting.is_valid)

  def test_value_above_pdb_max_is_not_valid(self):
    setting = settings_.IntSetting('count')

    setting.set_value(GLib.MAXINT + 1)

    self.assertFalse(setting.is_valid)

  def test_max_value_is_above_pdb_max_raises_error(self):
    with self.assertRaises(ValueError):
      settings_.IntSetting('count', max_value=GLib.MAXINT + 1)
  
  def test_max_value_is_valid(self):
    self.setting.set_value(100)

    self.assertTrue(self.setting.is_valid)

  def test_get_pdb_param(self):
    self.assertEqual(
      self.setting.get_pdb_param(),
      [
        dict(
          name='count',
          type=GObject.TYPE_INT,
          default=0,
          minimum=0,
          maximum=100,
          nick='Count',
          blurb='Count',
        )])

  def test_get_pdb_param_no_min_or_max_value(self):
    self.assertEqual(
      settings_.IntSetting('count').get_pdb_param(),
      [
        dict(
          name='count',
          type=GObject.TYPE_INT,
          default=0,
          nick='Count',
          blurb='Count',
        )])

  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'count',
        'type': 'int',
        'value': 0,
        'default_value': 0,
        'min_value': 0,
        'max_value': 100,
      })


class TestFloatSetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_.FloatSetting(
      'clip_percent', default_value=0.0, min_value=0.0, max_value=100.0)
  
  def test_value_below_min_is_not_valid(self):
    self.setting.set_value(-5.0)
    self.assertFalse(self.setting.is_valid)
  
  def test_minimum_value_is_valid(self):
    self.setting.set_value(0.0)

    self.assertTrue(self.setting.is_valid)
  
  def test_value_above_max_is_not_valid(self):
    self.setting.set_value(200.0)
    self.assertFalse(self.setting.is_valid)
  
  def test_maximum_value_is_valid(self):
    self.setting.set_value(100.0)

    self.assertTrue(self.setting.is_valid)


class TestCreateEnumSetting(unittest.TestCase):

  def test_with_default_default_value(self):
    setting = settings_.EnumSetting('precision', Gimp.Precision)

    self.assertEqual(setting.default_value, next(iter(Gimp.Precision.__enum_values__.values())))
    self.assertEqual(setting.enum_type, Gimp.Precision)
    self.assertEqual(setting.pdb_type, Gimp.Precision)

  def test_with_custom_default_value(self):
    setting = settings_.EnumSetting(
      'precision', Gimp.Precision, default_value=Gimp.Precision.DOUBLE_GAMMA)

    self.assertEqual(setting.default_value, Gimp.Precision.DOUBLE_GAMMA)

  def test_with_custom_default_value_as_int(self):
    setting = settings_.EnumSetting('precision', Gimp.Precision, default_value=750)

    self.assertEqual(setting.default_value, Gimp.Precision.DOUBLE_GAMMA)

  def test_with_enum_type_as_string(self):
    setting = settings_.EnumSetting(
      'distance_metric', 'GeglDistanceMetric', default_value=Gegl.DistanceMetric.EUCLIDEAN)

    self.assertEqual(setting.default_value, Gegl.DistanceMetric.EUCLIDEAN)
    self.assertEqual(setting.enum_type, Gegl.DistanceMetric)
    self.assertEqual(setting.pdb_type, Gegl.DistanceMetric)

  def test_with_enum_type_as_gtype(self):
    setting = settings_.EnumSetting(
      'distance_metric',
      Gegl.DistanceMetric.__gtype__,
      default_value=Gegl.DistanceMetric.EUCLIDEAN)

    self.assertEqual(setting.default_value, Gegl.DistanceMetric.EUCLIDEAN)
    self.assertEqual(setting.enum_type, Gegl.DistanceMetric)
    self.assertEqual(setting.pdb_type, Gegl.DistanceMetric)

  def test_string_enum_type_has_invalid_format_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.EnumSetting('distance_metric', 'gi')

  def test_string_enum_type_is_empty_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.EnumSetting('distance_metric', 'Gegl')

  def test_string_enum_type_is_not_a_class_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.EnumSetting('distance_metric', object())

  def test_string_enum_type_is_not_a_genum_subclass_raises_error(self):
    with self.assertRaises(TypeError):
      settings_.EnumSetting('distance_metric', 'GimpPDB')

  def test_pdb_type_is_ignored(self):
    setting = settings_.EnumSetting(
      'precision', Gimp.Precision,
      default_value=Gimp.Precision.DOUBLE_GAMMA, pdb_type=None)

    self.assertEqual(setting.enum_type, Gimp.Precision)
    self.assertEqual(setting.pdb_type, Gimp.Precision)


class TestEnumSetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_.EnumSetting(
      'precision', Gimp.Precision, default_value=Gimp.Precision.DOUBLE_GAMMA)

  def test_get_pdb_param_with_default_default_value(self):
    setting = settings_.EnumSetting('precision', Gimp.Precision)

    self.assertEqual(
      setting.get_pdb_param(),
      [
        dict(
          name='precision',
          type=Gimp.Precision,
          default=next(iter(Gimp.Precision.__enum_values__.values())),
          nick='Precision',
          blurb='Precision',
        )])

  def test_get_pdb_param_with_custom_default_value(self):
    self.assertEqual(
      self.setting.get_pdb_param(),
      [
        dict(
          name='precision',
          type=Gimp.Precision,
          default=Gimp.Precision.DOUBLE_GAMMA,
          nick='Precision',
          blurb='Precision',
        )])

  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'precision',
        'value': 750,
        'type': 'enum',
        'enum_type': 'GimpPrecision',
        'default_value': 750,
      })

  def test_set_value_with_int(self):
    self.setting.set_value(100)
    self.assertEqual(self.setting.value, Gimp.Precision.U8_LINEAR)

  def test_set_value_with_enum_instance(self):
    self.setting.set_value(Gimp.Precision.U8_LINEAR)
    self.assertEqual(self.setting.value, Gimp.Precision.U8_LINEAR)


class TestCreateChoiceSetting(unittest.TestCase):
  
  def test_default_default_value_is_first_item(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode', [('skip', 'Skip'), ('replace', 'Replace')])
    self.assertEqual(setting.default_value, setting.items['skip'])
  
  def test_no_items_raises_error(self):
    with self.assertRaises(ValueError):
      settings_.ChoiceSetting('overwrite_mode', [])
  
  def test_explicit_item_values(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('skip', 'Skip', 5), ('replace', 'Replace', 6)],
      default_value='replace')
    self.assertEqual(setting.items['skip'], 5)
    self.assertEqual(setting.items['replace'], 6)
  
  def test_inconsistent_number_of_elements_raises_error(self):
    with self.assertRaises(ValueError):
      settings_.ChoiceSetting(
        'overwrite_mode',
        [('skip', 'Skip', 4), ('replace', 'Replace')], default_value='replace')
    
  def test_same_explicit_item_value_multiple_times_raises_error(self):
    with self.assertRaises(ValueError):
      settings_.ChoiceSetting(
        'overwrite_mode', [('skip', 'Skip', 4), ('replace', 'Replace', 4)])
  
  def test_too_many_elements_in_items_raises_error(self):
    with self.assertRaises(ValueError):
      # noinspection PyTypeChecker
      settings_.ChoiceSetting(
        'overwrite_mode', [('skip', 'Skip', 1, 1), ('replace', 'Replace', 1, 1)])
  
  def test_too_few_elements_in_items_raises_error(self):
    with self.assertRaises(ValueError):
      # noinspection PyTypeChecker
      settings_.ChoiceSetting('overwrite_mode', [('skip',), ('replace',)])
  
  def test_no_empty_value(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode', [('skip', 'Skip'), ('replace', 'Replace')])
    self.assertIsNone(setting.empty_value)
  
  def test_valid_empty_value(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('choose', 'Choose your mode'), ('skip', 'Skip'), ('replace', 'Replace')],
      default_value='replace',
      empty_value='choose')
    self.assertEqual(setting.empty_value, setting.items['choose'])
  
  def test_empty_value_is_equal_to_default_default_value(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('choose', 'Choose your mode'), ('skip', 'Skip'), ('replace', 'Replace')],
      empty_value='choose')
    
    self.assertEqual(setting.default_value, setting.items['choose'])
    self.assertEqual(setting.empty_value, setting.items['choose'])
  
  def test_invalid_empty_value_raises_error(self):
    with self.assertRaises(ValueError):
      settings_.ChoiceSetting(
        'overwrite_mode',
        [('skip', 'Skip'), ('replace', 'Replace')],
        empty_value='invalid_value')
  

class TestChoiceSetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('skip', 'Skip'), ('replace', 'Replace')],
      default_value='replace',
      display_name='Overwrite mode')
  
  def test_set_invalid_item(self):
    self.setting.set_value(4)

    self.assertFalse(self.setting.is_valid)

    self.setting.set_value(-1)

    self.assertFalse(self.setting.is_valid)
  
  def test_get_invalid_item(self):
    with self.assertRaises(KeyError):
      # noinspection PyStatementEffect
      self.setting.items['invalid_item']
  
  def test_description(self):
    self.assertEqual(self.setting.description, 'Overwrite mode { Skip (0), Replace (1) }')
  
  def test_description_with_mnemonics_from_item_display_names(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('skip', '_Skip'), ('replace', '_Replace')],
      display_name='_Overwrite mode',
      default_value='replace')
    self.assertEqual(setting.description, 'Overwrite mode { Skip (0), Replace (1) }')
  
  def test_get_item_display_names_and_values(self):
    self.assertEqual(
      self.setting.get_item_display_names_and_values(), [('Skip', 0), ('Replace', 1)])
  
  def test_is_value_empty(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('choose', '-Choose Your Mode-'), ('skip', 'Skip'), ('replace', 'Replace')],
      default_value='replace',
      empty_value='choose',
      allow_empty_values=True)
    
    self.assertFalse(setting.is_value_empty())
    setting.set_value(setting.items['choose'])
    self.assertTrue(setting.is_value_empty())
  
  def test_set_empty_value_not_allowed(self):
    setting = settings_.ChoiceSetting(
      'overwrite_mode',
      [('choose', '-Choose Your Mode-'), ('skip', 'Skip'), ('replace', 'Replace')],
      default_value='replace',
      empty_value='choose')
    
    setting.set_value(setting.items['choose'])

    self.assertFalse(setting.is_valid)
  
  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'overwrite_mode',
        'value': 1,
        'type': 'choice',
        'default_value': 'replace',
        'items': [['skip', 'Skip'], ['replace', 'Replace']],
        'display_name': 'Overwrite mode',
      })


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp', new=stubs_gimp.GimpModuleStub())
@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
class TestImageSetting(unittest.TestCase):

  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp', new=stubs_gimp.GimpModuleStub())
  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
  def setUp(self):
    self.image = stubs_gimp.Image(width=2, height=2, base_type=Gimp.ImageBaseType.RGB)
    
    self.setting = settings_.ImageSetting('image', default_value=self.image)
  
  def test_set_value_with_object(self):
    image = stubs_gimp.Image(width=2, height=2, base_type=Gimp.ImageBaseType.RGB)
    
    self.setting.set_value(image)
    
    self.assertEqual(self.setting.value, image)
  
  def test_set_value_with_file_path(self):
    self.image.set_file(Gio.file_new_for_path('file_path'))
    
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]

      self.setting.set_value(os.path.abspath('file_path'))
    
    self.assertEqual(self.setting.value, self.image)
  
  def test_set_value_with_non_matching_file_path(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = []
      
      self.setting.set_value(os.path.abspath('file_path'))

    self.assertIsNone(self.setting.value)

  def test_set_value_with_id(self):
    self.image.id_ = 2

    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.Image.get_by_id.return_value = self.image

      self.setting.set_value(2)
    
    self.assertEqual(self.setting.value, self.image)
  
  def test_set_value_with_invalid_id(self):
    self.image.id_ = 2

    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.Image.get_by_id.return_value = None

      self.setting.set_value(3)

    self.assertIsNone(self.setting.value)
  
  def test_set_value_with_none(self):
    self.setting.set_value(None)
    
    self.assertIsNone(self.setting.value)
  
  def test_set_value_invalid_image(self):
    self.image.valid = False

    self.setting.set_value(self.image)
    self.assertFalse(self.setting.is_valid)
  
  def test_default_value_with_raw_type(self):
    self.image.set_file(Gio.file_new_for_path('file_path'))
    
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]
      
      setting = settings_.ImageSetting('image', default_value=os.path.abspath('file_path'))
    
    self.assertEqual(setting.default_value, self.image)
  
  def test_to_dict(self):
    self.image.set_file(Gio.file_new_for_path('file_path'))
    
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'image',
        'value': os.path.abspath('file_path'),
        'type': 'image',
        'default_value': os.path.abspath('file_path'),
      })

  def test_to_dict_with_missing_filename(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'image',
        'value': None,
        'type': 'image',
        'default_value': None,
      })
  
  def test_to_dict_if_image_is_none(self):
    setting = settings_.ImageSetting('image', default_value=None)
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'image',
        'value': None,
        'type': 'image',
        'default_value': None,
      })


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp', new=stubs_gimp.GimpModuleStub())
class TestGimpItemSetting(unittest.TestCase):
  
  class StubItemSetting(settings_.GimpItemSetting):
    pass
  
  def setUp(self):
    self.image = stubs_gimp.Image(width=2, height=2, base_type=Gimp.ImageBaseType.RGB)
    self.image.set_file(Gio.file_new_for_path('image_filepath'))
    
    self.parent_of_parent = stubs_gimp.Layer(name='group1', is_group=True)
    
    self.parent = stubs_gimp.Layer(name='group2', is_group=True)
    self.parent.parent = self.parent_of_parent
    
    self.layer = stubs_gimp.Layer(name='layer')
    self.layer.parent = self.parent
    self.layer.image = self.image
    
    self.image.layers = [self.parent_of_parent]
    self.parent_of_parent.children = [self.parent]
    self.parent.children = [self.layer]
    
    self.setting = self.StubItemSetting('item', default_value=self.layer)
  
  def test_set_value_with_object(self):
    layer = stubs_gimp.Layer(name='layer2')
    
    self.setting.set_value(layer)
    self.assertEqual(self.setting.value, layer)
  
  def test_set_value_with_list(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]

      self.setting.set_value([os.path.abspath('image_filepath'), 'Layer', 'group1/group2/layer'])
    
    self.assertEqual(self.setting.value, self.layer)
  
  def test_set_value_with_list_and_top_level_layer(self):
    self.layer.parent = None
    self.image.layers = [self.layer]
    
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]
      
      self.setting.set_value([os.path.abspath('image_filepath'), 'Layer', 'layer'])
    
    self.assertEqual(self.setting.value, self.layer)
  
  def test_set_value_with_list_invalid_length_raises_error(self):
    with self.assertRaises(ValueError):
      self.setting.set_value(['image_filepath'])
  
  def test_set_value_with_list_no_matching_image_returns_none(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = []
      
      self.setting.set_value([os.path.abspath('image_filepath'), 'Layer', 'group1/group2/layer'])
    
    self.assertIsNone(self.setting.value)
  
  def test_set_value_with_list_no_matching_layer_returns_none(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]
      
      self.setting.set_value(
        [os.path.abspath('image_filepath'), 'Layer', 'group1/group2/some_other_layer'])
    
    self.assertIsNone(self.setting.value)
  
  def test_set_value_with_list_no_matching_parent_returns_none(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]
      
      self.setting.set_value(
        [os.path.abspath('image_filepath'), 'Layer', 'group1/some_other_group2/layer'])
    
    self.assertIsNone(self.setting.value)
  
  def test_set_value_with_id(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp'
    ) as temp_mock_gimp_module:
      temp_mock_gimp_module.Item.get_by_id.return_value = self.layer
      
      self.setting.set_value(2)
    
    self.assertEqual(self.setting.value, self.layer)
  
  def test_set_value_with_invalid_id(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp'
    ) as temp_mock_gimp_module:
      temp_mock_gimp_module.Item.get_by_id.return_value = None
    
      self.setting.set_value(2)
    
    self.assertIsNone(self.setting.value)
  
  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'item',
        'value': [os.path.abspath('image_filepath'), 'Layer', 'group1/group2/layer'],
        'type': 'stub_item',
        'default_value': [os.path.abspath('image_filepath'), 'Layer', 'group1/group2/layer'],
      })
  
  def test_to_dict_value_is_none(self):
    self.assertDictEqual(
      self.StubItemSetting('item', default_value=None).to_dict(),
      {
        'name': 'item',
        'value': None,
        'type': 'stub_item',
        'default_value': None,
      })
  
  def test_to_dict_without_image_filename(self):
    self.image.set_file(None)

    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'item',
        'value': None,
        'type': 'stub_item',
        'default_value': None,
      })
  
  def test_to_dict_without_parents(self):
    self.layer.parent = None
    
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'item',
        'value': [os.path.abspath('image_filepath'), 'Layer', 'layer'],
        'type': 'stub_item',
        'default_value': [os.path.abspath('image_filepath'), 'Layer', 'layer'],
      })


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp', new=stubs_gimp.GimpModuleStub())
class TestLayerMaskSetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_.LayerMaskSetting('mask')

    self.mask = stubs_gimp.LayerMask(name='mask')

    self.image = stubs_gimp.Image(width=2, height=2, base_type=Gimp.ImageBaseType.RGB)
    self.image.set_file(Gio.file_new_for_path('image_filepath'))

    self.parent = stubs_gimp.Layer(name='group', is_group=True)

    self.layer = stubs_gimp.Layer(name='layer', mask=self.mask)
    self.layer.parent = self.parent
    self.layer.image = self.image

    self.image.layers = [self.parent]
    self.parent.children = [self.layer]

  def test_set_value_from_layer_mask(self):
    self.setting.set_value(self.mask)
    self.assertEqual(self.setting.value, self.mask)

  def test_set_value_with_id(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp'
    ) as temp_mock_gimp_module:
      temp_mock_gimp_module.Item.get_by_id.return_value = self.mask

      self.setting.set_value(2)

    self.assertEqual(self.setting.value, self.mask)

  def test_set_value_with_list_containing_layer_path(self):
    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.return_value = [self.image]

      self.setting.set_value([os.path.abspath('image_filepath'), 'Layer', 'group/layer'])

    self.assertEqual(self.setting.value, self.mask)

  def test_to_dict(self):
    self.setting.set_value(self.mask)

    with mock.patch(
          f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp'
    ) as temp_mock_gimp_module:
      temp_mock_gimp_module.Layer.from_mask.return_value = self.layer

      setting_dict = self.setting.to_dict()

    self.assertDictEqual(
      setting_dict,
      {
        'name': 'mask',
        'value': [os.path.abspath('image_filepath'), 'Layer', 'group/layer'],
        'type': 'layer_mask',
      })


class TestColorSetting(unittest.TestCase):
  
  def test_create_with_default_default_value(self):
    self._assert_rgb_equal(settings_.ColorSetting('color').default_value, Gimp.RGB())
  
  def test_set_value_with_object(self):
    color = Gimp.RGB()
    color.set(0.5, 0.5, 0.5)
    
    setting = settings_.ColorSetting('color')
    setting.set_value(color)
    
    self._assert_rgb_equal(setting.value, color)
  
  def test_set_value_with_list(self):
    setting = settings_.ColorSetting('color')
    setting.set_value([0.5, 0.2, 0.8])

    expected_color = Gimp.RGB()
    expected_color.set(0.5, 0.2, 0.8)

    self._assert_rgb_equal(setting.value, expected_color)
  
  def test_set_value_with_list_with_four_values(self):
    setting = settings_.ColorSetting('color')
    setting.set_value([0.5, 0.2, 0.8, 0.4])

    expected_color = Gimp.RGB()
    expected_color.set(0.5, 0.2, 0.8)
    expected_color.set_alpha(0.4)
    
    self._assert_rgb_equal(setting.value, expected_color)
  
  def test_to_dict(self):
    setting = settings_.ColorSetting('color')

    color = Gimp.RGB()
    color.set(0.5, 0.2, 0.8)

    setting.set_value(color)

    self.assertDictEqual(
      setting.to_dict(), {'name': 'color', 'value': [0.5, 0.2, 0.8, 0.0], 'type': 'color'})
  
  def test_to_dict_with_four_values(self):
    setting = settings_.ColorSetting('color')

    color = Gimp.RGB()
    color.set(0.5, 0.2, 0.8)
    color.set_alpha(0.4)

    setting.set_value(color)
    
    self.assertDictEqual(
      setting.to_dict(), {'name': 'color', 'value': [0.5, 0.2, 0.8, 0.4], 'type': 'color'})

  @staticmethod
  def _assert_rgb_equal(color1, color2):
    return (
      color1.r == color2.r
      and color1.g == color2.g
      and color1.b == color2.b
      and color1.a == color2.a
    )


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
class TestDisplaySetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_.DisplaySetting('display')
    self.display = stubs_gimp.Display(id_=2)

  def test_set_value_with_display_id(self):
    self.setting.set_value(2)

    self.assertEqual(self.setting.value, self.display)

  def test_to_dict(self):
    self.setting.set_value(self.display)

    self.assertDictEqual(
      self.setting.to_dict(), {'name': 'display', 'value': None, 'type': 'display'})


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
class TestParasiteSetting(unittest.TestCase):
  
  def test_create_with_default_default_value(self):
    setting = settings_.ParasiteSetting('parasite')
    
    self.assertEqual(setting.value.get_name(), 'parasite')
    self.assertEqual(setting.value.get_flags(), 0)
    self.assertEqual(setting.value.get_data(), [])

  def test_set_value_by_object(self):
    setting = settings_.ParasiteSetting('parasite')

    parasite = stubs_gimp.Parasite.new('parasite_stub', 1, b'data')

    setting.set_value(parasite)
    
    self.assertEqual(setting.value, parasite)
  
  def test_set_value_by_list(self):
    setting = settings_.ParasiteSetting('parasite')
    
    setting.set_value(['parasite_stub', 1, b'data'])
    
    self.assertEqual(setting.value.get_name(), 'parasite_stub')
    self.assertEqual(setting.value.get_flags(), 1)
    self.assertEqual(setting.value.get_data(), list(b'data'))
  
  def test_to_dict(self):
    setting = settings_.ParasiteSetting('parasite')
    
    parasite = stubs_gimp.Parasite.new('parasite_stub', 1, b'data')
    
    setting.set_value(parasite)
    
    self.assertDictEqual(
      setting.to_dict(),
      {'name': 'parasite', 'value': ['parasite_stub', 1, list(b'data')], 'type': 'parasite'})


class TestFileSetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_.FileSetting('file')

  def test_with_default_default_value(self):
    self.assertIsInstance(self.setting.value, Gio.File)
    self.assertIsNone(self.setting.value.get_path())

  def test_set_value_with_string(self):
    cwd = os.getcwd()
    self.setting.set_value(cwd)

    self.assertEqual(self.setting.value.get_path(), cwd)

  def test_set_value_with_none(self):
    self.setting.set_value(None)

    self.assertIsInstance(self.setting.value, Gio.File)
    self.assertIsNone(self.setting.value.get_path())

  def test_to_dict(self):
    cwd = os.getcwd()
    self.setting.set_value(cwd)

    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'file',
        'value': cwd,
        'type': 'file',
      })


class TestBytesSetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_.BytesSetting('bytes')

  def test_with_default_default_value(self):
    self.assertIsInstance(self.setting.value, GLib.Bytes)
    self.assertEqual(self.setting.value.get_data(), b'')

  def test_set_value_with_gbytes(self):
    self.setting.set_value(GLib.Bytes.new(b'Test\x00\x7f\xffdata'))

    self.assertEqual(self.setting.value.get_data(), b'Test\x00\x7f\xffdata')

  def test_set_value_with_string(self):
    self.setting.set_value('Test\x00\x7f\xffdata')

    self.assertEqual(self.setting.value.get_data(), b'Test\x00\x7f\xffdata')

  def test_set_value_with_bytes(self):
    self.setting.set_value(b'Test\x00\x7f\xffdata')

    self.assertEqual(self.setting.value.get_data(), b'Test\x00\x7f\xffdata')

  def test_set_value_with_list(self):
    self.setting.set_value(list(b'Test\x00\x7f\xffdata'))

    self.assertEqual(self.setting.value.get_data(), b'Test\x00\x7f\xffdata')

  def test_set_value_with_list_invalid_values_return_empty_bytes(self):
    self.setting.set_value([72, 280])

    self.assertEqual(self.setting.value.get_data(), b'')

  def test_to_dict(self):
    self.setting.set_value(b'Test\x00\x7f\xffdata')

    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'bytes',
        'value': list(b'Test\x00\x7f\xffdata'),
        'type': 'bytes',
      })


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
class TestBrushSetting(unittest.TestCase):

  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new=stubs_gimp.GimpModuleStub())
  def setUp(self):
    self.setting = settings_.BrushSetting('brush')
    self.brush = stubs_gimp.Brush(name='Star')

  def test_create_with_default_default_value(self):
    self.assertIsNone(self.setting.value)

  def test_create_with_custom_default_value(self):
    self.setting = settings_.BrushSetting('brush', default_value=self.brush)

    self.assertEqual(self.setting.value, self.brush)

  def test_set_value_with_object(self):
    brush = stubs_gimp.Brush()

    self.setting.set_value(brush)

    self.assertEqual(self.setting.value, brush)

  def test_set_value_with_dict(self):
    self.setting.set_value(
      {
        'name': 'Star',
        'angle': 2.0,
        'aspect_ratio': 2.5,
        'hardness': 1.0,
        'radius': 25.0,
        'shape': 2,
        'spacing': 50,
        'spikes': 5,
      }
    )

    self.assertIsInstance(self.setting.value, stubs_gimp.Brush)

    brush = self.setting.value
    self.assertEqual(brush.get_name(), 'Star')
    self.assertEqual(brush.get_angle().angle, 2.0)
    self.assertEqual(brush.get_aspect_ratio().aspect_ratio, 2.5)
    self.assertEqual(brush.get_hardness().hardness, 1.0)
    self.assertEqual(brush.get_radius().radius, 25.0)
    self.assertEqual(brush.get_shape().shape, 2)
    self.assertEqual(brush.get_spacing(), 50)
    self.assertEqual(brush.get_spikes().spikes, 5)
  
  def test_to_dict_with_default_value(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'brush',
        'type': 'brush',
        'value': None,
      })

  def test_to_dict(self):
    self.setting.set_value(
      {
        'name': 'Star',
        'angle': 2.0,
        'aspect_ratio': 2.5,
        'hardness': 1.0,
        'radius': 25.0,
        'shape': 2,
        'spacing': 50,
        'spikes': 5,
      }
    )

    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'brush',
        'type': 'brush',
        'value': {
          'name': 'Star',
          'angle': 2.0,
          'aspect_ratio': 2.5,
          'hardness': 1.0,
          'radius': 25.0,
          'shape': 2,
          'spacing': 50,
          'spikes': 5,
        }
      })


@mock.patch(
  f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp', new=stubs_gimp.GimpModuleStub())
class TestPaletteSetting(unittest.TestCase):

  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new=stubs_gimp.GimpModuleStub())
  def setUp(self):
    self.setting = settings_.PaletteSetting('palette')
    self.palette = stubs_gimp.Palette(name='Standard')

  def test_create_with_default_default_value(self):
    self.assertIsNone(self.setting.value)

  def test_create_with_custom_default_value(self):
    self.setting = settings_.PaletteSetting('palette', default_value=self.palette)

    self.assertEqual(self.setting.value, self.palette)

  def test_set_value_with_object(self):
    palette = stubs_gimp.Palette()

    self.setting.set_value(palette)

    self.assertEqual(self.setting.value, palette)

  def test_set_value_with_dict(self):
    self.setting.set_value(
      {
        'name': 'Standard',
        'columns': 3,
      }
    )

    self.assertIsInstance(self.setting.value, stubs_gimp.Palette)

    palette = self.setting.value
    self.assertEqual(palette.get_name(), 'Standard')
    self.assertEqual(palette.get_columns(), 3)

  def test_to_dict_with_default_value(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'palette',
        'type': 'palette',
        'value': None,
      })

  def test_to_dict(self):
    self.setting.set_value(
      {
        'name': 'Standard',
        'columns': 3,
      }
    )

    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'palette',
        'type': 'palette',
        'value': {
          'name': 'Standard',
          'columns': 3,
        }
      })


class TestCreateArraySetting(unittest.TestCase):
  
  def test_create(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float')
    
    self.assertEqual(setting.name, 'coordinates')
    self.assertEqual(setting.default_value, (1.0, 5.0, 10.0))
    self.assertEqual(setting.value, (1.0, 5.0, 10.0))
    self.assertEqual(setting.pdb_type, Gimp.FloatArray)
    self.assertEqual(setting.element_type, settings_.FloatSetting)

    self.assertIsInstance(setting.value_for_pdb, Gimp.FloatArray)
  
  def test_create_with_default_default_value(self):
    setting = settings_.ArraySetting('coordinates', element_type='float')
    
    self.assertEqual(setting.default_value, ())
    self.assertEqual(setting.value, ())
  
  def test_create_with_element_default_value(self):
    setting = settings_.ArraySetting('coordinates', element_type='float')
    setting.add_element()
    
    self.assertEqual(setting[0].value, 0.0)
  
  def test_create_passing_non_tuple_as_default_value_converts_initial_value_to_tuple(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=[1.0, 5.0, 10.0],
      element_type='float')
    
    self.assertEqual(setting.default_value, (1.0, 5.0, 10.0))
    self.assertEqual(setting.value, (1.0, 5.0, 10.0))
  
  def test_create_with_additional_read_only_element_arguments(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_min_value=-100.0,
      element_max_value=100.0)
    
    self.assertEqual(setting.element_min_value, -100.0)
    self.assertEqual(setting.element_max_value, 100.0)
    
    for setting_attribute in setting.__dict__:
      if setting_attribute.startswith('element_'):
        with self.assertRaises(AttributeError):
          setattr(setting, setting_attribute, None)
  
  def test_create_with_additional_arguments_overriding_internal_element_arguments(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_min_value=-100.0,
      element_max_value=100.0,
      element_display_name='Coordinate')
    
    self.assertEqual(setting.element_display_name, 'Coordinate')
  
  @parameterized.parameterized.expand([
    ('native_array_type_as_element_pdb_type_is_registrable',
     'float',
     (1.0, 5.0, 10.0),
     'automatic',
     Gimp.FloatArray),

    ('native_array_type_registration_is_disabled_explicitly',
     'float',
     (1.0, 5.0, 10.0),
     None,
     None),

    ('gimp_object_as_element_pdb_type_is_registrable',
     'brush',
     (stubs_gimp.Brush(), stubs_gimp.Brush(), stubs_gimp.Brush()),
     'automatic',
     Gimp.ObjectArray),

    ('gimp_object_registration_is_disabled_explicitly',
     'brush',
     (stubs_gimp.Brush(), stubs_gimp.Brush(), stubs_gimp.Brush()),
     None,
     None),
  ])
  def test_create_with_pdb_type(
        self, test_case_suffix, element_type, default_value, pdb_type, expected_pdb_type):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=default_value,
      pdb_type=pdb_type,
      element_type=element_type)
    
    self.assertEqual(setting.pdb_type, expected_pdb_type)
  
  def test_create_with_nonregistrable_type(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='generic',
      element_value_set=lambda value: value,
      element_value_save=lambda value: value)
    
    self.assertIsNone(setting.pdb_type)
    self.assertFalse(setting.can_be_registered_to_pdb())
  
  def test_create_with_explicit_valid_element_pdb_type(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1, 5, 10),
      element_type='int',
      element_pdb_type=GObject.TYPE_INT)
    
    self.assertEqual(setting.pdb_type, Gimp.Int32Array)
    self.assertEqual(setting.element_pdb_type, GObject.TYPE_INT)
  
  def test_create_invalid_element_pdb_type_is_changed_to_correct_type(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_pdb_type=GObject.TYPE_UINT64)

    self.assertEqual(setting.element_pdb_type, GObject.TYPE_DOUBLE)
  
  def test_create_multidimensional_array(self):
    values = ((1.0, 5.0, 10.0), (2.0, 15.0, 25.0), (-5.0, 10.0, 40.0))
    
    setting = settings_.ArraySetting(
      'path_coordinates',
      default_value=values,
      element_type='array',
      element_default_value=(0.0, 0.0, 0.0),
      element_element_type='float',
      element_element_default_value=1.0)
    
    self.assertTupleEqual(setting.default_value, values)
    self.assertEqual(setting.element_type, settings_.ArraySetting)
    self.assertEqual(setting.element_default_value, (0.0, 0.0, 0.0))
    
    for i in range(len(setting)):
      self.assertEqual(setting[i].element_type, settings_.FloatSetting)
      self.assertEqual(setting[i].default_value, (0.0, 0.0, 0.0))
      self.assertEqual(setting[i].value, values[i])
      self.assertFalse(setting[i].can_be_registered_to_pdb())
      
      for j in range(len(setting[i])):
        self.assertEqual(setting[i][j].default_value, 1.0)
        self.assertEqual(setting[i][j].value, values[i][j])
  
  def test_create_multidimensional_array_with_default_default_values(self):
    setting = settings_.ArraySetting(
      'path_coordinates',
      element_type='array',
      element_element_type='float')
    
    setting.add_element()
    self.assertEqual(setting.value, ((),))
    setting[0].add_element()
    self.assertEqual(setting.value, ((0.0,),))

  @parameterized.parameterized.expand([
    ('int',
     'int',
     (1, 5, 10),
     Gimp.Int32Array),

    ('float',
     'float',
     (1.0, 5.0, 10.0),
     Gimp.FloatArray),

    ('color',
     'color',
     (Gimp.RGB(), Gimp.RGB(), Gimp.RGB()),
     Gimp.RGBArray),

    ('image',
     'image',
     (stubs_gimp.Image(), stubs_gimp.Image(), stubs_gimp.Image()),
     Gimp.ObjectArray),

    ('layer',
     'layer',
     (stubs_gimp.Layer(), stubs_gimp.Layer(), stubs_gimp.Layer()),
     Gimp.ObjectArray),

    ('brush',
     'brush',
     (stubs_gimp.Brush(), stubs_gimp.Brush(), stubs_gimp.Brush()),
     Gimp.ObjectArray),
  ])
  def test_value_for_pdb_select_types(self, test_case_suffix, element_type, value, expected_type):
    setting = settings_.ArraySetting('array', element_type=element_type)

    setting.set_value(value)

    self.assertIsInstance(setting.value_for_pdb, expected_type)

  def test_value_for_pdb_for_string_array(self):
    setting = settings_.ArraySetting('array', element_type='string')

    setting.set_value(['1', '5', '10'])

    self.assertEqual(setting.value_for_pdb, ('1', '5', '10'))


class TestArraySetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_min_value=-100.0,
      element_max_value=100.0)
  
  def test_get_elements(self):
    self.assertListEqual(
      self.setting.get_elements(), [self.setting[0], self.setting[1], self.setting[2]])
    
  def test_get_elements_returns_a_copy(self):
    elements = self.setting.get_elements()
    del elements[0]
    self.assertNotEqual(self.setting.get_elements(), elements)
  
  def test_has_element_default_value_even_if_not_specified(self):
    setting = settings_.ArraySetting(
      'coordinates',
      element_type='float')
    
    self.assertTrue(hasattr(setting, 'element_default_value'))
    self.assertEqual(setting.element_default_value, 0.0)
  
  @parameterized.parameterized.expand([
    ('with_tuple', (20.0, 50.0, 40.0), (20.0, 50.0, 40.0)),
    ('with_list', [20.0, 50.0, 40.0], (20.0, 50.0, 40.0)),
  ])
  def test_set_value(self, test_case_suffix, input_value, expected_value):
    self.setting.set_value(input_value)
    
    self.assertEqual(self.setting.value, expected_value)
    for i, expected_element_value in enumerate(expected_value):
      self.assertEqual(self.setting[i].value, expected_element_value)

  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new=stubs_gimp.GimpModuleStub())
  def test_set_value_with_list_of_type_having_custom_set_value(self):
    palette = stubs_gimp.Palette(name='Standard')
    palette2 = stubs_gimp.Palette(name='Standard2')

    setting = settings_.ArraySetting('palettes', element_type='palette')
    
    setting.set_value([{'name': 'Standard'}, {'name': 'Standard2'}])
    
    self.assertEqual(setting.value, (palette, palette2))
  
  def test_set_value_invalid_type_is_wrapped_in_iterable(self):
    self.setting.set_value(45)

    self.assertEqual(self.setting.value, (45,))
  
  def test_reset_retains_default_value(self):
    self.setting.set_value((20.0, 50.0, 40.0))
    self.setting.reset()
    self.assertEqual(self.setting.value, (1.0, 5.0, 10.0))
    self.assertEqual(self.setting.default_value, (1.0, 5.0, 10.0))
  
  def test_to_dict(self):
    self.assertDictEqual(
      self.setting.to_dict(),
      {
        'name': 'coordinates',
        'value': [1.0, 5.0, 10.0],
        'type': 'array',
        'default_value': [1.0, 5.0, 10.0],
        'element_type': 'float',
        'element_max_value': 100.0,
        'element_min_value': -100.0,
      })

  @mock.patch(
    f'{pgutils.get_pygimplib_module_path()}.setting.settings.Gimp',
    new=stubs_gimp.GimpModuleStub())
  def test_to_dict_with_type_having_custom_to_dict(self):
    # While we do not use these objects, the `name`s are registered so they can
    # be looked up via the `Palette.get_by_name()` class method.
    palette = stubs_gimp.Palette(name='Standard')
    palette2 = stubs_gimp.Palette(name='Standard2')

    setting = settings_.ArraySetting('palettes', element_type='palette')

    setting.set_value([{'name': 'Standard'}, {'name': 'Standard2'}])
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'palettes',
        'value': [
          {'name': 'Standard', 'columns': 0},
          {'name': 'Standard2', 'columns': 0},
        ],
        'type': 'array',
        'element_type': 'palette',
      })
  
  def test_to_dict_with_element_type_as_class(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type=settings_.FloatSetting,
      element_default_value=0.0,
      element_min_value=-100.0,
      element_max_value=100.0)
    
    self.assertDictEqual(
      setting.to_dict(),
      {
        'name': 'coordinates',
        'value': [1.0, 5.0, 10.0],
        'type': 'array',
        'default_value': [1.0, 5.0, 10.0],
        'element_type': 'float',
        'element_default_value': 0.0,
        'element_max_value': 100.0,
        'element_min_value': -100.0,
      })
  
  @parameterized.parameterized.expand([
    ('first', 0, 1.0),
    ('middle', 1, 5.0),
    ('last', 2, 10.0),
    ('last_with_negative_index', -1, 10.0),
    ('second_to_last_with_negative_index', -2, 5.0),
  ])
  def test_getitem(self, test_case_suffix, index, expected_value):
    self.assertEqual(self.setting[index].value, expected_value)
  
  @parameterized.parameterized.expand([
    ('first_to_middle', None, 2, [1.0, 5.0]),
    ('middle_to_last', 1, None, [5.0, 10.0]),
    ('middle_to_last_explicit', 1, 3, [5.0, 10.0]),
    ('all', None, None, [1.0, 5.0, 10.0]),
    ('negative_last_to_middle', -1, -3, [10.0, 5.0], -1),
  ])
  def test_getitem_slice(
        self, test_case_suffix, index_begin, index_end, expected_value, step=None):
    self.assertEqual(
      [element.value for element in self.setting[index_begin:index_end:step]],
      expected_value)
  
  @parameterized.parameterized.expand([
    ('one_more_than_length', 3),
    ('more_than_length', 5),
  ])
  def test_getitem_out_of_bounds_raises_error(self, test_case_suffix, index):
    with self.assertRaises(IndexError):
      # noinspection PyStatementEffect
      self.setting[index]
  
  @parameterized.parameterized.expand([
    ('first_element', [0]),
    ('middle_element', [1]),
    ('last_element', [2]),
    ('two_elements', [1, 1]),
    ('all_elements', [0, 0, 0]),
  ])
  def test_delitem(self, test_case_suffix, indexes_to_delete):
    orig_len = len(self.setting)
    
    for index in indexes_to_delete:
      del self.setting[index]
    
    self.assertEqual(len(self.setting), orig_len - len(indexes_to_delete))
  
  @parameterized.parameterized.expand([
    ('one_more_than_length', 3),
    ('more_than_length', 5),
  ])
  def test_delitem_out_of_bounds_raises_error(self, test_case_suffix, index):
    with self.assertRaises(IndexError):
      # noinspection PyStatementEffect
      self.setting[index]
  
  @parameterized.parameterized.expand([
    ('append_default_value',
     None, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, -1, 0.0),
    
    ('insert_at_beginning_default_value',
     0, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, 0, 0.0),
    
    ('insert_in_middle_default_value',
     1, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, 1, 0.0),
    
    ('append_value',
     None, 40.0, -1, 40.0),
    
    ('insert_in_middle_value',
     1, 40.0, 1, 40.0),
  ])
  def test_add_element(
        self, test_case_suffix, index, value, insertion_index, expected_value):
    element = self.setting.add_element(index, value=value)
    self.assertEqual(len(self.setting), 4)
    self.assertIs(self.setting[insertion_index], element)
    self.assertEqual(self.setting[insertion_index].value, expected_value)
  
  def test_add_element_none_as_value(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(),
      element_type='generic',
      element_default_value=0,
      element_value_set=lambda value: value,
      element_value_save=lambda value: value)
    
    setting.add_element(value=None)
    self.assertIsNone(setting[-1].value)
  
  @parameterized.parameterized.expand([
    ('middle_to_first', 1, 0, [5.0, 1.0, 10.0]),
    ('middle_to_last', 1, 2, [1.0, 10.0, 5.0]),
    ('middle_to_last_above_bounds', 1, 3, [1.0, 10.0, 5.0]),
    ('first_to_middle', 0, 1, [5.0, 1.0, 10.0]),
    ('last_to_middle', 2, 1, [1.0, 10.0, 5.0]),
    ('middle_to_last_negative_position', 1, -1, [1.0, 10.0, 5.0]),
    ('middle_to_middle_negative_position', 1, -2, [1.0, 5.0, 10.0]),
  ])
  def test_reorder_element(
        self, test_case_suffix, index, new_index, expected_values):
    self.setting.reorder_element(index, new_index)
    self.assertEqual(
      [element.value for element in self.setting.get_elements()],
      expected_values)
  
  def test_set_element_value(self):
    self.setting[1].set_value(50.0)
    self.assertEqual(self.setting[1].value, 50.0)
    self.assertEqual(self.setting.value, (1.0, 50.0, 10.0))
  
  def test_set_element_value_validates_value(self):
    self.setting[1].set_value(200.0)

  def test_reset_element_sets_element_default_value(self):
    self.setting[1].reset()
    self.assertEqual(self.setting[1].value, 0.0)
    self.assertEqual(self.setting.value, (1.0, 0.0, 10.0))
  
  def test_connect_event_for_individual_elements_affects_those_elements_only(self):
    def _on_array_changed(array_setting):
      array_setting[2].set_value(70.0)
    
    def _on_element_changed(element, array_setting):
      array_setting[0].set_value(20.0)
    
    self.setting.connect_event('value-changed', _on_array_changed)
    
    self.setting[1].connect_event('value-changed', _on_element_changed, self.setting)
    self.setting[1].set_value(50.0)
    
    self.assertEqual(self.setting[0].value, 20.0)
    self.assertEqual(self.setting[1].value, 50.0)
    self.assertEqual(self.setting[2].value, 10.0)
    self.assertEqual(self.setting.value, (20.0, 50.0, 10.0))
    
    self.setting.set_value((60.0, 80.0, 30.0))
    self.assertEqual(self.setting.value, (60.0, 80.0, 70.0))
  
  @parameterized.parameterized.expand([
    ('default_index',
     None, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, None, 0.0),
    
    ('explicit_index',
     1, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, 1, 0.0),
  ])
  def test_before_add_element_event(
        self, test_case_suffix, index, value, expected_index, expected_value):
    event_args = []
    
    def _on_before_add_element(array_setting, index, value):
      event_args.append((index, value))
    
    self.setting.connect_event('before-add-element', _on_before_add_element)
    
    self.setting.add_element(index, value)
    self.assertEqual(event_args[0][0], expected_index)
    self.assertEqual(event_args[0][1], expected_value)
  
  @parameterized.parameterized.expand([
    ('default_index',
     None, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, -1, 0.0),
    
    ('explicit_zero_index',
     0, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, 0, 0.0),
    
    ('explicit_positive_index',
     1, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, 1, 0.0),
    
    ('explicit_negative_index',
     -1, settings_.ArraySetting.ELEMENT_DEFAULT_VALUE, -2, 0.0),
  ])
  def test_after_add_element_event(
        self, test_case_suffix, index, value, expected_index, expected_value):
    event_args = []
    
    def _on_after_add_element(array_setting, insertion_index, value):
      event_args.append((insertion_index, value))
    
    self.setting.connect_event('after-add-element', _on_after_add_element)
    
    self.setting.add_element(index, value)
    self.assertEqual(event_args[0][0], expected_index)
    self.assertEqual(event_args[0][1], expected_value)
  
  @parameterized.parameterized.expand([
    ('default_length_name_and_description',
     None,
     None,
     'num-coordinates',
     ''),
    
    ('custom_length_name_and_description',
     'num-axes-coordinates',
     'The number of axes for coordinates',
     'num-axes-coordinates',
     'The number of axes for coordinates'),
  ])
  def test_get_pdb_param_for_registrable_setting(
        self,
        test_case_suffix,
        length_name,
        length_description,
        expected_length_name,
        expected_length_description):
    self.assertEqual(
      self.setting.get_pdb_param(length_name, length_description),
      [
        dict(
          name=expected_length_name,
          type=GObject.TYPE_INT,
          default=0,
          minimum=0,
          nick=expected_length_description,
          blurb=expected_length_description,
        ),
        dict(
          name='coordinates',
          type=Gimp.FloatArray,
          nick='Coordinates',
          blurb='Coordinates',
        ),
      ])
  
  def test_get_pdb_param_for_nonregistrable_setting(self):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='generic',
      element_default_value=0.0,
      element_value_set=lambda value: value,
      element_value_save=lambda value: value)
    
    self.assertIsNone(setting.get_pdb_param())


class TestArraySettingCreateWithSize(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('default_sizes', None, None, 0, None),
    ('min_size_zero', 0, None, 0, None),
    ('min_size_positive', 1, None, 1, None),
    ('min_size_positive_max_size_positive', 1, 5, 1, 5),
    ('max_size_equal_to_default_value_length', 1, 3, 1, 3),
    ('min_and_max_size_equal_to_default_value_length', 3, 3, 3, 3),
  ])
  def test_create_with_size(
        self,
        test_case_suffix,
        min_size,
        max_size,
        expected_min_size,
        expected_max_size):
    setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_default_value=0.0,
      min_size=min_size,
      max_size=max_size)
    
    self.assertEqual(setting.min_size, expected_min_size)
    self.assertEqual(setting.max_size, expected_max_size)


class TestArraySettingSize(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_.ArraySetting(
      'coordinates',
      default_value=(1.0, 5.0, 10.0),
      element_type='float',
      element_default_value=0.0,
      element_min_value=-100.0,
      element_max_value=100.0,
      min_size=2,
      max_size=4)
  
  @parameterized.parameterized.expand([
    ('value_length_less_than_min_size', (1.0,)),
    ('value_length_greater_than_max_size', (1.0, 5.0, 10.0, 30.0, 70.0)),
  ])
  def test_set_value_invalid_size(self, test_case_suffix, value):
    self.setting.set_value(value)

    self.assertFalse(self.setting.is_valid)

  def test_add_element(self):
    self.setting.add_element()

    self.assertEqual(len(self.setting.get_elements()), 4)
  
  def test_add_element_more_than_max_size(self):
    self.setting.add_element()
    self.setting.add_element()

    self.assertEqual(len(self.setting.get_elements()), 5)
    self.assertFalse(self.setting.is_valid)
  
  def test_delete_element_with_respect_to_size(self):
    del self.setting[-1]

    self.assertEqual(len(self.setting.get_elements()), 2)
  
  def test_delete_element_less_than_min_size(self):
    del self.setting[-1]
    del self.setting[-1]

    self.assertEqual(len(self.setting.get_elements()), 1)
    self.assertFalse(self.setting.is_valid)


class TestContainerSettings(unittest.TestCase):
  
  def test_set_value_nullable_allows_none(self):
    setting = settings_.ListSetting('setting', nullable=True)
    
    setting.set_value(None)
    self.assertIsNone(setting.value)
  
  def test_set_value_for_list_setting(self):
    expected_value = [1, 4, 'five']
    
    setting = settings_.ListSetting('setting')
    
    setting.set_value(expected_value)
    self.assertEqual(setting.value, expected_value)
    
    setting.set_value(tuple(expected_value))
    self.assertListEqual(setting.value, expected_value)
  
  def test_set_value_for_tuple_setting(self):
    expected_value = (1, 4, 'five')
    
    setting = settings_.TupleSetting('setting')
    
    setting.set_value(expected_value)
    self.assertEqual(setting.value, expected_value)
    
    setting.set_value(list(expected_value))
    self.assertTupleEqual(setting.value, expected_value)
  
  def test_to_dict_for_tuple_setting(self):
    expected_value = (1, 4, 'five')
    
    setting = settings_.TupleSetting('setting')
    
    setting.set_value(expected_value)
    
    self.assertDictEqual(
      setting.to_dict(), {'name': 'setting', 'value': [1, 4, 'five'], 'type': 'tuple'})
  
  def test_set_value_for_set_setting(self):
    expected_value = {1, 4, 'five'}
    
    setting = settings_.SetSetting('setting')
    
    setting.set_value(expected_value)
    self.assertEqual(setting.value, expected_value)
    
    setting.set_value(list(expected_value))
    self.assertSetEqual(setting.value, expected_value)
  
  def test_to_dict_for_set_setting(self):
    expected_value = {1, 4, 'five'}
    
    setting = settings_.SetSetting('setting')

    setting.set_value(expected_value)
    
    self.assertDictEqual(
      setting.to_dict(), {'name': 'setting', 'value': list(expected_value), 'type': 'set'})


class TestGetSettingTypeFromGobjectType(unittest.TestCase):

  def test_int_setting(self):
    self.assertEqual(
      settings_.get_setting_type_from_gtype(GObject.TYPE_INT, None),
      (settings_.IntSetting, dict(pdb_type=GObject.TYPE_INT)),
    )

  def test_uint_setting(self):
    self.assertEqual(
      settings_.get_setting_type_from_gtype(GObject.TYPE_UINT, None),
      (settings_.IntSetting, dict(pdb_type=GObject.TYPE_UINT)),
    )

  def test_enum(self):
    self.assertEqual(
      settings_.get_setting_type_from_gtype(Gimp.ImageType.__gtype__, None),
      (settings_.EnumSetting, dict(enum_type=Gimp.ImageType.__gtype__)),
    )

  def test_builtin_array(self):
    self.assertEqual(
      settings_.get_setting_type_from_gtype(Gimp.FloatArray.__gtype__, None),
      (settings_.ArraySetting, dict(element_type=settings_.FloatSetting)),
    )

  def test_object_array(self):
    param_spec = collections.namedtuple('ParamSpecStub', ['name'])('drawables')

    # noinspection PyTypeChecker
    self.assertEqual(
      settings_.get_setting_type_from_gtype(Gimp.ObjectArray.__gtype__, param_spec),
      (settings_.ArraySetting, dict(element_type=settings_.DrawableSetting)),
    )

  def test_unrecognized_gtype_returns_none(self):
    self.assertIsNone(settings_.get_setting_type_from_gtype(Gimp.Procedure, None))
