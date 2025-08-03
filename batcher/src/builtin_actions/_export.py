"""Built-in "Export"/"Also export as..." action."""

import os
from typing import Callable, Dict, Union, Tuple

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import builtin_commands_common
from src import exceptions
from src import file_formats as file_formats_
from src import initnotifier
from src import invoker as invoker_
from src import itemtree
from src import overwrite
from src import pypdb
from src import renamer as renamer_
from src import uniquifier
from src import utils
from src import utils_pdb
from src.path import fileext
from src.path import validators as validators_
from src.procedure_groups import *
from src.pypdb import pdb

from . import _utils as builtin_actions_utils


__all__ = [
  'INTERACTIVE_OVERWRITE_MODES_LIST',
  'INTERACTIVE_OVERWRITE_MODES',
  'FileFormatModes',
  'ExportModes',
  'ExportStatuses',
  'ExportAction',
  'get_export_function',
  'on_after_add_export_action',
  'set_sensitive_for_image_name_pattern_in_export_for_default_export_action',
  'set_file_extension_options_for_default_export_action',
]


INTERACTIVE_OVERWRITE_MODES_LIST = [
  (overwrite.OverwriteModes.REPLACE, _('Replace')),
  (overwrite.OverwriteModes.SKIP, _('Skip')),
  (overwrite.OverwriteModes.RENAME_NEW, _('Rename new file')),
  (overwrite.OverwriteModes.RENAME_EXISTING, _('Rename existing file'))
]

INTERACTIVE_OVERWRITE_MODES = dict(INTERACTIVE_OVERWRITE_MODES_LIST)


class FileFormatModes:

  FILE_FORMAT_MODES = (
    USE_NATIVE_PLUGIN_VALUES,
    USE_EXPLICIT_VALUES,
  ) = 'use_native_plugin_values', 'use_explicit_values'


class ExportModes:
  
  EXPORT_MODES = (
    EACH_ITEM,
    EACH_TOP_LEVEL_ITEM_OR_FOLDER,
    SINGLE_IMAGE,
  ) = 'each_item', 'each_top_level_item_or_folder', 'single_image'


class ExportStatuses:
  EXPORT_STATUSES = (
    NOT_EXPORTED_YET, EXPORT_SUCCESSFUL, FORCE_INTERACTIVE, USE_DEFAULT_FILE_EXTENSION
  ) = (0, 1, 2, 3)


