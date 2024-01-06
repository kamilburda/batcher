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


from batcher.src import actions
from batcher.src import builtin_constraints
from batcher.src import builtin_procedures
from batcher.src import plugin_settings
from batcher.src.gui import main as gui_main


TEST_IMAGES_DIRPATH = os.path.join(
  ROOT_DIRPATH, 'batcher', 'src', 'tests', 'tests_requiring_gimp', 'test_images')
TEST_IMAGES_FILEPATH = os.path.join(TEST_IMAGES_DIRPATH, 'test_export_layers_contents.xcf')

OUTPUT_DIRPATH = os.path.join(
  GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES), 'Loading Screens', 'Components')

SCREENSHOTS_DIRPATH = os.path.join(ROOT_DIRPATH, 'docs', 'images')
SCREENSHOT_DIALOG_EXPORT_LAYERS_FILENAME = 'screenshot_dialog_export_layers.png'
SCREENSHOT_DIALOG_CUSTOMIZATION_FILENAME = 'screenshot_dialog_customization.png'
SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME = 'screenshot_dialog_edit_layers.png'


def main(settings=None):
  if not settings:
    settings = plugin_settings.create_settings()

  image = pdb.gimp_file_load(Gio.file_new_for_path(TEST_IMAGES_FILEPATH))

  layer_tree = pg.itemtree.LayerTree(image)

  settings['special/image'].set_value(image)

  gui_main.ExportLayersDialog(layer_tree, settings, run_gui_func=take_screenshots)

  image.delete()


def take_screenshots(gui, dialog, settings):
  os.makedirs(OUTPUT_DIRPATH, exist_ok=True)
  
  settings['main/output_directory'].set_value(OUTPUT_DIRPATH)
  settings['gui/show_more_settings'].set_value(False)
  
  decoration_offsets = move_dialog_to_corner(dialog, settings)
  
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
    gui,
    dialog,
    blur_folders=True,
  )
  
  settings['gui/show_more_settings'].set_value(True)
  
  actions.add(
    settings['main/procedures'],
    builtin_procedures.BUILTIN_PROCEDURES['insert_background'])
  actions.reorder(
    settings['main/procedures'], 'insert_background', 0)
  settings['main/procedures/use_layer_size/enabled'].set_value(False)
  
  actions.add(
    settings['main/constraints'],
    builtin_constraints.BUILTIN_CONSTRAINTS['without_color_tags'])
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  gui.name_preview.set_selected_items({gui.name_preview.batcher.item_tree['bottom-frame'].raw})
  
  dialog.set_focus(None)
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_CUSTOMIZATION_FILENAME,
    settings,
    decoration_offsets,
    gui,
    dialog,
    blur_folders=True,
  )
  
  settings['main/edit_mode'].set_value(True)
  
  while Gtk.events_pending():
    Gtk.main_iteration()
  
  take_and_process_screenshot(
    SCREENSHOTS_DIRPATH,
    SCREENSHOT_DIALOG_EDIT_LAYERS_FILENAME,
    settings,
    decoration_offsets,
    gui,
    dialog,
  )
  
  Gtk.main_quit()
  

def take_and_process_screenshot(
      screenshots_dirpath, filename, settings, decoration_offsets, gui, dialog, blur_folders=False):
  # HACK: Wait a while until the window is fully shown.
  time.sleep(1)
  
  screenshot_image = take_screenshot(dialog)
  
  if blur_folders:
    blur_folder_chooser(screenshot_image, gui, decoration_offsets)
  
  crop_to_dialog(screenshot_image, settings, decoration_offsets)

  selected_layers = screenshot_image.list_selected_layers()
  layer_array = GObject.Value(Gimp.ObjectArray)
  Gimp.value_set_object_array(layer_array, Gimp.Layer, selected_layers)
  
  pdb.gimp_file_save(
    screenshot_image,
    len(selected_layers),
    layer_array.get_boxed(),
    Gio.file_new_for_path(os.path.join(screenshots_dirpath, filename)))
  
  screenshot_image.delete()


def blur_folder_chooser(image, gui, decoration_offsets):
  folder_chooser_left_pane = (
    gui
    .folder_chooser
    .get_children()[0]
    .get_children()[0]
    .get_children()[0])

  toplevel_window = gui.folder_chooser.get_toplevel()

  widget_coordinates = folder_chooser_left_pane.translate_coordinates(toplevel_window, 0, 0)

  selection_to_blur = folder_chooser_left_pane.get_allocation()
  selection_to_blur.x += widget_coordinates[0]
  selection_to_blur.y += widget_coordinates[1] + decoration_offsets[1]

  image.select_rectangle(
    0, selection_to_blur.x, selection_to_blur.y, selection_to_blur.width, selection_to_blur.height)
  pdb.plug_in_gauss(image, image.list_selected_layers()[0], 25, 25, 0)
  pdb.gimp_selection_none(image)


def take_screenshot(dialog):
  return pdb.plug_in_screenshot(1, 0, 0, 0, 0)


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
  
  pdb.plug_in_autocrop(image, image.list_selected_layers()[0])
