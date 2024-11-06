import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import settings_from_pdb as settings_from_pdb_
from src import placeholders as placeholders_


@mock.patch(
  f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
  return_value=pg.tests.stubs_gimp.PdbStub,
)
class TestGetSettingDataFromPdbProcedure(unittest.TestCase):

  @mock.patch(
    f'{pg.utils.get_pygimplib_module_path()}.pypdb.Gimp.get_pdb',
    return_value=pg.tests.stubs_gimp.PdbStub,
  )
  def setUp(self, mock_get_pdb):
    self.procedure_name = 'file-png-save'

    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(value_type=Gimp.RunMode.__gtype__, name='run-mode', blurb='The run mode'),
        dict(
          value_type=GObject.GType.from_name('GimpCoreObjectArray'),
          name='drawables',
          blurb='Drawables'),
        dict(
          value_type=GObject.TYPE_STRING, name='filename', blurb='Filename to save the image in')],
      blurb='Saves files in PNG file format')

    settings_from_pdb_.pdb.remove_from_cache(self.procedure_name)

  def test_with_non_unique_param_names(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(
        value_type=GObject.GType.from_name('GimpCoreObjectArray'),
        name='drawables',
        blurb='More drawables'),
      dict(value_type=GObject.TYPE_STRING, name='filename', blurb='Another filename'),
      dict(value_type=GObject.TYPE_STRV, name='brushes', blurb='Brush names'),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    procedure, procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      extended_procedure_stub.get_name())

    self.assertIs(procedure, extended_procedure_stub)
    self.assertEqual(procedure_name, self.procedure_name)

    self.maxDiff = None

    self.assertListEqual(
      arguments,
      [
        {
          'name': 'run-mode',
          'type': pg.setting.EnumSetting,
          'default_value': Gimp.RunMode.NONINTERACTIVE,
          'enum_type': Gimp.RunMode.__gtype__,
          'display_name': 'The run mode',
        },
        {
          'name': 'drawables',
          'type': placeholders_.PlaceholderDrawableArraySetting,
          'element_type': pg.setting.DrawableSetting,
          'display_name': 'Drawables',
        },
        {
          'name': 'filename',
          'type': pg.setting.StringSetting,
          'pdb_type': GObject.TYPE_STRING,
          'display_name': 'Filename to save the image in',
        },
        {
          'name': 'drawables-2',
          'type': placeholders_.PlaceholderDrawableArraySetting,
          'element_type': pg.setting.DrawableSetting,
          'display_name': 'More drawables',
        },
        {
          'name': 'filename-2',
          'type': pg.setting.StringSetting,
          'pdb_type': GObject.TYPE_STRING,
          'display_name': 'Another filename',
        },
        {
          'name': 'brushes',
          'type': pg.setting.ArraySetting,
          'element_type': pg.setting.StringSetting,
          'display_name': 'Brush names',
        },
      ]
    )

  def test_unsupported_pdb_param_type(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(
        value_type='unsupported',
        default_value='test',
        name='param-with-unsupported-type',
        blurb='Test'),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      extended_procedure_stub.get_name())

    unsupported_param = arguments[-1]

    self.assertDictEqual(
      unsupported_param,
      {
        'type': placeholders_.PlaceholderUnsupportedParameterSetting,
        'name': 'param-with-unsupported-type',
        'display_name': 'Test',
        'default_param_value': 'test',
      }
    )

  def test_default_run_mode_is_noninteractive(self, mock_get_pdb):
    self.procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(self.procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[0]['default_value'], Gimp.RunMode.NONINTERACTIVE)

  def test_gimp_object_types_are_replaced_with_placeholders(self, mock_get_pdb):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type=Gimp.Image.__gtype__, name='image', blurb='The image'),
      dict(value_type=Gimp.Layer.__gtype__, name='layer', blurb='The layer to process'),
    ])

    extended_procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[-2]['type'], placeholders_.PlaceholderImageSetting)
    self.assertEqual(arguments[-1]['type'], placeholders_.PlaceholderLayerSetting)

  def test_with_hard_coded_custom_default_value(self, mock_get_pdb):
    self.procedure_name = 'plug-in-lighting'
    self.procedure_stub_kwargs['name'] = self.procedure_name

    self.procedure_stub_kwargs['arguments_spec'].append(
      dict(value_type=GObject.TYPE_BOOLEAN, name='new-image', default_value=True),
    )

    procedure_stub = stubs_gimp.PdbProcedureStub(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[-1]['default_value'], False)