class ExportAction(invoker_.CallableCommand):

  # noinspection PyAttributeOutsideInit
  def _initialize(self, batcher: 'src.core.Batcher', **kwargs):
    self._output_directory = Gio.file_new_for_path(utils.get_default_dirpath())
    self._file_extension = 'png'
    self._file_format_mode = FileFormatModes.USE_EXPLICIT_VALUES
    self._file_format_export_options = {}
    self._overwrite_mode = overwrite.OverwriteModes.ASK
    self._export_mode = ExportModes.EACH_ITEM
    self._single_image_name_pattern = None
    self._use_file_extension_in_item_name = False
    self._convert_file_extension_to_lowercase = False
    self._use_original_modification_date = False
    self._rotate_flip_image_based_on_exif_metadata = True

    self._assign_to_attributes_from_kwargs(kwargs)

    self._item_uniquifier = uniquifier.ItemUniquifier()
    self._file_extension_properties = builtin_actions_utils.FileExtensionProperties('export')
    self._processed_parents = set()
    self._default_file_extension = self._file_extension
    self._image_copies = []
    self._multi_layer_images = []

    if (self._export_mode == ExportModes.SINGLE_IMAGE
        and self._single_image_name_pattern is not None):
      self._renamer_for_single_image = renamer_.ItemRenamer(self._single_image_name_pattern)
    else:
      self._renamer_for_single_image = None

    batcher.invoker.add(_delete_images_on_cleanup, ['cleanup_contents'], [self._multi_layer_images])
    batcher.invoker.add(_delete_images_on_cleanup, ['cleanup_contents'], [self._image_copies])

  def _process(self, batcher: 'src.core.Batcher', **kwargs):
    self._assign_to_attributes_from_kwargs(kwargs)

    item = batcher.current_item
    current_file_extension = self._default_file_extension

    item_to_process = item
    layer_to_process = batcher.current_layer

    if self._export_mode != ExportModes.EACH_ITEM and batcher.process_export:
      if not self._multi_layer_images:
        multi_layer_image = utils_pdb.create_empty_image_copy(batcher.current_image)
        self._multi_layer_images.append(multi_layer_image)
      else:
        multi_layer_image = self._multi_layer_images[-1]
    else:
      multi_layer_image = None

    if batcher.edit_mode and batcher.process_export:
      image_copy, layer_to_process = batcher.create_copy(batcher.current_image, layer_to_process)
      self._image_copies.append(image_copy)

      if layer_to_process is None:
        layer_to_process = batcher.current_layer
      else:
        layer_to_process.set_name(item.name)
    else:
      image_copy = batcher.current_image

    if batcher.process_export and self._rotate_flip_image_based_on_exif_metadata:
      utils_pdb.rotate_or_flip_image_based_on_exif_metadata(image_copy)

    if multi_layer_image is None:
      image_to_process = image_copy
    else:
      image_to_process = multi_layer_image

    if self._export_mode == ExportModes.SINGLE_IMAGE:
      if batcher.process_export:
        layer_to_process = _merge_and_resize_image(batcher, image_copy, layer_to_process)
        layer_to_process = _copy_layer(layer_to_process, image_to_process, item)

      if _get_next_item(batcher, item) is not None:
        _remove_image_copies_for_edit_mode(batcher, self._image_copies)
        return
      else:
        item_to_process = _NameOnlyItem(None, itemtree.TYPE_ITEM, [], [], None, None)
        if self._single_image_name_pattern is not None:
          item_to_process.name = self._renamer_for_single_image.rename(batcher, item_to_process)
        else:
          item_to_process.name = item.name
    elif self._export_mode == ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER:
      if batcher.process_export:
        layer_to_process = _merge_and_resize_image(batcher, image_copy, layer_to_process)
        layer_to_process = _copy_layer(layer_to_process, image_to_process, item)

      current_top_level_item = _get_top_level_item(item)
      next_top_level_item = _get_top_level_item(_get_next_item(batcher, item))

      if current_top_level_item == next_top_level_item:
        _remove_image_copies_for_edit_mode(batcher, self._image_copies)
        return
      else:
        item_to_process = current_top_level_item

    if batcher.process_names:
      item_to_process.save_state(builtin_actions_utils.EXPORT_NAME_ITEM_STATE)

      if self._use_file_extension_in_item_name:
        current_file_extension = _get_current_file_extension(
          item_to_process, self._default_file_extension, self._file_extension_properties)

      if self._convert_file_extension_to_lowercase:
        current_file_extension = current_file_extension.lower()

      _process_parent_names(item_to_process, self._item_uniquifier, self._processed_parents)
      _process_item_name(
        item_to_process,
        self._item_uniquifier,
        current_file_extension,
        self._default_file_extension,
        force_default_file_extension=False)

    if batcher.process_export:
      if self._export_mode != ExportModes.EACH_ITEM:
        image_to_process.resize_to_layers()

      if self._overwrite_mode == overwrite.OverwriteModes.ASK:
        overwrite_chooser = batcher.overwrite_chooser
      else:
        overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(self._overwrite_mode)

      chosen_overwrite_mode, export_status = _export_item(
        batcher,
        item_to_process,
        image_to_process,
        layer_to_process,
        self._output_directory,
        self._file_format_mode,
        self._file_format_export_options,
        self._default_file_extension,
        self._file_extension_properties,
        overwrite_chooser,
        self._use_original_modification_date,
      )

      if export_status == ExportStatuses.USE_DEFAULT_FILE_EXTENSION:
        if batcher.process_names:
          _process_item_name(
            item_to_process,
            self._item_uniquifier,
            current_file_extension,
            self._default_file_extension,
            force_default_file_extension=True)

        if batcher.process_export:
          chosen_overwrite_mode, _unused = _export_item(
            batcher,
            item_to_process,
            image_to_process,
            layer_to_process,
            self._output_directory,
            self._file_format_mode,
            self._file_format_export_options,
            self._default_file_extension,
            self._file_extension_properties,
            overwrite_chooser,
            self._use_original_modification_date,
          )

      if chosen_overwrite_mode != overwrite.OverwriteModes.SKIP:
        self._file_extension_properties[
          fileext.get_file_extension(
            builtin_actions_utils.get_item_export_name(item_to_process))
        ].processed_count += 1
        # Append the original raw item
        # noinspection PyProtectedMember
        batcher._exported_items.append(item_to_process)

    if multi_layer_image is not None:
      _remove_multi_layer_images(self._multi_layer_images)

    _remove_image_copies_for_edit_mode(batcher, self._image_copies)

  def _assign_to_attributes_from_kwargs(self, kwargs):
    for name, value in kwargs.items():
      if not hasattr(self, f'_{name}'):
        raise ValueError(f'{type(self)}: attribute "_{name}" is not defined')

      setattr(self, f'_{name}', value)


