#!/usr/bin/env python3

"""Main plug-in file."""

import os

from src import utils

_PLUGIN_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))

utils.initialize_i18n(os.path.join(_PLUGIN_DIRPATH, 'locale'), 'batcher')

from src import logging

# Initialize logging as early as possible to capture any module-level errors.
logging.log_output(
  stderr_handles=['file'],
  log_dirpaths=[_PLUGIN_DIRPATH],
  log_error_filename='error.log',
  log_header_title=_PLUGIN_DIRPATH)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from config import CONFIG
from src import builtin_conditions
from src import commands as commands_
from src import constants
from src import itemtree
from src import setting as setting_
from src.gui import messages as messages_

messages_.set_gui_excepthook(
  title=CONFIG.PLUGIN_TITLE,
  report_uri_list=CONFIG.BUG_REPORT_URL_LIST,
)

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import core
from src import exceptions
from src import plugin_settings
from src import procedure as procedure_
from src import update
from src import utils_itemtree as utils_itemtree_
from src import utils_setting as utils_setting_
from src.gui import main as gui_main
from src.procedure_groups import *


SETTINGS_CONVERT = plugin_settings.create_settings_for_convert()
SETTINGS_EXPORT_IMAGES = plugin_settings.create_settings_for_export_images()
SETTINGS_EDIT_AND_SAVE_IMAGES = plugin_settings.create_settings_for_edit_and_save_images()
SETTINGS_EXPORT_LAYERS = plugin_settings.create_settings_for_export_layers()
SETTINGS_EDIT_LAYERS = plugin_settings.create_settings_for_edit_layers()


def plug_in_batch_convert(_procedure, config, _data):
  _set_procedure_group_and_default_setting_source(CONVERT_GROUP)

  run_mode = config.get_property('run-mode')

  image_tree = itemtree.ImageFileTree()

  def _fill_image_tree_with_loaded_inputs(settings):
    if run_mode == Gimp.RunMode.NONINTERACTIVE:
      image_tree.add(settings['main/inputs'].value)
    else:
      utils_itemtree_.add_objects_to_item_tree(image_tree, settings['gui/inputs_interactive'].value)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_CONVERT,
      image_tree,
      gui_main.BatchProcessingGui,
      gui_class_kwargs=dict(
        mode='export', item_type='image', title=_('Batch Convert')),
      process_loaded_settings_func=_fill_image_tree_with_loaded_inputs,
    )
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(
      SETTINGS_CONVERT,
      image_tree,
      mode='export',
      process_loaded_settings_func=_fill_image_tree_with_loaded_inputs,
    )
  else:
    return _run_noninteractive(SETTINGS_CONVERT, image_tree, config, mode='export')


def plug_in_batch_export_images(_procedure, config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_IMAGES_GROUP)

  run_mode = config.get_property('run-mode')

  image_tree = itemtree.GimpImageTree()
  image_tree.add_opened_images()

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_IMAGES,
      image_tree,
      gui_main.BatchProcessingGui,
      gui_class_kwargs=dict(
        mode='export', item_type='image', title=_('Export Images')),
    )
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(
      SETTINGS_EXPORT_IMAGES,
      image_tree,
      mode='export',
    )
  else:
    return _run_noninteractive(SETTINGS_EXPORT_IMAGES, image_tree, config, mode='export')


def plug_in_batch_export_images_quick(_procedure, config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_IMAGES_GROUP)

  run_mode = config.get_property('run-mode')

  image_tree = itemtree.GimpImageTree()
  image_tree.add_opened_images()

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_IMAGES,
      image_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='export', item_type='image', title=_('Export Images (Quick)')))
  else:
    return _run_with_last_vals(SETTINGS_EXPORT_IMAGES, image_tree, mode='export')


def plug_in_batch_edit_and_save_images(_procedure, config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_AND_SAVE_IMAGES_GROUP)

  run_mode = config.get_property('run-mode')

  image_tree = itemtree.GimpImageTree()
  image_tree.add_opened_images()

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_AND_SAVE_IMAGES,
      image_tree,
      gui_main.BatchProcessingGui,
      gui_class_kwargs=dict(
        mode='edit', item_type='image', title=_('Edit and Save Images')),
    )
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(SETTINGS_EDIT_AND_SAVE_IMAGES, image_tree, mode='edit')
  else:
    return _run_noninteractive(SETTINGS_EDIT_AND_SAVE_IMAGES, image_tree, config, mode='edit')


