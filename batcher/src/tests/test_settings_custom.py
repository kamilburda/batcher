import collections
import os

import unittest
import unittest.mock as mock

import pygimplib as pg
from pygimplib.tests import stubs_gimp

import batcher.src.settings_custom as settings_custom


def _get_images_and_items():
  image_1 = stubs_gimp.Image(id_=1, filepath='filename_1')
  image_2 = stubs_gimp.Image(id_=2, filepath='filename_2')
  
  images = [image_1, image_2]
  
  item_4 = stubs_gimp.Layer(name='item_4', id_=4, image=image_1, is_group=True)
  item_1 = stubs_gimp.Layer(name='item_1', id_=1, image=image_1)
  item_3 = stubs_gimp.Layer(name='item_3', id_=3, image=image_1, parent=item_4)
  item_7 = stubs_gimp.Layer(name='item_7', id_=7, image=image_2, is_group=True)
  item_5 = stubs_gimp.Layer(name='item_5', id_=5, image=image_2, parent=item_7)
  
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
    self.setting = settings_custom.FileExtensionSetting('file_ext', default_value='png')

  def test_with_adjust_value(self):
    setting = settings_custom.FileExtensionSetting(
      'file_ext', adjust_value=True, default_value='png')

    setting.set_value('.jpg')

    self.assertEqual(setting.value, 'jpg')

  def test_invalid_default_value(self):
    with self.assertRaises(pg.setting.SettingDefaultValueError):
      settings_custom.FileExtensionSetting('file_ext', default_value=None)

  def test_custom_error_message(self):
    self.setting.error_messages[pg.path.FileValidatorErrorStatuses.IS_EMPTY] = (
      'my custom message')
    try:
      self.setting.set_value('')
    except pg.setting.SettingValueError as e:
      self.assertEqual(str(e), 'my custom message')


class TestImagesAndGimpItemsSetting(unittest.TestCase):

  def setUp(self):
    self.setting = settings_custom.ImagesAndGimpItemsSetting('selected_layers')
    
    self.maxDiff = None
  
  def test_set_value_from_objects(self):
    images, items = _get_images_and_items()

    self.setting.set_value({
      images[0]: [items[0], items[1], (items[2], 'folder')],
      images[1]: [items[3], (items[4], 'folder')],
    })
    
    expected_value = collections.defaultdict(set)
    expected_value[images[0]] = {items[0], items[1], (items[2], 'folder')}
    expected_value[images[1]] = {items[3], (items[4], 'folder')}
    
    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_from_ids(self):
    images, items = _get_images_and_items_with_ids()

    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images

      self.setting.set_value(
        {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})

    expected_value = collections.defaultdict(set)
    expected_value[images[0]] = {items[0], items[1], (items[2], 'folder')}
    expected_value[images[1]] = {items[3], (items[5], 'folder')}

    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_from_paths(self):
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
    expected_value[images[0][0]] = {items[0], items[1], (items[2], 'folder')}
    expected_value[images[1][0]] = {items[3], (items[4], 'folder')}
    
    self.assertEqual(self.setting.value, expected_value)
  
  def test_set_value_invalid_list_length_raises_error(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images

      with self.assertRaises(ValueError):
        self.setting.set_value(
          {1: [1, 3, (4, 'folder', 'extra_item_1', 'extra_item_2')]})
  
  def test_set_value_invalid_collection_type_for_items_raises_error(self):
    images, items = _get_images_and_items_with_ids()

    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images
        
      with self.assertRaises(TypeError):
        self.setting.set_value(
          {1: object()})
  
  def test_to_dict_with_paths(self):
    images, items = _get_images_and_items_with_ids()

    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images

      self.setting.set_value(
        {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})

      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items

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
  
  def test_to_dict_with_image_without_filepaths(self):
    images, items = _get_images_and_items_with_ids()

    images[1].set_file(None)
    
    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items

      self.setting.set_value(
        {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})

      temp_mock_gimp_module_src.Image.get_by_id.side_effect = images
      temp_mock_gimp_module_src.Item.get_by_id.side_effect = items

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

    self.setting = settings_custom.ImagesAndDirectoriesSetting('images_and_directories')
    self.setting.set_value(self.images_and_directories)

  def test_update_images_and_dirpaths_add_new_images(self):
    self.image_list.extend(
      self._create_image_list([(5, 'new_image.png'), (6, None)]))
    
    with mock.patch('batcher.src.settings_custom.Gimp.list_images', new=self.get_image_list):
      self.setting.update_images_and_dirpaths()
    
    self.assertEqual(
      self.setting.value, self._create_images_and_directories(self.image_list))
  
  def test_update_images_and_dirpaths_remove_closed_images(self):
    self.image_list.pop(1)

    with mock.patch('batcher.src.settings_custom.Gimp.list_images', new=self.get_image_list):
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
    with mock.patch('batcher.src.settings_custom.Gimp') as temp_mock_gimp_module_src:
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