def _delete_images_on_cleanup(batcher, images):
  if batcher.process_export:
    for image in images:
      utils_pdb.try_delete_image(image)


def _get_top_level_item(item):
  if item is not None and item.parents:
    return item.parents[0]
  else:
    return item


def _get_next_item(batcher, item):
  if batcher.matching_items is not None:
    return batcher.matching_items[item]
  else:
    batcher.item_tree.next(item, with_folders=False)


def _process_parent_names(item, item_uniquifier, processed_parents):
  for parent in item.parents:
    if parent not in processed_parents:
      parent.save_state(builtin_actions_utils.EXPORT_NAME_ITEM_STATE)

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
  item_name = builtin_actions_utils.get_item_export_name(item)

  processed_item_name = item_name

  if not force_default_file_extension:
    if current_file_extension == default_file_extension:
      processed_item_name = f'{item_name}.{default_file_extension}'
    else:
      processed_item_name = fileext.get_filename_with_new_file_extension(
        item_name, current_file_extension, keep_extra_trailing_periods=True)
  else:
    processed_item_name = fileext.get_filename_with_new_file_extension(
      item_name, default_file_extension, keep_extra_trailing_periods=True)

  builtin_actions_utils.set_item_export_name(item, processed_item_name)

  _validate_name(item)
  _uniquify_name(
    item_uniquifier,
    item,
    position=_get_unique_substring_position(
      builtin_actions_utils.get_item_export_name(item),
      fileext.get_file_extension(builtin_actions_utils.get_item_export_name(item))),
  )


def _get_current_file_extension(item, default_file_extension, file_extension_properties):
  item_file_extension = fileext.get_file_extension(item.orig_name)
  
  if item_file_extension and file_extension_properties[item_file_extension].is_valid:
    return item_file_extension
  else:
    return default_file_extension


def _merge_and_resize_image(batcher, image, layer):
  """Merges all layers in the current image into one.
  
  Merging is necessary for:
  * custom actions inserting layers (background, foreground). Some file
    formats may discard all but one layer.
  * multi-layer images, with each layer containing background or foreground
    which are originally separate layers.
  """
  layer_name = layer.get_name()
  
  layer_merged = image.merge_visible_layers(Gimp.MergeType.EXPAND_AS_NECESSARY)
  layer_merged.resize_to_image_size()
  
  layer_merged.set_name(layer_name)
  image.set_selected_layers([layer_merged])
  
  if not batcher.edit_mode:
    batcher.current_layer = layer_merged
  
  return layer_merged


def _copy_layer(layer, dest_image, item):
  layer_copy = utils_pdb.copy_and_paste_layer(
    layer, dest_image, None, len(dest_image.get_layers()), True, True, True)

  # We use `item.name` instead of
  # `builtin_actions_utils.get_item_export_name()` so that the original
  # layer name is used in case of multi-layer export.
  layer_copy.set_name(item.name)
  
  return layer_copy


def _validate_name(item):
  builtin_actions_utils.set_item_export_name(
    item,
    validators_.FilenameValidator.validate(builtin_actions_utils.get_item_export_name(item)))


def _uniquify_name(item_uniquifier, item, position=None):
  item_name = builtin_actions_utils.get_item_export_name(item)

  uniquified_item_name = item_uniquifier.uniquify(item, item_name=item_name, position=position)

  builtin_actions_utils.set_item_export_name(item, uniquified_item_name)


def _get_unique_substring_position(str_, file_extension):
  return len(str_) - len(f'.{file_extension}')


