"""Built-in "Insert Overlay (Watermark)" action."""

import os

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import exceptions
from src import invoker as invoker_
from src import setting as setting_
from src import placeholders as placeholders_
from src.procedure_groups import *

from src import utils_pdb
from src.pypdb import pdb

from . import _utils as builtin_actions_utils


__all__ = [
  'InsertOverlayAction',
  'InsertTaggedLayersAction',
  'merge_overlay',
  'on_after_add_insert_overlay_for_layers_action',
  'on_after_add_insert_overlay_action',
  'on_after_add_merge_overlay_action',
]


class ContentType:

  CONTENT_TYPES = (
    FILE,
    TEXT,
    LAYERS_WITH_COLOR_TAG,
  ) = 'file', 'text', 'layers_with_color_tag'


class InsertionPositions:

  INSERTION_POSITIONS = (
    BACKGROUND,
    FOREGROUND,
  ) = 'background', 'foreground'


class InsertOverlayAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, image_batcher, **kwargs):
    self._insert_content = ContentType.FILE
    self._image_file = None
    self._text = '© Copyright'
    self._text_font_family = Gimp.Font.get_by_name('Arial Regular')
    self._text_font_size = {
      'pixel_value': 14.0,
      'percent_value': 5.0,
      'other_value': 1.0,
      'unit': Gimp.Unit.pixel(),
      'percent_object': 'current_layer',
      'percent_property': {
        ('current_image',): 'width',
        ('current_layer', 'background_layer', 'foreground_layer'): 'width',
      },
    }
    self._text_font_color = Gegl.Color()
    self._text_font_color.set_rgba(0.0, 0.0, 0.0, 1.0)
    self._position = InsertionPositions.BACKGROUND

    self._assign_to_attributes_from_kwargs(kwargs)

    self._image_copies = []

    image_batcher.invoker.add(_delete_images_on_cleanup, ['cleanup_contents'], [self._image_copies])

    # noinspection PyUnresolvedReferences
    if (self._insert_content == ContentType.FILE
        and self._image_file is not None
        and self._image_file.get_path() is not None
        and os.path.exists(self._image_file.get_path())):
      self._image_to_insert = pdb.gimp_file_load(
        run_mode=Gimp.RunMode.NONINTERACTIVE,
        file=self._image_file)

      self._image_copies.append(self._image_to_insert)
    else:
      self._image_to_insert = None

  def _process(self, image_batcher, **kwargs):
    if self._insert_content == ContentType.FILE and self._image_to_insert is None:
      raise exceptions.SkipCommand(_('Image file not specified.'))

    self._assign_to_attributes_from_kwargs(kwargs)

    image = image_batcher.current_image
    current_parent = image_batcher.current_layer.get_parent()

    index = image.get_item_position(image_batcher.current_layer)
    if self._position == 'background':
      index += 1

    inserted_layer = None

    if self._insert_content == ContentType.FILE:
      inserted_layer = _insert_layers(
        image, self._image_to_insert.get_layers(), current_parent, index)
    elif self._insert_content == ContentType.TEXT:
      inserted_layer = _insert_text_layer(
        image_batcher,
        image,
        self._text,
        self._text_font_family,
        self._text_font_size,
        self._text_font_color,
        current_parent,
        index,
      )

    # TODO: Allow adjusting scale, anchor, opacity, rotation, tiling, ...

    return inserted_layer

  def _assign_to_attributes_from_kwargs(self, kwargs):
    for name, value in kwargs.items():
      # Ignore internal arguments not displayed to the user.
      if hasattr(self, f'_{name}'):
        setattr(self, f'_{name}', value)


def _delete_images_on_cleanup(_batcher, images):
  for image in images:
    utils_pdb.try_delete_image(image)

  images.clear()


