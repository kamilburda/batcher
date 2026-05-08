"""Built-in "Insert Overlay (Watermark)" action."""

import os

import gi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import Gio

from src import builtin_commands_common
from src import commands
from src import constants
from src import exceptions
from src import invoker as invoker_
from src import placeholders as placeholders_
from src import renamer as renamer_
from src import setting as setting_
from src import utils
from src import utils_pdb
from src.procedure_groups import *
from src.pypdb import pdb

from . import _utils as builtin_actions_utils


__all__ = [
  'ContentType',
  'InsertOverlayAction',
  'on_after_add_insert_overlay_for_layers_action',
  'on_after_add_insert_overlay_action',
]


class ContentType:

  CONTENT_TYPES = (
    FILE,
    TEXT,
    LAYERS_WITH_COLOR_TAG,
  ) = 'file', 'text', 'layers_with_color_tag'


class InsertOverlayAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, batcher, **kwargs):
    self._insert_content = ContentType.FILE
    self._image_file = None
    self._image_file_pattern = '[image file]'
    self._text = '© Copyright'
    self._text_pattern = '© [current date]'
    self._color_tag = Gimp.ColorTag.BLUE
    self._use_pattern = False
    self._text_font_family = (
      Gimp.Font.get_by_name('Sans-serif') if Gimp.Font.get_by_name('Sans-serif') is not None
      else Gimp.fonts_get_list()[0]
    )
    self._text_font_size = {
      'pixel_value': 14.0,
      'percent_value': 5.0,
      'other_value': 1.0,
      'unit': Gimp.Unit.pixel(),
      'percent_object': 'current_layer',
      'percent_property': {
        placeholders_.ALL_IMAGE_PLACEHOLDERS: 'width',
        placeholders_.ALL_LAYER_PLACEHOLDERS: 'width',
      },
    }
    self._text_font_color = Gegl.Color()
    self._text_font_color.set_rgba(0.0, 0.0, 0.0, 1.0)
    self._size = {
      'pixel_value': 100.0,
      'percent_value': 100.0,
      'other_value': 1.0,
      'unit': Gimp.Unit.percent(),
    }
    self._adjust_placement = True
    self._placement = builtin_actions_utils.AnchorPoints.BOTTOM_RIGHT
    self._opacity = 100.0
    self._rotation_angle = 0.0
    self._offsets = {
      'x': 0.0,
      'y': 0.0,
    }
    self._num_tiles = 1
    self._position = builtin_actions_utils.InsertionPositions.BACKGROUND
    self._tagged_items = []

    self._assign_to_attributes_from_kwargs(kwargs)

    self._image_copies = []
    self._image_copies_for_pattern = []
    self._image_file_renamer = renamer_.ItemRenamer(
      self._image_file_pattern,
      fields_raw=dict(renamer_.get_fields(), **renamer_.get_fields(regexes=['image file']))
    )
    self._text_renamer = renamer_.ItemRenamer(
      self._text_pattern,
      fields_raw=dict(renamer_.get_fields(), **renamer_.get_fields(regexes=['image file'])),
    )

    batcher.invoker.add(self._delete_images_on_cleanup, ['cleanup_contents'], [self._image_copies])
    batcher.invoker.add(
      self._delete_images_on_cleanup,
      ['cleanup_contents'],
      [self._image_copies_for_pattern])
    # Also delete each loaded image during processing to minimize memory usage.
    batcher.invoker.add(
      self._delete_images_on_cleanup,
      ['after_process_item_contents'],
      [self._image_copies_for_pattern])

    # noinspection PyUnresolvedReferences
    if (self._insert_content == ContentType.FILE
        and not self._use_pattern
        and self._image_file is not None
        and self._image_file.get_path() is not None
        and os.path.exists(self._image_file.get_path())):
      self._image_to_insert = self._load_image(self._image_file, self._image_copies)
    else:
      self._image_to_insert = None

    if self._insert_content == ContentType.LAYERS_WITH_COLOR_TAG:
      if batcher.is_preview:
        processed_tagged_items = self._tagged_items
      else:
        processed_tagged_items = batcher.item_tree.iter(with_folders=False, filtered=False)

      self._processed_tagged_items = [
        item for item in processed_tagged_items
        if (self._color_tag != Gimp.ColorTag.NONE
            and item.raw.is_valid()
            and item.raw.get_color_tag() == self._color_tag)
      ]

      # This is used to obtain the localized display names of color tags.
      self._color_tag_tree_model = GimpUi.EnumComboBox.new_with_model(
        GimpUi.EnumStore.new(Gimp.ColorTag)).get_model()
    else:
      self._processed_tagged_items = []

  def _process(self, batcher, **kwargs):
    self._assign_to_attributes_from_kwargs(kwargs)

    image = batcher.current_image
    current_parent = batcher.current_layer.get_parent()

    index = image.get_item_position(batcher.current_layer)
    if self._position == builtin_actions_utils.InsertionPositions.BACKGROUND:
      index += 1

    inserted_layer = None

    if self._insert_content == ContentType.FILE:
      if self._use_pattern:
        image_filepath = self._image_file_renamer.rename(batcher)
        image_file = Gio.file_new_for_path(image_filepath)
        if image_file.get_path() is not None and os.path.exists(image_file.get_path()):
          image_to_insert = self._load_image(image_file, self._image_copies_for_pattern)
        else:
          raise ValueError(_('Image file "{}" does not exist.').format(image_filepath))
      else:
        if self._image_to_insert is None:
          raise exceptions.SkipCommand(_('Image file not specified.'))

        image_to_insert = self._image_to_insert

      inserted_layer = self._insert_layers(
        image,
        image_to_insert.get_layers(),
        current_parent,
        index,
      )
    elif self._insert_content == ContentType.TEXT:
      if self._use_pattern:
        text = self._text_renamer.rename(batcher)
      else:
        text = self._text

      inserted_layer = self._insert_text_layer(
        batcher,
        image,
        text,
        self._text_font_family,
        self._text_font_size,
        self._text_font_color,
        current_parent,
        index,
      )
    elif self._insert_content == ContentType.LAYERS_WITH_COLOR_TAG:
      if not self._processed_tagged_items:
        raise exceptions.SkipCommand(
          _('No layers with color tag: {}.').format(
            _get_color_tag_name(self._color_tag, self._color_tag_tree_model)))

      inserted_layer = self._insert_layers(
        image,
        [item.raw for item in self._processed_tagged_items],
        current_parent,
        index,
      )

    if inserted_layer is not None:
      self._scale_to_fit(batcher, inserted_layer)
      self._set_opacity(inserted_layer)
      self._rotate(inserted_layer)
      self._set_placement(batcher, inserted_layer)
      self._set_offsets(inserted_layer)
      self._tile(batcher, inserted_layer)

    return inserted_layer

  def _assign_to_attributes_from_kwargs(self, kwargs):
    for name, value in kwargs.items():
      # Ignore arguments not displayed to the user.
      if hasattr(self, f'_{name}'):
        setattr(self, f'_{name}', value)

  @staticmethod
  def _delete_images_on_cleanup(_batcher, images):
    for image in images:
      utils_pdb.try_delete_image(image)

    images.clear()

  @staticmethod
  def _load_image(image_file, image_copies):
    image_to_insert = pdb.gimp_file_load(
      run_mode=Gimp.RunMode.NONINTERACTIVE,
      file=image_file)

    image_copies.append(image_to_insert)

    return image_to_insert

  @staticmethod
  def _insert_layers(image, layers, parent, position):
    if not layers:
      return

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

  @staticmethod
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

  def _scale_to_fit(self, batcher, inserted_layer):
    if (self._insert_content == ContentType.TEXT
        or (self._size['percent_value'] == 100.0 and self._size['unit'] == Gimp.Unit.percent())):
      return

    size = dict(self._size)
    size['percent_object'] = f'{self._position}_layer'

    size['percent_property'] = {f'{self._position}_layer': 'width'}
    new_width_pixels = builtin_actions_utils.unit_to_pixels(batcher, size, 'x')

    size['percent_property'] = {f'{self._position}_layer': 'height'}
    new_height_pixels = builtin_actions_utils.unit_to_pixels(batcher, size, 'y')

    orig_width_pixels = inserted_layer.get_width()
    if orig_width_pixels == 0:
      orig_width_pixels = 1

    orig_height_pixels = inserted_layer.get_height()
    if orig_height_pixels == 0:
      orig_height_pixels = 1

    inserted_layer.scale(
      *self._get_scale_fit_values(
        orig_width_pixels,
        orig_height_pixels,
        new_width_pixels,
        new_height_pixels,
      ),
      True,
    )

  def _set_placement(self, batcher, inserted_layer):
    if self._insert_content == ContentType.LAYERS_WITH_COLOR_TAG and not self._adjust_placement:
      return

    image_width = batcher.current_image.get_width()
    image_height = batcher.current_image.get_height()

    width_pixels = inserted_layer.get_width()
    if width_pixels == 0:
      width_pixels = 1

    height_pixels = inserted_layer.get_height()
    if height_pixels == 0:
      height_pixels = 1
    
    if self._placement == builtin_actions_utils.AnchorPoints.TOP_LEFT:
      position = [0, 0]
    elif self._placement == builtin_actions_utils.AnchorPoints.TOP:
      position = [
        round((image_width - width_pixels) / 2),
        0,
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.TOP_RIGHT:
      position = [
        image_width - width_pixels,
        0,
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.LEFT:
      position = [
        0,
        round((image_height - height_pixels) / 2),
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.CENTER:
      position = [
        round((image_width - width_pixels) / 2),
        round((image_height - height_pixels) / 2),
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.RIGHT:
      position = [
        image_width - width_pixels,
        round((image_height - height_pixels) / 2),
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.BOTTOM_LEFT:
      position = [
        0,
        image_height - height_pixels,
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.BOTTOM:
      position = [
        round((image_width - width_pixels) / 2),
        image_height - height_pixels,
      ]
    elif self._placement == builtin_actions_utils.AnchorPoints.BOTTOM_RIGHT:
      position = [
        image_width - width_pixels,
        image_height - height_pixels,
      ]
    else:
      # This is `builtin_actions_utils.AnchorPoints.NONE` or some other
      # unrecognized value, in which case the layer is not moved.
      return

    inserted_layer.set_offsets(*position)

  def _rotate(self, inserted_layer):
    if self._rotation_angle == 0.0:
      return

    Gimp.context_push()
    Gimp.context_set_transform_resize(Gimp.TransformResize.ADJUST)
    Gimp.context_set_interpolation(Gimp.InterpolationType.CUBIC)
    Gimp.context_set_transform_direction(Gimp.TransformDirection.FORWARD)

    angle = {
      'unit': builtin_actions_utils.UNIT_DEGREE.name,
      'value': self._rotation_angle,
    }

    inserted_layer.transform_rotate(
      builtin_actions_utils.angle_to_radians(angle),
      True,
      0.0,
      0.0,
    )

    Gimp.context_pop()

  @staticmethod
  def _get_scale_fit_values(
        orig_width_pixels,
        orig_height_pixels,
        new_width_pixels,
        new_height_pixels,
  ):
    processed_new_width_pixels = new_width_pixels
    processed_new_height_pixels = round(
      orig_height_pixels * (new_width_pixels / orig_width_pixels))

    if processed_new_height_pixels > new_height_pixels:
      processed_new_height_pixels = new_height_pixels
      processed_new_width_pixels = round(
        orig_width_pixels * (new_height_pixels / orig_height_pixels))

    if processed_new_width_pixels == 0:
      processed_new_width_pixels = 1

    if processed_new_height_pixels == 0:
      processed_new_height_pixels = 1

    return processed_new_width_pixels, processed_new_height_pixels

  def _set_opacity(self, inserted_layer):
    if self._opacity < 100.0:
      inserted_layer.set_opacity(self._opacity)

  def _set_offsets(self, inserted_layer):
    orig_offsets = inserted_layer.get_offsets()
    inserted_layer.set_offsets(
      orig_offsets.offset_x + self._offsets['x'],
      orig_offsets.offset_y + self._offsets['y'],
    )

  def _tile(self, batcher, inserted_layer):
    if self._num_tiles > 1:
      inserted_layer.resize_to_image_size()
      pdb.plug_in_small_tiles(
        image=batcher.current_image,
        drawables=[inserted_layer],
        num_tiles=self._num_tiles,
      )


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


def on_after_add_insert_overlay_action(_actions, action, _orig_action_dict, conditions):
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

    _set_visible_for_placement_for_layers_with_color_tag(
      action['arguments/adjust_placement'],
      action['arguments/placement'],
    )

    action['arguments/adjust_placement'].connect_event(
      'value-changed',
      _set_visible_for_placement_for_layers_with_color_tag,
      action['arguments/placement'],
    )

    _set_visible_for_use_pattern(
      action['arguments/use_pattern'],
      action['arguments'],
    )

    action['arguments/use_pattern'].connect_event(
      'value-changed',
      _set_visible_for_use_pattern,
      action['arguments'],
    )

    action['arguments/use_pattern'].connect_event(
      'after-set-gui',
      _set_left_margin_for_use_pattern,
    )

    color_tag_tree_model = GimpUi.EnumComboBox.new_with_model(
      GimpUi.EnumStore.new(Gimp.ColorTag)).get_model()

    builtin_commands_common.set_up_display_name_change_for_command(
      _set_display_name_for_insert_overlay,
      action['arguments/insert_content'],
      action,
      [
        action['arguments/position'],
        action['arguments/color_tag'],
        color_tag_tree_model,
      ],
    )

    action['arguments/position'].connect_event(
      'value-changed',
      _set_display_name_for_insert_overlay_via_position,
      action,
      action['arguments/insert_content'],
      action['arguments/color_tag'],
      color_tag_tree_model,
    )

    action['arguments/color_tag'].connect_event(
      'value-changed',
      _set_display_name_for_insert_overlay_via_color_tag,
      action,
      action['arguments/insert_content'],
      action['arguments/position'],
      color_tag_tree_model,
    )

    if 'condition_name' in action['arguments']:
      action['arguments/condition_name'].gui.set_visible(False)

      _connect_changes_to_linked_without_color_tag_condition(
        action['arguments/condition_name'],
        conditions,
        action,
        color_tag_tree_model,
      )
      action['arguments/condition_name'].connect_event(
        'value-changed',
        _connect_changes_to_linked_without_color_tag_condition,
        conditions,
        action,
        color_tag_tree_model,
      )


def _set_visible_for_insert_overlay_arguments(
      insert_content_setting,
      arguments,
):
  is_content_type_file = insert_content_setting.value == ContentType.FILE
  is_content_type_text = insert_content_setting.value == ContentType.TEXT
  is_content_type_layers_for_color_tag = (
    insert_content_setting.value == ContentType.LAYERS_WITH_COLOR_TAG)

  arguments['image_file'].gui.set_visible(
    not arguments['use_pattern'].value and is_content_type_file)
  arguments['image_file_pattern'].gui.set_visible(
    arguments['use_pattern'].value and is_content_type_file)
  arguments['text'].gui.set_visible(
    not arguments['use_pattern'].value and is_content_type_text)
  arguments['text_pattern'].gui.set_visible(
    arguments['use_pattern'].value and is_content_type_text)
  arguments['color_tag'].gui.set_visible(is_content_type_layers_for_color_tag)
  arguments['use_pattern'].gui.set_visible(not is_content_type_layers_for_color_tag)
  arguments['text_font_family'].gui.set_visible(is_content_type_text)
  arguments['text_font_size'].gui.set_visible(is_content_type_text)
  arguments['text_font_color'].gui.set_visible(is_content_type_text)
  arguments['size'].gui.set_visible(not is_content_type_text)
  arguments['adjust_placement'].gui.set_visible(is_content_type_layers_for_color_tag)
  arguments['placement'].gui.set_visible(
    arguments['adjust_placement'].value or not is_content_type_layers_for_color_tag)


def _set_visible_for_placement_for_layers_with_color_tag(
      adjust_placement_setting,
      placement_setting,
):
  placement_setting.gui.set_visible(adjust_placement_setting.value)


def _set_visible_for_use_pattern(
      use_pattern_setting,
      arguments,
):
  is_content_type_file = arguments['insert_content'].value == ContentType.FILE
  is_content_type_text = arguments['insert_content'].value == ContentType.TEXT

  arguments['image_file'].gui.set_visible(
    not use_pattern_setting.value and is_content_type_file)
  arguments['image_file_pattern'].gui.set_visible(
    use_pattern_setting.value and is_content_type_file)
  arguments['text'].gui.set_visible(
    not use_pattern_setting.value and is_content_type_text)
  arguments['text_pattern'].gui.set_visible(
    use_pattern_setting.value and is_content_type_text)


def _set_left_margin_for_use_pattern(use_pattern_setting):
  if not use_pattern_setting.gui.is_null():
    use_pattern_setting.gui.widget.set_margin_start(constants.RELATED_WIDGETS_LEFT_MARGIN)


def _set_display_name_for_insert_overlay(
      insert_content_setting,
      action,
      position_setting,
      color_tag_setting,
      color_tag_tree_model,
):
  content = insert_content_setting.value
  position = position_setting.value
  color_tag_name = _get_color_tag_name(color_tag_setting.value, color_tag_tree_model)

  display_names = {
    (ContentType.FILE, builtin_actions_utils.InsertionPositions.BACKGROUND): _(
      'Insert Image as Background'),
    (ContentType.FILE, builtin_actions_utils.InsertionPositions.FOREGROUND): _(
      'Insert Image as Foreground'),
    (ContentType.TEXT, builtin_actions_utils.InsertionPositions.BACKGROUND): _(
      'Insert Text as Background'),
    (ContentType.TEXT, builtin_actions_utils.InsertionPositions.FOREGROUND): _(
      'Insert Text as Foreground'),
    (ContentType.LAYERS_WITH_COLOR_TAG, builtin_actions_utils.InsertionPositions.BACKGROUND): _(
      'Insert Layers ({}) as Background').format(color_tag_name),
    (ContentType.LAYERS_WITH_COLOR_TAG, builtin_actions_utils.InsertionPositions.FOREGROUND): _(
      'Insert Layers ({}) as Foreground').format(color_tag_name),
  }

  display_name = display_names.get((content, position), _('Insert Overlay (Watermark)'))
  action['display_name'].set_value(display_name)


def _set_display_name_for_insert_overlay_via_position(
      position_setting,
      action,
      insert_content_setting,
      color_tag_setting,
      color_tag_tree_model,
):
  _set_display_name_for_insert_overlay(
    insert_content_setting,
    action,
    position_setting,
    color_tag_setting,
    color_tag_tree_model,
  )


def _set_display_name_for_insert_overlay_via_color_tag(
      color_tag_setting,
      action,
      insert_overlay_insert_content_setting,
      insert_overlay_position_setting,
      color_tag_tree_model,
):
  _set_display_name_for_insert_overlay(
    insert_overlay_insert_content_setting,
    action,
    insert_overlay_position_setting,
    color_tag_setting,
    color_tag_tree_model,
  )


def _connect_changes_to_linked_without_color_tag_condition(
      condition_name_setting,
      conditions,
      insert_overlay_action,
      color_tag_tree_model,
):
  if condition_name_setting.value not in conditions:
    return

  without_color_tag_condition = conditions[condition_name_setting.value]

  # We expect the `condition_name` setting to be changed only once (when
  # the condition is added interactively). If it changed multiple times,
  # we would have to disconnect previous 'value-changed' events.

  _set_display_name_for_without_color_tag_condition(
    insert_overlay_action['arguments/color_tag'],
    without_color_tag_condition,
    color_tag_tree_model,
  )
  insert_overlay_action['arguments/color_tag'].connect_event(
    'value-changed',
    _set_display_name_for_without_color_tag_condition,
    without_color_tag_condition,
    color_tag_tree_model,
  )

  _set_color_tag_based_on_insert_overlay_action(
    insert_overlay_action['arguments/color_tag'],
    without_color_tag_condition['arguments/color_tag'],
  )
  insert_overlay_action['arguments/color_tag'].connect_event(
    'value-changed',
    _set_color_tag_based_on_insert_overlay_action,
    without_color_tag_condition['arguments/color_tag'],
  )

  insert_overlay_action['enabled'].connect_event(
    'value-changed',
    _set_enabled_and_sensitive_for_linked_command,
    without_color_tag_condition['enabled'],
    without_color_tag_condition['arguments/last_enabled_value'],
  )


def _set_display_name_for_without_color_tag_condition(
      insert_overlay_color_tag_setting,
      condition,
      color_tag_tree_model,
):
  color_tag = insert_overlay_color_tag_setting.value

  # FOR TRANSLATORS: Think of "Only items without color tag: <color tag>" when translating this
  condition['display_name'].set_value(
    _('Without Color Tag: {}').format(_get_color_tag_name(color_tag, color_tag_tree_model)))


def _set_color_tag_based_on_insert_overlay_action(
      color_tag_setting_from_insert_overlay_action,
      color_tag_setting_from_without_color_tag_condition,
):
  color_tag_setting_from_without_color_tag_condition.set_value(
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


def _get_color_tag_name(color_tag, color_tag_tree_model):
  return color_tag_tree_model[int(color_tag)][1]


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
      'type': 'name_pattern',
      'name': 'image_file_pattern',
      'default_value': '[image file]',
      'display_name': _('Image pattern'),
      'description': _('This way, you can insert different overlays for each input.'),
      'gui_type_kwargs': {
        'regexes': ['image file'],
      },
    },
    {
      'type': 'string',
      'name': 'text',
      'default_value': '© Copyright',
      'display_name': _('Text'),
    },
    {
      'type': 'name_pattern',
      'name': 'text_pattern',
      'display_name': _('Text pattern'),
      'default_value': '© Copyright [current date]',
      'gui_type_kwargs': {
        'regexes': ['image file'],
      },
    },
    {
      'type': 'enum',
      'name': 'color_tag',
      'enum_type': Gimp.ColorTag,
      'excluded_values': [Gimp.ColorTag.NONE],
      'display_name': _('Color tag'),
      'default_value': Gimp.ColorTag.BLUE,
    },
    {
      'type': 'bool',
      'name': 'use_pattern',
      'default_value': False,
      'display_name': _('Use pattern'),
      'description': _('Using a pattern allows inserting different files or text for each input.'),
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
          placeholders_.ALL_IMAGE_PLACEHOLDERS: 'width',
          placeholders_.ALL_LAYER_PLACEHOLDERS: 'width',
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
      'type': 'dimension',
      'name': 'size',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
      },
      'min_value': 0.0,
      'percent_placeholder_names': [],
      'display_name': _('Size'),
      'description': _(
        'Aspect ratio is preserved.'
        ' For absolute units, the inserted layer is scaled to fit'
        ' within the specified size (maximum width or height).'
      ),
    },
    {
      'type': 'double',
      'name': 'opacity',
      'default_value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    },
    {
      'type': 'double',
      'name': 'rotation_angle',
      'default_value': 0.0,
      'min_value': 0.0,
      'max_value': 360.0,
      'display_name': _('Rotation angle (degrees)'),
      'tags': [commands.MORE_OPTIONS_TAG],
    },
    {
      'type': 'bool',
      'name': 'adjust_placement',
      'default_value': True,
      'display_name': _('Adjust placement'),
    },
    {
      'type': 'anchor',
      'name': 'placement',
      'default_value': builtin_actions_utils.AnchorPoints.BOTTOM_RIGHT,
      'items': list(builtin_actions_utils.ANCHOR_POINTS_ITEMS_AND_DISPLAY_NAMES),
      'display_name': _('Placement'),
    },
    {
      'type': 'coordinates',
      'name': 'offsets',
      'default_value': {
        'x': 0.0,
        'y': 0.0,
      },
      'display_name': _('Offsets (X and Y)'),
      'tags': [commands.MORE_OPTIONS_TAG],
    },
    {
      'type': 'int',
      'name': 'num_tiles',
      'default_value': 1,
      'display_name': _('Number of tiles'),
      'description': _('Set this to a value greater than 1 to enable tiling.'),
      'min_value': 1,
      'max_value': 6,
      'tags': [commands.MORE_OPTIONS_TAG],
    },
    {
      'type': 'choice',
      'name': 'position',
      'default_value': builtin_actions_utils.InsertionPositions.FOREGROUND,
      'display_name': _('Position'),
      'items': [
        (builtin_actions_utils.InsertionPositions.FOREGROUND, _('Foreground')),
        (builtin_actions_utils.InsertionPositions.BACKGROUND, _('Background')),
      ],
      'gui_type': 'radio_button_box',
    },
  ],
}

INSERT_OVERLAY_FOR_LAYERS_DICT = utils.semi_deep_copy(INSERT_OVERLAY_FOR_IMAGES_DICT)
INSERT_OVERLAY_FOR_LAYERS_DICT.update({
  'name': 'insert_overlay_for_layers',
  'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
})
INSERT_OVERLAY_FOR_LAYERS_DICT['arguments'][0]['items'] = [
  (ContentType.FILE, _('File')),
  (ContentType.TEXT, _('Text')),
  (ContentType.LAYERS_WITH_COLOR_TAG, _('Layers with color tag')),
]
INSERT_OVERLAY_FOR_LAYERS_DICT['arguments'].extend([
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'gui_type': None,
      'tags': ['ignore_reset'],
    },
    {
      'type': 'string',
      'name': 'condition_name',
      'default_value': '',
      'gui_type': None,
    },
])
