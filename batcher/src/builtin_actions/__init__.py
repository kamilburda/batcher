"""Built-in actions."""

from src.builtin_actions import _align_and_offset
from src.builtin_actions._align_and_offset import *
from src.builtin_actions import _color_correction
from src.builtin_actions._color_correction import *
from src.builtin_actions import _crop
from src.builtin_actions._crop import *
from src.builtin_actions import _export
from src.builtin_actions._export import *
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
from src.builtin_actions import _rotate_and_flip
from src.builtin_actions._rotate_and_flip import *
from src.builtin_actions import _save
from src.builtin_actions._save import *
from src.builtin_actions import _scale
from src.builtin_actions._scale import *
from src.builtin_actions._utils import *


_BUILTIN_ACTIONS_LIST = [
  _align_and_offset.ALIGN_AND_OFFSET_DICT,
  _color_correction.COLOR_CORRECTION_DICT,
  _crop.CROP_FOR_IMAGES_DICT,
  _crop.CROP_FOR_LAYERS_DICT,
  _export.EXPORT_FOR_CONVERT_DICT,
  _export.EXPORT_FOR_EXPORT_IMAGES_DICT,
  _export.EXPORT_FOR_EDIT_AND_SAVE_IMAGES_DICT,
  _export.EXPORT_FOR_EXPORT_LAYERS_DICT,
  _export.EXPORT_FOR_EDIT_LAYERS_DICT,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.MERGE_BACKGROUND_DICT,
  _insert_background_foreground.MERGE_FOREGROUND_DICT,
  _misc.APPLY_OPACITY_FROM_GROUP_LAYERS_DICT,
  _misc.MERGE_FILTERS_DICT,
  _misc.MERGE_VISIBLE_LAYERS_DICT,
  _misc.REMOVE_FILE_EXTENSION_FROM_IMPORTED_IMAGES_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_FOR_EDIT_LAYERS_DICT,
  _rename.RENAME_FOR_CONVERT_DICT,
  _rename.RENAME_FOR_EXPORT_IMAGES_DICT,
  _rename.RENAME_FOR_EDIT_AND_SAVE_IMAGES_DICT,
  _rename.RENAME_FOR_EXPORT_LAYERS_DICT,
  _rename.RENAME_FOR_EDIT_LAYERS_DICT,
  _resize_canvas.RESIZE_CANVAS_DICT,
  _rotate_and_flip.ROTATE_AND_FLIP_FOR_IMAGES_DICT,
  _rotate_and_flip.ROTATE_AND_FLIP_FOR_LAYERS_DICT,
  _save.SAVE_DICT,
  _scale.SCALE_FOR_IMAGES_DICT,
  _scale.SCALE_FOR_LAYERS_DICT,
]

# Translated display names could be displayed out of alphabetical order,
# hence the sorting.
_BUILTIN_ACTIONS_LIST.sort(
  key=lambda item: item.get('menu_path', item.get('display_name', item['name'])))

# Create a separate dictionary for functions since objects cannot be saved
# to a persistent source. Saving them as strings would not be reliable as
# function names and paths may change when refactoring or adding/modifying features.
# The 'function' setting is set to an empty value as the function can be inferred
# via the command's 'orig_name' setting.
BUILTIN_ACTIONS = {}
BUILTIN_ACTIONS_FUNCTIONS = {}

for command_dict in _BUILTIN_ACTIONS_LIST:
  function = command_dict['function']
  command_dict['function'] = ''

  BUILTIN_ACTIONS[command_dict['name']] = command_dict
  BUILTIN_ACTIONS_FUNCTIONS[command_dict['name']] = function