# TODO: Merge with InsertOverlayAction
class InsertTaggedLayersAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(
        self,
        layer_batcher,
        color_tag,
        position,
        tagged_items,
        *_args,
        **_kwargs,
  ):
    if layer_batcher.is_preview:
      processed_tagged_items = tagged_items
    else:
      processed_tagged_items = layer_batcher.item_tree.iter(with_folders=False, filtered=False)

    self._tagged_items = [
      item for item in processed_tagged_items
      if (color_tag != Gimp.ColorTag.NONE
          and item.raw.is_valid()
          and item.raw.get_color_tag() == color_tag)
    ]

  def _process(
        self,
        layer_batcher,
        color_tag,
        position,
        tagged_items,
        *_args,
        **_kwargs,
  ):
    if not self._tagged_items:
      return

    image = layer_batcher.current_image
    current_parent = layer_batcher.current_layer.get_parent()

    index = image.get_item_position(layer_batcher.current_layer)
    if position == 'background':
      index += 1

    inserted_layer = _insert_layers(
      image, [item.raw for item in self._tagged_items], current_parent, index)

    return inserted_layer


def _insert_layers(image, layers, parent, position):
  first_tagged_layer_position = position
  
  for i, layer in enumerate(layers):
    layer_copy = utils_pdb.copy_and_paste_layer(
      layer, image, parent, first_tagged_layer_position + i, True, True, True)
    layer_copy.set_visible(True)

  if parent is None:
    children = image.get_layers()
  else:
    children = parent.get_children()

  merged_tagged_layer = None

  if len(layers) == 1:
    merged_tagged_layer = children[first_tagged_layer_position]
  else:
    second_to_last_tagged_layer_position = first_tagged_layer_position + len(layers) - 2
    # It should not matter which items we obtain the color tag from as all
    # items have the same color tag.
    merged_color_tag = children[second_to_last_tagged_layer_position].get_color_tag()

    for i in range(second_to_last_tagged_layer_position, first_tagged_layer_position - 1, -1):
      merged_tagged_layer = image.merge_down(children[i], Gimp.MergeType.EXPAND_AS_NECESSARY)

    # The merged-down layer does not possess the attributes of the original
    # layers, including the color tag, so we set it explicitly. This ensures
    # that tagged group layers are merged properly in "Merge back-/foreground"
    # actions.
    merged_tagged_layer.set_color_tag(merged_color_tag)

  return merged_tagged_layer


def _insert_text_layer(
      batcher,
      image,
      text,
      font_family,
      font_dimension,
      font_color,
      parent,
      position,
):
  if font_dimension['unit'] == Gimp.Unit.percent():
    font_size = builtin_actions_utils.unit_to_pixels(batcher, font_dimension, 'x')
    font_unit = Gimp.Unit.pixel()
  elif font_dimension['unit'] == Gimp.Unit.pixel():
    font_size = font_dimension['pixel_value']
    font_unit = Gimp.Unit.pixel()
  else:
    font_size = font_dimension['other_value']
    font_unit = font_dimension['unit']

  text_layer = Gimp.TextLayer.new(
    image,
    text,
    font_family,
    font_size,
    font_unit,
  )

  image.insert_layer(text_layer, parent, position)

  text_layer.set_color(setting_.ColorSetting.get_value_as_color(font_color))

  return text_layer


def merge_overlay(
      batcher,
      position: str = InsertionPositions.BACKGROUND,
      merge_type: Gimp.MergeType = Gimp.MergeType.EXPAND_AS_NECESSARY,
      *_args,
      **_kwargs,
):
  if position == InsertionPositions.BACKGROUND:
    _merge_layer(batcher, merge_type, _get_background_layer, 'current_layer')
  elif position == InsertionPositions.FOREGROUND:
    _merge_layer(batcher, merge_type, _get_foreground_layer, 'inserted_layer')
  else:
    raise ValueError(f'invalid position: {position}')


def _get_background_layer(batcher):
  return placeholders_.get_background_layer(None, batcher)


def _get_foreground_layer(batcher):
  return placeholders_.get_foreground_layer(None, batcher)


def _merge_layer(batcher, merge_type, get_inserted_layer_func, layer_to_merge_str):
  inserted_layer = get_inserted_layer_func(batcher)
  
  if inserted_layer is not None:
    name = batcher.current_layer.get_name()
    visible = batcher.current_layer.get_visible()
    orig_color_tag = batcher.current_layer.get_color_tag()
    
    if layer_to_merge_str == 'current_layer':
      layer_to_merge_down = batcher.current_layer
    elif layer_to_merge_str == 'inserted_layer':
      layer_to_merge_down = inserted_layer
    else:
      raise ValueError('invalid value for "layer_to_merge_str"')
    
    batcher.current_layer.set_visible(True)
    
    merged_layer = batcher.current_image.merge_down(layer_to_merge_down, merge_type)

    # Avoid errors if merge failed for some reason.
    if merged_layer is not None:
      merged_layer.set_name(name)

      batcher.current_layer = merged_layer

      batcher.current_layer.set_visible(visible)
      batcher.current_layer.set_color_tag(orig_color_tag)