def plug_in_batch_edit_and_save_images_quick(_procedure, config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_AND_SAVE_IMAGES_GROUP)

  run_mode = config.get_property('run-mode')

  image_tree = itemtree.GimpImageTree()
  image_tree.add_opened_images()

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_AND_SAVE_IMAGES,
      image_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='edit', item_type='image', title=_('Edit and Save Images (Quick)')))
  else:
    return _run_with_last_vals(SETTINGS_EXPORT_IMAGES, image_tree, mode='edit')


def plug_in_batch_export_layers(_procedure, run_mode, image, _drawables, config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingGui,
      gui_class_kwargs=dict(
        mode='export', item_type='layer', title=_('Export Layers'), current_image=image))
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(SETTINGS_EXPORT_LAYERS, layer_tree, mode='export')
  else:
    return _run_noninteractive(SETTINGS_EXPORT_LAYERS, layer_tree, config, mode='export')


def plug_in_batch_export_layers_quick(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='export', item_type='layer', title=_('Export Layers (Quick)'), current_image=image))
  else:
    return _run_with_last_vals(SETTINGS_EXPORT_LAYERS, layer_tree, mode='export')


def plug_in_batch_export_selected_layers(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='export', item_type='layer', title=_('Export Selected Layers'), current_image=image),
      process_loaded_settings_func=_set_conditions_to_only_selected_layers)
  else:
    return _run_with_last_vals(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      mode='export',
      process_loaded_settings_func=_set_conditions_to_only_selected_layers)


def plug_in_batch_edit_layers(_procedure, run_mode, image, _drawables, config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingGui,
      gui_class_kwargs=dict(
        mode='edit', item_type='layer', title=_('Edit Layers'), current_image=image))
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(SETTINGS_EDIT_LAYERS, layer_tree, mode='edit')
  else:
    return _run_noninteractive(SETTINGS_EDIT_LAYERS, layer_tree, config, mode='edit')


def plug_in_batch_edit_layers_quick(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='edit', item_type='layer', title=_('Edit Layers (Quick)'), current_image=image))
  else:
    return _run_with_last_vals(SETTINGS_EDIT_LAYERS, layer_tree, mode='edit')


def plug_in_batch_edit_selected_layers(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchProcessingQuickGui,
      gui_class_kwargs=dict(
        mode='edit', item_type='layer', title=_('Edit Selected Layers'), current_image=image),
      process_loaded_settings_func=_set_conditions_to_only_selected_layers)
  else:
    return _run_with_last_vals(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      mode='edit',
      process_loaded_settings_func=_set_conditions_to_only_selected_layers)


def _run_noninteractive(settings, item_tree, config, mode):
  if CONFIG.PROCEDURE_GROUP == CONVERT_GROUP:
    gimp_status, message = _load_inputs(
      item_tree, config.get_property('inputs'), config.get_property('max-num-inputs'))
    if gimp_status != Gimp.PDBStatusType.SUCCESS:
      return gimp_status, message

  settings_file = config.get_property('settings-file')

  if settings_file is not None and settings_file.get_path() is not None:
    gimp_status, message = _load_settings_from_file(settings, settings_file.get_path())
    if gimp_status != Gimp.PDBStatusType.SUCCESS:
      return gimp_status, message
  else:
    _set_settings_from_args(settings['main'], config)

  _run_plugin_noninteractive(settings, Gimp.RunMode.NONINTERACTIVE, item_tree, mode)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_with_last_vals(
      settings,
      item_tree,
      mode,
      process_loaded_settings_func=None,
):
  update_successful, message = _load_and_update_settings(settings, Gimp.RunMode.WITH_LAST_VALS)
  if not update_successful:
    return Gimp.PDBStatusType.EXECUTION_ERROR, message

  if process_loaded_settings_func is not None:
    process_loaded_settings_func(settings)

  _run_plugin_noninteractive(settings, Gimp.RunMode.WITH_LAST_VALS, item_tree, mode)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_interactive(
      settings,
      item_tree,
      gui_class,
      gui_class_args=None,
      gui_class_kwargs=None,
      process_loaded_settings_func=None,
):
  if gui_class_args is None:
    gui_class_args = ()

  if gui_class_kwargs is None:
    gui_class_kwargs = {}

  update_successful, message = _load_and_update_settings(settings, Gimp.RunMode.INTERACTIVE)
  if not update_successful:
    return Gimp.PDBStatusType.EXECUTION_ERROR, message

  if process_loaded_settings_func is not None:
    process_loaded_settings_func(settings)

  gui_class(item_tree, settings, *gui_class_args, **gui_class_kwargs)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_plugin_noninteractive(settings, run_mode, item_tree, mode):
  if CONFIG.PROCEDURE_GROUP == CONVERT_GROUP:
    batcher_class = core.ImageBatcher
  else:
    batcher_class = core.LayerBatcher

  batcher = batcher_class(
    item_tree=item_tree,
    actions=settings['main/actions'],
    conditions=settings['main/conditions'],
    refresh_item_tree=False,
    initial_export_run_mode=run_mode,
    edit_mode=mode == 'edit',
  )

  try:
    batcher.run(
      **utils_setting_.get_settings_for_batcher(settings['main']))
  except exceptions.BatcherCancelError:
    return Gimp.PDBStatusType.SUCCESS, 'canceled'
  except Exception as e:
    return Gimp.PDBStatusType.EXECUTION_ERROR, str(e)

  return Gimp.PDBStatusType.SUCCESS, ''


