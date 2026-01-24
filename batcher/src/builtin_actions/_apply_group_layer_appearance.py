"""Built-in "Apply Group Layer Appearance" action."""

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

from config import CONFIG
from src import utils_pdb
from src import setting as setting_
from src.procedure_groups import *
from src.pypdb import pdb
from src.gui import utils as gui_utils_


__all__ = [
  'apply_group_layer_appearance',
  'on_after_add_apply_group_layer_appearance_action',
]


def apply_group_layer_appearance(
      layer_batcher,
      apply_filters,
      apply_layer_modes,
      apply_opacity,
      apply_layer_masks,
      apply_blend_space,
      apply_composite_mode,
      apply_composite_space,
      merge_groups,
):
  layer = layer_batcher.current_layer
  image = layer.get_image()

  orig_layer_position = image.get_item_position(layer)
  orig_layer_name = layer.get_name()

  new_parents = []

  orig_layer = layer_batcher.current_item.raw
  orig_parent = orig_layer.get_parent()
  layer_parent = layer.get_parent()

  if orig_parent is None:
    # Nothing to do as the layer has no parent group layers.
    return

  current_orig_parent = orig_parent
  current_new_parent = layer.get_parent()
  while current_orig_parent is not None:
    group_layer = utils_pdb.copy_and_paste_layer(
      current_orig_parent,
      image,
      layer_parent,
      orig_layer_position,
      remove_lock_attributes=False,
      set_visible=True,
      merge_group=False,
      copy_contents=False,
    )

    if current_orig_parent == orig_parent:
      image.reorder_item(layer, group_layer, 0)
    else:
      image.reorder_item(current_new_parent, group_layer, 0)

    if apply_filters:
      _copy_filters(current_orig_parent, group_layer)

    if apply_layer_modes:
      group_layer.set_mode(current_orig_parent.get_mode())

    if apply_opacity:
      group_layer.set_opacity(current_orig_parent.get_opacity())

    if apply_layer_masks:
      raw_parent_layer_mask = current_orig_parent.get_mask()
      if raw_parent_layer_mask is not None:
        _copy_layer_mask(image, orig_layer, raw_parent_layer_mask, layer, group_layer)

    if apply_blend_space:
      group_layer.set_blend_space(current_orig_parent.get_blend_space())

    if apply_composite_mode:
      group_layer.set_composite_mode(current_orig_parent.get_composite_mode())

    if apply_composite_space:
      group_layer.set_composite_space(current_orig_parent.get_composite_space())

    new_parents.insert(0, group_layer)
    current_orig_parent = current_orig_parent.get_parent()
    current_new_parent = group_layer

  top_level_parent = new_parents[0]

  if merge_groups:
    merged_layer = top_level_parent.merge()
    merged_layer.set_name(orig_layer_name)

    layer_batcher.current_layer = merged_layer
  else:
    # Make sure that the original layer name is "transferred" to the inserted
    # top-level group and that the original layer has a suffix auto-assigned by
    # GIMP.
    top_level_parent.set_name(orig_layer_name)
    layer.set_name(top_level_parent.get_name())
    top_level_parent.set_name(orig_layer_name)

    layer_batcher.current_layer = top_level_parent


def _copy_filters(src_layer, dest_layer):
  filters = src_layer.get_filters()

  for filter_ in reversed(filters):
    filter_copy = Gimp.DrawableFilter.new(
      dest_layer, filter_.get_operation_name(), filter_.get_name())
    filter_copy.set_blend_mode(filter_.get_blend_mode())
    filter_copy.set_opacity(filter_.get_opacity())
    filter_copy.set_visible(filter_.get_visible())

    filter_config = filter_.get_config()
    filter_copy_config = filter_copy.get_config()

    for prop in filter_config.list_properties():
      filter_copy_config.set_property(prop.name, filter_config.get_property(prop.name))

    filter_copy.update()

    dest_layer.append_filter(filter_copy)