def on_after_add_insert_overlay_for_layers_action(
      _actions,
      action,
      _orig_action_dict,
      tagged_items_setting,
):
  if action['orig_name'].value == 'insert_overlay_for_layers':
    action['arguments/tagged_items'].gui.set_visible(False)
    _sync_tagged_items_with_action(tagged_items_setting, action)


def _sync_tagged_items_with_action(tagged_items_setting, action):

  def _on_tagged_items_changed(tagged_items_setting_, action_):
    action_['arguments/tagged_items'].set_value(tagged_items_setting_.value)

  _on_tagged_items_changed(tagged_items_setting, action)

  tagged_items_setting.connect_event('value-changed', _on_tagged_items_changed, action)


def on_after_add_insert_overlay_action(actions, action, _orig_action_dict, conditions):
  if action['orig_name'].value.startswith('insert_overlay_for_'):
    _set_visible_for_insert_overlay_arguments(
      action['arguments/insert_content'],
      action['arguments'],
    )

    action['arguments/insert_content'].connect_event(
      'value-changed',
      _set_visible_for_insert_overlay_arguments,
      action['arguments'],
    )

    _set_display_name_for_insert_overlay(
      action['arguments/position'],
      action['display_name'],
    )

    action['arguments/position'].connect_event(
      'value-changed',
      _set_display_name_for_insert_overlay,
      action['display_name'],
    )

    if 'merge_action_name' in action['arguments']:
      action['arguments/merge_action_name'].gui.set_visible(False)

      _connect_changes_to_linked_merge_overlay_action(
        action['arguments/merge_action_name'],
        actions,
        action,
      )
      action['arguments/merge_action_name'].connect_event(
        'value-changed',
        _connect_changes_to_linked_merge_overlay_action,
        actions,
        action,
      )

    if 'condition_name' in action['arguments']:
      action['arguments/condition_name'].gui.set_visible(False)

      _connect_changes_to_linked_not_overlay_condition(
        action['arguments/condition_name'],
        conditions,
        action,
      )
      action['arguments/condition_name'].connect_event(
        'value-changed',
        _connect_changes_to_linked_not_overlay_condition,
        conditions,
        action,
      )


def _set_visible_for_insert_overlay_arguments(
      insert_content_setting,
      arguments,
):
  is_content_type_file = insert_content_setting.value == ContentType.FILE
  is_content_type_text = insert_content_setting.value == ContentType.TEXT

  arguments['image_file'].gui.set_visible(is_content_type_file)

  arguments['text'].gui.set_visible(is_content_type_text)
  arguments['text_font_family'].gui.set_visible(is_content_type_text)
  arguments['text_font_size'].gui.set_visible(is_content_type_text)
  arguments['text_font_color'].gui.set_visible(is_content_type_text)


def _set_display_name_for_insert_overlay(
      insert_overlay_position_setting,
      display_name_setting,
):
  if insert_overlay_position_setting.value == InsertionPositions.BACKGROUND:
    display_name_setting.set_value(_('Insert Background'))
  elif insert_overlay_position_setting.value == InsertionPositions.FOREGROUND:
    display_name_setting.set_value(_('Insert Foreground'))
  else:
    display_name_setting.set_value(_('Insert Overlay (Watermark)'))


