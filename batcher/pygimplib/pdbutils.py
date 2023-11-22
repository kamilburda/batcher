"""Additional functions dealing with GIMP objects (images, layers, etc.) not
available in the GIMP procedural database (PDB) or the GIMP API.
"""

from collections.abc import Iterable
import contextlib
import os
from typing import List, Optional, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from . import constants as pgconstants
from . import invocation as pginvocation
from .pypdb import pdb


def duplicate_image_without_contents(image: Gimp.Image) -> Gimp.Image:
  """Duplicates an image without layers, channels or vectors (keeping only
  metadata such as dimensions, base type, parasites and more).
  
  For a full image copy, use the ``'gimp-image-duplicate'`` procedure.
  """
  # The code is taken from:
  # https://gitlab.gnome.org/GNOME/gimp/-/blob/master/app/core/gimpimage-duplicate.c
  new_image = Gimp.Image.new_with_precision(
    image.get_width(), image.get_height(), image.get_base_type(), image.get_precision())

  new_image.undo_disable()

  image_file = image.get_file()
  if image_file is not None:
    new_image.set_file(image_file)

  new_image.set_resolution(*image.get_resolution()[1:])
  pdb.gimp_image_set_unit(new_image, pdb.gimp_image_get_unit(image))

  _copy_image_parasites(image, new_image)

  color_profile = image.get_color_profile()
  if color_profile is not None:
    new_image.set_color_profile(color_profile)

  if image.get_base_type() == Gimp.ImageBaseType.INDEXED:
    new_image.set_colormap(*image.get_colormap())

  _copy_image_guides(image, new_image)

  _copy_image_sample_points(image, new_image)

  _copy_image_grid(image, new_image)

  image_metadata = image.get_metadata()
  if image_metadata is not None:
    new_image.set_metadata(image_metadata)

  new_image.undo_enable()

  return new_image


def _copy_image_parasites(image, new_image):
  for parasite_name in image.get_parasite_list():
    parasite = image.get_parasite(parasite_name)
    new_image.attach_parasite(
      Gimp.Parasite.new(parasite.get_name(), parasite.get_flags(), parasite.get_data()))


def _copy_image_guides(image, new_image):
  current_guide = image.find_next_guide(0)

  while current_guide != 0:
    orientation = image.get_guide_orientation(current_guide)
    position = image.get_guide_position(current_guide)

    if orientation == Gimp.OrientationType.HORIZONTAL:
      new_image.add_hguide(position)
    elif orientation == Gimp.OrientationType.VERTICAL:
      new_image.add_vguide(position)

    current_guide = image.find_next_guide(current_guide)


def _copy_image_sample_points(image, new_image):
  current_sample_point = image.find_next_sample_point(0)

  while current_sample_point != 0:
    new_image.add_sample_point(*image.get_sample_point_position(current_sample_point))
    current_sample_point = image.find_next_sample_point(current_sample_point)


def _copy_image_grid(image, new_image):
  new_image.grid_set_background_color(image.grid_get_background_color()[1])
  new_image.grid_set_foreground_color(image.grid_get_foreground_color()[1])
  new_image.grid_set_offset(*image.grid_get_offset()[1:])
  new_image.grid_set_spacing(*image.grid_get_spacing()[1:])
  new_image.grid_set_style(image.grid_get_style())


def find_images_by_filepath(image_filepath: str) -> List[Gimp.Image]:
  """Returns a list of currently opened images in GIMP matching the given file
  path.

  File path matching is performed via ``Gimp.Image.get_file()``.
  """
  return [
    image for image in Gimp.list_images()
    if image.get_file() and image.get_file().get_path() == image_filepath
  ]


def find_image_by_filepath(image_filepath: str, index: int = 0) -> Union[Gimp.Image, None]:
  """Returns the currently opened image in GIMP matching the given file path.
  
  If no match is found, ``None`` is returned.
  
  File path matching is performed via ``Gimp.Image.get_file()``.
  
  For multiple matches, the first matching image is returned by default. There
  may be multiple opened images from the same file path, but there is no way to
  tell which image is the one the user desires to work with. To adjust which
  image to return, pass a custom ``index`` value indicating the position to
  return. If the index is out of bounds, the highest possible index is returned
  given a positive value and the lowest possible index given a negative value.
  """
  images = find_images_by_filepath(image_filepath)
  if images:
    if index > 0:
      index = min(index, len(images) - 1)
    elif index < 0:
      index = max(index, -len(images))
    
    image = images[index]
  else:
    image = None
  
  return image