def _copy_layer_mask(image, src_layer, src_layer_mask, dest_layer, dest_group_layer):
  if not pdb.gimp_selection_is_empty(image=image):
    orig_selection = pdb.gimp_selection_save(image=image)
    pdb.gimp_selection_none(image=image)
  else:
    orig_selection = None

  src_layer_offsets = src_layer.get_offsets()
  src_layer_mask_offsets = src_layer_mask.get_offsets()
  dest_layer_offsets = dest_layer.get_offsets()

  dest_layer_mask = dest_group_layer.create_mask(Gimp.AddMaskType.WHITE)
  dest_group_layer.add_mask(dest_layer_mask)

  Gimp.edit_copy([src_layer_mask])
  Gimp.edit_paste(dest_layer_mask, paste_into=True)

  floating_selection = image.get_floating_sel()
  if floating_selection is not None:
    floating_selection.set_offsets(
      src_layer_mask_offsets.offset_x + dest_layer_offsets.offset_x - src_layer_offsets.offset_x,
      src_layer_mask_offsets.offset_y + dest_layer_offsets.offset_y - src_layer_offsets.offset_y,
    )
    Gimp.floating_sel_anchor(floating_selection)

  dest_group_layer.set_edit_mask(False)

  if orig_selection is not None:
    image.select_item(Gimp.ChannelOps.REPLACE, orig_selection)
    image.remove_channel(orig_selection)


def on_after_add_apply_group_layer_appearance_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value == 'apply_group_layer_appearance':
    action['arguments/merge_groups'].connect_event(
      'value-changed',
      _warn_if_merge_groups_is_not_enabled,
    )


def _warn_if_merge_groups_is_not_enabled(merge_groups_setting):
  if CONFIG.RUN_MODE == Gimp.RunMode.INTERACTIVE and not merge_groups_setting.value:
    if not isinstance(merge_groups_setting.gui, setting_.NullPresenter):
      gui_utils_.display_popover(
        merge_groups_setting.gui.widget,
        _('If unchecked, the current layer is turned into a group layer.'
          ' Subsequent actions may fail if they invoke plug-ins or destructive layer effects.'),
        icon_name=GimpUi.ICON_DIALOG_WARNING,
        max_width_chars=35,
      )


APPLY_GROUP_LAYER_APPEARANCE_DICT = {
  'name': 'apply_group_layer_appearance',
  'function': apply_group_layer_appearance,
  'display_name': _('Apply Group Layer Appearance'),
  'menu_path': _('Layers and Composition'),
  'description': _(
    'Applies attributes (filters, opacity, mode, ...) from all parent group layers'
    ' to the current layer to match its appearance in GIMP.'),
  'arguments': [
    {
      'type': 'bool',
      'name': 'apply_filters',
      'default_value': True,
      'display_name': _('Apply filters (layer effects)'),
    },
    {
      'type': 'bool',
      'name': 'apply_layer_modes',
      'default_value': True,
      'display_name': _('Apply layer modes'),
    },
    {
      'type': 'bool',
      'name': 'apply_opacity',
      'default_value': True,
      'display_name': _('Apply opacity'),
    },
    {
      'type': 'bool',
      'name': 'apply_layer_masks',
      'default_value': True,
      'display_name': _('Apply layer masks'),
    },
    {
      'type': 'bool',
      'name': 'apply_blend_space',
      'default_value': True,
      'display_name': _('Apply blend space'),
    },
    {
      'type': 'bool',
      'name': 'apply_composite_mode',
      'default_value': True,
      'display_name': _('Apply composite mode'),
    },
    {
      'type': 'bool',
      'name': 'apply_composite_space',
      'default_value': True,
      'display_name': _('Apply composite space'),
    },
    {
      'type': 'bool',
      'name': 'merge_groups',
      'default_value': True,
      'display_name': _('Merge groups with layer'),
    },
  ],
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
}
