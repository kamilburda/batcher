#!/usr/bin/env python3

"""Automatic taking and processing screenshots of the plug-in dialog for
documentation purposes.
"""

import os
import sys
import time

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg
from pygimplib import pdb

from src import utils as utils_
from src.procedure_groups import *


ROOT_DIRPATH = os.path.abspath(
  os.path.dirname(os.path.dirname(pg.utils.get_current_module_filepath())))

PLUGIN_DIRPATH = os.path.join(ROOT_DIRPATH, 'batcher')

sys.path.append(PLUGIN_DIRPATH)


from src import plugin_settings
from src.gui import main as gui_main


TEST_IMAGES_DIRPATH = os.path.join(
  ROOT_DIRPATH, 'batcher', 'src', 'tests', 'tests_requiring_gimp', 'test_images')
TEST_IMAGE_FOR_LAYERS_FILEPATH = os.path.join(TEST_IMAGES_DIRPATH, 'test_contents.xcf')

OUTPUT_DIRPATH = os.path.join(pg.utils.get_default_dirpath(), 'Loading Screens', 'Components')

SCREENSHOTS_DIRPATH = os.path.join(ROOT_DIRPATH, 'docs', 'images')
SCREENSHOT_DIALOG_CONVERT_FILENAME = 'screenshot_dialog_convert.png'
SCREENSHOT_DIALOG_EXPORT_IMAGES_FILENAME = 'screenshot_dialog_export_images.png'
SCREENSHOT_DIALOG_EXPORT_IMAGES_QUICK_FILENAME = 'screenshot_dialog_export_images_quick.png'
SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME = 'screenshot_dialog_export_layers.png'
SCREENSHOT_DIALOG_EXPORT_LAYERS_QUICK_FILENAME = 'screenshot_dialog_export_layers_quick.png'
SCREENSHOT_DIALOG_BROWSER_DIALOG_FILENAME = 'screenshot_procedure_browser_dialog.png'
SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME = 'screenshot_dialog_edit_layers.png'

_WAIT_TIME_FOR_PREVIEW_SECONDS = 0.2


def main():
  os.makedirs(OUTPUT_DIRPATH, exist_ok=True)

  input_files_dirpath = os.path.join(TEST_IMAGES_DIRPATH, 'convert_inputs')

  image_file_tree = pg.itemtree.ImageFileTree()
  image_file_tree.add([
    os.path.join(input_files_dirpath, filename)
    for filename in os.listdir(input_files_dirpath)])

  pg.config.PROCEDURE_GROUP = CONVERT_GROUP

  convert_settings = plugin_settings.create_settings_for_convert()
  convert_settings['gui/inputs_interactive'].set_value(
    utils_.item_tree_items_to_objects(image_file_tree))

  gui_main.BatchProcessingGui(
    image_file_tree,
    convert_settings,
    'export',
    'image',
    title='Batch Convert',
    run_gui_func=take_screenshots_for_convert,
  )

  pg.config.PROCEDURE_GROUP = EXPORT_IMAGES_GROUP

  image_filepaths = [
    os.path.join(root_dirpath, filename)
    for root_dirpath, dirnames_, filenames in os.walk(input_files_dirpath)
    for filename in filenames
    if os.path.isfile(os.path.join(root_dirpath, filename))
  ]
  existing_images = Gimp.get_images()
  images = [
    pdb.gimp_file_load(file=Gio.file_new_for_path(filepath))
    for filepath in image_filepaths]

  gimp_image_tree = pg.itemtree.GimpImageTree()
  gimp_image_tree.add_opened_images()
  gimp_image_tree.remove([gimp_image_tree[image.get_id()] for image in existing_images])

  gui_main.BatchProcessingGui(
    gimp_image_tree,
    plugin_settings.create_settings_for_export_images(),
    'export',
    'image',
    title='Export Images',
    run_gui_func=take_screenshots_for_export_images,
  )

  gui_main.BatchProcessingQuickGui(
    gimp_image_tree,
    plugin_settings.create_settings_for_export_images(),
    'export',
    'image',
    title='Export Images (Quick)',
    run_gui_func=take_screenshots_for_export_images_quick,
  )

  for image in images:
    image.delete()

  pg.config.PROCEDURE_GROUP = EXPORT_LAYERS_GROUP

  image = pdb.gimp_file_load(file=Gio.file_new_for_path(TEST_IMAGE_FOR_LAYERS_FILEPATH))

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  gui_main.BatchProcessingGui(
    layer_tree,
    plugin_settings.create_settings_for_export_layers(),
    'export',
    'layer',
    title='Export Layers',
    run_gui_func=take_screenshots_for_export_layers,
  )

  gui_main.BatchProcessingQuickGui(
    layer_tree,
    plugin_settings.create_settings_for_export_layers(),
    'export',
    'layer',
    title='Export Layers (Quick)',
    run_gui_func=take_screenshots_for_export_layers_quick,
  )

  pg.config.PROCEDURE_GROUP = EDIT_LAYERS_GROUP

  gui_main.BatchProcessingGui(
    layer_tree,
    plugin_settings.create_settings_for_edit_layers(),
    'edit',
    'layer',
    title='Edit Layers',
    run_gui_func=take_screenshots_for_edit_layers,
  )

  for _i in range(Gtk.main_level()):
    Gtk.main_quit()

  image.delete()


def take_screenshots_for_convert(gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  settings['main/output_directory'].set_value(Gio.file_new_for_path(OUTPUT_DIRPATH))

  _wait_until_preview_is_updated(n_repetitions=2)

  dialog.set_focus(None)

  selected_item = next(
    iter(
      item for item in gui.name_preview.batcher.item_tree.iter(filtered=False)
      if item.id.endswith('main-background.xcf')))

  gui.name_preview.set_selected_items([selected_item.key])

  _wait_until_preview_is_updated()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_CONVERT_FILENAME,
    settings,
    decoration_offsets,
  )