def _connect_changes_to_linked_merge_overlay_action(
      merge_action_name_setting,
      actions,
      insert_overlay_action,
):
  if merge_action_name_setting.value not in actions:
    return

  merge_overlay_action = actions[merge_action_name_setting.value]

  # We expect the `merge_action_name` setting to be changed only once (when
  # the action is added interactively). If it changed multiple times, we
  # would have to disconnect previous 'value-changed' events.

  _set_position_for_merge_overlay(
    insert_overlay_action['arguments/position'],
    merge_overlay_action['arguments/position'],
  )
  insert_overlay_action['arguments/position'].connect_event(
    'value-changed',
    _set_position_for_merge_overlay,
    merge_overlay_action['arguments/position'],
  )

  insert_overlay_action['enabled'].connect_event(
    'value-changed',
    _set_enabled_and_sensitive_for_linked_command,
    merge_overlay_action['enabled'],
    merge_overlay_action['arguments/last_enabled_value'],
  )


def _set_position_for_merge_overlay(insert_position_setting, merge_position_setting):
  merge_position_setting.set_value(insert_position_setting.value)


def _connect_changes_to_linked_not_overlay_condition(
      condition_name_setting,
      conditions,
      insert_overlay_action,
):
  if condition_name_setting.value not in conditions:
    return

  not_overlay_condition = conditions[condition_name_setting.value]

  # We expect the `condition_name` setting to be changed only once (when
  # the condition is added interactively). If it changed multiple times,
  # we would have to disconnect previous 'value-changed' events.

  _set_display_name_for_not_overlay_condition(
    insert_overlay_action['arguments/position'],
    not_overlay_condition['display_name'],
  )
  insert_overlay_action['arguments/position'].connect_event(
    'value-changed',
    _set_display_name_for_not_overlay_condition,
    not_overlay_condition['display_name'],
  )

  _set_color_tag_based_on_insert_overlay_action(
    insert_overlay_action['arguments/color_tag'],
    not_overlay_condition['arguments/color_tag'],
  )
  insert_overlay_action['arguments/color_tag'].connect_event(
    'value-changed',
    _set_color_tag_based_on_insert_overlay_action,
    not_overlay_condition['arguments/color_tag'],
  )

  insert_overlay_action['enabled'].connect_event(
    'value-changed',
    _set_enabled_and_sensitive_for_linked_command,
    not_overlay_condition['enabled'],
    not_overlay_condition['arguments/last_enabled_value'],
  )


def _set_display_name_for_not_overlay_condition(
      insert_overlay_position_setting,
      display_name_setting,
):
  if insert_overlay_position_setting.value == InsertionPositions.BACKGROUND:
    # FOR TRANSLATORS: Think of "Only items that are not background" when translating this
    display_name_setting.set_value(_('Not Background'))
  elif insert_overlay_position_setting.value == InsertionPositions.FOREGROUND:
    # FOR TRANSLATORS: Think of "Only items that are not foreground" when translating this
    display_name_setting.set_value(_('Not Foreground'))
  else:
    # FOR TRANSLATORS: Think of "Only items that are not overlay (watermark)" when translating this
    display_name_setting.set_value(_('Not Overlay (Watermark)'))


def _set_color_tag_based_on_insert_overlay_action(
      color_tag_setting_from_insert_overlay_action,
      color_tag_setting_from_not_overlay_condition,
):
  color_tag_setting_from_not_overlay_condition.set_value(
    color_tag_setting_from_insert_overlay_action.value)


def _set_enabled_and_sensitive_for_linked_command(
      insert_enabled_setting,
      linked_command_enabled_setting,
      linked_command_last_enabled_value_setting,
):
  if not insert_enabled_setting.value:
    linked_command_last_enabled_value_setting.set_value(linked_command_enabled_setting.value)
    linked_command_enabled_setting.set_value(False)
  else:
    linked_command_enabled_setting.set_value(linked_command_last_enabled_value_setting.value)

  linked_command_enabled_setting.gui.set_sensitive(insert_enabled_setting.value)


def on_after_add_merge_overlay_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value == 'merge_overlay':
    action['arguments/position'].gui.set_visible(False)
    action['arguments/last_enabled_value'].gui.set_visible(False)

    _set_display_name_for_merge_overlay(
      action['arguments/position'],
      action['display_name'],
    )

    action['arguments/position'].connect_event(
      'value-changed',
      _set_display_name_for_merge_overlay,
      action['display_name'],
    )


