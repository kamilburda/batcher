"""Plug-in settings."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

import pygimplib as pg

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures
# Despite being unused, `setting_classes` must be imported so that the
# setting and GUI classes defined there are properly registered (via respective
# metaclasses in `pg.setting.meta`).
# noinspection PyUnresolvedReferences
from src import setting_classes
from src import utils


_RELATED_WIDGETS_LEFT_MARGIN = 15


def create_settings_for_convert():
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
      'type': 'enum',
      'name': 'run_mode',
      'enum_type': Gimp.RunMode,
      'default_value': Gimp.RunMode.NONINTERACTIVE,
      'display_name': _('Run mode'),
      'description': _('The run mode'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file',
      'name': 'inputs',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _(
        'Text file containing input files and folders on each line'
        ' (non-interactive run mode only)'),
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'int',
      'name': 'max_num_inputs',
      'default_value': 2000,
      'min_value': 0,
      'display_name': _(
        'Maximum number of input files to process'
        ' (set to 0 to remove this restriction; non-interactive run mode only)'),
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'description': _('Image filename pattern (empty string = image name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
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
    builtin_procedures.BUILTIN_PROCEDURES['export_for_convert']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings('image_file_tree_items')
  gui_settings.add([
    _create_inputs_interactive_setting_dict(),
    _create_show_original_item_names_setting_dict(False),
    _create_keep_inputs_setting_dict(True, _('Keep Input Images')),
    _create_auto_close_setting_dict(False),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 640),
      paned_outside_previews_position=330,
      paned_between_previews_position=300,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  remove_folder_structure_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['remove_folder_structure'])
  remove_folder_structure_procedure_dict['enabled'] = False
  remove_folder_structure_procedure_dict['display_options_on_create'] = False

  scale_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['scale_for_images'])
  scale_procedure_dict['enabled'] = False
  scale_procedure_dict['display_options_on_create'] = False

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[
        remove_folder_structure_procedure_dict,
        scale_procedure_dict,
      ]),
  ])

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['recognized_file_format']]),
  ])

  _set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(settings['main'])
  _set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)
  settings['main/procedures'].connect_event('after-add-action', _on_after_add_scale_procedure)

  return settings


def create_settings_for_export_images():
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
      'type': 'enum',
      'name': 'run_mode',
      'enum_type': Gimp.RunMode,
      'default_value': Gimp.RunMode.NONINTERACTIVE,
      'display_name': _('Run mode'),
      'description': _('The run mode'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'file_extension',
      'name': 'file_extension',
      'default_value': 'png',
      'display_name': _('File extension'),
      'adjust_value': True,
      'auto_update_gui_to_setting': False,
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[image name]',
      'display_name': _('Image filename pattern'),
      'description': _('Image filename pattern (empty string = image name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
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
    builtin_procedures.BUILTIN_PROCEDURES['export_for_export_images']['arguments'])
  # Remove settings already present in the main settings.
  export_arguments = export_arguments[2:]

  export_settings.add(export_arguments)

  settings['main'].add([export_settings])

  gui_settings = _create_gui_settings('gimp_image_tree_items')
  gui_settings.add([
    _create_auto_close_setting_dict(True),
    _create_show_quick_settings_setting_dict(),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 540),
      paned_outside_previews_position=330,
      paned_between_previews_position=225,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  scale_procedure_dict = utils.semi_deep_copy(
    builtin_procedures.BUILTIN_PROCEDURES['scale_for_images'])
  scale_procedure_dict['enabled'] = False
  scale_procedure_dict['display_options_on_create'] = False

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[
        scale_procedure_dict,
      ]),
  ])

  not_saved_or_exported_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['not_saved_or_exported'])
  not_saved_or_exported_constraint_dict['enabled'] = False

  with_unsaved_changes_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['with_unsaved_changes'])
  with_unsaved_changes_constraint_dict['enabled'] = False

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        not_saved_or_exported_constraint_dict,
        with_unsaved_changes_constraint_dict,
      ]),
  ])

  _set_sensitive_for_image_name_pattern_in_export_for_default_export_procedure(settings['main'])
  _set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)
  settings['main/procedures'].connect_event('after-add-action', _on_after_add_scale_procedure)

  return settings


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
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'output_directory',
      'default_value': Gio.file_new_for_path(pg.utils.get_default_dirpath()),
      'action': Gimp.FileChooserAction.SELECT_FOLDER,
      'display_name': _('Output folder'),
    },
    {
      'type': 'name_pattern',
      'name': 'name_pattern',
      'default_value': '[layer name]',
      'display_name': _('Layer filename pattern'),
      'description': _('Layer filename pattern (empty string = layer name)'),
      'gui_type': None,
    },
    {
      'type': 'choice',
      'name': 'overwrite_mode',
      'default_value': 'rename_new',
      'items': utils.semi_deep_copy(builtin_procedures.INTERACTIVE_OVERWRITE_MODES_LIST),
      'display_name': _('How to handle conflicting files (non-interactive run mode only)'),
      'gui_type': None,
    },
    {
      'type': 'file',
      'name': 'settings_file',
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'pdb_type': None,
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
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

  gui_settings = _create_gui_settings('gimp_item_tree_items')
  gui_settings.add([
    _create_auto_close_setting_dict(True),
    _create_show_quick_settings_setting_dict(),
    _create_images_and_directories_setting_dict(),
  ])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(640, 540),
      paned_outside_previews_position=330,
      paned_between_previews_position=225,
    )
  )

  gui_settings.add([size_gui_settings])

  settings.add([gui_settings])

  settings['main'].add([
    actions_.create(
      name='procedures',
      initial_actions=[builtin_procedures.BUILTIN_PROCEDURES['resize_to_layer_size']]),
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
  _set_file_extension_options_for_default_export_procedure(settings['main'])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)
  settings['main/procedures'].connect_event('after-add-action', _on_after_add_scale_procedure)

  settings['main/procedures'].connect_event(
    'after-add-action',
    _on_after_add_insert_background_foreground_for_layers,
    settings['main/tagged_items'],
  )

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
      'action': Gimp.FileChooserAction.OPEN,
      'none_ok': True,
      'display_name': _('File with saved settings'),
      'description': _('File with saved settings (optional)'),
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'tagged_items',
      'name': 'tagged_items',
      'default_value': [],
      'pdb_type': None,
      'gui_type': None,
      'tags': ['ignore_reset', 'ignore_load', 'ignore_save'],
    },
    {
      'type': 'string',
      'name': 'plugin_version',
      'default_value': pg.config.PLUGIN_VERSION,
      'pdb_type': None,
      'gui_type': None,
    },
  ])

  gui_settings = _create_gui_settings('gimp_item_tree_items')
  gui_settings.add([_create_auto_close_setting_dict(False)])

  size_gui_settings = pg.setting.Group(name='size')
  size_gui_settings.add(
    _create_size_gui_settings(
      dialog_position=(),
      dialog_size=(570, 500),
      paned_outside_previews_position=300,
      paned_between_previews_position=220,
    )
  )

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

  selected_in_gimp_constraint_dict = utils.semi_deep_copy(
    builtin_constraints.BUILTIN_CONSTRAINTS['selected_in_gimp'])
  selected_in_gimp_constraint_dict['enabled'] = False

  settings['main'].add([
    actions_.create(
      name='constraints',
      initial_actions=[
        builtin_constraints.BUILTIN_CONSTRAINTS['layers'],
        visible_constraint_dict,
        selected_in_gimp_constraint_dict,
      ]),
  ])

  settings['main/procedures'].connect_event('after-add-action', _on_after_add_export_procedure)
  settings['main/procedures'].connect_event('after-add-action', _on_after_add_scale_procedure)

  settings['main/procedures'].connect_event(
    'after-add-action',
    _on_after_add_insert_background_foreground_for_layers,
    settings['main/tagged_items'],
  )

  return settings


def _create_gui_settings(item_tree_items_setting_type):
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
      'default_value': (800, 450),
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
      'type': item_tree_items_setting_type,
      'name': 'selected_items',
    },
    {
      'type': item_tree_items_setting_type,
      'name': 'name_preview_items_collapsed_state',
    },
    {
      'type': item_tree_items_setting_type,
      'name': 'image_preview_displayed_items',
    },
    procedure_browser_settings,
  ])

  return gui_settings


def _create_size_gui_settings(
      dialog_position,
      dialog_size,
      paned_outside_previews_position,
      paned_between_previews_position,
):
  return [
    {
      'type': 'tuple',
      'name': 'dialog_position',
      'default_value': dialog_position,
    },
    {
      'type': 'tuple',
      'name': 'dialog_size',
      'default_value': dialog_size,
    },
    {
      'type': 'integer',
      'name': 'paned_outside_previews_position',
      'default_value': paned_outside_previews_position,
      'gui_type': None,
    },
    {
      'type': 'integer',
      'name': 'paned_between_previews_position',
      'default_value': paned_between_previews_position,
      'gui_type': None,
    },
  ]


def _create_inputs_interactive_setting_dict():
  return {
    'type': 'list',
    'name': 'inputs_interactive',
    'display_name': _('Input files and folders'),
    'pdb_type': None,
    'gui_type': None,
  }


def _create_show_original_item_names_setting_dict(default_value):
  return {
    'type': 'bool',
    'name': 'show_original_item_names',
    'default_value': default_value,
    'display_name': _('Show Original Names'),
  }


def _create_keep_inputs_setting_dict(default_value, title):
  return {
    'type': 'bool',
    'name': 'keep_inputs',
    'default_value': default_value,
    'display_name': title,
    'gui_type': 'check_menu_item',
  }


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


def _create_images_and_directories_setting_dict():
  return {
    'type': 'images_and_directories',
    'name': 'images_and_directories',
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
    main_settings['export/file_format_export_options'])

  main_settings['export/file_format_mode'].connect_event(
    'value-changed',
    _show_hide_file_format_export_options,
    main_settings['export/file_format_export_options'])

  pg.notifier.connect(
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


def _on_after_add_export_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('export_for_'):
    _set_sensitive_for_image_name_pattern_in_export(
      procedure['arguments/export_mode'],
      procedure['arguments/single_image_name_pattern'])
    
    procedure['arguments/export_mode'].connect_event(
      'value-changed',
      _set_sensitive_for_image_name_pattern_in_export,
      procedure['arguments/single_image_name_pattern'])

    _show_hide_file_format_export_options(
      procedure['arguments/file_format_mode'],
      procedure['arguments/file_format_export_options'])

    procedure['arguments/file_format_mode'].connect_event(
      'value-changed',
      _show_hide_file_format_export_options,
      procedure['arguments/file_format_export_options'])

    _set_file_format_export_options(
      procedure['arguments/file_extension'],
      procedure['arguments/file_format_export_options'])

    procedure['arguments/file_extension'].connect_event(
      'value-changed',
      _set_file_format_export_options,
      procedure['arguments/file_format_export_options'])

    # This is needed in case settings are reset, since the file extension is
    # reset first and the options, after resetting, would contain values for
    # the default file extension, which could be different.
    procedure['arguments/file_format_export_options'].connect_event(
      'after-reset',
      _set_file_format_export_options_from_extension,
      procedure['arguments/file_extension'])


def _set_sensitive_for_image_name_pattern_in_export(
      export_mode_setting, single_image_name_pattern_setting):
  if export_mode_setting.value == builtin_procedures.ExportModes.SINGLE_IMAGE:
    single_image_name_pattern_setting.gui.set_sensitive(True)
  else:
    single_image_name_pattern_setting.gui.set_sensitive(False)


def _set_file_format_export_options(file_extension_setting, file_format_export_options_setting):
  file_format_export_options_setting.set_active_file_format(file_extension_setting.value)


def _set_file_format_export_options_from_extension(
      file_format_export_options_setting, file_extension_setting):
  file_format_export_options_setting.set_active_file_format(file_extension_setting.value)


def _show_hide_file_format_export_options(
      file_format_mode_setting, file_format_export_options_setting):
  file_format_export_options_setting.gui.set_visible(
    file_format_mode_setting.value == 'use_explicit_values')


def _on_after_add_scale_procedure(_procedures, procedure, _orig_procedure_dict):
  if procedure['orig_name'].value.startswith('scale_for_'):
    _set_sensitive_for_local_origin(
      procedure['arguments/object_to_scale'],
      procedure['arguments/local_origin'],
    )

    procedure['arguments/object_to_scale'].connect_event(
      'value-changed',
      _set_sensitive_for_local_origin,
      procedure['arguments/local_origin'])

    _set_sensitive_for_dimensions_given_aspect_ratio(
      procedure['arguments/aspect_ratio'],
      procedure['arguments/new_width'],
      procedure['arguments/new_height'],
    )

    procedure['arguments/aspect_ratio'].connect_event(
      'value-changed',
      _set_sensitive_for_dimensions_given_aspect_ratio,
      procedure['arguments/new_width'],
      procedure['arguments/new_height'],
    )

    _set_sensitive_for_padding_color_given_aspect_ratio(
      procedure['arguments/aspect_ratio'],
      procedure['arguments/padding_color'],
    )

    procedure['arguments/aspect_ratio'].connect_event(
      'value-changed',
      _set_sensitive_for_padding_color_given_aspect_ratio,
      procedure['arguments/padding_color'],
    )

    procedure['arguments/image_resolution'].connect_event(
      'after-set-gui',
      _set_left_margin_for_resolution,
    )

    _set_sensitive_for_resolution(
      procedure['arguments/set_image_resolution'],
      procedure['arguments/image_resolution'],
    )

    procedure['arguments/set_image_resolution'].connect_event(
      'value-changed',
      _set_sensitive_for_resolution,
      procedure['arguments/image_resolution'],
    )


def _set_sensitive_for_local_origin(object_to_scale_setting, local_origin_setting):
  local_origin_setting.gui.set_sensitive(object_to_scale_setting.value != 'current_image')


def _set_sensitive_for_dimensions_given_aspect_ratio(
      aspect_ratio_setting,
      new_width_setting,
      new_height_setting,
):
  adjust_width = aspect_ratio_setting.value == builtin_procedures.AspectRatios.KEEP_ADJUST_WIDTH
  adjust_height = aspect_ratio_setting.value == builtin_procedures.AspectRatios.KEEP_ADJUST_HEIGHT

  new_width_setting.gui.set_sensitive(not adjust_height)
  new_height_setting.gui.set_sensitive(not adjust_width)


def _set_sensitive_for_padding_color_given_aspect_ratio(
      aspect_ratio_setting,
      padding_color_setting,
):
  padding_color_setting.gui.set_sensitive(
    aspect_ratio_setting.value == builtin_procedures.AspectRatios.FIT_WITH_PADDING)


def _set_left_margin_for_resolution(image_resolution_setting):
  if not isinstance(image_resolution_setting.gui, pg.setting.NullPresenter):
    image_resolution_setting.gui.widget.set_margin_start(_RELATED_WIDGETS_LEFT_MARGIN)


def _set_sensitive_for_resolution(set_image_resolution_setting, image_resolution_setting):
  image_resolution_setting.gui.set_sensitive(set_image_resolution_setting.value)


def _on_after_add_insert_background_foreground_for_layers(
      _procedures,
      procedure,
      _orig_procedure_dict,
      tagged_items_setting,
):
  if procedure['orig_name'].value in [
       'insert_background_for_layers', 'insert_foreground_for_layers']:
    procedure['arguments/tagged_items'].gui.set_visible(False)
    _sync_tagged_items_with_procedure(tagged_items_setting, procedure)


def _sync_tagged_items_with_procedure(tagged_items_setting, procedure):

  def _on_tagged_items_changed(tagged_items_setting_, procedure_):
    procedure_['arguments/tagged_items'].set_value(tagged_items_setting_.value)

  _on_tagged_items_changed(tagged_items_setting, procedure)

  tagged_items_setting.connect_event('value-changed', _on_tagged_items_changed, procedure)