def _export_item(
      batcher,
      item,
      image,
      layer,
      output_directory,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      overwrite_chooser,
      use_original_modification_date,
):
  output_filepath = builtin_actions_utils.get_item_filepath(item, output_directory)
  file_extension = fileext.get_file_extension(builtin_actions_utils.get_item_export_name(item))
  export_status = ExportStatuses.NOT_EXPORTED_YET

  try:
    chosen_overwrite_mode, output_filepath = overwrite.handle_overwrite(
      output_filepath,
      overwrite_chooser,
      _get_unique_substring_position(output_filepath, file_extension))
  except OSError as e:
    raise exceptions.ImageExportError(
      str(e),
      builtin_actions_utils.get_item_export_name(item),
      file_extension,
    )

  batcher.progress_updater.update_text(_('Saving "{}"').format(output_filepath))
  
  if chosen_overwrite_mode == overwrite.OverwriteModes.CANCEL:
    raise exceptions.BatcherCancelError('canceled')
  
  if chosen_overwrite_mode != overwrite.OverwriteModes.SKIP:
    _make_dirs(item, os.path.dirname(output_filepath), default_file_extension)
    
    export_status = _export_item_once_wrapper(
      batcher,
      _get_run_mode(batcher, file_format_mode, file_extension, file_extension_properties),
      item,
      image,
      layer,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      use_original_modification_date,
    )
    
    if export_status == ExportStatuses.FORCE_INTERACTIVE:
      export_status = _export_item_once_wrapper(
        batcher,
        Gimp.RunMode.INTERACTIVE,
        item,
        image,
        layer,
        output_filepath,
        file_extension,
        file_format_mode,
        file_format_export_options,
        default_file_extension,
        file_extension_properties,
        use_original_modification_date,
      )
  
  return chosen_overwrite_mode, export_status


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
      message, builtin_actions_utils.get_item_export_name(item), default_file_extension)


def _export_item_once_wrapper(
      batcher,
      run_mode,
      item,
      image,
      layer,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      use_original_modification_date,
):
  with batcher.export_context_manager(
         run_mode, image, layer, output_filepath,
         *batcher.export_context_manager_args, **batcher.export_context_manager_kwargs):
    export_status = _export_item_once(
      run_mode,
      item,
      image,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      use_original_modification_date,
    )
  
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
      run_mode,
      item,
      image,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      default_file_extension,
      file_extension_properties,
      use_original_modification_date,
):
  def _raise_image_export_error(exception):
    raise exceptions.ImageExportError(
      str(exception), builtin_actions_utils.get_item_export_name(item), default_file_extension)

  try:
    _export_image(
      run_mode,
      item,
      image,
      output_filepath,
      file_extension,
      file_format_mode,
      file_format_export_options,
      use_original_modification_date,
    )
  except pypdb.PDBProcedureError as e:
    if e.status == Gimp.PDBStatusType.CANCEL:
      raise exceptions.BatcherCancelError('canceled')
    elif e.status == Gimp.PDBStatusType.CALLING_ERROR:
      if run_mode != Gimp.RunMode.INTERACTIVE:
        return ExportStatuses.FORCE_INTERACTIVE
      else:
        _raise_image_export_error(e)
    elif e.status == Gimp.PDBStatusType.EXECUTION_ERROR:
      if file_extension != default_file_extension:
        file_extension_properties[file_extension].is_valid = False
        return ExportStatuses.USE_DEFAULT_FILE_EXTENSION
      else:
        _raise_image_export_error(e)
    else:
      _raise_image_export_error(e)
  else:
    return ExportStatuses.EXPORT_SUCCESSFUL


def _export_image(
      run_mode: Gimp.RunMode,
      item: itemtree.Item,
      image: Gimp.Image,
      filepath: Union[str, Gio.File],
      file_extension: str,
      file_format_mode: str,
      file_format_export_options: Dict,
      use_original_modification_date: bool,
):
  if not isinstance(filepath, Gio.File):
    image_file = Gio.file_new_for_path(filepath)
  else:
    image_file = filepath

  export_func, kwargs = get_export_function(
    file_extension, file_format_mode, file_format_export_options)

  export_func(
    run_mode=run_mode,
    image=image,
    file=image_file,
    options=None,
    **kwargs)

  if use_original_modification_date:
    _set_original_modification_date(item, filepath)

  return pdb.last_status


def _set_original_modification_date(item, filepath):
  if isinstance(item, itemtree.ImageFileItem) and os.path.isfile(item.id):
    orig_filepath_stat = os.stat(item.id)
    os.utime(filepath, times=(orig_filepath_stat.st_atime, orig_filepath_stat.st_mtime))


