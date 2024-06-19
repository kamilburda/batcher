#!/usr/bin/env python3

"""Main plug-in file."""

import builtins
import gettext
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

gettext.bindtextdomain(
  'batcher', os.path.join(os.path.dirname(pg.utils.get_current_module_filepath()), 'locale'))
gettext.textdomain('batcher')

builtins._ = gettext.gettext

from src import actions as actions_
from src.gui import messages as messages_

messages_.set_gui_excepthook(
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


def plug_in_batch_export_layers(
      _procedure, run_mode, image, _n_drawables, _drawables, config, _data):
  _set_default_setting_source(_EXPORT_LAYERS_SOURCE_NAME)

  layer_tree = pg.itemtree.LayerTree(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(layer_tree, gui_main.ExportLayersDialog)
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(layer_tree)
  else:
    return _run_noninteractive(layer_tree, config)


def plug_in_batch_export_layers_quick(
      _procedure, run_mode, image, _n_drawables, _drawables, _config, _data):
  _set_default_setting_source(_EXPORT_LAYERS_SOURCE_NAME)

  layer_tree = pg.itemtree.LayerTree(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(layer_tree, gui_main.ExportLayersQuickDialog)
  else:
    return _run_with_last_vals(layer_tree)


def _run_noninteractive(layer_tree, config):
  settings_file = config.get_property('settings-file')

  if settings_file:
    gimp_status, message = _load_settings_from_file(settings_file)
    if gimp_status != Gimp.PDBStatusType.SUCCESS:
      return gimp_status, message
  else:
    _set_settings_from_args(SETTINGS['main'], config)

  _run_plugin_noninteractive(Gimp.RunMode.NONINTERACTIVE, layer_tree)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_with_last_vals(layer_tree):
  update_successful, message = _load_and_update_settings(SETTINGS, Gimp.RunMode.WITH_LAST_VALS)
  if not update_successful:
    return Gimp.PDBStatusType.EXECUTION_ERROR, message

  _run_plugin_noninteractive(Gimp.RunMode.WITH_LAST_VALS, layer_tree)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_interactive(layer_tree, gui_class):
  update_successful, message = _load_and_update_settings(SETTINGS, Gimp.RunMode.INTERACTIVE)
  if not update_successful:
    return Gimp.PDBStatusType.EXECUTION_ERROR, message

  gui_class(layer_tree, SETTINGS)

  return Gimp.PDBStatusType.SUCCESS, ''


def _run_plugin_noninteractive(run_mode, layer_tree):
  batcher = core.Batcher(
    run_mode, layer_tree.image, SETTINGS['main/procedures'], SETTINGS['main/constraints'])

  try:
    batcher.run(item_tree=layer_tree, **utils_.get_settings_for_batcher(SETTINGS['main']))
  except exceptions.BatcherCancelError:
    return Gimp.PDBStatusType.SUCCESS, 'canceled'
  except Exception as e:
    return Gimp.PDBStatusType.EXECUTION_ERROR, str(e)

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_default_setting_source(source_name):
  pg.config.SOURCE_NAME = source_name

  pg.setting.Persistor.set_default_setting_sources(
    {'persistent': pg.setting.GimpParasiteSource(source_name)})


def _load_and_update_settings(settings, run_mode):
  status, load_message = update.load_and_update(settings)

  if status != update.TERMINATE:
    return True, ''

  if run_mode == Gimp.RunMode.INTERACTIVE:
    response = messages_.display_message(
      (_('Settings for this plug-in could not be loaded and must be reset. Proceed?')
       + '\n'
       + _('Details: {}').format(load_message)),
      Gtk.MessageType.WARNING,
      buttons=Gtk.ButtonsType.YES_NO,
      button_response_id_to_focus=Gtk.ResponseType.NO)

    if response == Gtk.ResponseType.YES:
      pg.setting.Persistor.clear()
      actions_.clear(settings['main/procedures'])
      actions_.clear(settings['main/constraints'])

      return True, ''
    else:
      return (
        False,
        (_('Settings could not be loaded and were not reset.')
         + '\n\n'
         + _('Details: {}').format(load_message)))
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    pg.setting.Persistor.clear()

    return (
      False,
      (_('Settings could not be loaded and had to be reset.')
       + '\n\n'
       + _('Details: {}').format(load_message)))

  return False, load_message


def _load_settings_from_file(settings_file):
  settings_filepath = settings_file.get_path()

  if not os.path.isfile(settings_filepath):
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR,
      _('"{}" is not a valid file with settings').format(settings_filepath))

  setting_source = pg.setting.JsonFileSource(pg.config.SOURCE_NAME, settings_filepath)

  status, message = update.load_and_update(SETTINGS, sources={'persistent': setting_source})
  if status == update.TERMINATE:
    error_message = _('Failed to import settings from file "{}".').format(settings_filepath)

    if message:
      error_message += ' ' + _('Details: {}').format(message)

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


pg.register_procedure(
  plug_in_batch_export_layers,
  arguments=pg.setting.create_params(SETTINGS['main']),
  menu_label=_('E_xport Layers...'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Export layers as separate images'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_export_layers_quick,
  menu_label=_('E_xport Layers (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Export layers as separate images instantly'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.main()
