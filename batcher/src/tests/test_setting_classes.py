import collections
import os

import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import setting_classes


def _get_images_and_items():
  image_1 = stubs_gimp.Image(filepath='filename_1')
  image_2 = stubs_gimp.Image(filepath='filename_2')
  
  images = [image_1, image_2]
  
  item_4 = stubs_gimp.Layer(name='item_4', image=image_1, is_group=True)
  item_1 = stubs_gimp.Layer(name='item_1', image=image_1)
  item_3 = stubs_gimp.Layer(name='item_3', image=image_1, parent=item_4)
  item_7 = stubs_gimp.Layer(name='item_7', image=image_2, is_group=True)
  item_5 = stubs_gimp.Layer(name='item_5', image=image_2, parent=item_7)
  
  image_1.layers = [item_1, item_4]
  item_4.children = [item_3]
  image_2.layers = [item_7]
  item_7.children = [item_5]
  
  items = [item_1, item_3, item_4, item_5, item_7]
  
  return images, items


def _get_images_and_items_with_ids():
  images, items = _get_images_and_items()
  
  # `None` indicates invalid images/items that must not be in the expected data.
  images = [images[0], images[1], None]
  items = [items[0], items[1], items[2], items[3], None, items[4], None, None, None]
  
  return images, items


def _get_images_and_items_with_paths():
  images, items = _get_images_and_items()
  
  images = [[images[0]], [images[1]], []]
  
  return images, items


class TestFileExtensionSetting(unittest.TestCase):

  def setUp(self):
    self.setting = setting_classes.FileExtensionSetting('file_ext', default_value='png')

  def test_with_adjust_value(self):
    setting = setting_classes.FileExtensionSetting(
      'file_ext', adjust_value=True, default_value='png')

    setting.set_value('.jpg')

    self.assertEqual(setting.value, 'jpg')


@mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestImagesAndGimpItemsSetting(unittest.TestCase):

  def setUp(self):
    self.setting = setting_classes.ImagesAndGimpItemsSetting('selected_layers')
    
    self.maxDiff = None
  
  def test_set_value_from_objects(self, *_mocks):
    images, items = _get_images_and_items()

    self.setting.set_value({
      images[0]: [items[0], items[1], (items[2], 'folder')],
      images[1]: [items[3], (items[4], 'folder')],
    })
    
    expected_value = collections.defaultdict(set)
    expected_value[images[0]] = {items[0].id_, items[1].id_, (items[2].id_, 'folder')}
    expected_value[images[1]] = {items[3].id_, (items[4].id_, 'folder')}
    
    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_from_ids(self, *_mocks):
    images, items = _get_images_and_items_with_ids()

    self.setting.set_value({
      images[0].id_: [items[0].id_, items[1].id_, (items[2].id_, 'folder')],
      images[1].id_: [items[3].id_, (-10, 'folder'), [items[5].id_, 'folder'], -11],
      -2: [-12, -13]})

    expected_value = collections.defaultdict(set)
    expected_value[images[0]] = {items[0].id_, items[1].id_, (items[2].id_, 'folder')}
    expected_value[images[1]] = {items[3].id_, (items[5].id_, 'folder')}

    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_from_paths(self, *_mocks):
    images, items = _get_images_and_items_with_paths()

    with mock.patch(
          f'{pg.utils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.side_effect = images
      temp_mock_gimp_module.Layer = stubs_gimp.GimpModuleStub.Layer

      self.setting.set_value(
        {os.path.abspath('filename_1'): [
          ('Layer', 'item_1'),
          ('Layer', 'item_4/item_3'),
          ('Layer', 'item_4', 'folder')],
         os.path.abspath('filename_2'): [
          ('Layer', 'item_7/item_5'),
          ('Layer', 'item_6', 'folder'),
          ('Layer', 'item_7', 'folder'),
          ('Layer', 'item_8')],
         os.path.abspath('filename_3'): [
           ('Layer', 'item_9'),
           ('Layer', 'item_10')]})

    expected_value = collections.defaultdict(set)
    expected_value[images[0][0]] = {items[0].id_, items[1].id_, (items[2].id_, 'folder')}
    expected_value[images[1][0]] = {items[3].id_, (items[4].id_, 'folder')}

    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_invalid_list_length_raises_error(self, *_mocks):
    images, items = _get_images_and_items_with_ids()

    with self.assertRaises(ValueError):
      self.setting.set_value({
        images[0].id_: [
          items[0].id_, items[1].id_, (items[2].id_, 'folder', 'extra_item_1', 'extra_item_2')]})

  def test_set_value_invalid_collection_type_for_items_raises_error(self, *_mocks):
    images, items = _get_images_and_items_with_ids()

    with self.assertRaises(TypeError):
      self.setting.set_value({images[0].id_: object()})

  def test_to_dict_with_paths(self, *_mocks):
    images, items = _get_images_and_items_with_ids()

    self.setting.set_value({
      images[0].id_: [items[0].id_, items[1].id_, (items[2].id_, 'folder')],
      images[1].id_: [items[3].id_, (-10, 'folder'), [items[5].id_, 'folder'], -11],
      -2: [-12, -13]})

    expected_dict = {
      'name': 'selected_layers',
      'type': 'images_and_gimp_items',
      'value': {
        os.path.abspath('filename_1'): [
          ['Layer', 'item_1'],
          ['Layer', 'item_4/item_3'],
          ['Layer', 'item_4', 'folder']],
        os.path.abspath('filename_2'): [
          ['Layer', 'item_7/item_5'],
          ['Layer', 'item_7', 'folder']],
      },
    }

    actual_dict = self.setting.to_dict()

    self.assertEqual(actual_dict['name'], expected_dict['name'])
    self.assertEqual(actual_dict['type'], expected_dict['type'])
    # We need to compare 'value' field element by element since unordered sets
    # are converted to lists, and we cannot guarantee stable order in sets.
    for key in expected_dict['value']:
      self.assertIn(key, actual_dict['value'])
      for item in expected_dict['value'][key]:
        self.assertIn(item, actual_dict['value'][key])

  def test_to_dict_with_image_without_filepaths(self, *_mocks):
    images, items = _get_images_and_items_with_ids()

    images[1].set_file(None)

    self.setting.set_value({
      images[0].id_: [items[0].id_, items[1].id_, (items[2].id_, 'folder')],
      images[1].id_: [items[3].id_, (-10, 'folder'), [items[5].id_, 'folder'], -11],
      -2: [-12, -13]})

    expected_dict = {
      'name': 'selected_layers',
      'type': 'images_and_gimp_items',
      'value': {
        os.path.abspath('filename_1'): [
          ['Layer', 'item_1'],
          ['Layer', 'item_4/item_3'],
          ['Layer', 'item_4', 'folder']],
      },
    }

    actual_dict = self.setting.to_dict()

    self.assertEqual(actual_dict['name'], expected_dict['name'])
    self.assertEqual(actual_dict['type'], expected_dict['type'])
    # We need to compare 'value' field element by element since unordered sets
    # are converted to lists, and we cannot guarantee stable order in sets.
    for key in expected_dict['value']:
      self.assertIn(key, actual_dict['value'])
      for item in expected_dict['value'][key]:
        self.assertIn(item, actual_dict['value'][key])


class TestImagesAndDirectoriesSetting(unittest.TestCase):
  
  def setUp(self):
    self.image_ids_and_filepaths = [
      (0, None), (1, 'image.png'), (2, 'test.jpg'),
      (4, 'another_test.gif')]
    self.image_list = self._create_image_list(self.image_ids_and_filepaths)
    self.images_and_directories = self._create_images_and_directories(self.image_list)

    self.setting = setting_classes.ImagesAndDirectoriesSetting('images_and_directories')
    self.setting.set_value(self.images_and_directories)

  def test_update_images_and_dirpaths_add_new_images(self):
    self.image_list.extend(
      self._create_image_list([(5, 'new_image.png'), (6, None)]))
    
    with mock.patch('src.setting_classes.Gimp.list_images', new=self.get_image_list):
      self.setting.update_images_and_dirpaths()
    
    self.assertEqual(
      self.setting.value, self._create_images_and_directories(self.image_list))
  
  def test_update_images_and_dirpaths_remove_closed_images(self):
    self.image_list.pop(1)

    with mock.patch('src.setting_classes.Gimp.list_images', new=self.get_image_list):
      self.setting.update_images_and_dirpaths()
    
    self.assertEqual(
      self.setting.value, self._create_images_and_directories(self.image_list))
  
  def test_update_directory(self):
    self.setting.update_dirpath(self.image_list[1], 'test_directory')
    self.assertEqual(self.setting.value[self.image_list[1]], 'test_directory')
  
  def test_value_setitem_does_not_change_setting_value(self):
    image_to_test = self.image_list[1]
    self.setting.value[image_to_test] = 'test_directory'
    self.assertNotEqual(self.setting.value[image_to_test], 'test_directory')
    self.assertEqual(
      self.setting.value[image_to_test],
      self.images_and_directories[image_to_test])

  def test_set_value_from_image_ids(self):
    with mock.patch('src.setting_classes.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = self.image_list

      self.setting.set_value({0: 'dirpath1', 1: 'dirpath2'})

    self.assertDictEqual(
      self.setting.value,
      {self.image_list[0]: 'dirpath1', self.image_list[1]: 'dirpath2'})

  def test_set_value_from_image_paths(self):
    with mock.patch(
          f'{pg.utils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.list_images.side_effect = [[self.image_list[1]], [self.image_list[2]]]

      self.setting.set_value(
        {os.path.abspath('image.png'): 'dirpath1', os.path.abspath('test.jpg'): 'dirpath2'})

    self.assertDictEqual(
      self.setting.value,
      {self.image_list[1]: 'dirpath1', self.image_list[2]: 'dirpath2'})

  def get_image_list(self):
    # `self.image_list` is wrapped into a method so that `mock.patch.object` can
    # be called on it.
    return self.image_list

  @staticmethod
  def _create_image_list(image_ids_and_filepaths):
    return [
      stubs_gimp.Image(id_=image_id, filepath=filepath)
      for image_id, filepath in image_ids_and_filepaths]

  @staticmethod
  def _create_images_and_directories(image_list):
    images_and_directories = {}
    for image in image_list:
      images_and_directories[image] = (
        os.path.dirname(image.get_file().get_path()) if image.get_file() is not None else None)
    return images_and_directories


@mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
class TestFileFormatOptionsSetting(unittest.TestCase):

  @mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
  @mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
  def setUp(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
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
        'type': pg.setting.FloatSetting,
        'display_name': 'quality',
        'default_value': 0.9,
      },
    ]

    self.setting = setting_classes.FileFormatOptionsSetting(
      'file_format_export_options', 'export', 'png')

    self._ACTIVE_KEY = setting_classes.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY

  def test_set_active_file_format(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-save', self.jpg_options

    self.setting.set_active_file_format('jpg')

    mock_get_setting_data_from_pdb_procedure.assert_called_once()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertIn('jpg', self.setting.value)

  def test_set_active_file_format_with_alias(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-save', self.jpg_options

    self.setting.set_active_file_format('jpeg')

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertIn('jpg', self.setting.value)

  def test_set_active_file_format_to_unrecognized_format(
        self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    self.setting.set_active_file_format('unknown')

    mock_get_setting_data_from_pdb_procedure.assert_not_called()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'unknown')
    self.assertNotIn('unknown', self.setting.value)

  def test_to_dict(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-png-save', self.png_options

    self.setting.set_active_file_format('png')
    self.setting.set_active_file_format('unknown')

    self.setting.value['png']['compression'].set_value(7)

    self.maxDiff = None

    self.assertEqual(
      self.setting.to_dict(),
      {
        'name': 'file_format_export_options',
        'type': 'file_format_options',
        'import_or_export': 'export',
        'initial_file_format': 'png',
        'value': {
          self._ACTIVE_KEY: 'unknown',
          'png': [
            {
              'name': 'interlaced',
              'type': 'bool',
              'display_name': 'interlaced',
              'default_value': False,
              'value': False,
            },
            {
              'name': 'compression',
              'type': 'int',
              'display_name': 'compression',
              'default_value': 9,
              'value': 7,
            },
          ],
        },
      }
    )

  def test_set_value_from_settings(self, *_mocks):
    png_group = pg.setting.Group('file_format_options')
    png_group.add([
      {
        'name': 'interlaced',
        'type': 'bool',
        'display_name': 'interlaced',
        'default_value': False,
      },
    ])

    jpeg_group = pg.setting.Group('file_format_options')
    jpeg_group.add([
      {
        'name': 'quality',
        'type': pg.setting.FloatSetting,
        'display_name': 'quality',
        'default_value': 0.9,
      },
      {
        'name': 'optimize',
        'type': 'bool',
        'display_name': 'optimize',
        'default_value': False,
      },
    ])

    self.setting.set_value({
      'png': png_group,
      'jpg': jpeg_group,
      self._ACTIVE_KEY: 'jpg',
    })

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertNotIn('compression', self.setting.value['png'])
    self.assertEqual(self.setting.value['png']['interlaced'].value, False)
    self.assertEqual(self.setting.value['jpg']['quality'].value, 0.9)
    self.assertEqual(self.setting.value['jpg']['optimize'].value, False)

    self.assertIsNot(png_group, self.setting.value['png'])
    self.assertIsNot(jpeg_group, self.setting.value['jpg'])

  def test_set_value_from_raw_list(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    self.setting.set_value({
      'jpg': [
        {
          'name': 'optimize',
          'type': 'bool',
          'display_name': 'optimize',
          'default_value': False,
        },
      ],
      'gif': [
        {
          'name': 'loop',
          'type': 'bool',
          'display_name': 'loop',
          'default_value': True,
        },
      ],
      self._ACTIVE_KEY: 'jpg',
    })

    mock_get_setting_data_from_pdb_procedure.assert_not_called()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertNotIn('png', self.setting.value)
    self.assertNotIn('quality', self.setting.value['jpg'])
    self.assertEqual(self.setting.value['jpg']['optimize'].value, False)
    self.assertEqual(self.setting.value['gif']['loop'].value, True)

  def test_validate_value_with_missing_none_key(self, *_mocks):
    png_group = pg.setting.Group('file_format_options')
    png_group.add([
      {
        'name': 'interlaced',
        'type': 'bool',
        'display_name': 'interlaced',
        'default_value': False,
      },
    ])

    self.assertIsInstance(self.setting.validate({'png': png_group}), pg.setting.ValueNotValidData)
