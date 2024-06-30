"""Built-in procedure to export a given item as an image."""

import collections
import os
from typing import Generator, Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib

import pygimplib as pg

from src import exceptions
from src import fileformats
from src import overwrite
from src import renamer as renamer_
from src import uniquifier
from src.path import fileext
from src.path import validators as validators_


class ExportModes:
  
  EXPORT_MODES = (
    EACH_LAYER,
    EACH_TOP_LEVEL_LAYER_OR_GROUP,
    ENTIRE_IMAGE_AT_ONCE,
  ) = 0, 1, 2


def export(
      batcher: 'src.core.Batcher',
      output_directory: str = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
      file_extension: str = 'png',
      export_mode: int = ExportModes.EACH_LAYER,
      single_image_filename_pattern: Optional[str] = None,
      use_file_extension_in_item_name: bool = False,
      convert_file_extension_to_lowercase: bool = False,
      preserve_layer_name_after_export: bool = False,
) -> Generator[None, None, None]:
  item_uniquifier = uniquifier.ItemUniquifier()
  file_extension_properties = _FileExtensionProperties()
  processed_parent_names = set()
  default_file_extension = file_extension

  if export_mode == ExportModes.ENTIRE_IMAGE_AT_ONCE and single_image_filename_pattern is not None:
    renamer_for_image = renamer_.ItemRenamer(single_image_filename_pattern)
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
        if single_image_filename_pattern is not None:
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
    
    if preserve_layer_name_after_export:
      item_to_process.push_state()
    
    if batcher.process_names:
      if use_file_extension_in_item_name:
        current_file_extension = _get_current_file_extension(
          item_to_process, default_file_extension, file_extension_properties)
      
      if convert_file_extension_to_lowercase:
        current_file_extension = current_file_extension.lower()
      
      _process_parent_folder_names(item_to_process, item_uniquifier, processed_parent_names)
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
      
      overwrite_mode, export_status = _export_item(
        batcher,
        item_to_process,
        image_to_process,
        raw_item_to_process,
        output_directory,
        default_file_extension,
        file_extension_properties)
      
      if export_status == ExportStatuses.USE_DEFAULT_FILE_EXTENSION:
        if batcher.process_names:
          _process_item_name(
            item_to_process,
            item_uniquifier,
            current_file_extension,
            default_file_extension,
            force_default_file_extension=True)
        
        if batcher.process_export:
          overwrite_mode, _unused = _export_item(
            batcher,
            item_to_process,
            image_to_process,
            raw_item_to_process,
            output_directory,
            default_file_extension,
            file_extension_properties)
      
      if overwrite_mode != overwrite.OverwriteModes.SKIP:
        file_extension_properties[
          fileext.get_file_extension(item_to_process.name)].processed_count += 1
        # Append the original raw item
        batcher._exported_raw_items.append(item_to_process.raw)
    
    if preserve_layer_name_after_export:
      item_to_process.pop_state()
    
    _sync_raw_item_name(batcher, item_to_process)
    
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


def _process_parent_folder_names(item, item_uniquifier, processed_parent_names):
  for parent in item.parents:
    if parent not in processed_parent_names:
      _validate_name(parent)
      item_uniquifier.uniquify(parent)
      
      processed_parent_names.add(parent)


def _process_item_name(
      item,
      item_uniquifier,
      current_file_extension,
      default_file_extension,
      force_default_file_extension,
):
  if not force_default_file_extension:
    if current_file_extension == default_file_extension:
      item.name += f'.{default_file_extension}'
    else:
      item.name = fileext.get_filename_with_new_file_extension(
        item.name, current_file_extension, keep_extra_trailing_periods=True)
  else:
    item.name = fileext.get_filename_with_new_file_extension(
      item.name, default_file_extension, keep_extra_trailing_periods=True)
  
  _validate_name(item)
  item_uniquifier.uniquify(
    item,
    position=_get_unique_substring_position(item.name, fileext.get_file_extension(item.name)))


