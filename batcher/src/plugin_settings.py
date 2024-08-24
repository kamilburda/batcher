"""Plug-in settings."""

import collections

import pygimplib as pg

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures
from src import export as export_
from src import overwrite
# Despite being unused, `setting_classes` must be imported so that the
# setting and GUI classes defined there are properly registered (via respective
# metaclasses in `pg.setting.meta`).
# noinspection PyUnresolvedReferences
from src import setting_classes
from src import utils


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
      'default_value': pg.utils.get_pictures_directory(),
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
        ('rename_existing', _('Rename _existing file'), overwrite.OverwriteModes.RENAME_EXISTING)],
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
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

  export_settings = pg.setting.Group(
    name='export',
    setting_attributes={
      'pdb_type': None,
    },
  )

  export_arguments = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['export_for_export_layers']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings()
  gui_settings.add([
    _create_auto_close_setting_dict(True),
    _create_show_quick_settings_setting_dict(),
  ])

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
    actions_.create(
      name='procedures',
      initial_actions=[builtin_procedures.BUILTIN_PROCEDURES['use_layer_size']]),
  ])

  visible_constraint_dict = utils.semi_deep_copy(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False
  
  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict]),
  ])

  _set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)
  
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
  gui_settings.add([_create_auto_close_setting_dict(False)])

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

  rename_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['rename_for_edit_layers'])
  rename_procedure_dict['enabled'] = False
  rename_procedure_dict['display_options_on_create'] = False
  rename_procedure_dict['arguments'][0]['default_value'] = 'image[001]'

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[rename_procedure_dict]),
  ])

  visible_constraint_dict = utils.semi_deep_copy(builtin_constraints.BUILTIN_CONSTRAINTS['visible'])
  visible_constraint_dict['enabled'] = False

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict]),
  ])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)

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


def _create_auto_close_setting_dict(default_value):
  return {
    'type': 'bool',
    'name': 'auto_close',
    'default_value': default_value,
    'display_name': _('Close when Done'),
    'gui_type': 'check_menu_item',
  }


def _create_show_quick_settings_setting_dict():
  return {
    'type': 'bool',
    'name': 'show_quick_settings',
    'default_value': True,
    'gui_type': None,
  }


def _set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(main_settings):
  _set_sensitive_for_image_name_pattern_in_export(
    main_settings['export/export_mode'],
    main_settings['export/single_image_name_pattern'])

  main_settings['export/export_mode'].connect_event(
    'value-changed',
    _set_sensitive_for_image_name_pattern_in_export,
    main_settings['export/single_image_name_pattern'])


def _set_file_extension_options_for_default_export_procedure(main_settings):
  _show_hide_file_format_export_options(
    main_settings['export/file_format_mode'],
    main_settings['export/file_format_options'])

  main_settings['file_format_mode'].connect_event(
    'value-changed',
    _show_hide_file_format_export_options,
    main_settings['export/file_format_options'])

  _set_file_format_export_options(
    main_settings['file_extension'],
    main_settings['export/file_format_options'])

  main_settings['file_extension'].connect_event(
    'value-changed',
    _set_file_format_export_options,
    main_settings['export/file_format_options'])


def _on_after_add_export_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('export_for_'):
    _set_sensitive_for_image_name_pattern_in_export(
      procedure['arguments/export_mode'],
      procedure['arguments/single_image_name_pattern'])
    
    procedure['arguments/export_mode'].connect_event(
      'value-changed',
      _set_sensitive_for_image_name_pattern_in_export,
      procedure['arguments/single_image_name_pattern'])


def _set_sensitive_for_image_name_pattern_in_export(
      export_mode_setting, single_image_name_pattern_setting):
  if export_mode_setting.value == export_.ExportModes.ENTIRE_IMAGE_AT_ONCE:
    single_image_name_pattern_setting.gui.set_sensitive(True)
  else:
    single_image_name_pattern_setting.gui.set_sensitive(False)


def _set_file_format_export_options(file_extension_setting, file_format_options_setting):
  file_format_options_setting.set_active_file_format(file_extension_setting.value)


def _show_hide_file_format_export_options(file_format_mode_setting, file_format_options_setting):
  file_format_options_setting.gui.set_visible(file_format_mode_setting.is_item('use_explicit_values'))


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
