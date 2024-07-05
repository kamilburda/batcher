"""Plug-in settings."""

import collections

from gi.repository import GLib

import pygimplib as pg

from src import actions
from src import builtin_constraints
from src import builtin_procedures
from src import export as export_
from src import overwrite
# Despite being unused, `setting_classes` must be imported so that the
# setting and GUI classes defined there are properly registered (via respective
# metaclasses in `pg.setting.meta`).
# noinspection PyUnresolvedReferences
from src import setting_classes


def create_settings_for_export_layers():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })
  
  settings['main'].add([
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
    },
    {
      'type': 'string',
      'name': 'output_directory',
      'default_value': GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
      'display_name': _('Output directory'),
      'gui_type': None,
      'auto_update_gui_to_setting': False,
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[layer name]',
      'display_name': _('Layer filename pattern'),
      'description': _('Layer filename pattern (empty string = layer name)'),
      'gui_type': None,
      'auto_update_gui_to_setting': False,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': [
        ('replace', _('_Replace'), overwrite.OverwriteModes.REPLACE),
        ('skip', _('_Skip'), overwrite.OverwriteModes.SKIP),
        ('rename_new', _('Rename _new file'), overwrite.OverwriteModes.RENAME_NEW),
        ('rename_existing', _('Rename _existing file'),
         overwrite.OverwriteModes.RENAME_EXISTING)],
      'display_name': _('Overwrite mode (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'images_and_gimp_items',
      'name': 'selected_layers',
      'default_value': collections.defaultdict(set),
      'display_name': _('Selected layers'),
      'pdb_type': None,
      'gui_type': None,
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  gui_settings = _create_gui_settings()

  size_gui_settings = pg.setting.Group(name='size')

  size_gui_settings.add([
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': (),
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': (660, 540),
    },
    {
      'type': 'integer',
      'name': 'paned_outside_previews_position',
      'default_value': 370,
      'gui_type': None,
    },
    {
      'type': 'float',
      'name': 'paned_between_previews_position',
      'default_value': 260,
      'gui_type': None,
    },
  ])

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  settings['main'].add([
    actions.create(
      name='procedures',
      initial_actions=[builtin_procedures.BUILTIN_PROCEDURES['use_layer_size']]),
  ])

  visible_constraint_dict = dict(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False
  visible_constraint_dict['display_options_on_create'] = False
  
  settings['main'].add([
    actions.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict]),
  ])
  
  settings['main/procedures'].connect_event('after-add-action', _on_after_add_procedure)

  settings['main/procedures'].connect_event(
    'after-add-action', _on_after_add_procedure_for_export_layers, settings['main'])
  
  settings['main/constraints'].connect_event(
    'after-add-action',
    _on_after_add_constraint,
    settings['main/selected_layers'])
  
  return settings


def create_settings_for_edit_layers():
  settings = pg.setting.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
      }
    ]
  })

  settings['main'].add([
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'images_and_gimp_items',
      'name': 'selected_layers',
      'default_value': collections.defaultdict(set),
      'display_name': _('Selected layers'),
      'pdb_type': None,
      'gui_type': None,
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  gui_settings = _create_gui_settings()

  size_gui_settings = pg.setting.Group(name='size')

  size_gui_settings.add([
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': (),
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': (570, 500),
    },
    {
      'type': 'integer',
      'name': 'paned_outside_previews_position',
      'default_value': 300,
      'gui_type': None,
    },
    {
      'type': 'float',
      'name': 'paned_between_previews_position',
      'default_value': 220,
      'gui_type': None,
    },
  ])

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  rename_procedure_dict = dict(builtin_procedures.BUILTIN_PROCEDURES['rename_for_edit_layers'])
  rename_procedure_dict['enabled'] = False
  rename_procedure_dict['display_options_on_create'] = False
  rename_procedure_dict['arguments'][0]['default_value'] = 'image[001]'

  settings['main'].add([
    actions.create(
      name='procedures',
      initial_actions=[rename_procedure_dict]),
  ])

  visible_constraint_dict = dict(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False
  visible_constraint_dict['display_options_on_create'] = False

  settings['main'].add([
    actions.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict]),
  ])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_procedure)

  settings['main/constraints'].connect_event(
    'after-add-action',
    _on_after_add_constraint,
    settings['main/selected_layers'])

  return settings


