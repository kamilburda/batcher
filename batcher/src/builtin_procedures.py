"""Built-in plug-in procedures."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib

from src import background_foreground
from src import export as export_
from src import renamer as renamer_

import pygimplib as pg


NAME_ONLY_TAG = 'name'


def set_selected_and_current_layer(batcher):
  # If an image has no layers, there is nothing we do here. An exception may
  # be raised if a procedure requires at least one layer. An empty image
  # could occur e.g. if all layers were removed by the previous procedures.

  if batcher.current_raw_item.is_valid():
    batcher.current_image.set_selected_layers([batcher.current_raw_item])
  else:
    selected_layers = batcher.current_image.list_selected_layers()

    if selected_layers:
      # There is no way to know which layer is the "right" one, so we resort to
      # taking the first.
      selected_layer = selected_layers[0]

      if selected_layer.is_valid():
        # The selected layer(s) may have been set by the procedure.
        batcher.current_raw_item = selected_layer
      else:
        current_image_layers = batcher.current_image.list_layers()
        if current_image_layers:
          # There is no way to know which layer is the "right" one, so we resort
          # to taking the first.
          batcher.current_raw_item = current_image_layers[0]
          batcher.current_image.set_selected_layers([current_image_layers[0]])


def set_selected_and_current_layer_after_action(batcher):
  action_applied = yield
  
  if action_applied or action_applied is None:
    set_selected_and_current_layer(batcher)


def sync_item_name_and_raw_item_name(batcher):
  yield
  
  if batcher.process_names and not batcher.is_preview:
    batcher.current_item.name = batcher.current_raw_item.get_name()


def preserve_locks_between_actions(batcher):
  # We assume `edit_mode` is `True`, we can therefore safely use `Item.raw`
  # instead of `current_raw_item`. We need to use `Item.raw` for parents as
  # well.
  item = batcher.current_item
  locks_content = {}
  locks_visibility = {}

  for item_or_parent in [item] + item.parents:
    if item_or_parent.raw.is_valid():
      locks_content[item_or_parent] = item_or_parent.raw.get_lock_content()
      locks_visibility[item_or_parent] = item_or_parent.raw.get_lock_visibility()

  if item.raw.is_valid():
    lock_position = item.raw.get_lock_position()
    lock_alpha = item.raw.get_lock_alpha()
  else:
    lock_position = None
    lock_alpha = None

  for item_or_parent, lock_content in locks_content.items():
    if lock_content:
      item_or_parent.raw.set_lock_content(False)

  for item_or_parent, lock_visibility in locks_visibility.items():
    if lock_visibility:
      item_or_parent.raw.set_lock_visibility(False)

  if lock_position:
    item.raw.set_lock_position(False)
  if lock_alpha:
    item.raw.set_lock_alpha(False)

  yield

  for item_or_parent, lock_content in locks_content.items():
    if lock_content and item_or_parent.raw.is_valid():
      item_or_parent.raw.set_lock_content(lock_content)

  for item_or_parent, lock_visibility in locks_visibility.items():
    if lock_visibility and item_or_parent.raw.is_valid():
      item_or_parent.raw.set_lock_visibility(lock_visibility)

  if item.raw.is_valid():
    if lock_position:
      item.raw.set_lock_position(lock_position)
    if lock_alpha:
      item.raw.set_lock_alpha(lock_alpha)


def remove_folder_hierarchy_from_item(batcher):
  item = batcher.current_item

  item.parents = []
  item.children = []


def apply_transparency_from_layer_groups(batcher):
  new_layer_opacity = batcher.current_raw_item.get_opacity() / 100.0
  for parent in batcher.current_item.parents:
    new_layer_opacity = new_layer_opacity * (parent.raw.get_opacity() / 100.0)
  
  batcher.current_raw_item.set_opacity(new_layer_opacity * 100.0)


def rename_layer(batcher, pattern, rename_layers=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern)
  renamed_parents = set()
  
  while True:
    if rename_layers:
      batcher.current_item.name = renamer.rename(batcher)
    
    if rename_folders:
      for parent in batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(batcher, item=parent)
          renamed_parents.add(parent)
    
    if batcher.process_names and not batcher.is_preview:
      batcher.current_raw_item.set_name(batcher.current_item.name)
    
    yield


def resize_to_layer_size(batcher):
  image = batcher.current_image
  layer = batcher.current_raw_item
  
  layer_offset_x, layer_offset_y = layer.get_offsets()[1:]
  image.resize(layer.get_width(), layer.get_height(), -layer_offset_x, -layer_offset_y)


_BUILTIN_PROCEDURES_LIST = [
  {
    'name': 'apply_transparency_from_layer_groups',
    'function': apply_transparency_from_layer_groups,
    'display_name': _('Apply transparency from layer groups'),
  },
  {
    'name': 'insert_background',
    'function': background_foreground.insert_background_layer,
    'display_name': _('Insert background'),
    'menu_path': _('Background, foreground'),
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'color_tag',
        'name': 'color_tag',
        'display_name': _('Color tag'),
        'default_value': Gimp.ColorTag.BLUE,
      },
    ],
  },
  {
    'name': 'insert_foreground',
    'function': background_foreground.insert_foreground_layer,
    'display_name': _('Insert foreground'),
    'menu_path': _('Background, foreground'),
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'color_tag',
        'name': 'color_tag',
        'display_name': _('Color tag'),
        'default_value': Gimp.ColorTag.GREEN,
      },
    ],
  },
  {
    'name': 'merge_background',
    'function': background_foreground.merge_background,
    'display_name': _('Merge background'),
    'menu_path': _('Background, foreground'),
    'arguments': [
      {
        'type': 'enum',
        'name': 'merge_type',
        'enum_type': Gimp.MergeType,
        'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
        'display_name': _('Merge type'),
      },
    ],
  },
  {
    'name': 'merge_foreground',
    'function': background_foreground.merge_foreground,
    'display_name': _('Merge foreground'),
    'menu_path': _('Background, foreground'),
    'arguments': [
      {
        'type': 'enum',
        'name': 'merge_type',
        'enum_type': Gimp.MergeType,
        'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
        'display_name': _('Merge type'),
      },
    ],
  },
  {
    'name': 'export',
    'function': export_.export,
    'display_name': _('Export'),
    'additional_tags': [NAME_ONLY_TAG],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'dirpath',
        'name': 'output_directory',
        'default_value': GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
        'display_name': _('Output folder'),
        'gui_type': 'folder_chooser_button',
      },
      {
        'type': 'file_extension',
        'name': 'file_extension',
        'default_value': 'png',
        'display_name': _('File extension'),
        'gui_type': 'file_extension_entry',
        'adjust_value': True,
      },
      {
        'type': 'choice',
        'name': 'export_mode',
        'default_value': 'each_layer',
        'items': [
          ('each_layer', _('For each layer'), export_.ExportModes.EACH_LAYER),
          ('each_top_level_layer_or_group',
           _('For each top-level layer or group'),
           export_.ExportModes.EACH_TOP_LEVEL_LAYER_OR_GROUP),
          ('entire_image_at_once',
           _('For the entire image at once'),
           export_.ExportModes.ENTIRE_IMAGE_AT_ONCE),
        ],
        'display_name': _('Perform export:'),
      },
      {
        'type': 'filename_pattern',
        'name': 'single_image_filename_pattern',
        'default_value': '[image name]',
        'display_name': _('Image filename pattern'),
        'gui_type': 'filename_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'use_file_extension_in_item_name',
        'default_value': False,
        'display_name': _('Use file extension in layer name'),
        'gui_type': 'check_button_no_text',
      },
      {
        'type': 'bool',
        'name': 'convert_file_extension_to_lowercase',
        'default_value': False,
        'display_name': _('Convert file extension to lowercase'),
        'gui_type': 'check_button_no_text',
      },
      {
        'type': 'bool',
        'name': 'preserve_layer_name_after_export',
        'default_value': False,
        'display_name': _('Preserve layer name after export'),
        'gui_type': 'check_button_no_text',
      },
    ],
  },
  {
    'name': 'remove_folder_structure',
    'function': remove_folder_hierarchy_from_item,
    'display_name': _('Remove folder structure'),
    'additional_tags': [NAME_ONLY_TAG],
  },
  {
    'name': 'rename',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [NAME_ONLY_TAG],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'filename_pattern',
        'name': 'pattern',
        'default_value': '[layer name]',
        'display_name': _('Layer filename pattern'),
        'gui_type': 'filename_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'rename_layers',
        'default_value': True,
        'display_name': _('Rename layers'),
        'gui_type': 'check_button_no_text',
      },
      {
        'type': 'bool',
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename folders'),
        'gui_type': 'check_button_no_text',
      },
    ],
  },
  {
    'name': 'use_layer_size',
    'function': resize_to_layer_size,
    'display_name': _('Use layer size'),
  },
]

# Create a separate dictionary for functions since objects cannot be saved
# to a persistent source. Saving them as strings would not be reliable as
# function names and paths may change when refactoring or adding/modifying features.
# The 'function' setting is set to an empty value as the function can be inferred
# via the action's 'orig_name' setting.
BUILTIN_PROCEDURES = {}
BUILTIN_PROCEDURES_FUNCTIONS = {}

for action_dict in _BUILTIN_PROCEDURES_LIST:
  function = action_dict['function']
  action_dict['function'] = ''
  
  BUILTIN_PROCEDURES[action_dict['name']] = action_dict
  BUILTIN_PROCEDURES_FUNCTIONS[action_dict['name']] = function
