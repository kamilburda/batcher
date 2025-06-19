"""Test cases for Export Layers. Requires GIMP to be running."""

import inspect
import os
import shutil
import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from config import CONFIG
from src import builtin_actions
from src import commands
from src import core
from src import itemtree
from src import plugin_settings
from src import utils
from src import utils_pdb
from src import utils_setting as utils_setting_
from src.procedure_groups import *


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))
TEST_IMAGES_DIRPATH = os.path.join(_CURRENT_MODULE_DIRPATH, 'test_images')

DEFAULT_EXPECTED_RESULTS_DIRPATH = os.path.join(
  TEST_IMAGES_DIRPATH, 'export_layers_expected_results')
OUTPUT_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'temp_output')
INCORRECT_RESULTS_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'incorrect_results')


class TestExportLayersCompareLayerContents(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    CONFIG.PROCEDURE_GROUP = EXPORT_LAYERS_GROUP

    Gimp.context_push()

    cls.test_image_filepath = os.path.join(
      TEST_IMAGES_DIRPATH, 'export_layers_inputs', 'test_contents.xcf')
    cls.test_image = cls._load_image()
    
    cls.output_dirpath = OUTPUT_DIRPATH
    
    if os.path.exists(cls.output_dirpath):
      shutil.rmtree(cls.output_dirpath)
    
    if os.path.exists(INCORRECT_RESULTS_DIRPATH):
      shutil.rmtree(INCORRECT_RESULTS_DIRPATH)

    gimp_version = '-'.join(
      str(version_number_part) for version_number_part in cls._get_gimp_version_as_tuple()[:2]
    )

    version_specific_expected_results_dirpath = (
      f'{DEFAULT_EXPECTED_RESULTS_DIRPATH}_{gimp_version}')
    
    if os.path.isdir(version_specific_expected_results_dirpath):
      cls.expected_results_root_dirpath = version_specific_expected_results_dirpath
    else:
      cls.expected_results_root_dirpath = DEFAULT_EXPECTED_RESULTS_DIRPATH
    
    # key: path to directory containing expected results
    # value: `Gimp.Image` instance
    cls.expected_images = {}
  
  @classmethod
  def tearDownClass(cls):
    cls.test_image.delete()
    for image in cls.expected_images.values():
      image.delete()
    
    Gimp.context_pop()
  
  def setUp(self):
    self.image_with_results = None
  
  def tearDown(self):
    if self.image_with_results is not None:
      self.image_with_results.delete()

    if os.path.exists(self.output_dirpath):
      shutil.rmtree(self.output_dirpath)
  
  def test_default_settings(self):
    self.compare(
      expected_results_dirpath=os.path.join(self.expected_results_root_dirpath, 'default'),
    )
  
  def test_use_image_size(self):
    self.compare(
      action_names_to_remove=['resize_canvas'],
      expected_results_dirpath=os.path.join(self.expected_results_root_dirpath, 'use_image_size'),
    )
  
  def test_background(self):
    self.compare(
      action_names_to_add={'insert_background_for_layers': 0},
      expected_results_dirpath=os.path.join(self.expected_results_root_dirpath, 'background'),
      additional_init_before_run=(
        lambda image: self._set_color_tag(image, 'main-background', Gimp.ColorTag.BLUE)),
    )
  
  def test_foreground(self):
    self.compare(
      action_names_to_add={'insert_foreground_for_layers': 0},
      expected_results_dirpath=os.path.join(self.expected_results_root_dirpath, 'foreground'),
      additional_init_before_run=(
        lambda image: self._set_color_tag(image, 'main-background', Gimp.ColorTag.GREEN)),
    )
    
    self._reload_image()

  @staticmethod
  def _set_color_tag(image, layer_name, color_tag):
    for layer in image.get_layers():
      if layer.get_name() == layer_name:
        layer.set_color_tag(color_tag)

  def compare(
        self,
        action_names_to_add=None,
        action_names_to_remove=None,
        different_results_and_expected_layers=None,
        expected_results_dirpath=None,
        additional_init_before_run=None,
  ):
    settings = plugin_settings.create_settings_for_export_layers()
    settings['main/output_directory'].set_value(Gio.file_new_for_path(self.output_dirpath))
    settings['main/file_extension'].set_value('xcf')
    
    if expected_results_dirpath is None:
      expected_results_dirpath = self.expected_results_root_dirpath
    
    if expected_results_dirpath not in self.expected_images:
      self.expected_images[expected_results_dirpath], expected_layers = (
        self._load_layers_from_dirpath(expected_results_dirpath))
    else:
      expected_layers = {
        layer.get_name(): layer
        for layer in self.expected_images[expected_results_dirpath].get_layers()}
    
    self._export(
      settings, action_names_to_add, action_names_to_remove, additional_init_before_run)
    
    self.image_with_results, layers = self._load_layers_from_dirpath(self.output_dirpath)

    if different_results_and_expected_layers is not None:
      for layer_name, expected_layer_name in different_results_and_expected_layers:
        expected_layers[layer_name] = expected_layers[expected_layer_name]
    
    for layer in layers.values():
      test_case_name = inspect.stack()[1][-3]
      self._compare_layers(
        layer,
        expected_layers[layer.get_name()],
        settings,
        test_case_name,
        expected_results_dirpath)

  def _export(
        self,
        settings,
        action_names_to_add,
        action_names_to_remove,
        additional_init_before_run,
  ):
    if action_names_to_add is None:
      action_names_to_add = {}
    
    if action_names_to_remove is None:
      action_names_to_remove = []
    
    for action_name, order in action_names_to_add.items():
      commands.add(
        settings['main/actions'],
        builtin_actions.BUILTIN_ACTIONS[action_name])
      if order is not None:
        commands.reorder(settings['main/actions'], action_name, order)
    
    for action_name in action_names_to_remove:
      if action_name in settings['main/actions']:
        commands.remove(settings['main/actions'], action_name)

    if additional_init_before_run is not None:
      additional_init_before_run(self.test_image)

    item_tree = itemtree.LayerTree()
    item_tree.add_from_image(self.test_image)

    batcher = core.LayerBatcher(
      item_tree=item_tree,
      actions=settings['main/actions'],
      conditions=settings['main/conditions'],
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
    )
    
    batcher.run(**utils_setting_.get_settings_for_batcher(settings['main']))
    
    for action_name in action_names_to_add:
      commands.remove(settings['main/actions'], action_name)
  
  def _compare_layers(
        self, layer, expected_layer, settings, test_case_name, expected_results_dirpath):
    comparison_result = utils_pdb.compare_layers([layer, expected_layer])

    if not comparison_result:
      self._save_incorrect_layers(
        layer, expected_layer, settings, test_case_name, expected_results_dirpath)
    
    self.assertEqual(
      comparison_result,
      True,
      msg=(
        'Layers are not identical:'
        f'\nprocessed layer: {layer.get_name()}\nexpected layer: {expected_layer.get_name()}'))
  
  def _save_incorrect_layers(
        self, layer, expected_layer, settings, test_case_name, expected_results_dirpath):
    incorrect_layers_dirpath = os.path.join(INCORRECT_RESULTS_DIRPATH, test_case_name)
    os.makedirs(incorrect_layers_dirpath, exist_ok=True)
    
    self._copy_incorrect_layer(
      layer, settings, self.output_dirpath, incorrect_layers_dirpath, '_actual')
    self._copy_incorrect_layer(
      expected_layer,
      settings,
      expected_results_dirpath,
      incorrect_layers_dirpath,
      '_expected')
  
  @staticmethod
  def _copy_incorrect_layer(
        layer, settings, layer_dirpath, incorrect_layers_dirpath, filename_suffix):
    layer_input_filename = f'{layer.get_name()}.{settings["main/file_extension"].value}'
    layer_output_filename = (
      f'{layer.get_name()}{filename_suffix}.{settings["main/file_extension"].value}')
    
    shutil.copy(
      os.path.join(layer_dirpath, layer_input_filename),
      os.path.join(incorrect_layers_dirpath, layer_output_filename))
  
  @classmethod
  def _load_image(cls):
    return Gimp.file_load(
      Gimp.RunMode.NONINTERACTIVE, Gio.file_new_for_path(cls.test_image_filepath))
  
  @classmethod
  def _reload_image(cls):
    cls.test_image.delete()
    cls.test_image = cls._load_image()
  
  @classmethod
  def _load_layers_from_dirpath(cls, layers_dirpath):
    return cls._load_layers(cls._list_layer_filepaths(layers_dirpath))
  
  @staticmethod
  def _load_layers(layer_filepaths):
    """Loads layers from the specified file paths into a new image. Returns the
    image and a dictionary of (layer name: Gimp.Layer instance) pairs.
    """
    image = utils_pdb.load_layers(
      layer_filepaths, image=None, strip_file_extension=True)
    return image, {layer.get_name(): layer for layer in image.get_layers()}
  
  @staticmethod
  def _list_layer_filepaths(layers_dirpath):
    layer_filepaths = []
    
    for filename in os.listdir(layers_dirpath):
      path = os.path.join(layers_dirpath, filename)
      if os.path.isfile(path):
        layer_filepaths.append(path)
    
    return layer_filepaths

  @staticmethod
  def _get_gimp_version_as_tuple():
    return Gimp.MAJOR_VERSION, Gimp.MINOR_VERSION, Gimp.MICRO_VERSION