def _set_display_name_for_merge_overlay(position_setting, display_name_setting):
  if position_setting.value == InsertionPositions.BACKGROUND:
    display_name_setting.set_value(_('Merge Background'))
  elif position_setting.value == InsertionPositions.FOREGROUND:
    display_name_setting.set_value(_('Merge Foreground'))
  else:
    display_name_setting.set_value(_('Merge Overlay (Watermark)'))


INSERT_OVERLAY_FOR_IMAGES_DICT = {
  'name': 'insert_overlay_for_images',
  'function': InsertOverlayAction,
  'display_name': _('Insert Overlay (Watermark)'),
  'menu_path': _('Layers and Composition'),
  'description': _(
    'Inserts the specified image behind or in front of the current layer.'
    '\n\nYou can apply subsequent actions on the inserted layer using'
    ' "{}" or "{}".'
  ).format(_('Layer Above (Foreground)'), _('Layer Below (Background)')),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EDIT_AND_SAVE_IMAGES_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'choice',
      'name': 'insert_content',
      'default_value': ContentType.FILE,
      'display_name': _('Insert content'),
      'items': [
        (ContentType.FILE, _('File')),
        (ContentType.TEXT, _('Text')),
      ],
      'gui_type': 'radio_button_box',
    },
    {
      'type': 'file',
      'name': 'image_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Image'),
      'none_ok': True,
    },
    {
      'type': 'string',
      'name': 'text',
      'default_value': '© Copyright',
      'display_name': _('Text'),
    },
    {
      'type': 'font',
      'name': 'text_font_family',
      'default_value': None,
      'display_name': _('Font'),
    },
    {
      'type': 'dimension',
      'name': 'text_font_size',
      'default_value': {
        'pixel_value': 14.0,
        'percent_value': 5.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': ['current_image', 'current_layer'],
      'display_name': _('Font size'),
    },
    {
      'type': 'color',
      'name': 'text_font_color',
      'default_value': [0.0, 0.0, 0.0, 1.0],
      'display_name': _('Font color'),
    },
    {
      'type': 'choice',
      'name': 'position',
      'default_value': InsertionPositions.FOREGROUND,
      'display_name': _('Position'),
      'items': [
        (InsertionPositions.FOREGROUND, _('Foreground')),
        (InsertionPositions.BACKGROUND, _('Background')),
      ],
      'gui_type': 'radio_button_box',
    },
    {
      'type': 'string',
      'name': 'merge_action_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}

INSERT_OVERLAY_FOR_LAYERS_DICT = {
  'name': 'insert_overlay_for_layers',
  'function': InsertTaggedLayersAction,
  'display_name': _('Insert Overlay (Watermark)'),
  'menu_path': _('Layers and Composition'),
  'description': _(
    'Inserts layers behind or in front of the current layer.'
    '\n\nYou can apply subsequent actions on the inserted layer using'
    ' "{}" or "{}".'
  ).format(_('Layer Above (Foreground)'), _('Layer Below (Background)')),
  'display_options_on_create': True,
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
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
      'type': 'choice',
      'name': 'position',
      'default_value': InsertionPositions.FOREGROUND,
      'display_name': _('Position'),
      'items': [
        (InsertionPositions.FOREGROUND, _('Foreground')),
        (InsertionPositions.BACKGROUND, _('Background')),
      ],
      'gui_type': 'radio_button_box',
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'gui_type': None,
      'tags': ['ignore_reset'],
    },
    {
      'type': 'string',
      'name': 'merge_action_name',
      'default_value': '',
      'gui_type': None,
    },
    {
      'type': 'string',
      'name': 'condition_name',
      'default_value': '',
      'gui_type': None,
    },
  ],
}


MERGE_OVERLAY_DICT = {
  'name': 'merge_overlay',
  'function': merge_overlay,
  'display_name': _('Merge Overlay (Watermark)'),
  'menu_path': _('Layers and Composition'),
  # This action is added/removed automatically alongside `insert_overlay_for_*`.
  'additional_tags': [],
  'arguments': [
    {
      'type': 'choice',
      'name': 'position',
      'default_value': InsertionPositions.BACKGROUND,
      'items': [
        (InsertionPositions.BACKGROUND, _('Background')),
        (InsertionPositions.FOREGROUND, _('Foreground')),
      ],
      'gui_type': None,
    },
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
}
