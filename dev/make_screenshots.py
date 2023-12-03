#!/usr/bin/env python3

"""Automatic taking and processing screenshots of the plug-in dialog for
documentation purposes.
"""

import os
import time

import gi
from gi.repository import GLib
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from batcher import pygimplib as pg
from batcher.pygimplib import pdb

from batcher.src import actions
from batcher.src import builtin_constraints
from batcher.src import builtin_procedures
from batcher.src import settings_main
from batcher.src.gui import main as gui_main


PLUGINS_DIRPATH = os.path.abspath(
  os.path.dirname(os.path.dirname(pg.utils.get_current_module_filepath())))

TEST_IMAGES_DIRPATH = os.path.join(pg.config.PLUGIN_DIRPATH, 'tests', 'test_images')
TEST_IMAGES_FILEPATH = os.path.join(TEST_IMAGES_DIRPATH, 'test_export_layers_contents.xcf')

OUTPUT_DIRPATH = os.path.join(
  GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES), 'Loading Screens', 'Components')

SCREENSHOTS_DIRPATH = os.path.join(PLUGINS_DIRPATH, 'docs', 'images')
SCREENSHOT_DIALOG_BASIC_USAGE_FILENAME = 'screenshot_dialog_basic_usage.png'
SCREENSHOT_DIALOG_CUSTOMIZING_EXPORT_FILENAME = 'screenshot_dialog_customizing_export.png'
SCREENSHOT_DIALOG_BATCH_EDITING_FILENAME = 'screenshot_dialog_batch_editing.png'


def main(settings=None):
  if not settings:
    settings = settings_main.create_settings()

  image = pdb.gimp_file_load(TEST_IMAGES_FILEPATH, os.path.basename(TEST_IMAGES_FILEPATH))

  layer_tree = pg.itemtree.LayerTree(image, name=pg.config.SOURCE_NAME)

  settings['special/image'].set_value(image)

  gui_main.ExportLayersDialog(layer_tree, settings, run_gui_func=take_screenshots)

  pdb.gimp_image_delete(image)


def take_screenshots(gui, dialog, settings):
  os.makedirs(OUTPUT_DIRPATH, exist_ok=True)
  
  settings['gui/current_directory'].set_value(OUTPUT_DIRPATH)
  settings['gui/show_more_settings'].set_value(False)
  
  decoration_offsets = move_dialog_to_corner(dialog, settings)
  
  gui.name_preview.set_selected_items(
    {gui.name_preview.batcher.item_tree['main-background'].raw.get_id()})
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  dialog.set_focus(None)
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_BASIC_USAGE_FILENAME,
    settings,
    decoration_offsets,
    gui,
    blur_folders=True,
  )
  
  settings['gui/show_more_settings'].set_value(True)
  
  actions.clear(settings['main/procedures'])
  actions.clear(settings['main/constraints'])
  
  actions.add(
    settings['main/procedures'],
    builtin_procedures.BUILTIN_PROCEDURES['insert_background_layers'])
  actions.reorder(
    settings['main/procedures'], 'insert_background_layers', 0)
  settings['main/procedures/use_layer_size/enabled'].set_value(False)
  
  actions.add(
    settings['main/constraints'],
    builtin_constraints.BUILTIN_CONSTRAINTS['without_color_tags'])
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  gui.name_preview.set_selected_items(
    {gui.name_preview.batcher.item_tree['bottom-frame'].raw.get_id()})
  
  dialog.set_focus(None)
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_CUSTOMIZING_EXPORT_FILENAME,
    settings,
    decoration_offsets,
    gui,
    blur_folders=True,
  )
  
  settings['main/edit_mode'].set_value(True)
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_BATCH_EDITING_FILENAME,
    settings,
    decoration_offsets,
    gui,
  )
  
  Gtk.main_quit()
  

def take_and_process_screenshot(
      screenshots_dirpath, filename, settings, decoration_offsets, gui, blur_folders=False):
  #HACK: Wait a while until the window is fully shown.
  time.sleep(1)
  
  screenshot_image = take_screenshot()
  
  if blur_folders:
    blur_folder_chooser(screenshot_image, gui, decoration_offsets)
  
  crop_to_dialog(screenshot_image, settings, decoration_offsets)
  
  pdb.gimp_file_save(
    screenshot_image,
    screenshot_image.active_layer,
    os.path.join(screenshots_dirpath, filename),
    filename)
  
  pdb.gimp_image_delete(screenshot_image)


def blur_folder_chooser(image, gui, decoration_offsets):
  scrolled_window = (gui.folder_chooser
    .get_children()[0]
    .get_children()[0].get_children()[1]
    .get_children()[0].get_children()[0])
  folder_chooser_left_pane = scrolled_window.get_children()[0]
  
  selection_to_blur = folder_chooser_left_pane.get_allocation()
  selection_to_blur.y += decoration_offsets[1]
  
  pdb.gimp_image_select_rectangle(image, 0, *selection_to_blur)
  pdb.plug_in_gauss(image, image.active_layer, 25, 25, 0)
  pdb.gimp_selection_none(image)


def take_screenshot():
  return pdb.plug_in_screenshot(1, -1, 0, 0, 0, 0)


def move_dialog_to_corner(dialog, settings):
  settings['gui/size/dialog_position'].set_value((0, 0))
  dialog.set_gravity(Gdk.Gravity.STATIC)
  decoration_offset_x, decoration_offset_y = dialog.get_position()
  dialog.set_gravity(Gdk.Gravity.NORTH_WEST)
  settings['gui/size/dialog_position'].set_value((-decoration_offset_x, 0))
  
  return decoration_offset_x, decoration_offset_y


def crop_to_dialog(image, settings, decoration_offsets):
  settings['gui/size/dialog_size'].gui.update_setting_value()
  
  pdb.gimp_image_crop(
    image,
    settings['gui/size/dialog_size'].value[0],
    settings['gui/size/dialog_size'].value[1] + decoration_offsets[1],
    0,
    0)
  
  pdb.plug_in_autocrop(image, image.active_layer)
