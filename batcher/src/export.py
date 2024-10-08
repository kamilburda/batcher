"""Built-in procedure to export a given item as an image."""

import collections
from collections.abc import Iterable
import os
from typing import Callable, Dict, Generator, List, Optional, Union, Tuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

import pygimplib as pg
from pygimplib import pdb

from src import exceptions
from src import file_formats as file_formats_
from src import overwrite
from src import renamer as renamer_
from src import uniquifier
from src.path import fileext
from src.path import validators as validators_


EXPORT_NAME_ITEM_STATE = 'export_name'


class FileFormatModes:

  FILE_FORMAT_MODES =(
    USE_NATIVE_PLUGIN_VALUES,
    USE_EXPLICIT_VALUES,
  ) = 0, 1


class ExportModes:
  
  EXPORT_MODES = (
    EACH_LAYER,
    EACH_TOP_LEVEL_LAYER_OR_GROUP,
    ENTIRE_IMAGE_AT_ONCE,
  ) = 0, 1, 2


def export(
      batcher: 'src.core.Batcher',
      output_directory: str = pg.utils.get_pictures_directory(),
      file_extension: str = 'png',
      file_format_mode: int = FileFormatModes.USE_EXPLICIT_VALUES,
      file_format_export_options: Optional[Dict] = None,
      overwrite_mode: int = overwrite.OverwriteModes.ASK,
      export_mode: int = ExportModes.EACH_LAYER,
      single_image_name_pattern: Optional[str] = None,
      use_file_extension_in_item_name: bool = False,
      convert_file_extension_to_lowercase: bool = False,
) -> Generator[None, None, None]:
  if file_format_export_options is None:
    file_format_export_options = {}

  item_uniquifier = uniquifier.ItemUniquifier()
  file_extension_properties = _FileExtensionProperties()
  processed_parents = set()
  default_file_extension = file_extension

  if export_mode == ExportModes.ENTIRE_IMAGE_AT_ONCE and single_image_name_pattern is not None:
    renamer_for_image = renamer_.ItemRenamer(single_image_name_pattern)
  else:
    renamer_for_image = None
  
  if export_mode != ExportModes.EACH_LAYER and batcher.process_export:
    multi_layer_image = pg.pdbutils.duplicate_image_without_contents(batcher.input_image)
    multi_layer_image.undo_freeze()
    batcher.invoker.add(_delete_image_on_cleanup, ['cleanup_contents'], [multi_layer_image])
  else:
    multi_layer_image = None
  
  if batcher.edit_mode and batcher.process_export:
    image_copy = pg.pdbutils.duplicate_image_without_contents(batcher.input_image)
    image_copy.undo_freeze()
    batcher.invoker.add(_delete_image_on_cleanup, ['cleanup_contents'], [image_copy])
  else:
    image_copy = batcher.current_image
  
  while True:
    item = batcher.current_item
    current_file_extension = default_file_extension
    
    item_to_process = item
    raw_item_to_process = batcher.current_raw_item
    
    if batcher.edit_mode and batcher.process_export:
      raw_item_to_process = _copy_layer(raw_item_to_process, image_copy, item)
    
    if multi_layer_image is None:
      image_to_process = image_copy
    else:
      image_to_process = multi_layer_image
    
    if export_mode == ExportModes.ENTIRE_IMAGE_AT_ONCE:
      if batcher.process_export:
        raw_item_to_process = _merge_and_resize_image(batcher, image_copy, raw_item_to_process)
        raw_item_to_process = _copy_layer(raw_item_to_process, image_to_process, item)
      
      if batcher.item_tree.next(item, with_folders=False) is not None:
        _refresh_image_copy_for_edit_mode(batcher, image_copy)
        yield
        continue
      else:
        item_to_process = pg.itemtree.Item(item.raw, pg.itemtree.TYPE_ITEM, [], [], None, None)
        if single_image_name_pattern is not None:
          item_to_process.name = renamer_for_image.rename(batcher, item_to_process)
        else:
          item_to_process.name = item.name
    elif export_mode == ExportModes.EACH_TOP_LEVEL_LAYER_OR_GROUP:
      if batcher.process_export:
        raw_item_to_process = _merge_and_resize_image(batcher, image_copy, raw_item_to_process)
        raw_item_to_process = _copy_layer(raw_item_to_process, image_to_process, item)
      
      current_top_level_item = _get_top_level_item(item)
      next_top_level_item = _get_top_level_item(batcher.item_tree.next(item, with_folders=False))
      
      if current_top_level_item == next_top_level_item:
        _refresh_image_copy_for_edit_mode(batcher, image_copy)
        yield
        continue
      else:
        item_to_process = current_top_level_item

    if batcher.process_names:
      item_to_process.save_state(EXPORT_NAME_ITEM_STATE)

      if use_file_extension_in_item_name:
        current_file_extension = _get_current_file_extension(
          item_to_process, default_file_extension, file_extension_properties)
      
      if convert_file_extension_to_lowercase:
        current_file_extension = current_file_extension.lower()
      
      _process_parent_names(item_to_process, item_uniquifier, processed_parents)
      _process_item_name(
        item_to_process,
        item_uniquifier,
        current_file_extension,
        default_file_extension,
        force_default_file_extension=False)
    
    if batcher.process_export:
      if export_mode == ExportModes.EACH_LAYER:
        raw_item_to_process = _merge_and_resize_image(batcher, image_copy, raw_item_to_process)
      else:
        image_to_process.resize_to_layers()

      if overwrite_mode == overwrite.OverwriteModes.ASK:
        overwrite_chooser = batcher.overwrite_chooser
      else:
        overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(overwrite_mode)

      chosen_overwrite_mode, export_status = _export_item(
        batcher,
        item_to_process,
        image_to_process,
        raw_item_to_process,
        output_directory,
        file_format_mode,
        file_format_export_options,
        default_file_extension,
        file_extension_properties,
        overwrite_chooser)
      
      if export_status == ExportStatuses.USE_DEFAULT_FILE_EXTENSION:
        if batcher.process_names:
          _process_item_name(
            item_to_process,
            item_uniquifier,
            current_file_extension,
            default_file_extension,
            force_default_file_extension=True)
        
        if batcher.process_export:
          chosen_overwrite_mode, _unused = _export_item(
            batcher,
            item_to_process,
            image_to_process,
            raw_item_to_process,
            output_directory,
            file_format_mode,
            file_format_export_options,
            default_file_extension,
            file_extension_properties,
            overwrite_chooser)
      
      if chosen_overwrite_mode != overwrite.OverwriteModes.SKIP:
        file_extension_properties[
          fileext.get_file_extension(_get_item_export_name(item_to_process))].processed_count += 1
        # Append the original raw item
        batcher._exported_raw_items.append(item_to_process.raw)
    
    if multi_layer_image is not None:
      _refresh_image(multi_layer_image)
    
    _refresh_image_copy_for_edit_mode(batcher, image_copy)
    
    yield