def get_export_function(
      file_extension: str,
      file_format_mode: str,
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
    if file_format.has_export_proc():
      file_format_option_kwargs = file_formats_.fill_and_get_file_format_options_as_kwargs(
        file_format_export_options, file_extension, 'export')

      if file_format_option_kwargs is not None:
        return file_format.get_export_func(), file_format_option_kwargs

  return pdb.gimp_file_save, {}


def _remove_image_copies_for_edit_mode(batcher, image_copies):
  if batcher.edit_mode and batcher.process_export:
    for image in image_copies:
      utils_pdb.try_delete_image(image)
    image_copies.clear()


def _remove_multi_layer_images(images):
  for image in images:
    utils_pdb.try_delete_image(image)
  images.clear()


class _NameOnlyItem(itemtree.Item):
  """`itemtree.Item` subclass used to store the item name only."""

  @property
  def raw(self):
    return None

  def _list_child_objects(self):
    return []

  def _get_name_from_object(self) -> str:
    return ''

  def _get_id_from_object(self):
    return None


def on_after_add_export_action(_actions, action, _orig_action_dict):
  if action['orig_name'].value.startswith('export_for_'):
    _set_sensitive_for_image_name_pattern_in_export(
      action['arguments/export_mode'],
      action['arguments/single_image_name_pattern'])

    action['arguments/export_mode'].connect_event(
      'value-changed',
      _set_sensitive_for_image_name_pattern_in_export,
      action['arguments/single_image_name_pattern'])

    _show_hide_file_format_export_options(
      action['arguments/file_format_mode'],
      action['arguments/file_format_export_options'])

    action['arguments/file_format_mode'].connect_event(
      'value-changed',
      _show_hide_file_format_export_options,
      action['arguments/file_format_export_options'])

    _set_file_format_export_options(
      action['arguments/file_extension'],
      action['arguments/file_format_export_options'])

    action['arguments/file_extension'].connect_event(
      'value-changed',
      _set_file_format_export_options,
      action['arguments/file_format_export_options'])

    # This is needed in case settings are reset, since the file extension is
    # reset first and the options, after resetting, would contain values for
    # the default file extension, which could be different.
    action['arguments/file_format_export_options'].connect_event(
      'after-reset',
      _set_file_format_export_options_from_extension,
      action['arguments/file_extension'])


def set_sensitive_for_image_name_pattern_in_export_for_default_export_action(
      main_settings):
  _set_sensitive_for_image_name_pattern_in_export(
    main_settings['export/export_mode'],
    main_settings['export/single_image_name_pattern'])

  main_settings['export/export_mode'].connect_event(
    'value-changed',
    _set_sensitive_for_image_name_pattern_in_export,
    main_settings['export/single_image_name_pattern'])


def set_file_extension_options_for_default_export_action(main_settings):
  _show_hide_file_format_export_options(
    main_settings['export/file_format_mode'],
    main_settings['export/file_format_export_options'])

  main_settings['export/file_format_mode'].connect_event(
    'value-changed',
    _show_hide_file_format_export_options,
    main_settings['export/file_format_export_options'])

  initnotifier.notifier.connect(
    'start-procedure',
    lambda _notifier: _set_file_format_export_options(
      main_settings['file_extension'],
      main_settings['export/file_format_export_options']))

  main_settings['file_extension'].connect_event(
    'value-changed',
    _set_file_format_export_options,
    main_settings['export/file_format_export_options'])

  # This is needed in case settings are reset, since the file extension is
  # reset first and the options, after resetting, would contain values for
  # the default file extension, which could be different.
  main_settings['export/file_format_export_options'].connect_event(
    'after-reset',
    _set_file_format_export_options_from_extension,
    main_settings['file_extension'])


def _set_sensitive_for_image_name_pattern_in_export(
      export_mode_setting, single_image_name_pattern_setting):
  if export_mode_setting.value == ExportModes.SINGLE_IMAGE:
    single_image_name_pattern_setting.gui.set_sensitive(True)
  else:
    single_image_name_pattern_setting.gui.set_sensitive(False)


def _set_file_format_export_options(
      file_extension_setting, file_format_export_options_setting):
  file_format_export_options_setting.set_active_file_formats([file_extension_setting.value])


def _set_file_format_export_options_from_extension(
      file_format_export_options_setting, file_extension_setting):
  file_format_export_options_setting.set_active_file_formats([file_extension_setting.value])


def _show_hide_file_format_export_options(
      file_format_mode_setting, file_format_export_options_setting):
  file_format_export_options_setting.gui.set_visible(
    file_format_mode_setting.value == 'use_explicit_values')


_EXPORT_OVERWRITE_MODES_LIST = [
  (overwrite.OverwriteModes.ASK, _('Ask')),
  *INTERACTIVE_OVERWRITE_MODES_LIST
]

EXPORT_FOR_CONVERT_DICT = {
  'name': 'export_for_convert',
  'function': ExportAction,
  'display_name': _('Also export as...'),
  'description': _('Exports an image to another file format.'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, CONVERT_GROUP],
  'display_options_on_create': True,
  'arguments': [
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
      'set_default_if_not_exists': True,
      'gui_type_kwargs': {
        'show_clear_button': False,
      },
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
        (FileFormatModes.USE_NATIVE_PLUGIN_VALUES, _('Interactively')),
        (FileFormatModes.USE_EXPLICIT_VALUES, _('Use options below')),
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
      'gui_type': 'file_format_options',
      'display_name': _('File format options'),
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
        (ExportModes.EACH_ITEM, _('For each image')),
        (ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER,
         _('For each top-level image or folder')),
        (ExportModes.SINGLE_IMAGE, _('As a single image')),
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
    {
      'type': 'bool',
      'name': 'rotate_flip_image_based_on_exif_metadata',
      'default_value': True,
      'display_name': _('Rotate or flip image based on Exif metadata'),
    },
  ],
}

EXPORT_FOR_EXPORT_IMAGES_DICT = utils.semi_deep_copy(EXPORT_FOR_CONVERT_DICT)
EXPORT_FOR_EXPORT_IMAGES_DICT.update({
  'name': 'export_for_export_images',
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EXPORT_IMAGES_GROUP],
})
EXPORT_FOR_EXPORT_IMAGES_DICT['arguments'][5]['items'].pop(1)
del EXPORT_FOR_EXPORT_IMAGES_DICT['arguments'][9]
del EXPORT_FOR_EXPORT_IMAGES_DICT['arguments'][7]

