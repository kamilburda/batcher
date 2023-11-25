#!/usr/bin/env python3

"""Main plug-in file."""

import os
import sys

import pygimplib as pg

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import core
from src import exceptions
from src import settings_main
from src import update
from src import utils as utils_
from src.gui import main as gui_main


SETTINGS = settings_main.create_settings()


def plug_in_export_layers(run_mode, image, *args):
  SETTINGS['special/run_mode'].set_value(run_mode)
  SETTINGS['special/image'].set_value(image)
  
  layer_tree = pg.itemtree.LayerTree(image, name=pg.config.SOURCE_NAME)
  
  status, _unused = update.update(
    SETTINGS, 'ask_to_clear' if run_mode == Gimp.RunMode.INTERACTIVE else 'clear')
  if status == update.ABORT:
    return
  
  if run_mode == Gimp.RunMode.INTERACTIVE:
    _run_export_layers_interactive(layer_tree)
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    _run_with_last_vals(layer_tree)
  else:
    _run_noninteractive(layer_tree, args)


def plug_in_export_layers_repeat(run_mode, image):
  layer_tree = pg.itemtree.LayerTree(image, name=pg.config.SOURCE_NAME)
  
  status, _unused = update.update(
    SETTINGS, 'ask_to_clear' if run_mode == Gimp.RunMode.INTERACTIVE else 'clear')
  if status == update.ABORT:
    return
  
  if run_mode == Gimp.RunMode.INTERACTIVE:
    SETTINGS['special/first_plugin_run'].load()
    if SETTINGS['special/first_plugin_run'].value:
      _run_export_layers_interactive(layer_tree)
    else:
      _run_export_layers_repeat_interactive(layer_tree)
  else:
    _run_with_last_vals(layer_tree)


def plug_in_export_layers_with_config(run_mode, image, config_filepath):
  if not config_filepath or not os.path.isfile(config_filepath):
    sys.exit(1)
  
  layer_tree = pg.itemtree.LayerTree(image, name=pg.config.SOURCE_NAME)
  
  if config_filepath.endswith('.pkl'):
    setting_source_class = pg.setting.PickleFileSource
  else:
    setting_source_class = pg.setting.JsonFileSource
  
  setting_source = setting_source_class(
    pg.config.SOURCE_NAME, config_filepath, source_type='persistent')
  
  status, _unused = update.update(
    SETTINGS, handle_invalid='abort', sources={'persistent': setting_source})
  if status == update.ABORT:
    sys.exit(1)
  
  load_result = SETTINGS.load({'persistent': setting_source})
  if load_result.status not in [
       pg.setting.Persistor.SUCCESS, pg.setting.Persistor.PARTIAL_SUCCESS]:
    sys.exit(1)
  
  _run_plugin_noninteractive(Gimp.RunMode.NONINTERACTIVE, layer_tree)


def _run_noninteractive(layer_tree, args):
  main_settings = [
    setting for setting in SETTINGS['main'].walk()
    if setting.can_be_registered_to_pdb()]
  
  for setting, arg in zip(main_settings, pg.setting.iter_args(args, main_settings)):
    setting.set_value(arg)
  
  _run_plugin_noninteractive(Gimp.RunMode.NONINTERACTIVE, layer_tree)


def _run_with_last_vals(layer_tree):
  SETTINGS['main'].load()
  
  _run_plugin_noninteractive(Gimp.RunMode.WITH_LAST_VALS, layer_tree)


def _run_export_layers_interactive(layer_tree):
  gui_main.ExportLayersDialog(layer_tree, SETTINGS)


def _run_export_layers_repeat_interactive(layer_tree):
  gui_main.ExportLayersRepeatDialog(layer_tree, SETTINGS)


def _run_plugin_noninteractive(run_mode, layer_tree):
  batcher = core.Batcher(
    run_mode, layer_tree.image, SETTINGS['main/procedures'], SETTINGS['main/constraints'])
  
  try:
    batcher.run(item_tree=layer_tree, **utils_.get_settings_for_batcher(SETTINGS['main']))
  except exceptions.BatcherCancelError:
    pass


pg.register_procedure(
  plug_in_export_layers,
  arguments=pg.setting.create_params(SETTINGS['special'], SETTINGS['main']),
  menu_label=_('E_xport Layers...'),
  menu_path='<Image>/File/Export',
  documentation=(_('Export layers as separate images'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_export_layers_repeat,
  arguments=pg.setting.create_params(SETTINGS['special']),
  menu_label=_('E_xport Layers (repeat)'),
  menu_path='<Image>/File/Export',
  documentation=(
    _('Run "{}" with the last values specified').format(pg.config.PLUGIN_TITLE),
    _('If the plug-in is run for the first time (i.e. no last values exist),'
      ' default values will be used.'),
  ),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_export_layers_with_config,
  arguments=pg.setting.create_params(
    SETTINGS['special/run_mode'],
    SETTINGS['special/image'],
    pg.setting.StringSetting(name='config_filepath', display_name=_('Path to configuration file')),
  ),
  documentation=(
    _('Run "{}" with the specified configuration file').format(pg.config.PLUGIN_TITLE),
    _('The configuration file can be obtained by exporting settings'
      " in the plug-in's interactive dialog."
      ' This procedure will fail if the specified configuration file does not exist'
      ' or is not valid.')
  ),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)

pg.main()