def _delete_image_on_cleanup(batcher, image):
  if batcher.process_export:
    if image is not None:
      pg.pdbutils.try_delete_image(image)


def _get_top_level_item(item):
  if item is not None and item.parents:
    return item.parents[0]
  else:
    return item


def _process_parent_names(item, item_uniquifier, processed_parents):
  for parent in item.parents:
    if parent not in processed_parents:
      parent.save_state(EXPORT_NAME_ITEM_STATE)

      _validate_name(parent)
      _uniquify_name(item_uniquifier, parent)

      processed_parents.add(parent)


def _process_item_name(
      item,
      item_uniquifier,
      current_file_extension,
      default_file_extension,
      force_default_file_extension,
):
  item_name = _get_item_export_name(item)

  processed_item_name = item_name

  if not force_default_file_extension:
    if current_file_extension == default_file_extension:
      processed_item_name = item_name + f'.{default_file_extension}'
    else:
      processed_item_name = fileext.get_filename_with_new_file_extension(
        item_name, current_file_extension, keep_extra_trailing_periods=True)
  else:
    processed_item_name = fileext.get_filename_with_new_file_extension(
      item_name, default_file_extension, keep_extra_trailing_periods=True)

  _set_item_export_name(item, processed_item_name)

  _validate_name(item)
  _uniquify_name(
    item_uniquifier,
    item,
    position=_get_unique_substring_position(
      _get_item_export_name(item), fileext.get_file_extension(_get_item_export_name(item))),
  )


def _get_current_file_extension(item, default_file_extension, file_extension_properties):
  item_file_extension = fileext.get_file_extension(_get_item_export_name(item))
  
  if item_file_extension and file_extension_properties[item_file_extension].is_valid:
    return item_file_extension
  else:
    return default_file_extension


def _merge_and_resize_image(batcher, image, raw_item):
  """Merges all layers in the current image into one.
  
  Merging is necessary for:
  * custom procedures inserting layers (background, foreground). Some file
    formats may discard all but one layer.
  * multi-layer images, with each layer containing background or foreground
    which are originally separate layers.
  """
  raw_item_name = raw_item.get_name()
  
  raw_item_merged = image.merge_visible_layers(Gimp.MergeType.EXPAND_AS_NECESSARY)
  raw_item_merged.resize_to_image_size()
  
  raw_item_merged.set_name(raw_item_name)
  image.set_selected_layers([raw_item_merged])
  
  if not batcher.edit_mode:
    batcher.current_raw_item = raw_item_merged
  
  return raw_item_merged