EXPORT_FOR_EDIT_AND_SAVE_IMAGES_DICT = utils.semi_deep_copy(EXPORT_FOR_EXPORT_IMAGES_DICT)
EXPORT_FOR_EDIT_AND_SAVE_IMAGES_DICT.update({
  'name': 'export_for_edit_and_save_images',
  'display_name': _('Export'),
  'description': _('Exports an image to the specified file format.'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_AND_SAVE_IMAGES_GROUP],
})

EXPORT_FOR_EXPORT_LAYERS_DICT = utils.semi_deep_copy(EXPORT_FOR_CONVERT_DICT)
EXPORT_FOR_EXPORT_LAYERS_DICT.update({
  'name': 'export_for_export_layers',
  'description': _('Exports a layer to another file format.'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EXPORT_LAYERS_GROUP],
})
EXPORT_FOR_EXPORT_LAYERS_DICT['arguments'][5]['items'] = [
  (ExportModes.EACH_ITEM, _('For each layer')),
  (ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER,
   _('For each top-level layer or group')),
  (ExportModes.SINGLE_IMAGE, _('As a single image')),
]
EXPORT_FOR_EXPORT_LAYERS_DICT['arguments'][6]['default_value'] = '[image name]'
EXPORT_FOR_EXPORT_LAYERS_DICT['arguments'][7]['display_name'] = _(
  'Use file extension in layer name')
del EXPORT_FOR_EXPORT_LAYERS_DICT['arguments'][9]

EXPORT_FOR_EDIT_LAYERS_DICT = utils.semi_deep_copy(EXPORT_FOR_CONVERT_DICT)
EXPORT_FOR_EDIT_LAYERS_DICT.update({
  'name': 'export_for_edit_layers',
  'display_name': _('Export'),
  'description': _('Exports a layer to the specified file format.'),
  'additional_tags': [builtin_commands_common.NAME_ONLY_TAG, EDIT_LAYERS_GROUP],
})
EXPORT_FOR_EDIT_LAYERS_DICT['arguments'][5]['items'] = [
  (ExportModes.EACH_ITEM, _('For each layer')),
  (ExportModes.EACH_TOP_LEVEL_ITEM_OR_FOLDER,
   _('For each top-level layer or group')),
  (ExportModes.SINGLE_IMAGE, _('As a single image')),
]
EXPORT_FOR_EDIT_LAYERS_DICT['arguments'][6]['default_value'] = '[image name]'
EXPORT_FOR_EDIT_LAYERS_DICT['arguments'][7]['display_name'] = _(
  'Use file extension in layer name')
del EXPORT_FOR_EDIT_LAYERS_DICT['arguments'][9]