def _load_inputs(item_tree, filepath, max_num_inputs):
  if filepath is None:
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR, f'File containing inputs is not specified')
  elif not os.path.isfile(filepath):
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR, f'File "{filepath}" does not exist or is not a file')

  try:
    with open(filepath, 'r', encoding=constants.TEXT_FILE_ENCODING) as inputs_file:
      inputs = [path for path in inputs_file.read().splitlines() if path]
  except Exception as e:
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR, f'Error obtaining inputs from file "{filepath}": {e}')

  item_tree.add(inputs)

  if max_num_inputs != 0 and len(item_tree) > max_num_inputs:
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR,
      (f'File "{filepath}" contains more than {max_num_inputs} files to process'
       ' (including files in folders).'
       ' Check if you specified the files and folders you truly wish to process.'
       ' To remove this restriction, set "max-num-inputs" to 0.'))

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_procedure_group_and_default_setting_source(procedure_group):
  CONFIG.PROCEDURE_GROUP = procedure_group

  setting_.Persistor.set_default_setting_sources(
    {'persistent': setting_.GimpParasiteSource(procedure_group)})


def _load_and_update_settings(settings, run_mode):
  status, load_message = update.load_and_update(settings, procedure_group=CONFIG.PROCEDURE_GROUP)

  if status != update.TERMINATE:
    return True, ''

  if run_mode == Gimp.RunMode.INTERACTIVE:
    messages_.display_alert_message(
      title=CONFIG.PLUGIN_TITLE,
      message_type=Gtk.MessageType.WARNING,
      message_markup=_(
        'Settings for this plug-in could not be updated to the latest version'
        ' and must be reset.'),
      message_secondary_markup=_(
        'If you believe this is an error in the plug-in, you can help fix it'
        ' by sending a report with the text under the details.'),
      display_details_initially=False,
      details=load_message,
      report_description=_(
        'Send a report with the text in the details above to one of the following sites'),
      report_uri_list=CONFIG.BUG_REPORT_URL_LIST)

    setting_.Persistor.clear()
    commands_.clear(settings['main/actions'])
    commands_.clear(settings['main/conditions'])

    return True, ''
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    setting_.Persistor.clear()

    return (
      False,
      (_('Settings could not be loaded and had to be reset.')
       + '\n\n'
       + _('Details: {}').format(load_message)))

  return False, load_message


