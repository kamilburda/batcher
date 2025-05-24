"""Built-in "Remove folder structure" procedure."""

from src import builtin_actions_common
from src.procedure_groups import *


__all__ = [
  'remove_folder_structure_from_item',
  'remove_folder_structure_from_item_for_edit_layers',
]


def remove_folder_structure_from_item(batcher):
  item = batcher.current_item

  item.parents = []
  item.children = []


def remove_folder_structure_from_item_for_edit_layers(
      layer_batcher,
      consider_parent_visible=False,
):
  item = layer_batcher.current_item

  if layer_batcher.edit_mode and not layer_batcher.is_preview:
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


REMOVE_FOLDER_STRUCTURE_DICT = {
  'name': 'remove_folder_structure',
  'function': remove_folder_structure_from_item,
  'display_name': _('Remove folder structure'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, CONVERT_GROUP, EXPORT_LAYERS_GROUP],
}

REMOVE_FOLDER_STRUCTURE_DICT_FOR_EDIT_LAYERS = {
  'name': 'remove_folder_structure_for_edit_layers',
  'function': remove_folder_structure_from_item_for_edit_layers,
  'display_name': _('Remove folder structure'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
  'arguments': [
    {
      'type': 'bool',
      'name': 'consider_parent_visible',
      'default_value': False,
      'display_name': _('Consider visibility of parent folders'),
    },
  ],
}
