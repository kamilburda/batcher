"""Built-in actions."""

from src.builtin_actions import _align_and_offset
from src.builtin_actions._align_and_offset import *
from src.builtin_actions import _apply_group_layer_appearance
from src.builtin_actions._apply_group_layer_appearance import *
from src.builtin_actions import _color_correction
from src.builtin_actions._color_correction import *
from src.builtin_actions import _crop
from src.builtin_actions._crop import *
from src.builtin_actions import _export
from src.builtin_actions._export import *
from src.builtin_actions import _flip
from src.builtin_actions._flip import *
from src.builtin_actions import _gmic_filter
from src.builtin_actions._gmic_filter import *
from src.builtin_actions import _import
from src.builtin_actions._import import *
from src.builtin_actions import _insert_background_foreground
from src.builtin_actions._insert_background_foreground import *
from src.builtin_actions import _misc
from src.builtin_actions._misc import *
from src.builtin_actions import _remove_folder_structure
from src.builtin_actions._remove_folder_structure import *
from src.builtin_actions import _rename
from src.builtin_actions._rename import *
from src.builtin_actions import _resize_canvas
from src.builtin_actions._resize_canvas import *
from src.builtin_actions import _rotate
from src.builtin_actions._rotate import *
from src.builtin_actions import _save
from src.builtin_actions._save import *
from src.builtin_actions import _scale
from src.builtin_actions._scale import *
from src.builtin_actions._utils import *


_BUILTIN_ACTIONS_LIST = [
  _rename.RENAME_FOR_CONVERT_DICT,
  _rename.RENAME_FOR_EXPORT_IMAGES_DICT,
  _rename.RENAME_FOR_EDIT_AND_SAVE_IMAGES_DICT,
  _rename.RENAME_FOR_EXPORT_LAYERS_DICT,
  _rename.RENAME_FOR_EDIT_LAYERS_DICT,
  _misc.REMOVE_FILE_EXTENSION_FROM_IMPORTED_IMAGES_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_FOR_EDIT_LAYERS_DICT,
  _import.IMPORT_DICT,
  _export.EXPORT_FOR_CONVERT_DICT,
  _export.EXPORT_FOR_EXPORT_IMAGES_DICT,
  _export.EXPORT_FOR_EDIT_AND_SAVE_IMAGES_DICT,
  _export.EXPORT_FOR_EXPORT_LAYERS_DICT,
  _export.EXPORT_FOR_EDIT_LAYERS_DICT,
  _save.SAVE_DICT,
  _scale.SCALE_FOR_IMAGES_DICT,
  _scale.SCALE_FOR_LAYERS_DICT,
  _resize_canvas.RESIZE_CANVAS_DICT,
  _crop.CROP_FOR_IMAGES_DICT,
  _crop.CROP_FOR_LAYERS_DICT,
  _align_and_offset.ALIGN_AND_OFFSET_DICT,
  _flip.FLIP_HORIZONTALLY_FOR_IMAGES_DICT,
  _flip.FLIP_HORIZONTALLY_FOR_LAYERS_DICT,
  _flip.FLIP_VERTICALLY_FOR_IMAGES_DICT,
  _flip.FLIP_VERTICALLY_FOR_LAYERS_DICT,
  _rotate.ROTATE_FOR_IMAGES_DICT,
  _rotate.ROTATE_FOR_LAYERS_DICT,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.MERGE_BACKGROUND_DICT,
  _insert_background_foreground.MERGE_FOREGROUND_DICT,
  _apply_group_layer_appearance.APPLY_GROUP_LAYER_APPEARANCE_DICT,
  _misc.MERGE_FILTERS_DICT,
  _misc.MERGE_VISIBLE_LAYERS_DICT,
  _color_correction.BRIGHTNESS_CONTRAST_DICT,
  _color_correction.LEVELS_DICT,
  _color_correction.CURVES_DICT,
  _color_correction.WHITE_BALANCE_DICT,
  _gmic_filter.GMIC_FILTER_DICT,
]

# Create a separate dictionary for functions since objects cannot be saved to
# a persistent source. Saving them as strings would not be reliable as
# function names and paths may change when refactoring or adding/modifying
# features. The 'function' setting is set to an empty value as the function
# can be inferred via the command's 'orig_name' setting.
BUILTIN_ACTIONS = {}
BUILTIN_ACTIONS_FUNCTIONS = {}

# These are functions indicating when a command should be available. This can
# be useful e.g. to hide a command when a third-party plug-in the command
# depends on is not present, or to make the command (un)available for
# particular versions of GIMP.
BUILTIN_ACTIONS_AVAILABILITY_FUNCTIONS = {}

for command_dict in _BUILTIN_ACTIONS_LIST:
  function = command_dict['function']
  command_dict['function'] = ''

  BUILTIN_ACTIONS[command_dict['name']] = command_dict
  BUILTIN_ACTIONS_FUNCTIONS[command_dict['name']] = function

  if 'available' in command_dict:
    BUILTIN_ACTIONS_AVAILABILITY_FUNCTIONS[command_dict['name']] = command_dict.pop('available')