def _load_settings_from_file(settings, settings_filepath):
  if not os.path.isfile(settings_filepath):
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR,
      _('"{}" is not a valid file with settings').format(settings_filepath))

  setting_source = setting_.JsonFileSource(CONFIG.PROCEDURE_GROUP, settings_filepath)

  status, message = update.load_and_update(
    settings, sources={'persistent': setting_source}, procedure_group=CONFIG.PROCEDURE_GROUP)
  if status == update.TERMINATE:
    error_message = _('Failed to import settings from file "{}".').format(settings_filepath)

    if message:
      error_message += ' ' + _('Details: {}').format(message)

    return Gimp.PDBStatusType.EXECUTION_ERROR, error_message

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_settings_from_args(settings, config):
  args_as_settings = [
    setting for setting in settings
    if isinstance(setting, setting_.Setting) and setting.can_be_used_in_pdb()]

  args = [config.get_property(prop.name) for prop in config.list_properties()]
  # `config.list_properties()` contains additional properties or parameters
  # added by GIMP (e.g. `Gimp.Procedure` object). It appears these are added
  # before the plug-in-specific PDB parameters.
  args = args[max(len(args) - len(args_as_settings), 0):]

  for setting, arg in zip(args_as_settings, args):
    setting.set_value(arg)


def _set_conditions_to_only_selected_layers(settings):
  commands_.clear(settings['main/conditions'], add_initial_commands=False)

  commands_.add(
    settings['main/conditions'], builtin_conditions.BUILTIN_CONDITIONS['selected_in_gimp'])


procedure_.register_procedure(
  plug_in_batch_convert,
  procedure_type=Gimp.Procedure,
  arguments=setting_.create_params(SETTINGS_CONVERT['main']),
  menu_label=_('_Batch Convert...'),
  menu_path='<Image>/File/[Export]',
  image_types='',
  sensitivity_mask=Gimp.ProcedureSensitivityMask.ALWAYS,
  documentation=(
    _('Batch-process image files'),
    _('This procedure performs batch conversion of image files'
      ' to the specified file format, optionally applying arbitrary procedures'
      ' to each item and ignoring items according to the specified conditions.'),
  ),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_export_images,
  procedure_type=Gimp.Procedure,
  arguments=setting_.create_params(SETTINGS_EXPORT_IMAGES['main']),
  menu_label=_('E_xport Images...'),
  menu_path='<Image>/File/[Export]',
  image_types='',
  sensitivity_mask=Gimp.ProcedureSensitivityMask.ALWAYS,
  documentation=(_('Exports images opened in GIMP'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_export_images_quick,
  procedure_type=Gimp.Procedure,
  arguments=setting_.create_params(SETTINGS_EXPORT_IMAGES['main/run_mode']),
  menu_label=_('E_xport Images (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='',
  sensitivity_mask=Gimp.ProcedureSensitivityMask.ALWAYS,
  documentation=(_('Quickly export images opened in GIMP'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_edit_and_save_images,
  procedure_type=Gimp.Procedure,
  arguments=setting_.create_params(SETTINGS_EDIT_AND_SAVE_IMAGES['main']),
  menu_label=_('E_dit and Save Images...'),
  menu_path='<Image>/File/[Export]',
  image_types='',
  sensitivity_mask=Gimp.ProcedureSensitivityMask.ALWAYS,
  documentation=(_('Edits and saves images opened in GIMP as XCF'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_edit_and_save_images_quick,
  procedure_type=Gimp.Procedure,
  arguments=setting_.create_params(SETTINGS_EDIT_AND_SAVE_IMAGES['main/run_mode']),
  menu_label=_('E_dit and Save Images (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='',
  sensitivity_mask=Gimp.ProcedureSensitivityMask.ALWAYS,
  documentation=(_('Edits and saves images opened in GIMP as XCF instantly'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_export_layers,
  arguments=setting_.create_params(SETTINGS_EXPORT_LAYERS['main']),
  menu_label=_('E_xport Layers...'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Export layers as separate images'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_export_layers_quick,
  menu_label=_('E_xport Layers (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Quickly export layers as separate images'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_export_selected_layers,
  menu_label=_('E_xport Selected Layers'),
  menu_path='<Layers>/Layers Menu/[Batch]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Quickly export selected layers as separate images'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_edit_layers,
  arguments=setting_.create_params(SETTINGS_EDIT_LAYERS['main']),
  menu_label=_('E_dit Layers...'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit layers'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_edit_layers_quick,
  menu_label=_('E_dit Layers (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit layers instantly'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.register_procedure(
  plug_in_batch_edit_selected_layers,
  menu_label=_('E_dit Selected Layers'),
  menu_path='<Layers>/Layers Menu/[Batch]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit selected layers instantly'), ''),
  attribution=(CONFIG.AUTHOR_NAME, CONFIG.AUTHOR_NAME, CONFIG.COPYRIGHT_YEARS),
)


procedure_.main()
