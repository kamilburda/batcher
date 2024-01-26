#!/usr/bin/env python3

"""Main plug-in file."""

import os

import pygimplib as pg

from src import _gui_messages

_gui_messages.set_gui_excepthook(
  title=pg.config.PLUGIN_TITLE,
  report_uri_list=pg.config.BUG_REPORT_URL_LIST,
)

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import core
from src import exceptions
from src import plugin_settings
from src import update
from src import utils as utils_
from src.gui import main as gui_main


SETTINGS = plugin_settings.create_settings()

_EXPORT_LAYERS_SOURCE_NAME = 'plug-in-batch-export-layers'


def plug_in_batch_export_layers(_procedure, run_mode, image, _n_drawables, _drawables, config):
  SETTINGS['special/run_mode'].set_value(run_mode)
  SETTINGS['special/image'].set_value(image)

  _set_default_setting_source(_EXPORT_LAYERS_SOURCE_NAME)

  status = _update_plugin(SETTINGS, run_mode)
  if status == update.TERMINATE:
    return

  layer_tree = pg.itemtree.LayerTree(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_export_layers_interactive(layer_tree)
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(layer_tree)
  else:
    return _run_noninteractive(layer_tree, config)


def plug_in_batch_export_layers_now(_procedure, run_mode, image, _n_drawables, _drawables, _config):
  SETTINGS['special/run_mode'].set_value(run_mode)
  SETTINGS['special/image'].set_value(image)

  _set_default_setting_source(_EXPORT_LAYERS_SOURCE_NAME)

  status = _update_plugin(SETTINGS, run_mode)
  if status == update.TERMINATE:
    return

  layer_tree = pg.itemtree.LayerTree(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_export_layers_now_interactive(layer_tree)
  else:
    return _run_with_last_vals(layer_tree)


def _set_default_setting_source(source_name):
  pg.config.SOURCE_NAME = source_name

  pg.setting.Persistor.set_default_setting_sources(
    {'persistent': pg.setting.GimpParasiteSource(source_name)})


def _update_plugin(settings, run_mode):
  status, _message = update.update(
    settings,
    'ask_to_clear' if run_mode == Gimp.RunMode.INTERACTIVE else 'clear')

  return status


def _load_settings_from_file(settings_file):
  settings_filepath = settings_file.get_path()

  if not os.path.isfile(settings_filepath):
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR,
      _('"{}" is not a valid file with settings').format(settings_filepath))

  setting_source = pg.setting.JsonFileSource(pg.config.SOURCE_NAME, settings_filepath)

  status, update_message = update.update(
    SETTINGS, handle_invalid='terminate', sources={'persistent': setting_source})
  if status == update.TERMINATE:
    error_message = _('Failed to update the file with settings to the latest version.')

    if update_message:
      error_message += ' ' + _('Reason: {}').format(update_message)

    return Gimp.PDBStatusType.EXECUTION_ERROR, error_message

  load_result = SETTINGS.load({'persistent': setting_source})
  if load_result.status not in [
       pg.setting.Persistor.SUCCESS, pg.setting.Persistor.PARTIAL_SUCCESS]:
    error_message = _('Failed to load settings from file.')

    load_message = '\n'.join(load_result.messages_per_source.values()).strip()
    if load_message:
      error_message += ' ' + _('Reason: {}').format(load_message)

    return Gimp.PDBStatusType.EXECUTION_ERROR, error_message

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_settings_from_args(settings, config):
  args_as_settings = [
    setting for setting in settings
    if isinstance(setting, pg.setting.Setting) and setting.can_be_registered_to_pdb()]

  args = [config.get_property(prop.name) for prop in config.list_properties()]
  # `config.list_properties()` contains additional properties or parameters
  # added by GIMP (e.g. `Gimp.Procedure` object). It appears these are added
  # before the plug-in-specific PDB parameters.
  args = args[max(len(args) - len(args_as_settings), 0):]

  for setting, arg in zip(args_as_settings, pg.setting.iter_args(args, args_as_settings)):
    setting.set_value(arg)


def _run_noninteractive(layer_tree, config):
  settings_file = config.get_property('settings-file')

  if settings_file:
    gimp_status, message = _load_settings_from_file(settings_file)
    if gimp_status != Gimp.PDBStatusType.SUCCESS:
      return gimp_status, message
  else:
    _set_settings_from_args(SETTINGS['main'], config)

  _run_plugin_noninteractive(Gimp.RunMode.NONINTERACTIVE, layer_tree)


def _run_with_last_vals(layer_tree):
  SETTINGS['main'].load()
  
  _run_plugin_noninteractive(Gimp.RunMode.WITH_LAST_VALS, layer_tree)


def _run_export_layers_interactive(layer_tree):
  gui_main.ExportLayersDialog(layer_tree, SETTINGS)


def _run_export_layers_now_interactive(layer_tree):
  gui_main.ExportLayersNowDialog(layer_tree, SETTINGS)


def _run_plugin_noninteractive(run_mode, layer_tree):
  batcher = core.Batcher(
    run_mode, layer_tree.image, SETTINGS['main/procedures'], SETTINGS['main/constraints'])

  try:
    batcher.run(item_tree=layer_tree, **utils_.get_settings_for_batcher(SETTINGS['main']))
  except exceptions.BatcherCancelError:
    pass
  except Exception as e:
    return Gimp.PDBStatusType.EXECUTION_ERROR, str(e)


pg.register_procedure(
  plug_in_batch_export_layers,
  arguments=pg.setting.create_params(SETTINGS['main']),
  menu_label=_('E_xport Layers...'),
  menu_path='<Image>/File/{}'.format(_('Batch')),
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Export layers as separate images'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_export_layers_now,
  menu_label=_('E_xport Layers Now'),
  menu_path='<Image>/File/{}'.format(_('Batch')),
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Export layers as separate images instantly'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.main()
