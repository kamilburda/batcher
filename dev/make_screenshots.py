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
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import batcher.pygimplib as pg
from batcher.pygimplib import pdb

from batcher.src.setting_source_names import *


ROOT_DIRPATH = os.path.abspath(
  os.path.dirname(os.path.dirname(pg.utils.get_current_module_filepath())))

PLUGIN_DIRPATH = os.path.join(ROOT_DIRPATH, 'batcher')

sys.path.append(PLUGIN_DIRPATH)


from batcher.src import plugin_settings
from batcher.src.gui import main as gui_main


TEST_IMAGES_DIRPATH = os.path.join(
  ROOT_DIRPATH, 'batcher', 'src', 'tests', 'tests_requiring_gimp', 'test_images')
TEST_IMAGES_FILEPATH = os.path.join(TEST_IMAGES_DIRPATH, 'test_export_layers_contents.xcf')

OUTPUT_DIRPATH = os.path.join(pg.utils.get_pictures_directory(), 'Loading Screens', 'Components')

SCREENSHOTS_DIRPATH = os.path.join(ROOT_DIRPATH, 'docs', 'images')
SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME = 'screenshot_dialog_export_layers.png'
SCREENSHOT_DIALOG_EXPORT_LAYERS_QUICK_FILENAME = 'screenshot_dialog_export_layers_quick.png'
SCREENSHOT_DIALOG_BROWSER_DIALOG_FILENAME = 'screenshot_procedure_browser_dialog.png'
SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME = 'screenshot_dialog_edit_layers.png'


def main():
  image = pdb.gimp_file_load(Gio.file_new_for_path(TEST_IMAGES_FILEPATH))

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  gui_main.BatchLayerProcessingGui(
    layer_tree,
    plugin_settings.create_settings_for_export_layers(),
    EXPORT_LAYERS_SOURCE_NAME,
    'export',
    run_gui_func=take_screenshots_for_export_layers,
  )

  gui_main.BatchLayerProcessingGui(
    layer_tree,
    plugin_settings.create_settings_for_edit_layers(),
    EDIT_LAYERS_SOURCE_NAME,
    'edit',
    run_gui_func=take_screenshots_for_edit_layers,
  )

  gui_main.BatchLayerProcessingQuickGui(
    layer_tree,
    plugin_settings.create_settings_for_export_layers(),
    EXPORT_LAYERS_SOURCE_NAME,
    'export',
    title='Export Layers (Quick)',
    run_gui_func=take_screenshots_for_export_layers_quick,
  )

  for _i in range(Gtk.main_level()):
    Gtk.main_quit()

  image.delete()


def take_screenshots_for_export_layers(gui, dialog, settings):
  os.makedirs(OUTPUT_DIRPATH, exist_ok=True)
  
  settings['main/output_directory'].set_value(OUTPUT_DIRPATH)
  
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  # HACK: Wait until the preview is updated.
  time.sleep(0.1)

  while Gtk.events_pending():
    Gtk.main_iteration()

  dialog.set_focus(None)

  main_background_layer = next(
    iter(
      layer for layer in gui.name_preview.batcher.item_tree.image.get_layers()
      if layer.get_name() == 'main-background'))

  gui.name_preview.set_selected_items({main_background_layer.get_id()})

  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
  )

  gui.procedure_list.browser.fill_contents_if_empty()
  gui.procedure_list.browser.widget.show_all()

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


def take_screenshots_for_edit_layers(gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])

  # HACK: Wait until the preview is updated.
  time.sleep(0.1)

  while Gtk.events_pending():
    Gtk.main_iteration()

  dialog.set_focus(None)

  main_background_layer = next(
    iter(
      layer for layer in gui.name_preview.batcher.item_tree.image.get_layers()
      if layer.get_name() == 'main-background'))

  gui.name_preview.set_selected_items({main_background_layer.get_id()})

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
  )


def take_screenshots_for_export_layers_quick(_gui, dialog, settings):
  decoration_offsets = move_dialog_to_corner(dialog)

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EXPORT_LAYERS_QUICK_FILENAME,
    settings,
    decoration_offsets,
    crop_to=dialog.get_size(),
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

  selected_layers = screenshot_image.get_selected_layers()

  pdb.gimp_file_save(
    screenshot_image,
    len(selected_layers),
    selected_layers,
    Gio.file_new_for_path(os.path.join(screenshots_dirpath, filename)))
  
  screenshot_image.delete()


def take_screenshot():
  return pdb.plug_in_screenshot(1, 0, 0, 0, 0)


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
  
  pdb.gimp_image_crop(
    image,
    width,
    height + decoration_offsets[1],
    0,
    0)
  
  pdb.plug_in_autocrop(image, image.get_selected_layers()[0])
