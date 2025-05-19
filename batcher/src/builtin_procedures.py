"""Built-in plug-in procedures."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

import pygimplib as pg

from src import background_foreground
from src import builtin_actions_common
from src import export as export_
from src import overwrite
from src import placeholders as placeholders_
from src import renamer as renamer_
from src import utils
from src.procedure_groups import *


def set_selected_and_current_layer(batcher):
  # If an image has no layers, there is nothing we do here. An exception may
  # be raised if a procedure requires at least one layer. An empty image
  # could occur e.g. if all layers were removed by the previous procedures.

  image = batcher.current_image

  if image is None or not image.is_valid():
    # The image does not exist anymore and there is nothing we can do.
    return

  if batcher.current_layer.is_valid():
    image.set_selected_layers([batcher.current_layer])
  else:
    selected_layers = image.get_selected_layers()

    if selected_layers:
      # There is no way to know which layer is the "right" one, so we resort to
      # taking the first.
      selected_layer = selected_layers[0]

      if selected_layer.is_valid():
        # The selected layer(s) may have been set by the procedure.
        batcher.current_layer = selected_layer
      else:
        image_layers = image.get_layers()
        if image_layers:
          # There is no way to know which layer is the "right" one, so we resort
          # to taking the first.
          batcher.current_layer = image_layers[0]
          image.set_selected_layers([image_layers[0]])


def set_selected_and_current_layer_after_action(batcher):
  action_applied = yield
  
  if action_applied or action_applied is None:
    set_selected_and_current_layer(batcher)


def sync_item_name_and_layer_name(layer_batcher):
  yield
  
  if layer_batcher.process_names and not layer_batcher.is_preview:
    layer_batcher.current_item.name = layer_batcher.current_layer.get_name()


def preserve_layer_locks_between_actions(layer_batcher):
  # We assume `edit_mode` is `True`, we can therefore safely use `Item.raw`.
  # We need to use `Item.raw` for parents as well.
  item = layer_batcher.current_item
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


def align_and_offset_layers(
      batcher,
      layers_to_align,
      reference_object,
      reference_layer,
      horizontal_align,
      vertical_align,
      x_offset,
      x_offset_unit,
      y_offset,
      y_offset_unit,
):
  image_width = batcher.current_image.get_width()
  image_height = batcher.current_image.get_height()

  if reference_layer is not None:
    ref_layer_x, ref_layer_y = reference_layer.get_offsets()[1:]
    ref_layer_width = reference_layer.get_width()
    ref_layer_height = reference_layer.get_height()
  else:
    ref_layer_x = 0
    ref_layer_y = 0
    ref_layer_width = 1
    ref_layer_height = 1

  for layer in layers_to_align:
    new_x, new_y = layer.get_offsets()[1:]

    if horizontal_align == HorizontalAlignments.LEFT:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_x = 0
      elif reference_object == AlignReferenceObjects.LAYER:
        new_x = ref_layer_x
    elif horizontal_align == HorizontalAlignments.CENTER:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_x = (image_width - layer.get_width()) // 2
      elif reference_object == AlignReferenceObjects.LAYER:
        new_x = ref_layer_x + (ref_layer_width - layer.get_width()) // 2
    elif horizontal_align == HorizontalAlignments.RIGHT:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_x = image_width - layer.get_width()
      elif reference_object == AlignReferenceObjects.LAYER:
        new_x = ref_layer_x + ref_layer_width - layer.get_width()

    if vertical_align == VerticalAlignments.TOP:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_y = 0
      elif reference_object == AlignReferenceObjects.LAYER:
        new_y = ref_layer_y
    elif vertical_align == VerticalAlignments.CENTER:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_y = (image_height - layer.get_height()) // 2
      elif reference_object == AlignReferenceObjects.LAYER:
        new_y = ref_layer_y + (ref_layer_height - layer.get_height()) // 2
    elif vertical_align == VerticalAlignments.BOTTOM:
      if reference_object == AlignReferenceObjects.IMAGE:
        new_y = image_height - layer.get_height()
      elif reference_object == AlignReferenceObjects.LAYER:
        new_y = ref_layer_y + ref_layer_height - layer.get_height()

    if x_offset:
      if x_offset_unit == Units.PIXELS:
        new_x += round(x_offset)
      elif x_offset_unit == Units.PERCENT_IMAGE_WIDTH:
        new_x += round((image_width * x_offset) / 100)
      elif x_offset_unit == Units.PERCENT_IMAGE_HEIGHT:
        new_x += round((image_height * x_offset) / 100)
      elif x_offset_unit == Units.PERCENT_LAYER_WIDTH:
        new_x += round((ref_layer_width * x_offset) / 100)
      elif x_offset_unit == Units.PERCENT_LAYER_HEIGHT:
        new_x += round((ref_layer_height * x_offset) / 100)

    if y_offset:
      if y_offset_unit == Units.PIXELS:
        new_y += round(y_offset)
      elif y_offset_unit == Units.PERCENT_IMAGE_WIDTH:
        new_y += round((image_width * y_offset) / 100)
      elif y_offset_unit == Units.PERCENT_IMAGE_HEIGHT:
        new_y += round((image_height * y_offset) / 100)
      elif y_offset_unit == Units.PERCENT_LAYER_WIDTH:
        new_y += round((ref_layer_width * y_offset) / 100)
      elif y_offset_unit == Units.PERCENT_LAYER_HEIGHT:
        new_y += round((ref_layer_height * y_offset) / 100)

    layer.set_offsets(new_x, new_y)


def apply_opacity_from_group_layers(layer_batcher):
  new_layer_opacity = layer_batcher.current_layer.get_opacity() / 100.0

  raw_parent = layer_batcher.current_item.raw.get_parent()
  while raw_parent is not None:
    new_layer_opacity = new_layer_opacity * (raw_parent.get_opacity() / 100.0)
    raw_parent = raw_parent.get_parent()

  layer_batcher.current_layer.set_opacity(new_layer_opacity * 100.0)


def merge_filters(_batcher, layer):
  layer.merge_filters()


def merge_visible_layers(image_batcher, merge_type):
  image = image_batcher.current_image

  image.merge_visible_layers(merge_type)

  for layer in image.get_layers():
    if not layer.get_visible():
      image.remove_layer(layer)


def remove_folder_structure_from_item(batcher):
  item = batcher.current_item

  item.parents = []
  item.children = []


def remove_folder_structure_from_item_for_edit_layers(
      layer_batcher, consider_parent_visible=False):
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


def rename_image(image_batcher, pattern, rename_images=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern, rename_images, rename_folders)
  renamed_parents = set()

  while True:
    if rename_folders:
      for parent in image_batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(image_batcher, item=parent)
          renamed_parents.add(parent)

    if rename_images:
      image_batcher.current_item.name = renamer.rename(image_batcher)

    yield


def rename_layer(layer_batcher, pattern, rename_layers=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern, rename_layers, rename_folders)
  renamed_parents = set()

  while True:
    if rename_folders:
      for parent in layer_batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(layer_batcher, item=parent)
          renamed_parents.add(parent)

          if (layer_batcher.edit_mode
              and layer_batcher.process_names
              and not layer_batcher.is_preview):
            parent.raw.set_name(parent.name)

    if rename_layers:
      layer_batcher.current_item.name = renamer.rename(layer_batcher)

      if layer_batcher.process_names and not layer_batcher.is_preview:
        layer_batcher.current_layer.set_name(layer_batcher.current_item.name)

    yield


def resize_to_layer_size(_batcher, layers):
  if len(layers) == 1:
    layer = layers[0]

    layer_offset_x, layer_offset_y = layer.get_offsets()[1:]
    layer.get_image().resize(
      layer.get_width(), layer.get_height(), -layer_offset_x, -layer_offset_y)
  elif len(layers) > 1:
    image = layers[0].get_image()

    layer_offset_list = [layer.get_offsets()[1:] for layer in layers]

    min_x = min(offset[0] for offset in layer_offset_list)
    min_y = min(offset[1] for offset in layer_offset_list)

    max_x = max(offset[0] + layer.get_width() for layer, offset in zip(layers, layer_offset_list))
    max_y = max(offset[1] + layer.get_height() for layer, offset in zip(layers, layer_offset_list))

    image.resize(max_x - min_x, max_y - min_y, -min_x, -min_y)


def scale(
      batcher,
      object_to_scale,
      new_width,
      new_height,
      interpolation,
      local_origin,
      aspect_ratio,
      padding_color,
      set_image_resolution,
      image_resolution,
):
  if set_image_resolution:
    if isinstance(object_to_scale, Gimp.Image):
      object_to_scale.set_resolution(image_resolution['x'], image_resolution['y'])
    elif isinstance(object_to_scale, Gimp.Item):
      object_to_scale.get_image().set_resolution(image_resolution['x'], image_resolution['y'])

  new_width_pixels = _unit_to_pixels(batcher, new_width, 'width')
  new_height_pixels = _unit_to_pixels(batcher, new_height, 'height')

  orig_width_pixels = object_to_scale.get_width()
  orig_height_pixels = object_to_scale.get_height()

  if orig_width_pixels == 0:
    orig_width_pixels = 1

  if orig_height_pixels == 0:
    orig_height_pixels = 1

  if aspect_ratio in [AspectRatios.KEEP_ADJUST_WIDTH, AspectRatios.KEEP_ADJUST_HEIGHT]:
    processed_width_pixels, processed_height_pixels = _get_scale_keep_aspect_ratio_values(
      aspect_ratio,
      orig_width_pixels,
      orig_height_pixels,
      new_width_pixels,
      new_height_pixels)
  elif aspect_ratio in [AspectRatios.FIT, AspectRatios.FIT_WITH_PADDING]:
    processed_width_pixels, processed_height_pixels = _get_scale_fit_values(
      orig_width_pixels, orig_height_pixels, new_width_pixels, new_height_pixels)
  else:
    processed_width_pixels = new_width_pixels
    processed_height_pixels = new_height_pixels

  Gimp.context_push()
  Gimp.context_set_interpolation(interpolation)

  if processed_width_pixels == 0:
    processed_width_pixels = 1

  if processed_height_pixels == 0:
    processed_height_pixels = 1

  if isinstance(object_to_scale, Gimp.Image):
    object_to_scale.scale(processed_width_pixels, processed_height_pixels)
  else:
    object_to_scale.scale(processed_width_pixels, processed_height_pixels, local_origin)

  if aspect_ratio == AspectRatios.FIT_WITH_PADDING:
    _fill_with_padding(
      batcher,
      object_to_scale,
      new_width_pixels,
      new_height_pixels,
      padding_color,
    )

  Gimp.context_pop()


def _unit_to_pixels(batcher, dimension, dimension_name):
  if dimension['unit'] == Gimp.Unit.percent():
    placeholder_object = placeholders_.PLACEHOLDERS[dimension['percent_object']]
    gimp_object = placeholder_object.replace_args(None, batcher)

    if dimension_name == 'width':
      gimp_object_dimension = gimp_object.get_width()
    elif dimension_name == 'height':
      gimp_object_dimension = gimp_object.get_height()
    else:
      raise ValueError('value for dimension_name not valid')

    pixels = (dimension['percent_value'] / 100) * gimp_object_dimension
  elif dimension['unit'] == Gimp.Unit.pixel():
    pixels = dimension['pixel_value']
  else:
    image_resolution = batcher.current_image.get_resolution()
    if dimension_name == 'width':
      image_resolution_for_dimension = image_resolution.xresolution
    elif dimension_name == 'height':
      image_resolution_for_dimension = image_resolution.yresolution
    else:
      raise ValueError('value for dimension_name not valid')

    pixels = (
      dimension['other_value'] / dimension['unit'].get_factor() * image_resolution_for_dimension)

  int_pixels = round(pixels)

  if int_pixels <= 0:
    int_pixels = 1

  return int_pixels


def _get_scale_keep_aspect_ratio_values(
      aspect_ratio,
      orig_width_pixels,
      orig_height_pixels,
      new_width_pixels,
      new_height_pixels,
):
  if aspect_ratio == AspectRatios.KEEP_ADJUST_WIDTH:
    processed_new_width_pixels = new_width_pixels
    processed_new_height_pixels = round(
      orig_height_pixels * (processed_new_width_pixels / orig_width_pixels))
  elif aspect_ratio == AspectRatios.KEEP_ADJUST_HEIGHT:
    processed_new_height_pixels = new_height_pixels
    processed_new_width_pixels = round(
      orig_width_pixels * (processed_new_height_pixels / orig_height_pixels))
  else:
    raise ValueError('invalid value for dimension_to_keep; must be "width" or "height"')

  return processed_new_width_pixels, processed_new_height_pixels


def _get_scale_fit_values(
      orig_width_pixels, orig_height_pixels, new_width_pixels, new_height_pixels):
  processed_new_width_pixels = new_width_pixels
  processed_new_height_pixels = round(
    orig_height_pixels * (new_width_pixels / orig_width_pixels))

  if processed_new_height_pixels > new_height_pixels:
    processed_new_height_pixels = new_height_pixels
    processed_new_width_pixels = round(
      orig_width_pixels * (new_height_pixels / orig_height_pixels))

  return processed_new_width_pixels, processed_new_height_pixels


def _fill_with_padding(
      batcher,
      gimp_object,
      new_width_pixels,
      new_height_pixels,
      padding_color,
):
  if isinstance(gimp_object, Gimp.Image):
    drawable_with_padding = batcher.current_layer
    image_of_drawable_with_padding = gimp_object
  else:
    drawable_with_padding = gimp_object
    image_of_drawable_with_padding = gimp_object.get_image()

  object_width = gimp_object.get_width()
  object_height = gimp_object.get_height()

  if new_width_pixels > object_width:
    offset_x = (new_width_pixels - object_width) // 2
    offset_y = 0
    layer_to_fill_start_width = offset_x
    layer_to_fill_start_height = new_height_pixels
    layer_to_fill_end_width = offset_x + (new_width_pixels - object_width) % 2
    layer_to_fill_end_height = new_height_pixels
  else:
    offset_x = 0
    offset_y = (new_height_pixels - object_height) // 2
    layer_to_fill_start_width = new_width_pixels
    layer_to_fill_start_height = offset_y
    layer_to_fill_end_width = new_width_pixels
    layer_to_fill_end_height = offset_y + (new_height_pixels - object_height) % 2

  if isinstance(gimp_object, Gimp.Image):
    if new_width_pixels > object_width:
      layer_to_fill_start_offset_x = 0
      layer_to_fill_start_offset_y = 0
      layer_to_fill_end_offset_x = offset_x + object_width
      layer_to_fill_end_offset_y = offset_y
    else:
      layer_to_fill_start_offset_x = 0
      layer_to_fill_start_offset_y = 0
      layer_to_fill_end_offset_x = offset_x
      layer_to_fill_end_offset_y = offset_y + object_height

    gimp_object.resize(new_width_pixels, new_height_pixels, offset_x, offset_y)
  else:
    drawable_with_padding_offsets = gimp_object.get_offsets()

    if new_width_pixels > object_width:
      layer_to_fill_start_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_start_offset_y = drawable_with_padding_offsets.offset_y
      layer_to_fill_end_offset_x = drawable_with_padding_offsets.offset_x + object_width + offset_x
      layer_to_fill_end_offset_y = drawable_with_padding_offsets.offset_y
    else:
      layer_to_fill_start_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_start_offset_y = drawable_with_padding_offsets.offset_y
      layer_to_fill_end_offset_x = drawable_with_padding_offsets.offset_x
      layer_to_fill_end_offset_y = drawable_with_padding_offsets.offset_y + object_height + offset_y

    gimp_object.transform_translate(offset_x, offset_y)

  Gimp.context_set_foreground(pg.setting.ColorSetting.get_value_as_color(padding_color))
  Gimp.context_set_opacity(
    pg.setting.ColorSetting.get_value_as_color(padding_color).get_rgba().alpha * 100)

  if layer_to_fill_start_width != 0 and layer_to_fill_start_height != 0:
    layer_to_fill_start = Gimp.Layer.new(
      image_of_drawable_with_padding,
      drawable_with_padding.get_name(),
      layer_to_fill_start_width,
      layer_to_fill_start_height,
      Gimp.ImageType.RGBA_IMAGE,
      100.0,
      Gimp.LayerMode.NORMAL,
    )
    layer_to_fill_start.set_offsets(layer_to_fill_start_offset_x, layer_to_fill_start_offset_y)
    image_of_drawable_with_padding.insert_layer(
      layer_to_fill_start,
      drawable_with_padding.get_parent(),
      image_of_drawable_with_padding.get_item_position(drawable_with_padding) + 1,
    )
    layer_to_fill_start.edit_fill(Gimp.FillType.FOREGROUND)
    merged_drawable_with_padding = image_of_drawable_with_padding.merge_down(
      drawable_with_padding, Gimp.MergeType.EXPAND_AS_NECESSARY)
  else:
    merged_drawable_with_padding = drawable_with_padding

  if layer_to_fill_end_width != 0 and layer_to_fill_end_height != 0:
    layer_to_fill_end = Gimp.Layer.new(
      image_of_drawable_with_padding,
      merged_drawable_with_padding.get_name(),
      layer_to_fill_end_width,
      layer_to_fill_end_height,
      Gimp.ImageType.RGBA_IMAGE,
      100.0,
      Gimp.LayerMode.NORMAL,
    )
    layer_to_fill_end.set_offsets(layer_to_fill_end_offset_x, layer_to_fill_end_offset_y)
    image_of_drawable_with_padding.insert_layer(
      layer_to_fill_end,
      merged_drawable_with_padding.get_parent(),
      image_of_drawable_with_padding.get_item_position(merged_drawable_with_padding) + 1,
    )
    layer_to_fill_end.edit_fill(Gimp.FillType.FOREGROUND)
    image_of_drawable_with_padding.merge_down(
      merged_drawable_with_padding, Gimp.MergeType.EXPAND_AS_NECESSARY)


class AspectRatios:
  ASPECT_RATIOS = (
    STRETCH,
    KEEP_ADJUST_WIDTH,
    KEEP_ADJUST_HEIGHT,
    FIT,
    FIT_WITH_PADDING,
  ) = (
    'stretch',
    'keep_adjust_width',
    'keep_adjust_height',
    'fit',
    'fit_with_padding',
  )


class Units:
  UNITS = (
    PERCENT_IMAGE_WIDTH,
    PERCENT_IMAGE_HEIGHT,
    PERCENT_LAYER_WIDTH,
    PERCENT_LAYER_HEIGHT,
    PIXELS,
  ) = (
    'percentage_of_image_width',
    'percentage_of_image_height',
    'percentage_of_layer_width',
    'percentage_of_layer_height',
    'pixels',
  )


class HorizontalAlignments:
  HORIZONTAL_ALIGNMENTS = (
    KEEP,
    LEFT,
    CENTER,
    RIGHT,
  ) = (
    'keep',
    'left',
    'center',
    'right',
  )


class VerticalAlignments:
  VERTICAL_ALIGNMENTS = (
    KEEP,
    TOP,
    CENTER,
    BOTTOM,
  ) = (
    'keep',
    'top',
    'center',
    'bottom',
  )


class AlignReferenceObjects:
  ALIGN_REFERENCE_OBJECTS = (
    IMAGE,
    LAYER,
  ) = (
    'image',
    'layer',
  )


INTERACTIVE_OVERWRITE_MODES_LIST = [
  (overwrite.OverwriteModes.REPLACE, _('Replace')),
  (overwrite.OverwriteModes.SKIP, _('Skip')),
  (overwrite.OverwriteModes.RENAME_NEW, _('Rename new file')),
  (overwrite.OverwriteModes.RENAME_EXISTING, _('Rename existing file'))
]

INTERACTIVE_OVERWRITE_MODES = dict(INTERACTIVE_OVERWRITE_MODES_LIST)


_EXPORT_OVERWRITE_MODES_LIST = [
  (overwrite.OverwriteModes.ASK, _('Ask')),
  *INTERACTIVE_OVERWRITE_MODES_LIST
]


_EXPORT_PROCEDURE_DICT_FOR_CONVERT = {
  'name': 'export_for_convert',
  'function': export_.export,
  'display_name': _('Also export as...'),
  'description': _('Exports an image to another file format.'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, CONVERT_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
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
        (export_.FileFormatModes.USE_NATIVE_PLUGIN_VALUES, _('Interactively')),
        (export_.FileFormatModes.USE_EXPLICIT_VALUES, _('Use options below')),
      ],
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
      'default_value': 'each_item',
      'items': [
        (export_.ExportModes.EACH_ITEM, _('For each image')),
        (export_.ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER,
         _('For each top-level image or folder')),
        (export_.ExportModes.SINGLE_IMAGE, _('As a single image')),
      ],
      'display_name': _('Perform export:'),
    },
    {
      'type': 'name_pattern',
      'name': 'single_image_name_pattern',
      'default_value': _('Untitled'),
      'display_name': _('Image filename pattern'),
      'gui_type': 'name_pattern_entry',
    },
    {
      'type': 'bool',
      'name': 'use_file_extension_in_item_name',
      'default_value': False,
      'display_name': _('Use original file extension'),
    },
    {
      'type': 'bool',
      'name': 'convert_file_extension_to_lowercase',
      'default_value': False,
      'display_name': _('Convert file extension to lowercase'),
    },
    {
      'type': 'bool',
      'name': 'use_original_modification_date',
      'default_value': False,
      'display_name': _('Use original modification date'),
    },
  ],
}

_EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES = utils.semi_deep_copy(
  _EXPORT_PROCEDURE_DICT_FOR_CONVERT)

_EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES.update({
  'name': 'export_for_export_images',
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_IMAGES_GROUP],
})
_EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES['arguments'][5]['items'].pop(1)
del _EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES['arguments'][9]
del _EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES['arguments'][7]


_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS = utils.semi_deep_copy(
  _EXPORT_PROCEDURE_DICT_FOR_CONVERT)

_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS.update({
  'name': 'export_for_export_layers',
  'description': _('Exports a layer to another file format.'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_LAYERS_GROUP],
})
_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS['arguments'][5]['items'] = [
  (export_.ExportModes.EACH_ITEM, _('For each layer')),
  (export_.ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER, _('For each top-level layer or group')),
  (export_.ExportModes.SINGLE_IMAGE, _('As a single image')),
]
_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS['arguments'][6]['default_value'] = '[image name]'
_EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS['arguments'][7]['display_name'] = _(
  'Use file extension in layer name')
del _EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS['arguments'][9]

_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS = utils.semi_deep_copy(
  _EXPORT_PROCEDURE_DICT_FOR_CONVERT)

_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS.update({
  'name': 'export_for_edit_layers',
  'display_name': _('Export'),
  'description': _('Exports a layer to the specified file format.'),
  'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
})
_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS['arguments'][5]['items'] = [
  (export_.ExportModes.EACH_ITEM, _('For each layer')),
  (export_.ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER, _('For each top-level layer or group')),
  (export_.ExportModes.SINGLE_IMAGE, _('As a single image')),
]
_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS['arguments'][6]['default_value'] = '[image name]'
_EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS['arguments'][7]['display_name'] = _(
  'Use file extension in layer name')
del _EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS['arguments'][9]


_SCALE_PROCEDURE_DICT_FOR_IMAGES = {
  'name': 'scale_for_images',
  'function': scale,
  'display_name': _('Scale'),
  'display_options_on_create': True,
  'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
  'arguments': [
    {
      'type': 'placeholder_image_or_layer',
      'name': 'object_to_scale',
      'default_value': 'current_image',
      'display_name': _('Apply to (image or layer):'),
    },
    {
      'type': 'dimension',
      'name': 'new_width',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('New width'),
    },
    {
      'type': 'dimension',
      'name': 'new_height',
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
        'percent_object': 'current_image',
      },
      'min_value': 0.0,
      'percent_placeholder_names': [
        'current_image', 'current_layer', 'background_layer', 'foreground_layer'],
      'display_name': _('New height'),
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
    },
    {
      'type': 'choice',
      'name': 'aspect_ratio',
      'default_value': AspectRatios.STRETCH,
      'items': [
        (AspectRatios.STRETCH, _('None (Stretch)')),
        (AspectRatios.KEEP_ADJUST_WIDTH, _('Keep, adjust width')),
        (AspectRatios.KEEP_ADJUST_HEIGHT, _('Keep, adjust height')),
        (AspectRatios.FIT, _('Fit')),
        (AspectRatios.FIT_WITH_PADDING, _('Fit with padding')),
      ],
      'display_name': _('Aspect ratio'),
    },
    {
      'type': 'color',
      'name': 'padding_color',
      'default_value': [0.0, 0.0, 0.0, 0.0],
      'display_name': _('Padding color'),
    },
    {
      'type': 'bool',
      'name': 'set_image_resolution',
      'default_value': False,
      'display_name': _('Set image resolution in DPI'),
    },
    {
      'type': 'resolution',
      'name': 'image_resolution',
      'default_value': {
        'x': 72.0,
        'y': 72.0,
      },
    },
  ],
}

_SCALE_PROCEDURE_DICT_FOR_LAYERS = utils.semi_deep_copy(_SCALE_PROCEDURE_DICT_FOR_IMAGES)

_SCALE_PROCEDURE_DICT_FOR_LAYERS.update({
  'name': 'scale_for_layers',
  'additional_tags': [EXPORT_LAYERS_GROUP, EDIT_LAYERS_GROUP],
})
_SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][0]['default_value'] = 'current_layer'
_SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][1]['default_value']['percent_object'] = (
  'current_layer')
_SCALE_PROCEDURE_DICT_FOR_LAYERS['arguments'][2]['default_value']['percent_object'] = (
  'current_layer')


_BUILTIN_PROCEDURES_LIST = [
  {
    'name': 'apply_opacity_from_group_layers',
    'function': apply_opacity_from_group_layers,
    'display_name': _('Apply opacity from group layers'),
    'description': _('Combines opacity from all parent group layers and the current layer.'),
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
    'name': 'align_and_offset_layers',
    'function': align_and_offset_layers,
    'display_name': _('Align and offset'),
    'description': _(
      'Aligns layer(s) with the image or, if specified, another layer.'
      '\n\nYou may specify additional offsets after the alignment is applied.'),
    'display_options_on_create': True,
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
    'arguments': [
      {
        'type': 'placeholder_layer_array',
        'name': 'layers_to_align',
        'element_type': 'layer',
        'default_value': 'current_layer_for_array',
        'display_name': _('Layers to align'),
      },
      {
        'type': 'choice',
        'name': 'reference_object',
        'default_value': AlignReferenceObjects.IMAGE,
        'items': [
          (AlignReferenceObjects.IMAGE, _('Image')),
          (AlignReferenceObjects.LAYER, _('Another layer')),
        ],
        'display_name': _('Object to align layers with'),
      },
      {
        'type': 'placeholder_layer',
        'name': 'reference_layer',
        'display_name': _('Another layer to align layers with'),
      },
      {
        'type': 'choice',
        'name': 'horizontal_align',
        'default_value': HorizontalAlignments.KEEP,
        'items': [
          (HorizontalAlignments.KEEP, _('Keep')),
          (HorizontalAlignments.LEFT, _('Left')),
          (HorizontalAlignments.CENTER, _('Center')),
          (HorizontalAlignments.RIGHT, _('Right')),
        ],
        'display_name': _('Horizontal alignment'),
      },
      {
        'type': 'choice',
        'name': 'vertical_align',
        'default_value': VerticalAlignments.KEEP,
        'items': [
          (VerticalAlignments.KEEP, _('Keep')),
          (VerticalAlignments.TOP, _('Top')),
          (VerticalAlignments.CENTER, _('Center')),
          (VerticalAlignments.BOTTOM, _('Bottom')),
        ],
        'display_name': _('Vertical alignment'),
      },
      {
        'type': 'double',
        'name': 'x_offset',
        'default_value': 0.0,
        'display_name': _('Additional X-offset'),
      },
      {
        'type': 'choice',
        'name': 'x_offset_unit',
        'default_value': Units.PIXELS,
        'items': [
          (Units.PERCENT_IMAGE_WIDTH, _('% of image width')),
          (Units.PERCENT_IMAGE_HEIGHT, _('% of image height')),
          (Units.PERCENT_LAYER_WIDTH, _('% of another layer width')),
          (Units.PERCENT_LAYER_HEIGHT, _('% of another layer height')),
          (Units.PIXELS, _('Pixels')),
        ],
        'display_name': _('Unit for the additional X-offset'),
      },
      {
        'type': 'double',
        'name': 'y_offset',
        'default_value': 0.0,
        'display_name': _('Additional Y-offset'),
      },
      {
        'type': 'choice',
        'name': 'y_offset_unit',
        'default_value': Units.PIXELS,
        'items': [
          (Units.PERCENT_IMAGE_WIDTH, _('% of image width')),
          (Units.PERCENT_IMAGE_HEIGHT, _('% of image height')),
          (Units.PERCENT_LAYER_WIDTH, _('% of another layer width')),
          (Units.PERCENT_LAYER_HEIGHT, _('% of another layer height')),
          (Units.PIXELS, _('Pixels')),
        ],
        'display_name': _('Unit for the additional Y-offset'),
      },
    ],
  },
  {
    'name': 'insert_background_for_images',
    'function': background_foreground.insert_background_from_file,
    'display_name': _('Insert background'),
    'description': _('Inserts the specified image behind the current layer.'),
    'display_options_on_create': True,
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
    'arguments': [
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
        'name': 'merge_procedure_name',
        'default_value': '',
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'insert_background_for_layers',
    'function': background_foreground.insert_background_from_color_tags,
    'display_name': _('Insert background'),
    'description': _('Inserts layers having the specified color tag behind the current layer.'),
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
        'type': 'tagged_items',
        'name': 'tagged_items',
        'default_value': [],
        'gui_type': None,
        'tags': ['ignore_reset'],
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
    'name': 'insert_foreground_for_images',
    'function': background_foreground.insert_foreground_from_file,
    'display_name': _('Insert foreground'),
    'description': _('Inserts the specified image in front of the current layer.'),
    'display_options_on_create': True,
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
    'arguments': [
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
        'name': 'merge_procedure_name',
        'default_value': '',
        'gui_type': None,
      },
    ],
  },
  {
    'name': 'insert_foreground_for_layers',
    'function': background_foreground.insert_foreground_from_color_tags,
    'display_name': _('Insert foreground'),
    'description': _(
      'Inserts layers having the specified color tag in front of the current layer.'),
    'display_options_on_create': True,
    'additional_tags': [EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
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
        'type': 'tagged_items',
        'name': 'tagged_items',
        'default_value': [],
        'gui_type': None,
        'tags': ['ignore_reset'],
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
  _EXPORT_PROCEDURE_DICT_FOR_CONVERT,
  _EXPORT_PROCEDURE_DICT_FOR_EXPORT_IMAGES,
  _EXPORT_PROCEDURE_DICT_FOR_EXPORT_LAYERS,
  _EXPORT_PROCEDURE_DICT_FOR_EDIT_LAYERS,
  {
    'name': 'merge_background',
    'function': background_foreground.merge_background,
    'display_name': _('Merge background'),
    # This procedure is added/removed automatically alongside `insert_background_for_*`.
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
    # This procedure is added/removed automatically alongside `insert_foreground_for_*`.
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
    'name': 'merge_filters',
    'function': merge_filters,
    'display_name': _('Merge filters'),
    'description': _('Merges all visible filters (layer effects) in the specified layer.'),
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EDIT_LAYERS_GROUP, EXPORT_LAYERS_GROUP],
    'arguments': [
      {
        'type': 'placeholder_layer',
        'name': 'layer',
        'display_name': _('Layer'),
      },
    ],
  },
  {
    'name': 'merge_visible_layers',
    'function': merge_visible_layers,
    'display_name': _('Merge visible layers'),
    'description': _(
      'Merges all visible layers within the image into a single layer. Invisible layers are'
      ' removed.\n\nThis is useful if the image contains multiple layers and you want to apply'
      ' filters (layer effects) or other procedures on the entire image.'),
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP],
    'arguments': [
      {
        'type': 'enum',
        'name': 'merge_type',
        'enum_type': Gimp.MergeType,
        'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
        'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
        'display_name': _('Merge type'),
      },
    ],
  },
  {
    'name': 'remove_folder_structure',
    'function': remove_folder_structure_from_item,
    'display_name': _('Remove folder structure'),
    'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, CONVERT_GROUP, EXPORT_LAYERS_GROUP],
  },
  {
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
  },
  {
    'name': 'rename_for_convert',
    'function': rename_image,
    'display_name': _('Rename'),
    'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, CONVERT_GROUP],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'name_pattern',
        'name': 'pattern',
        'default_value': '[image name]',
        'display_name': _('Image filename pattern'),
        'gui_type': 'name_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'rename_images',
        'default_value': True,
        'display_name': _('Rename images'),
      },
      {
        'type': 'bool',
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename folders'),
      },
    ],
  },
  {
    'name': 'rename_for_export_images',
    'function': rename_image,
    'display_name': _('Rename'),
    'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_IMAGES_GROUP],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': 'name_pattern',
        'name': 'pattern',
        'default_value': '[image name]',
        'display_name': _('Image filename pattern'),
        'gui_type': 'name_pattern_entry',
      },
      {
        'type': 'bool',
        'name': 'rename_images',
        'default_value': True,
        'display_name': _('Rename images'),
      },
    ],
  },
  {
    'name': 'rename_for_export_layers',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EXPORT_LAYERS_GROUP],
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
      },
      {
        'type': 'bool',
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename folders'),
      },
    ],
  },
  {
    'name': 'rename_for_edit_layers',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [builtin_actions_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
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
      },
      {
        'type': 'bool',
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename group layers'),
      },
    ],
  },
  _SCALE_PROCEDURE_DICT_FOR_IMAGES,
  _SCALE_PROCEDURE_DICT_FOR_LAYERS,
  {
    'name': 'resize_to_layer_size',
    'function': resize_to_layer_size,
    'display_name': _('Resize to layer size'),
    'description': _('Resizes the image canvas to fit the specified layer(s).'),
    'additional_tags': [CONVERT_GROUP, EXPORT_IMAGES_GROUP, EXPORT_LAYERS_GROUP],
    'arguments': [
      {
        'type': 'placeholder_layer_array',
        'name': 'layers',
        'element_type': 'layer',
        'default_value': 'current_layer_for_array',
        'display_name': _('Layers'),
      },
    ]
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