def _copy_layer(raw_item, dest_image, item):
  raw_item_copy = pg.pdbutils.copy_and_paste_layer(
    raw_item, dest_image, None, len(dest_image.list_layers()), True, True, True)

  # We use `item.name` instead of `_get_item_export_name()` so that the original
  # layer name is used in case of multi-layer export.
  raw_item_copy.set_name(item.name)
  
  return raw_item_copy


def _validate_name(item):
  _set_item_export_name(
    item,
    validators_.FilenameValidator.validate(_get_item_export_name(item)))


def _uniquify_name(item_uniquifier, item, position=None):
  item_name = _get_item_export_name(item)

  uniquified_item_name = item_uniquifier.uniquify(item, item_name=item_name, position=position)

  _set_item_export_name(item, uniquified_item_name)


def _get_item_export_name(item):
  item_state = item.get_named_state(EXPORT_NAME_ITEM_STATE)
  return item_state['name'] if item_state is not None else item.name


def _set_item_export_name(item, name):
  item.get_named_state(EXPORT_NAME_ITEM_STATE)['name'] = name


def _get_unique_substring_position(str_, file_extension):
  return len(str_) - len(f'.{file_extension}')


def _export_item(
      batcher,
      item,
      image,
      raw_item,
      output_directory,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      overwrite_chooser,
):
  output_filepath = _get_item_filepath(item, output_directory)
  file_extension = fileext.get_file_extension(_get_item_export_name(item))
  export_status = ExportStatuses.NOT_EXPORTED_YET

  chosen_overwrite_mode, output_filepath = overwrite.handle_overwrite(
    output_filepath,
    overwrite_chooser,
    _get_unique_substring_position(output_filepath, file_extension))

  batcher.progress_updater.update_text(_('Saving "{}"').format(output_filepath))
  
  if chosen_overwrite_mode == overwrite.OverwriteModes.CANCEL:
    raise exceptions.BatcherCancelError('cancelled')
  
  if chosen_overwrite_mode != overwrite.OverwriteModes.SKIP:
    _make_dirs(item, os.path.dirname(output_filepath), default_file_extension)
    
    export_status = _export_item_once_wrapper(
      batcher,
      _get_run_mode(batcher, file_format_mode, file_extension, file_extension_properties),
      image,
      raw_item,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties)
    
    if export_status == ExportStatuses.FORCE_INTERACTIVE:
      export_status = _export_item_once_wrapper(
        batcher,
        Gimp.RunMode.INTERACTIVE,
        image,
        raw_item,
        output_filepath,
        file_extension,
        file_format_mode,
        file_format_export_options,
        default_file_extension,
        file_extension_properties)
  
  return chosen_overwrite_mode, export_status


def _get_item_filepath(item, dirpath):
  """Returns a file path based on the specified directory path and the name of
  the item and its parents.
  
  The file path created has the following format:
    
    <directory path>/<item path components>/<item name>
  
  If the directory path is not an absolute path or is ``None``, the
  current working directory is prepended.
  
  Item path components consist of parents' item names, starting with the
  topmost parent.
  """
  if dirpath is None:
    dirpath = ''
  
  path = os.path.abspath(dirpath)
  
  path_components = [_get_item_export_name(parent) for parent in item.parents]
  if path_components:
    path = os.path.join(path, os.path.join(*path_components))
  
  return os.path.join(path, _get_item_export_name(item))


def _make_dirs(item, dirpath, default_file_extension):
  try:
    os.makedirs(dirpath, exist_ok=True)
  except OSError as e:
    try:
      message = e.strerror
      if e.filename is not None:
        message += f': "{e.filename}"'
    except (IndexError, AttributeError):
      message = str(e)
    
    raise exceptions.InvalidOutputDirectoryError(
      message, _get_item_export_name(item), default_file_extension)


def _export_item_once_wrapper(
      batcher,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
):
  with batcher.export_context_manager(
         run_mode, image, raw_item, output_filepath,
         *batcher.export_context_manager_args, **batcher.export_context_manager_kwargs):
    export_status = _export_item_once(
      batcher,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties)
  
  return export_status


def _get_run_mode(batcher, file_format_mode, file_extension, file_extension_properties):
  if file_format_mode == FileFormatModes.USE_EXPLICIT_VALUES:
    return Gimp.RunMode.NONINTERACTIVE

  file_extension_property = file_extension_properties[file_extension]
  if file_extension_property.is_valid and file_extension_property.processed_count > 0:
    return Gimp.RunMode.WITH_LAST_VALS
  else:
    return batcher.initial_export_run_mode