def get_item_from_image_and_item_path(
      image: Gimp.Image, item_class_name: str, item_path: str,
) -> Union[Gimp.Item, None]:
  """Returns a ``Gimp.Item`` given the image, item class name and item path.
  
  ``item_class_name`` corresponds to one of the GIMP item classes, e.g.
  ``'Layer'`` or ``'Channel'``.
  
  ``item_path`` consists of the item name and all of its parent layer groups,
  separated by ``'/'``. For example, if the item name is``' 'Left''`` its
  parent groups are ``'Hands'`` (immediate parent) and ``'Body'`` (parent of
  ``'Hands'``), then the item path is ``'Body/Hands/Left'``.
  """
  item_path_components = item_path.split(pgconstants.GIMP_ITEM_PATH_SEPARATOR)
  
  if len(item_path_components) < 1:
    return None
  
  matching_image_child = _find_item_by_name_in_children(
    item_path_components[0], _get_children_from_image(image, item_class_name))
  if matching_image_child is None:
    return None
  
  if len(item_path_components) == 1:
    return matching_image_child
  
  parent = matching_image_child
  matching_item = None
  for parent_or_item_name in item_path_components[1:]:
    matching_item = _find_item_by_name_in_children(parent_or_item_name, parent.list_children())
    
    if matching_item is None:
      return None
    
    parent = matching_item
  
  return matching_item


def _find_item_by_name_in_children(item_name, children):
  for child in children:
    if child.get_name() == item_name:
      return child
  
  return None


def _get_children_from_image(image, item_class_name):
  item_type = getattr(Gimp, item_class_name, None)
  
  if item_type == Gimp.Layer:
    return image.list_layers()
  elif item_type == Gimp.Channel:
    return image.list_channels()
  elif item_type == Gimp.Vectors:
    return image.list_vectors()
  else:
    raise TypeError(
      f'invalid item type "{item_class_name}"; must be Layer, Channel or Vectors')


def get_item_as_path(item: Gimp.Item, include_image: bool = True) -> Union[List[str], None]:
  """Returns a ``Gimp.Item`` instance as a list of
  ``[item class name, item path]`` or
  ``[image file path, item class name, item path]``.
  
  Item class name and item path are described in
  ``get_item_from_image_and_item_path()``.
  """
  if item is None:
    return None
  
  item_as_path = []
  
  if include_image:
    if item.get_image() is not None and item.get_image().get_file() is not None:
      item_as_path.append(item.get_image().get_file().get_path())
    else:
      return None

  parents = _get_item_parents(item)
  item_path = pgconstants.GIMP_ITEM_PATH_SEPARATOR.join(
    parent_or_item.get_name() for parent_or_item in parents + [item])
  
  item_as_path.extend([type(item).__name__, item_path])
  
  return item_as_path


def _get_item_parents(item):
  parents = []
  current_parent = item.get_parent()
  while current_parent is not None:
    parents.insert(0, current_parent)
    current_parent = current_parent.get_parent()
  
  return parents


def try_delete_image(image: Gimp.Image):
  """Deletes the specified image if it exists and is valid."""
  if image.is_valid():
    image.delete()


def load_layer(
      filepath: str,
      image: Gimp.Image,
      strip_file_extension: bool = False,
) -> Gimp.Layer:
  """Loads an image as a layer given its file path to an existing image.

  This is a wrapper for ``Gimp.file_load_layer`` with additional parameters.
  The loaded layer is also inserted at the end of the image.

  The layer name corresponds to the file name (base name of the file path).
  If ``strip_file_extension`` is ``True``, the file extension from the layer
  name is removed.

  If the file contains multiple layers, you may customize the index of the
  desired layer to load (``layer_to_load_index``). Only top-level layers are
  supported (i.e. not layers inside layer groups). If the index is greater
  than the number of layers in the loaded image or is negative, the last
  layer is loaded.
  """
  layer = Gimp.file_load_layer(
    Gimp.RunMode.NONINTERACTIVE, image, Gio.file_new_for_path(filepath))

  layer_name = os.path.basename(filepath)
  if strip_file_extension:
    layer_name = os.path.splitext(layer_name)[0]
  layer.set_name(layer_name)

  image.insert_layer(layer, None, len(image.list_layers()))

  return layer


def load_layers(
      filepaths: Iterable[str],
      image: Optional[Gimp.Image] = None,
      strip_file_extension: bool = False,
) -> Gimp.Image:
  """Loads multiple layers to one image and returns the image.
  
  The layers are loaded at the end of the image.
  
  If ``image`` is ``None``, a new image is created. If ``image`` is not
  ``None``, the layers are loaded to the specified image.
  
  The layer names correspond to the file names (base names of the file paths).
  If ``strip_file_extension`` is ``True``, file extensions from the layer
  names are removed.
  """
  create_new_image = image is None

  if create_new_image:
    image = Gimp.Image.new(1, 1, Gimp.ImageBaseType.RGB)
  
  for filepath in filepaths:
    load_layer(filepath, image, strip_file_extension)
  
  if create_new_image:
    image.resize_to_layers()
  
  return image


