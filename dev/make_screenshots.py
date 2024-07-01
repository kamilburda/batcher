#!/usr/bin/env python3

"""Automatic taking and processing screenshots of the plug-in dialog for
documentation purposes.
"""

import os
import sys
import time

import gi
from gi.repository import GLib
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


ROOT_DIRPATH = os.path.abspath(
  os.path.dirname(os.path.dirname(pg.utils.get_current_module_filepath())))

PLUGIN_DIRPATH = os.path.join(ROOT_DIRPATH, 'batcher')

sys.path.append(PLUGIN_DIRPATH)


from batcher.src import plugin_settings
from batcher.src.gui import main as gui_main


TEST_IMAGES_DIRPATH = os.path.join(
  ROOT_DIRPATH, 'batcher', 'src', 'tests', 'tests_requiring_gimp', 'test_images')
TEST_IMAGES_FILEPATH = os.path.join(TEST_IMAGES_DIRPATH, 'test_export_layers_contents.xcf')

OUTPUT_DIRPATH = os.path.join(
  GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES), 'Loading Screens', 'Components')

SCREENSHOTS_DIRPATH = os.path.join(ROOT_DIRPATH, 'docs', 'images')
SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME = 'screenshot_dialog_export_layers.png'
SCREENSHOT_DIALOG_BROWSER_DIALOG_FILENAME = 'screenshot_procedure_browser_dialog.png'
SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME = 'screenshot_dialog_edit_layers.png'


def main(settings=None):
  if not settings:
    settings = plugin_settings.create_settings_for_export_layers()

  image = pdb.gimp_file_load(Gio.file_new_for_path(TEST_IMAGES_FILEPATH))

  layer_tree = pg.itemtree.LayerTree(image)

  gui_main.BatchLayerProcessingGui(layer_tree, settings, 'export', run_gui_func=take_screenshots)

  image.delete()


def take_screenshots(gui, dialog, settings):
  os.makedirs(OUTPUT_DIRPATH, exist_ok=True)
  
  settings['main/output_directory'].set_value(OUTPUT_DIRPATH)
  
  decoration_offsets = move_dialog_to_corner(dialog, settings['gui/size/dialog_position'])
  
  gui.name_preview.set_selected_items({gui.name_preview.batcher.item_tree['main-background'].raw})
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  dialog.set_focus(None)
  
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

  browser_decoration_offsets = move_dialog_to_corner(
    dialog, settings['gui/procedure_browser/dialog_position'])

  while Gtk.events_pending():
    Gtk.main_iteration()

  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_BROWSER_DIALOG_FILENAME,
    settings,
    browser_decoration_offsets,
    crop_to='browser_dialog',
  )

  gui.procedure_list.browser.widget.hide()

  # FIXME: Rework this to allow running an Edit Layers dialog
  settings['main/edit_mode'].set_value(True)

  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
  )
  
  Gtk.main_quit()
  

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
  else:
    crop_to_dialog(
      screenshot_image, settings['gui/size/dialog_size'], decoration_offsets)

  selected_layers = screenshot_image.list_selected_layers()
  layer_array = GObject.Value(Gimp.ObjectArray)
  Gimp.value_set_object_array(layer_array, Gimp.Layer, selected_layers)
  
  pdb.gimp_file_save(
    screenshot_image,
    len(selected_layers),
    layer_array.get_boxed(),
    Gio.file_new_for_path(os.path.join(screenshots_dirpath, filename)))
  
  screenshot_image.delete()


def take_screenshot():
  return pdb.plug_in_screenshot(1, 0, 0, 0, 0)


def move_dialog_to_corner(dialog, dialog_position_setting):
  dialog_position_setting.set_value((0, 0))
  dialog.set_gravity(Gdk.Gravity.STATIC)
  decoration_offset_x, decoration_offset_y = dialog.get_position()
  dialog.set_gravity(Gdk.Gravity.NORTH_WEST)
  dialog_position_setting.set_value((-decoration_offset_x, 0))
  
  return decoration_offset_x, decoration_offset_y


def crop_to_dialog(image, dialog_size_setting, decoration_offsets):
  dialog_size_setting.gui.update_setting_value()
  
  pdb.gimp_image_crop(
    image,
    dialog_size_setting.value[0],
    dialog_size_setting.value[1] + decoration_offsets[1],
    0,
    0)
  
  pdb.plug_in_autocrop(image, image.list_selected_layers()[0])
