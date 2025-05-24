"""Built-in procedures."""

from src.builtin_procedures import _align_and_offset
from src.builtin_procedures._align_and_offset import *
from src.builtin_procedures import _export
from src.builtin_procedures._export import *
from src.builtin_procedures import _insert_background_foreground
from src.builtin_procedures._insert_background_foreground import *
from src.builtin_procedures import _misc
from src.builtin_procedures._misc import *
from src.builtin_procedures import _remove_folder_structure
from src.builtin_procedures._remove_folder_structure import *
from src.builtin_procedures import _rename
from src.builtin_procedures._rename import *
from src.builtin_procedures import _resize_canvas
from src.builtin_procedures._resize_canvas import *
from src.builtin_procedures import _scale
from src.builtin_procedures._scale import *


_BUILTIN_PROCEDURES_LIST = [
  _align_and_offset.ALIGN_AND_OFFSET_PROCEDURE_DICT,
  _export.EXPORT_PROCEDURE_DICT_FOR_CONVERT,
  _export.EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES,
  _export.EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS,
  _export.EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_BACKGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_IMAGES_DICT,
  _insert_background_foreground.INSERT_FOREGROUND_FOR_LAYERS_DICT,
  _insert_background_foreground.MERGE_BACKGROUND_DICT,
  _insert_background_foreground.MERGE_FOREGROUND_DICT,
  _misc.APPLY_OPACITY_FROM_GROUP_LAYERS_DICT,
  _misc.MERGE_FILTERS_DICT,
  _misc.MERGE_VISIBLE_LAYERS_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_DICT,
  _remove_folder_structure.REMOVE_FOLDER_STRUCTURE_DICT_FOR_EDIT_LAYERS,
  _rename.RENAME_FOR_CONVERT_DICT,
  _rename.RENAME_FOR_EXPORT_IMAGES_DICT,
  _rename.RENAME_FOR_EXPORT_LAYERS_DICT,
  _rename.RENAME_FOR_EDIT_LAYERS_DICT,
  _resize_canvas.RESIZE_TO_LAYER_SIZE_DICT,
  _scale.SCALE_PROCEDURE_DICT_FOR_IMAGES,
  _scale.SCALE_PROCEDURE_DICT_FOR_LAYERS,
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
