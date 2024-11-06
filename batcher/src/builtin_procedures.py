"""Built-in plug-in procedures."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import background_foreground
from src import export as export_
from src import overwrite
from src import renamer as renamer_
from src import utils
from src.builtin_actions_common import *


def set_selected_and_current_layer(batcher):
  # If an image has no layers, there is nothing we do here. An exception may
  # be raised if a procedure requires at least one layer. An empty image
  # could occur e.g. if all layers were removed by the previous procedures.

  if batcher.current_raw_item.is_valid():
    batcher.current_image.set_selected_layers([batcher.current_raw_item])
  else:
    selected_layers = batcher.current_image.get_selected_layers()

    if selected_layers:
      # There is no way to know which layer is the "right" one, so we resort to
      # taking the first.
      selected_layer = selected_layers[0]

      if selected_layer.is_valid():
        # The selected layer(s) may have been set by the procedure.
        batcher.current_raw_item = selected_layer
      else:
        current_image_layers = batcher.current_image.get_layers()
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


def remove_folder_structure_from_item_for_export_layers(batcher):
  item = batcher.current_item

  item.parents = []
  item.children = []


def remove_folder_structure_from_item_for_edit_layers(batcher, consider_parent_visible=False):
  item = batcher.current_item

  if batcher.edit_mode and not batcher.is_preview:
    image = item.raw.get_image()
    raw_immediate_parent = item.parent.raw if item.parents else None

    if raw_immediate_parent is not None:
      raw_top_level_parent = item.parents[0].raw if item.parents else None
      image.reorder_item(item.raw, None, image.get_item_position(raw_top_level_parent))

      if not raw_immediate_parent.get_children():
        image.remove_layer(raw_immediate_parent)

      if consider_parent_visible and item.parents:
        item.raw.set_visible(all(parent.raw.get_visible() for parent in item.parents))

  item.parents = []
  item.children = []


def apply_opacity_from_group_layers(batcher):
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

      if batcher.process_names and not batcher.is_preview:
        batcher.current_raw_item.set_name(batcher.current_item.name)
    
    if rename_folders:
      for parent in batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(batcher, item=parent)
          renamed_parents.add(parent)

          if batcher.edit_mode and batcher.process_names and not batcher.is_preview:
            parent.raw.set_name(parent.name)
    
    yield


def resize_to_layer_size(batcher):
  image = batcher.current_image
  layer = batcher.current_raw_item
  
  layer_offset_x, layer_offset_y = layer.get_offsets()[1:]
  image.resize(layer.get_width(), layer.get_height(), -layer_offset_x, -layer_offset_y)


def scale(
      _batcher,
      image,
      raw_item,
      new_width,
      width_unit,
      new_height,
      height_unit,
      interpolation,
      local_origin,
):
  width_pixels = _convert_to_pixels(image, raw_item, new_width, width_unit)
  height_pixels = _convert_to_pixels(image, raw_item, new_height, height_unit)

  Gimp.context_push()
  Gimp.context_set_interpolation(interpolation)

  raw_item.scale(width_pixels, height_pixels, local_origin)

  Gimp.context_pop()


def _convert_to_pixels(image, raw_item, dimension, dimension_unit):
  if dimension_unit == PERCENT_IMAGE_WIDTH:
    pixels = (dimension / 100) * image.get_width()
  elif dimension_unit == PERCENT_IMAGE_HEIGHT:
    pixels = (dimension / 100) * image.get_height()
  elif dimension_unit == PERCENT_LAYER_WIDTH:
    pixels = (dimension / 100) * raw_item.get_width()
  elif dimension_unit == PERCENT_LAYER_HEIGHT:
    pixels = (dimension / 100) * raw_item.get_height()
  else:
    pixels = dimension

  int_pixels = int(pixels)

  if int_pixels <= 0:
    int_pixels = 1

  return int_pixels


_SCALE_OBJECT_TYPES = IMAGE, LAYER = (0, 1)

_SCALE_UNITS = (
  PERCENT_LAYER_WIDTH,
  PERCENT_LAYER_HEIGHT,
  PERCENT_IMAGE_WIDTH,
  PERCENT_IMAGE_HEIGHT,
  PIXELS,
) = (0, 1, 2, 3, 4)


INTERACTIVE_OVERWRITE_MODES_LIST = [
  ('replace', _('Replace'), overwrite.OverwriteModes.REPLACE),
  ('skip', _('Skip'), overwrite.OverwriteModes.SKIP),
  ('rename_new', _('Rename new file'), overwrite.OverwriteModes.RENAME_NEW),
  ('rename_existing', _('Rename existing file'), overwrite.OverwriteModes.RENAME_EXISTING)
]


INTERACTIVE_OVERWRITE_MODES = {
  item[0]: item[1:] for item in INTERACTIVE_OVERWRITE_MODES_LIST
}


_EXPORT_OVERWRITE_MODES_LIST = [
  ('ask', _('Ask'), overwrite.OverwriteModes.ASK),
  *INTERACTIVE_OVERWRITE_MODES_LIST
]


_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS = {
  'name': 'export_for_export_layers',
  'function': export_.export,
  'display_name': _('Also export as...'),
  'description': _('Exports a layer to another file format.'),
  'additional_tags': [NAME_ONLY_TAG, EXPORT_LAYERS_TAG],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'dirpath',
      'name': 'output_directory',
      'default_value': pg.utils.get_pictures_directory(),
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
      'auto_update_gui_to_setting': False,
    },
    {
      'type': 'choice',
      'name': 'file_format_mode',
      'default_value': 'use_explicit_values',
      'items': [
        ('use_native_plugin_values',
         _('Interactively'),
         export_.FileFormatModes.USE_NATIVE_PLUGIN_VALUES),
        ('use_explicit_values',
         _('Use options below'),
         export_.FileFormatModes.USE_EXPLICIT_VALUES)],
      'display_name': _('How to adjust file format options:'),
      'description': _(
        'Native dialogs usually allow you to adjust more options such as image metadata,'
        ' while adjusting options in place is more convenient as no extra dialog is displayed'
        ' before the export.'),
      'gui_type': 'radio_button_box',
    },
    {
      'type': 'file_format_options',
      'name': 'file_format_export_options',
      'import_or_export': 'export',
      'initial_file_format': 'png',
      'gui_type': 'file_format_options',
      'display_name': _('File format options')
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'ask',
      'items': _EXPORT_OVERWRITE_MODES_LIST,
      'display_name': _('If a file already exists:'),
    },
    {
      'type': 'choice',
      'name': 'export_mode',
      'default_value': 'each_layer',
      'items': [
        ('each_layer', _('For each layer'), export_.ExportModes.EACH_LAYER),
        ('each_top_level_layer_or_group',
         _('For each top-level layer or group'),
         export_.ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER),
        ('entire_image_at_once',
         _('For the entire image at once'),
         export_.ExportModes.ENTIRE_IMAGE_AT_ONCE),
      ],
      'display_name': _('Perform export:'),
    },
    {
      'type': 'name_pattern',
      'name': 'single_image_name_pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'use_file_extension_in_item_name',
      'default_value': False,
      'display_name': _('Use file extension in layer name'),
      'gui_type': 'check_button',
    },
    {
      'type': 'bool',
      'name': 'convert_file_extension_to_lowercase',
      'default_value': False,
      'display_name': _('Convert file extension to lowercase'),
      'gui_type': 'check_button',
    },
  ],
}


_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS = utils.semi_deep_copy(
  _EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS)

_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS.update({
  'name': 'export_for_edit_layers',
  'display_name': _('Export'),
  'description': _('Exports a layer to the specified file format.'),
  'additional_tags': [NAME_ONLY_TAG, EDIT_LAYERS_TAG],
})


_BUILTIN_PROCEDURES_LIST = [
  {
    'name': 'apply_opacity_from_group_layers',
    'function': apply_opacity_from_group_layers,
    'display_name': _('Apply opacity from group layers'),
    'description': _('Combines opacity from all parent group layers and the current layer.'),
    'additional_tags': [EDIT_LAYERS_TAG, EXPORT_LAYERS_TAG],
  },
  {
    'name': 'insert_background',
    'function': background_foreground.insert_background_layer,
    'display_name': _('Insert background'),
    'description': _('Inserts layers having the specified color tag behind the current layer.'),
    'display_options_on_create': True,
    'additional_tags': [EDIT_LAYERS_TAG, EXPORT_LAYERS_TAG],
    'arguments': [
      {
        'type': 'enum',
        'name': 'color_tag',
        'enum_type': Gimp.ColorTag,
        'excluded_values': [Gimp.ColorTag.NONE],
        'display_name': _('Color tag'),
        'default_value': Gimp.ColorTag.BLUE,
      },
      {
        'type': 'string',
        'name': 'merge_procedure_name',
        'default_value': '',
        'gui_type': None,
      },
      {
        'type': 'string',
        'name': 'constraint_name',
        'default_value': '',
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'insert_foreground',
    'function': background_foreground.insert_foreground_layer,
    'display_name': _('Insert foreground'),
    'description': _(
      'Inserts layers having the specified color tag in front of the current layer.'),
    'display_options_on_create': True,
    'additional_tags': [EDIT_LAYERS_TAG, EXPORT_LAYERS_TAG],
    'arguments': [
      {
        'type': 'enum',
        'name': 'color_tag',
        'enum_type': Gimp.ColorTag,
        'excluded_values': [Gimp.ColorTag.NONE],
        'display_name': _('Color tag'),
        'default_value': Gimp.ColorTag.GREEN,
      },
      {
        'type': 'string',
        'name': 'merge_procedure_name',
        'default_value': '',
        'gui_type': None,
      },
      {
        'type': 'string',
        'name': 'constraint_name',
        'default_value': '',
        'gui_type': None,
      },
    ],
  },
  _EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS,
  _EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS,
  {
    'name': 'merge_background',
    'function': background_foreground.merge_background,
    'display_name': _('Merge background'),
    # This procedure is added/removed automatically alongside `insert_background`.
    'additional_tags': [],
    'arguments': [
      {
        'type': 'enum',
        'name': 'merge_type',
        'enum_type': Gimp.MergeType,
        'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
        'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
        'display_name': _('Merge type'),
      },
      {
        'type': 'bool',
        'name': 'last_enabled_value',
        'default_value': True,
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'merge_foreground',
    'function': background_foreground.merge_foreground,
    'display_name': _('Merge foreground'),
    # This procedure is added/removed automatically alongside `insert_foreground`.
    'additional_tags': [],
    'arguments': [
      {
        'type': 'enum',
        'name': 'merge_type',
        'enum_type': Gimp.MergeType,
        'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
        'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
        'display_name': _('Merge type'),
      },
      {
        'type': 'bool',
        'name': 'last_enabled_value',
        'default_value': True,
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'remove_folder_structure_for_export_layers',
    'function': remove_folder_structure_from_item_for_export_layers,
    'display_name': _('Remove folder structure'),
    'additional_tags': [NAME_ONLY_TAG, EXPORT_LAYERS_TAG],
  },
  {
    'name': 'remove_folder_structure_for_edit_layers',
    'function': remove_folder_structure_from_item_for_edit_layers,
    'display_name': _('Remove folder structure'),
    'additional_tags': [NAME_ONLY_TAG, EDIT_LAYERS_TAG],
    'arguments': [
      {
        'type': 'bool',
        'name': 'consider_parent_visible',
        'default_value': False,
        'display_name': _('Consider visibility of parent folders'),
        'gui_type': 'check_button',
      },
    ],
  },
  {
    'name': 'rename_for_export_layers',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [NAME_ONLY_TAG, EXPORT_LAYERS_TAG],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'name_pattern',
        'name': 'pattern',
        'default_value': '[layer name]',
        'display_name': _('Layer filename pattern'),
        'gui_type': 'name_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'rename_layers',
        'default_value': True,
        'display_name': _('Rename layers'),
        'gui_type': 'check_button',
      },
      {
        'type': 'bool',
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename folders'),
        'gui_type': 'check_button',
      },
    ],
  },
  {
    'name': 'rename_for_edit_layers',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [NAME_ONLY_TAG, EDIT_LAYERS_TAG],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'name_pattern',
        'name': 'pattern',
        'default_value': '[layer name]',
        'display_name': _('Layer name pattern'),
        'gui_type': 'name_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'rename_layers',
        'default_value': True,
        'display_name': _('Rename layers'),
        'gui_type': 'check_button',
      },
      {
        'type': 'bool',
        'name': 'rename_group_layers',
        'default_value': False,
        'display_name': _('Rename group layers'),
        'gui_type': 'check_button',
      },
    ],
  },
  {
    'name': 'scale',
    'function': scale,
    'display_name': _('Scale'),
    'display_options_on_create': True,
    'additional_tags': [EDIT_LAYERS_TAG, EXPORT_LAYERS_TAG],
    'arguments': [
      {
        'type': 'placeholder_image',
        'name': 'image',
        'display_name': _('Image'),
      },
      {
        'type': 'placeholder_layer',
        'name': 'layer',
        'display_name': _('Layer'),
      },
      {
        'type': 'double',
        'default_value': 100.0,
        'name': 'new_width',
        'display_name': _('New width'),
      },
      {
        'type': 'choice',
        'default_value': 'percentage_of_layer_width',
        'name': 'width_unit',
        'items': [
          ('percentage_of_layer_width', _('% of layer width'), PERCENT_LAYER_WIDTH),
          ('percentage_of_layer_height', _('% of layer height'), PERCENT_LAYER_HEIGHT),
          ('percentage_of_image_width', _('% of image width'), PERCENT_IMAGE_WIDTH),
          ('percentage_of_image_height', _('% of image height'), PERCENT_IMAGE_HEIGHT),
          ('pixels', _('Pixels'), PIXELS),
        ],
        'display_name': _('Unit for width'),
      },
      {
        'type': 'double',
        'default_value': 100.0,
        'name': 'new_height',
        'display_name': _('New height'),
      },
      {
        'type': 'choice',
        'default_value': 'percentage_of_layer_height',
        'name': 'height_unit',
        'items': [
          ('percentage_of_layer_width', _('% of layer width'), PERCENT_LAYER_WIDTH),
          ('percentage_of_layer_height', _('% of layer height'), PERCENT_LAYER_HEIGHT),
          ('percentage_of_image_width', _('% of image width'), PERCENT_IMAGE_WIDTH),
          ('percentage_of_image_height', _('% of image height'), PERCENT_IMAGE_HEIGHT),
          ('pixels', _('Pixels'), PIXELS),
        ],
        'display_name': _('Unit for height'),
      },
      {
        'type': 'enum',
        'enum_type': Gimp.InterpolationType,
        'name': 'interpolation',
        'display_name': _('Interpolation'),
      },
      {
        'type': 'bool',
        'name': 'local_origin',
        'default_value': False,
        'display_name': _('Use local origin'),
        'gui_type': 'check_button',
      },
    ],
  },
  {
    'name': 'use_layer_size',
    'function': resize_to_layer_size,
    'display_name': _('Use layer size'),
    'description': _('Resizes the current layer to use the layer size rather than the image size.'),
    'additional_tags': [EXPORT_LAYERS_TAG],
  },
]

# Translated display names could be displayed out of alphabetical order,
# hence the sorting.
_BUILTIN_PROCEDURES_LIST.sort(
  key=lambda item: item.get('menu_path', item.get('display_name', item['name'])))

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