def _export_item_once(
      batcher,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
):
  def _raise_export_error(exception):
    raise exceptions.ExportError(str(exception), raw_item.get_name(), default_file_extension)

  try:
    _export_image(
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options)
  except pg.PDBProcedureError as e:
    if e.status == Gimp.PDBStatusType.CANCEL:
      raise exceptions.BatcherCancelError('cancelled')
    elif e.status == Gimp.PDBStatusType.CALLING_ERROR:
      if run_mode != Gimp.RunMode.INTERACTIVE:
        return ExportStatuses.FORCE_INTERACTIVE
      else:
        _raise_export_error(e)
    elif e.status == Gimp.PDBStatusType.EXECUTION_ERROR:
      if file_extension != default_file_extension:
        file_extension_properties[file_extension].is_valid = False
        return ExportStatuses.USE_DEFAULT_FILE_EXTENSION
      else:
        _raise_export_error(e)
    else:
      _raise_export_error(e)
  else:
    return ExportStatuses.EXPORT_SUCCESSFUL


def _export_image(
      run_mode: Gimp.RunMode,
      image: Gimp.Image,
      layer_or_layers: Union[Gimp.Layer, List[Gimp.Layer]],
      filepath: Union[str, Gio.File],
      file_extension: str,
      file_format_mode: int,
      file_format_export_options: Dict,
):
  if not isinstance(layer_or_layers, Iterable):
    layers = [layer_or_layers]
  else:
    layers = layer_or_layers

  if not isinstance(filepath, Gio.File):
    image_file = Gio.file_new_for_path(filepath)
  else:
    image_file = filepath

  layer_array = GObject.Value(Gimp.ObjectArray)
  Gimp.value_set_object_array(layer_array, Gimp.Layer, layers)

  export_func, kwargs = get_export_function(
    file_extension, file_format_mode, file_format_export_options)

  export_func(image, len(layers), layer_array.get_boxed(), image_file, run_mode=run_mode, **kwargs)

  return pdb.last_status


def get_export_function(
      file_extension: str,
      file_format_mode: int,
      file_format_export_options: Dict,
) -> Tuple[Callable, Dict]:
  """Returns the file export procedure and file format settings given the
  file extension.

  The same file format settings are returned if ``file_format_mode`` is
  ``FileFormatModes.USE_EXPLICIT_VALUES``. Otherwise, an empty dictionary is
  returned.

  If the file extension is not recognized, the default GIMP export procedure is
  returned (``gimp-file-save``).
  """
  if (file_format_mode == FileFormatModes.USE_EXPLICIT_VALUES
      and file_extension in file_formats_.FILE_FORMATS_DICT):
    file_format = file_formats_.FILE_FORMATS_DICT[file_extension]
    if file_format.export_procedure_name:
      file_format_option_kwargs = file_formats_.fill_and_get_file_format_options_as_kwargs(
        file_format_export_options, file_extension, 'export')

      if file_format_option_kwargs is not None:
        return getattr(pdb, file_format.export_procedure_name), file_format_option_kwargs

  return pdb.gimp_file_save, {}


def _refresh_image_copy_for_edit_mode(batcher, image_copy):
  if batcher.edit_mode and batcher.process_export:
    _refresh_image(image_copy)


def _refresh_image(image):
  for layer in image.list_layers():
    image.remove_layer(layer)


class _FileExtension:
  """Class holding properties for a file extension."""
  
  def __init__(self):
    self.is_valid = True
    """If ``True``, the file extension is valid and can be used in filenames
    for file export procedures.
    """
    self.processed_count = 0
    """Number of items with the file extension that have been exported."""


class _FileExtensionProperties:
  """Mapping of file extensions from `file_formats.FILE_FORMATS` to
  `_FileExtension` instances.
  
  File extension as a key is always converted to lowercase.
  """
  def __init__(self):
    self._properties = collections.defaultdict(_FileExtension)
    
    for file_format in file_formats_.FILE_FORMATS:
      # This ensures that the file format dialog will be displayed only once per
      # file format if multiple file extensions for the same format are used
      # (e.g. 'jpg', 'jpeg' or 'jpe' for the JPEG format).
      extension_properties = _FileExtension()
      for file_extension in file_format.file_extensions:
        self._properties[file_extension.lower()] = extension_properties
  
  def __getitem__(self, key):
    return self._properties[key.lower()]


class ExportStatuses:
  EXPORT_STATUSES = (
    NOT_EXPORTED_YET, EXPORT_SUCCESSFUL, FORCE_INTERACTIVE, USE_DEFAULT_FILE_EXTENSION
  ) = (0, 1, 2, 3)