def _create_gui_settings():
  gui_settings = pg.setting.Group(name='gui')

  procedure_browser_settings = pg.setting.Group(name='procedure_browser')

  procedure_browser_settings.add([
    {
      'type': 'integer',
      'name': 'paned_position',
      'default_value': 325,
      'gui_type': None,
    },
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': (),
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': (675, 450),
    },
  ])

  gui_settings.add([
    {
      'type': 'bool',
      'name': 'name_preview_sensitive',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_sensitive',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_automatic_update',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'bool',
      'name': 'image_preview_automatic_update_if_below_maximum_duration',
      'default_value': True,
      'gui_type': None,
    },
    {
      'type': 'images_and_gimp_items',
      'name': 'name_preview_layers_collapsed_state',
    },
    {
      'type': 'images_and_gimp_items',
      'name': 'image_preview_displayed_layers',
    },
    {
      'type': 'images_and_directories',
      'name': 'images_and_directories',
    },
    procedure_browser_settings,
  ])

  return gui_settings


def _on_after_add_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value == 'export':
    _set_sensitive_for_image_name_pattern_in_export(
      procedure['arguments/export_mode'],
      procedure['arguments/single_image_name_pattern'])
    
    procedure['arguments/export_mode'].connect_event(
      'value-changed',
      _set_sensitive_for_image_name_pattern_in_export,
      procedure['arguments/single_image_name_pattern'])


def _on_after_add_procedure_for_export_layers(
      _procedures, procedure, _orig_procedure_dict, main_settings):
  if procedure['orig_name'].value == 'export':
    _set_initial_output_directory_in_export_if_undefined(
      procedure['arguments/output_directory'],
      main_settings['output_directory'])

    procedure['arguments/output_directory'].connect_event(
      'value-changed',
      _set_initial_output_directory_in_export_if_undefined,
      main_settings['output_directory'])


def _set_initial_output_directory_in_export_if_undefined(
      export_output_directory_setting, output_directory_setting):
  # The check avoids plug-in failing to display the GUI due to an invalid
  # directory.
  if output_directory_setting.value:
    # This check prevents the directory for the custom Export procedure to be
    # overwritten at each start of the plug-in.
    if export_output_directory_setting.value is None:
      export_output_directory_setting.set_value(output_directory_setting.value)
  else:
    # Assign a safe value
    if export_output_directory_setting.value is None:
      export_output_directory_setting.set_value(output_directory_setting.default_value)


def _set_sensitive_for_image_name_pattern_in_export(
      export_mode_setting, single_image_name_pattern_setting):
  if export_mode_setting.value == export_.ExportModes.ENTIRE_IMAGE_AT_ONCE:
    single_image_name_pattern_setting.gui.set_sensitive(True)
  else:
    single_image_name_pattern_setting.gui.set_sensitive(False)


def _on_after_add_constraint(
      _constraints,
      constraint,
      _orig_constraint_dict,
      selected_items_setting):
  if constraint['orig_name'].value == 'selected_in_preview':
    constraint['arguments/selected_layers'].gui.set_visible(False)
    _sync_selected_items_with_constraint(selected_items_setting, constraint)


def _sync_selected_items_with_constraint(selected_items_setting, constraint):
  
  def _on_selected_items_changed(selected_items_setting_, selected_items_constraint):
    selected_items_constraint['arguments/selected_layers'].set_value(selected_items_setting_.value)

  _on_selected_items_changed(selected_items_setting, constraint)
  
  selected_items_setting.connect_event('value-changed', _on_selected_items_changed, constraint)
