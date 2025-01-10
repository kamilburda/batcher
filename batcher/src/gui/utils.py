import collections
import os
import re
import urllib.parse
import struct
import sys

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import core
from src import setting_classes
from src.gui import placeholders as gui_placeholders_

import pygimplib as pg


def attach_label_to_grid(
      grid,
      setting,
      row_index,
      column_index=0,
      width=1,
      height=1,
      width_chars=20,
      max_width_chars=40,
      set_name_as_tooltip=True,
):
  if isinstance(
        setting.gui, (pg.setting.CheckButtonPresenter, setting_classes.FileFormatOptionsPresenter)):
    return

  label = Gtk.Label(
    xalign=0.0,
    yalign=0.5,
    width_chars=width_chars,
    max_width_chars=max_width_chars,
    wrap=True,
  )
  label.show()

  if _has_setting_display_name(setting):
    label.set_text(setting.display_name)
    if set_name_as_tooltip:
      label.set_tooltip_text(setting.name)
  else:
    label.set_text(setting.name)

  grid.attach(label, column_index, row_index, width, height)


def attach_widget_to_grid(
      grid,
      setting,
      row_index,
      column_index=1,
      width=1,
      height=1,
      column_index_for_widget_without_label=0,
      width_for_widget_without_label=2,
      set_name_as_tooltip=True,
      width_chars_for_check_button_labels=25,
):
  widget_to_attach = setting.gui.widget

  if isinstance(setting.gui, pg.setting.SETTING_GUI_TYPES.null):
    widget_to_attach = gui_placeholders_.create_placeholder_widget()
  else:
    if (isinstance(setting, pg.setting.ArraySetting)
        and not setting.element_type.get_allowed_gui_types()):
      widget_to_attach = gui_placeholders_.create_placeholder_widget()

  widget_to_attach.set_hexpand(True)

  if not isinstance(
        setting.gui, (pg.setting.CheckButtonPresenter, setting_classes.FileFormatOptionsPresenter)):
    final_column_index = column_index
    final_width = width
  else:
    final_column_index = column_index_for_widget_without_label
    final_width = width_for_widget_without_label

    if set_name_as_tooltip and _has_setting_display_name(setting):
      widget_to_attach.set_tooltip_text(setting.name)

    if isinstance(setting.gui, pg.setting.CheckButtonPresenter):
      widget_to_attach.get_child().set_width_chars(width_chars_for_check_button_labels)

  grid.attach(widget_to_attach, final_column_index, row_index, final_width, height)


def _has_setting_display_name(setting):
  return setting.display_name is not None and setting.display_name.strip()


def image_file_tree_items_to_paths(item_tree: pg.itemtree.ItemTree):
  return [
    [item.id, item.parent.id] if item.parent is not None else [item.id, None]
    for item in item_tree.iter_all()]


def add_paths_to_image_file_tree(item_tree: pg.itemtree.ItemTree, filepaths_and_parent_folders):
  parent_items = collections.defaultdict(lambda: None)

  for filepath, parent_dirpath in filepaths_and_parent_folders:
    added_items = item_tree.add(
      [filepath], parent_item=parent_items[parent_dirpath], expand_folders=False)

    if added_items and added_items[0].type == pg.itemtree.TYPE_FOLDER:
      parent_items[filepath] = added_items[0]


def get_batcher_class(item_type):
  if item_type == 'image':
    return core.ImageBatcher
  elif item_type == 'layer':
    return core.LayerBatcher
  else:
    raise ValueError('item_type must be either "image" or "layer"')


def get_paths_from_clipboard(clipboard):
  text = clipboard.wait_for_text()
  if text is not None:
    return [path for path in text.splitlines() if os.path.exists(path)]

  selection_data = clipboard.wait_for_contents(Gdk.Atom.intern('CF_HDROP', False))
  returned_paths = _get_paths_from_windows_cf_hdrop(selection_data)
  if returned_paths is not None:
    return returned_paths

  selection_data = clipboard.wait_for_contents(Gdk.Atom.intern('text/uri-list', False))
  returned_paths = _get_paths_from_text_uri_list(selection_data)
  if returned_paths is not None:
    return returned_paths

  return []


def get_paths_from_drag_data(selection_data):
  if selection_data.get_target().name() == 'text/uri-list':
    returned_paths = _get_paths_from_text_uri_list(selection_data)
    if returned_paths is not None:
      return returned_paths

  if selection_data.get_target().name() == 'CF_HDROP':
    returned_paths = _get_paths_from_windows_cf_hdrop(selection_data)
    if returned_paths is not None:
      return returned_paths

  return []


def _get_paths_from_windows_cf_hdrop(selection_data):
  if selection_data is not None:
    # The code is based on: https://stackoverflow.com/a/77205658
    data = selection_data.get_data()
    if data:
      # https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/ns-shlobj_core-dropfiles
      windows_dropfiles_struct_for_cf_hdrop_format_size_bytes = 20
      offset, _x_coord, _y_coord, _is_nonclient, is_unicode = struct.unpack(
        'Illii', data[:windows_dropfiles_struct_for_cf_hdrop_format_size_bytes])
      decoded_data = data[offset:].decode('utf-16' if is_unicode else 'ansi')

      return [path for path in decoded_data.split('\0') if os.path.exists(path)]

  return None


def _get_paths_from_text_uri_list(selection_data):
  if selection_data is not None:
    # More info: https://www.iana.org/assignments/media-types/text/uri-list
    data = selection_data.get_data()
    if data:
      decoded_data = urllib.parse.unquote(data, encoding=sys.getfilesystemencoding())

      paths = []
      for raw_path in decoded_data.split('\r\n'):
        path = raw_path.replace('/0', '')
        path = re.sub(r'^file:/+', r'', path)

        if path:
          if os.name != 'nt':
            path = f'/{path}'

          if os.path.exists(path):
            paths.append(path)

      return paths

  return None