def copy_and_paste_layer(
      layer: Gimp.Layer,
      image: Gimp.Image,
      parent: Optional[Gimp.Layer] = None,
      position: int = 0,
      remove_lock_attributes: bool = False,
      set_visible: bool = False,
      merge_group: bool = False,
) -> Gimp.Layer:
  """Copies the specified layer into the specified image and returns the layer
  copy.
  
  If ``parent`` is ``None``, the layer is inserted in the main stack (outside
  any layer group).
  
  If ``remove_lock_attributes`` is ``True``, all lock-related attributes are
  removed (lock position, alpha channel, etc.) for the layer copy.
  
  If ``set_visible`` is ``True``, the layer's visible state is set to ``True``.
  
  If ``merge_group`` is ``True`` and the layer is a group, the group is
  merged into a single layer.
  """
  layer_copy = Gimp.Layer.new_from_drawable(layer, image)
  image.insert_layer(layer_copy, parent, position)
  
  if remove_lock_attributes:
    layer_copy.set_lock_content(False)
    layer_copy.set_lock_position(False)
    layer_copy.set_lock_visibility(False)
    layer_copy.set_lock_alpha(False)
  
  if set_visible:
    layer_copy.set_visible(True)
  
  if merge_group and layer_copy.is_group():
    layer_copy = image.merge_layer_group(layer_copy)
  
  return layer_copy


def compare_layers(
      layers: Iterable[Gimp.Layer],
      compare_alpha_channels: bool = True,
      compare_has_alpha: bool = False,
      apply_layer_attributes: bool = True,
      apply_layer_masks: bool = True,
) -> bool:
  """Returns ``True`` if the contents of all specified layers or groups are
  identical.

  The default values of the optional parameters correspond to how the layers
  are displayed in the image canvas.

  If ``compare_alpha_channels`` is ``True``, alpha channels are also compared.

  If ``compare_has_alpha`` is ``True``, the presence of alpha channels in all
  layers is compared. If some layers have alpha channels and others do not,
  ``False`` is returned.

  If ``apply_layer_attributes`` is ``True``, layer attributes (opacity,
  mode) are taken into consideration when comparing, otherwise they are ignored.

  If ``apply_layer_masks`` is ``True``, layer masks are applied if they are
  enabled. If the masks are disabled or ``apply_layer_masks`` is ``False``,
  the layer masks are ignored.
  """
  
  def _copy_layers(image, layers, parent=None, position=0):
    layer_group = Gimp.Layer.group_new(image)
    image.insert_layer(layer_group, parent, position)
    
    for layer in layers:
      copy_and_paste_layer(layer, image, layer_group, 0, remove_lock_attributes=True)
    
    for layer in layer_group.list_children():
      layer.set_visible(True)
    
    return layer_group
  
  def _process_layers(image, layer_group, apply_layer_attributes, apply_layer_masks):
    for layer in layer_group.list_children():
      if layer.is_group():
        image.merge_layer_group(layer)
      else:
        if layer.get_opacity() != 100.0 or layer.get_mode() != Gimp.LayerMode.NORMAL:
          if apply_layer_attributes:
            layer = _apply_layer_attributes(image, layer, layer_group)
          else:
            layer.set_opacity(100.0)
            layer.set_mode(Gimp.LayerMode.NORMAL)
        
        if layer.get_mask() is not None:
          if apply_layer_masks and layer.get_apply_mask():
            layer.remove_mask(Gimp.MaskApplyMode.APPLY)
          else:
            layer.remove_mask(Gimp.MaskApplyMode.DISCARD)
  
  def _is_identical(layer_group):
    layer_group.list_children()[0].set_mode(Gimp.LayerMode.DIFFERENCE)
    
    for layer in layer_group.list_children()[1:]:
      layer.set_visible(False)
    
    for layer in layer_group.list_children()[1:]:
      layer.set_visible(True)
      
      histogram_data = layer_group.histogram(Gimp.HistogramChannel.VALUE, 1 / 255, 1.0)
      
      if histogram_data.percentile != 0.0:
        return False
      
      layer.set_visible(False)
    
    return True
  
  def _set_mask_to_layer(layer):
    Gimp.edit_copy([layer.get_mask()])
    floating_selection = Gimp.edit_paste(layer, True)[0]
    Gimp.floating_sel_anchor(floating_selection)
    layer.remove_mask(Gimp.MaskApplyMode.DISCARD)
  
  def _apply_layer_attributes(image, layer, parent_group):
    temp_group = Gimp.Layer.group_new(image)
    image.insert_layer(temp_group, parent_group, 0)
    image.reorder_item(layer, temp_group, 0)
    layer = image.merge_layer_group(temp_group)
    
    return layer
  
  def _prepare_for_comparison_of_alpha_channels(layer):
    _extract_alpha_channel_to_layer_mask(layer)
    _remove_alpha_channel(layer)
  
  def _extract_alpha_channel_to_layer_mask(layer):
    mask = layer.create_mask(Gimp.AddMaskType.ALPHA)
    layer.add_mask(mask)
    layer.set_apply_mask(False)
  
  def _remove_alpha_channel(layer):
    layer.flatten()
  
  layers = list(layers)
  
  all_layers_have_same_size = (
    all(layers[0].get_width() == layer.get_width() for layer in layers[1:])
    and all(layers[0].get_height() == layer.get_height() for layer in layers[1:]))
  if not all_layers_have_same_size:
    return False
  
  all_layers_are_same_image_type = all(layers[0].type() == layer.type() for layer in layers[1:])
  if compare_has_alpha and not all_layers_are_same_image_type:
    return False
  
  image = Gimp.Image.new(1, 1, Gimp.ImageBaseType.RGB)
  layer_group = _copy_layers(image, layers)
  image.resize_to_layers()
  _process_layers(image, layer_group, apply_layer_attributes, apply_layer_masks)
  
  has_alpha = False
  for layer in layer_group.list_children():
    if layer.has_alpha():
      has_alpha = True
      _prepare_for_comparison_of_alpha_channels(layer)
  
  identical = _is_identical(layer_group)
  
  if identical and compare_alpha_channels and has_alpha:
    for layer in layer_group.list_children():
      if layer.get_mask() is not None:
        _set_mask_to_layer(layer)
      else:
        layer.fill(Gimp.FillType.WHITE)
    
    identical = _is_identical(layer_group)
  
  image.delete()
  
  return identical


