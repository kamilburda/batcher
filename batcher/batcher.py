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
from src import builtin_constraints
from src.gui import messages as messages_

messages_.set_gui_excepthook(
  title=pg.config.PLUGIN_TITLE,
  report_uri_list=pg.config.BUG_REPORT_URL_LIST,
)

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import core
from src import exceptions
from src import plugin_settings
from src import update
from src import utils as utils_
from src.gui import main as gui_main
from src.procedure_groups import *


SETTINGS_EXPORT_LAYERS = plugin_settings.create_settings_for_export_layers()
SETTINGS_EDIT_LAYERS = plugin_settings.create_settings_for_edit_layers()


def plug_in_batch_export_layers(_procedure, run_mode, image, _drawables, config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingGui,
      gui_class_kwargs=dict(mode='export', current_image=image))
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(SETTINGS_EXPORT_LAYERS, layer_tree, mode='export')
  else:
    return _run_noninteractive(SETTINGS_EXPORT_LAYERS, layer_tree, config, mode='export')


def plug_in_batch_export_layers_quick(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingQuickGui,
      gui_class_kwargs=dict(mode='export', title=_('Export Layers (Quick)'), current_image=image))
  else:
    return _run_with_last_vals(SETTINGS_EXPORT_LAYERS, layer_tree, mode='export')


def plug_in_batch_export_selected_layers(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EXPORT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingQuickGui,
      gui_class_kwargs=dict(mode='export', title=_('Export Selected Layers'), current_image=image),
      process_loaded_settings_func=_set_constraints_to_only_selected_layers)
  else:
    return _run_with_last_vals(
      SETTINGS_EXPORT_LAYERS,
      layer_tree,
      mode='export',
      process_loaded_settings_func=_set_constraints_to_only_selected_layers)


def plug_in_batch_edit_layers(_procedure, run_mode, image, _drawables, config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingGui,
      gui_class_kwargs=dict(mode='edit', current_image=image))
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    return _run_with_last_vals(SETTINGS_EDIT_LAYERS, layer_tree, mode='edit')
  else:
    return _run_noninteractive(SETTINGS_EDIT_LAYERS, layer_tree, config, mode='edit')


def plug_in_batch_edit_layers_quick(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingQuickGui,
      gui_class_kwargs=dict(mode='edit', title=_('Edit Layers (Quick)'), current_image=image))
  else:
    return _run_with_last_vals(SETTINGS_EDIT_LAYERS, layer_tree, mode='edit')


def plug_in_batch_edit_selected_layers(_procedure, run_mode, image, _drawables, _config, _data):
  _set_procedure_group_and_default_setting_source(EDIT_LAYERS_GROUP)

  layer_tree = pg.itemtree.LayerTree()
  layer_tree.add_from_image(image)

  if run_mode == Gimp.RunMode.INTERACTIVE:
    return _run_interactive(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      gui_main.BatchLayerProcessingQuickGui,
      gui_class_kwargs=dict(mode='edit', title=_('Edit Selected Layers'), current_image=image),
      process_loaded_settings_func=_set_constraints_to_only_selected_layers)
  else:
    return _run_with_last_vals(
      SETTINGS_EDIT_LAYERS,
      layer_tree,
      mode='edit',
      process_loaded_settings_func=_set_constraints_to_only_selected_layers)


def _run_noninteractive(settings, item_tree, config, mode):
  if pg.config.PROCEDURE_GROUP == CONVERT_GROUP:
    item_tree.add(config.get_property('inputs'))

  settings_file = config.get_property('settings-file')

  if settings_file:
    gimp_status, message = _load_settings_from_file(settings, settings_file)
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
  if pg.config.PROCEDURE_GROUP == CONVERT_GROUP:
    batcher = core.ImageBatcher(
      item_tree=item_tree,
      procedures=settings['main/procedures'],
      constraints=settings['main/constraints'],
      refresh_item_tree=False,
      initial_export_run_mode=run_mode,
      edit_mode=mode == 'edit',
    )
  else:
    batcher = core.LayerBatcher(
      item_tree=item_tree,
      procedures=settings['main/procedures'],
      constraints=settings['main/constraints'],
      refresh_item_tree=False,
      initial_export_run_mode=run_mode,
      edit_mode=mode == 'edit',
    )

  try:
    batcher.run(
      **utils_.get_settings_for_batcher(settings['main']))
  except exceptions.BatcherCancelError:
    return Gimp.PDBStatusType.SUCCESS, 'canceled'
  except Exception as e:
    return Gimp.PDBStatusType.EXECUTION_ERROR, str(e)

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_procedure_group_and_default_setting_source(procedure_group):
  pg.config.PROCEDURE_GROUP = procedure_group

  pg.setting.Persistor.set_default_setting_sources(
    {'persistent': pg.setting.GimpParasiteSource(procedure_group)})