def take_screenshots_for_export_images(gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  _wait_until_preview_is_updated(n_repetitions=2)

  settings['main/output_directory'].set_value(Gio.file_new_for_path(OUTPUT_DIRPATH))

  dialog.set_focus(None)

  selected_item = next(
    iter(
      item.raw for item in gui.name_preview.batcher.item_tree
      if item.raw.get_name().startswith('main-background')))

  gui.name_preview.set_selected_items([selected_item.get_id()])

  _wait_until_preview_is_updated()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_IMAGES_FILENAME,
    settings,
    decoration_offsets,
  )


def take_screenshots_for_export_images_quick(_gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog)

  while Gtk.events_pending():
    Gtk.main_iteration()

  settings['main/output_directory'].set_value(Gio.file_new_for_path(OUTPUT_DIRPATH))

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_IMAGES_QUICK_FILENAME,
    settings,
    decoration_offsets,
    crop_to=dialog.get_size(),
  )


def take_screenshots_for_export_layers(gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  _wait_until_preview_is_updated(n_repetitions=2)

  settings['main/output_directory'].set_value(Gio.file_new_for_path(OUTPUT_DIRPATH))

  dialog.set_focus(None)

  selected_item = next(
    iter(
      item.raw for item in gui.name_preview.batcher.item_tree
      if item.raw.get_name() == 'main-background'))

  gui.name_preview.set_selected_items([selected_item.get_id()])

  _wait_until_preview_is_updated()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
  )

  gui.procedure_list.browser.fill_contents_if_empty()
  gui.procedure_list.browser.widget.show_all()
  gui.procedure_list.browser.select_action('gegl:gaussian-blur')

  while Gtk.events_pending():
    Gtk.main_iteration()

  gui.procedure_list.browser.widget.set_focus(None)

  move_dialog_to_corner(
    dialog, settings['gui/procedure_browser/dialog_position'], *decoration_offsets)

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_BROWSER_DIALOG_FILENAME,
    settings,
    decoration_offsets,
    crop_to='browser_dialog',
  )

  gui.procedure_list.browser.widget.hide()


def take_screenshots_for_export_layers_quick(_gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog)

  while Gtk.events_pending():
    Gtk.main_iteration()

  settings['main/output_directory'].set_value(Gio.file_new_for_path(OUTPUT_DIRPATH))

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_LAYERS_QUICK_FILENAME,
    settings,
    decoration_offsets,
    crop_to=dialog.get_size(),
  )


def take_screenshots_for_edit_layers(gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  _wait_until_preview_is_updated(n_repetitions=2)

  dialog.set_focus(None)

  selected_item = next(
    iter(
      item.raw for item in gui.name_preview.batcher.item_tree
      if item.raw.get_name() == 'main-background'))

  gui.name_preview.set_selected_items([selected_item.get_id()])

  _wait_until_preview_is_updated()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
  )


def take_and_process_screenshot(
      screenshots_dirpath,
      filename,
      settings,
      decoration_offsets,
      crop_to='main_dialog',
):
  # HACK: Wait a while until the window is fully shown.
  time.sleep(1)
  
  screenshot_image = take_screenshot()

  if crop_to == 'browser_dialog':
    crop_to_dialog(
      screenshot_image, settings['gui/procedure_browser/dialog_size'], decoration_offsets)
  elif crop_to == 'main_dialog':
    crop_to_dialog(
      screenshot_image, settings['gui/size/dialog_size'], decoration_offsets)
  else:
    crop_to_dialog(screenshot_image, crop_to, decoration_offsets)

  pdb.gimp_file_save(
    run_mode=Gimp.RunMode.NONINTERACTIVE,
    image=screenshot_image,
    file=Gio.file_new_for_path(os.path.join(screenshots_dirpath, filename)),
    options=None,
  )
  
  screenshot_image.delete()


def take_screenshot():
  return pdb.plug_in_screenshot(
    shoot_type='screen',
    x1=0,
    y1=0,
    x2=0,
    y2=0,
    include_pointer=False,
  )


def move_dialog_to_corner(
      dialog, dialog_position_setting=None, decoration_offset_x=None, decoration_offset_y=None):
  if decoration_offset_x is None:
    if dialog_position_setting is not None:
      dialog_position_setting.set_value((0, 0))
    else:
      dialog.move(0, 0)

    dialog.set_gravity(Gdk.Gravity.STATIC)
    decoration_offset_x, decoration_offset_y = dialog.get_position()

  dialog.set_gravity(Gdk.Gravity.NORTH_WEST)
  if dialog_position_setting is not None:
    dialog_position_setting.set_value((-decoration_offset_x, 0))
  else:
    dialog.move(-decoration_offset_x, 0)

  return decoration_offset_x, decoration_offset_y


def crop_to_dialog(image, size_setting_or_tuple, decoration_offsets):
  if isinstance(size_setting_or_tuple, tuple):
    width, height = size_setting_or_tuple
  else:
    size_setting_or_tuple.gui.update_setting_value()
    width = size_setting_or_tuple.value[0]
    height = size_setting_or_tuple.value[1]
  
  image.crop(width, height + decoration_offsets[1], 0, 0)
  
  image.autocrop(image.get_selected_layers()[0])


def _wait_until_preview_is_updated(n_repetitions=1):
  for unused_ in range(n_repetitions):
    # Wait until the preview is updated.
    time.sleep(_WAIT_TIME_FOR_PREVIEW_SECONDS)

    while Gtk.events_pending():
      Gtk.main_iteration()