@contextlib.contextmanager
def redirect_messages(
      message_handler: Gimp.MessageHandlerType = Gimp.MessageHandlerType.MESSAGE_BOX
) -> contextlib.AbstractContextManager:
  """Temporarily redirects GIMP messages to the specified message handler.
  
  Use this function as a context manager:
    
    with redirect_messages():
      # do stuff
  """
  orig_message_handler_type = Gimp.message_get_handler()
  Gimp.message_set_handler(message_handler)
  
  try:
    yield
  finally:
    Gimp.message_set_handler(orig_message_handler_type)


class GimpMessageFile:
  """Class providing a file-like way to write output as GIMP messages.
  
  You can use this class to redirect output or error output to the GIMP console.
  """
  
  def __init__(
        self,
        message_handler: Gimp.MessageHandlerType = Gimp.MessageHandlerType.ERROR_CONSOLE,
        message_prefix: Optional[str] = None,
        message_delay_milliseconds: int = 0):
    """Initializes the instance.
    
    Args:
      message_handler:
        Handler to which messages are output. Possible values are the same as
        for ``Gimp.message_get_handler()``.
      message_prefix:
        If not ``None``, prepend this string to each message.
      message_delay_milliseconds:
        Delay in milliseconds before displaying the output. This is useful to
        aggregate multiple messages into one in order to avoid printing an
        excessive number of message headers.
    """
    self._message_handler = message_handler
    self._message_prefix = str(message_prefix) if message_prefix is not None else ''
    self._message_delay_milliseconds = message_delay_milliseconds
    
    self._buffer_size = 4096
    
    self._orig_message_handler_type = None
    
    self._message_buffer = self._message_prefix
  
  def write(self, data):
    # Message handler cannot be set upon instantiation as this method may be
    # called during GIMP initialization when the GIMP API is not fully
    # initialized yet.
    self._orig_message_handler_type = Gimp.message_get_handler()
    Gimp.message_set_handler(self._message_handler)
    
    self._write(data)
    
    self.write = self._write
  
  def _write(self, data):
    if len(self._message_buffer) < self._buffer_size:
      self._message_buffer += data
      pginvocation.timeout_add_strict(self._message_delay_milliseconds, self.flush)
    else:
      pginvocation.timeout_remove(self.flush)
      self.flush()
  
  def flush(self):
    Gimp.message(self._message_buffer)
    self._message_buffer = self._message_prefix
  
  def close(self):
    if self._orig_message_handler_type is not None:
      Gimp.message_set_handler(self._orig_message_handler_type)