def _load_and_update_settings(settings, run_mode):
  status, load_message = update.load_and_update(settings, procedure_group=pg.config.PROCEDURE_GROUP)

  if status != update.TERMINATE:
    return True, ''

  if run_mode == Gimp.RunMode.INTERACTIVE:
    messages_.display_alert_message(
      title=pg.config.PLUGIN_TITLE,
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
      report_uri_list=pg.config.BUG_REPORT_URL_LIST)

    pg.setting.Persistor.clear()
    actions_.clear(settings['main/procedures'])
    actions_.clear(settings['main/constraints'])

    return True, ''
  elif run_mode == Gimp.RunMode.WITH_LAST_VALS:
    pg.setting.Persistor.clear()

    return (
      False,
      (_('Settings could not be loaded and had to be reset.')
       + '\n\n'
       + _('Details: {}').format(load_message)))

  return False, load_message


def _load_settings_from_file(settings, settings_file):
  settings_filepath = settings_file.get_path()

  if not os.path.isfile(settings_filepath):
    return (
      Gimp.PDBStatusType.EXECUTION_ERROR,
      _('"{}" is not a valid file with settings').format(settings_filepath))

  setting_source = pg.setting.JsonFileSource(pg.config.PROCEDURE_GROUP, settings_filepath)

  status, message = update.load_and_update(
    settings, sources={'persistent': setting_source}, procedure_group=pg.config.PROCEDURE_GROUP)
  if status == update.TERMINATE:
    error_message = _('Failed to import settings from file "{}".').format(settings_filepath)

    if message:
      error_message += ' ' + _('Details: {}').format(message)

    return Gimp.PDBStatusType.EXECUTION_ERROR, error_message

  return Gimp.PDBStatusType.SUCCESS, ''


def _set_settings_from_args(settings, config):
  args_as_settings = [
    setting for setting in settings
    if isinstance(setting, pg.setting.Setting) and setting.can_be_used_in_pdb()]

  args = [config.get_property(prop.name) for prop in config.list_properties()]
  # `config.list_properties()` contains additional properties or parameters
  # added by GIMP (e.g. `Gimp.Procedure` object). It appears these are added
  # before the plug-in-specific PDB parameters.
  args = args[max(len(args) - len(args_as_settings), 0):]

  for setting, arg in zip(args_as_settings, args):
    setting.set_value(arg)


def _set_constraints_to_only_selected_layers(settings):
  actions_.clear(settings['main/constraints'], add_initial_actions=False)

  actions_.add(
    settings['main/constraints'], builtin_constraints.BUILTIN_CONSTRAINTS['selected_in_gimp'])


pg.register_procedure(
  plug_in_batch_export_layers,
  arguments=pg.setting.create_params(SETTINGS_EXPORT_LAYERS['main']),
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
  documentation=(_('Quickly export layers as separate images'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_export_selected_layers,
  menu_label=_('E_xport Selected Layers'),
  menu_path='<Layers>/Layers Menu/[Batch]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Quickly export selected layers as separate images'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_edit_layers,
  arguments=pg.setting.create_params(SETTINGS_EDIT_LAYERS['main']),
  menu_label=_('E_dit Layers...'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit layers'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_edit_layers_quick,
  menu_label=_('E_dit Layers (Quick)'),
  menu_path='<Image>/File/[Export]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.NO_DRAWABLES
    | Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit layers instantly'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.register_procedure(
  plug_in_batch_edit_selected_layers,
  menu_label=_('E_dit Selected Layers'),
  menu_path='<Layers>/Layers Menu/[Batch]',
  image_types='*',
  sensitivity_mask=(
    Gimp.ProcedureSensitivityMask.DRAWABLE
    | Gimp.ProcedureSensitivityMask.DRAWABLES),
  documentation=(_('Batch-edit selected layers instantly'), ''),
  attribution=(pg.config.AUTHOR_NAME, pg.config.AUTHOR_NAME, pg.config.COPYRIGHT_YEARS),
)


pg.main()