def _get_current_file_extension(item, default_file_extension, file_extension_properties):
  item_file_extension = fileext.get_file_extension(item.name)
  
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
  raw_item_copy.set_name(item.name)
  
  return raw_item_copy


def _validate_name(item):
  item.name = validators_.FilenameValidator.validate(item.name)


def _get_unique_substring_position(str_, file_extension):
  return len(str_) - len(f'.{file_extension}')


def _export_item(
      batcher,
      item,
      image,
      raw_item,
      output_directory,
      default_file_extension,
      file_extension_properties,
):
  output_filepath = _get_item_filepath(item, output_directory)
  file_extension = fileext.get_file_extension(item.name)
  export_status = ExportStatuses.NOT_EXPORTED_YET

  overwrite_mode, output_filepath = overwrite.handle_overwrite(
    output_filepath,
    batcher.overwrite_chooser,
    _get_unique_substring_position(output_filepath, file_extension))

  batcher.progress_updater.update_text(_('Saving "{}"').format(output_filepath))
  
  if overwrite_mode == overwrite.OverwriteModes.CANCEL:
    raise exceptions.BatcherCancelError('cancelled')
  
  if overwrite_mode != overwrite.OverwriteModes.SKIP:
    _make_dirs(item, os.path.dirname(output_filepath), default_file_extension)
    
    export_status = _export_item_once_wrapper(
      batcher,
      fileformats.get_save_procedure(file_extension),
      _get_run_mode(batcher, file_extension, file_extension_properties),
      image,
      raw_item,
      output_filepath,
      file_extension,
      default_file_extension,
      file_extension_properties)
    
    if export_status == ExportStatuses.FORCE_INTERACTIVE:
      export_status = _export_item_once_wrapper(
        batcher,
        fileformats.get_save_procedure(file_extension),
        Gimp.RunMode.INTERACTIVE,
        image,
        raw_item,
        output_filepath,
        file_extension,
        default_file_extension,
        file_extension_properties)
  
  return overwrite_mode, export_status


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
  
  path_components = [parent.name for parent in item.parents]
  if path_components:
    path = os.path.join(path, os.path.join(*path_components))
  
  return os.path.join(path, item.name)


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
    
    raise exceptions.InvalidOutputDirectoryError(message, item.name, default_file_extension)


def _export_item_once_wrapper(
      batcher,
      export_func,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      default_file_extension,
      file_extension_properties,
):
  with batcher.export_context_manager(
         run_mode, image, raw_item, output_filepath,
         *batcher.export_context_manager_args, **batcher.export_context_manager_kwargs):
    export_status = _export_item_once(
      batcher,
      export_func,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      default_file_extension,
      file_extension_properties)
  
  return export_status


def _get_run_mode(batcher, file_extension, file_extension_properties):
  file_extension_property = file_extension_properties[file_extension]
  if file_extension_property.is_valid and file_extension_property.processed_count > 0:
    return Gimp.RunMode.WITH_LAST_VALS
  else:
    return batcher.initial_run_mode


def _export_item_once(
      batcher,
      export_func,
      run_mode,
      image,
      raw_item,
      output_filepath,
      file_extension,
      default_file_extension,
      file_extension_properties,
):
  def _raise_export_error(exception):
    raise exceptions.ExportError(str(exception), raw_item.get_name(), default_file_extension)

  try:
    export_func(
      run_mode,
      image,
      raw_item,
      output_filepath)
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


def _sync_raw_item_name(batcher, item_to_process):
  if batcher.current_item == item_to_process and batcher.process_names and not batcher.is_preview:
    batcher.current_raw_item.set_name(batcher.current_item.name)


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
  """Mapping of file extensions from `fileformats.FILE_FORMATS` to
  `_FileExtension` instances.
  
  File extension as a key is always converted to lowercase.
  """
  def __init__(self):
    self._properties = collections.defaultdict(_FileExtension)
    
    for file_format in fileformats.FILE_FORMATS:
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
