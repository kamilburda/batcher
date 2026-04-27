import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from src import builtin_actions
from src import commands as commands_
from src.procedure_groups import *

from .. import _utils as update_utils_


def update(data, _settings, _procedure_groups):
  main_settings_list, _index = update_utils_.get_top_level_group_list(data, 'main')

  if main_settings_list is not None:
    actions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'actions')

    if actions_list is not None:
      for index, action_dict in enumerate(actions_list):
        action_list = action_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(action_list, 'orig_name')
        arguments_list, _index = update_utils_.get_child_group_list(action_list, 'arguments')
        description_setting_dict, _index = update_utils_.get_child_group_list(
          action_list, 'description')

        if ((orig_name_setting_dict['value'].startswith('insert_background_for_')
             or orig_name_setting_dict['value'].startswith('insert_foreground_for_'))
            and arguments_list is not None):
          _insert_background_foreground_update_action(
            arguments_list, orig_name_setting_dict, description_setting_dict)

        if (orig_name_setting_dict['value'] in ['merge_background', 'merge_foreground']
            and arguments_list is not None):
          _merge_background_foreground_update_action(
            arguments_list, orig_name_setting_dict, action_dict)

    conditions_list, _index = update_utils_.get_child_group_list(main_settings_list, 'conditions')
    if conditions_list is not None:
      for condition_dict in conditions_list:
        condition_list = condition_dict['settings']

        orig_name_setting_dict, _index = update_utils_.get_child_setting(
          condition_list, 'orig_name')

        if orig_name_setting_dict['value'] in ['not_background', 'not_foreground']:
          _not_background_foreground_update_orig_name(orig_name_setting_dict)


def _insert_background_foreground_update_action(
      arguments_list, orig_name_setting_dict, description_setting_dict):
  _insert_background_foreground_rename_action(orig_name_setting_dict)
  _insert_background_foreground_update_description(orig_name_setting_dict, description_setting_dict)
  _insert_background_foreground_replace_arguments(arguments_list, orig_name_setting_dict)


def _insert_background_foreground_rename_action(orig_name_setting_dict):
  orig_name = orig_name_setting_dict['value']
  new_orig_name = orig_name.replace('background', 'overlay').replace('foreground', 'overlay')

  orig_name_setting_dict['value'] = new_orig_name
  orig_name_setting_dict['default_value'] = new_orig_name


def _insert_background_foreground_update_description(
      orig_name_setting_dict, description_setting_dict):
  if description_setting_dict is None:
    return

  orig_name = orig_name_setting_dict['value']
  new_description = builtin_actions.BUILTIN_ACTIONS[orig_name]['description']

  description_setting_dict['value'] = new_description
  description_setting_dict['default_value'] = new_description


def _insert_background_foreground_replace_arguments(arguments_list, orig_name_setting_dict):
  object_type_str = 'image' if orig_name_setting_dict['value'].endswith('_for_images') else 'layer'

  insert_content = (
    builtin_actions.ContentType.LAYERS_WITH_COLOR_TAG if object_type_str == 'layer'
    else builtin_actions.ContentType.FILE)
  orig_image_file = arguments_list[0]['value'] if object_type_str == 'image' else None
  orig_color_tag = arguments_list[0]['value'] if object_type_str == 'layer' else Gimp.ColorTag.BLUE
  orig_tagged_items = arguments_list[1]['value'] if object_type_str == 'layer' else []
  orig_condition_name = arguments_list[3]['value'] if object_type_str == 'layer' else ''
  adjust_placement = True if object_type_str == 'image' else False
  position = (
    builtin_actions.InsertionPositions.FOREGROUND if 'foreground' in orig_name_setting_dict['value']
    else builtin_actions.InsertionPositions.BACKGROUND)

  arguments_list[:] = [
    {
      'type': 'choice',
      'name': 'insert_content',
      'value': insert_content,
      'default_value': builtin_actions.ContentType.FILE,
      'display_name': _('Insert content'),
      'items': [
        (builtin_actions.ContentType.FILE, _('File')),
        (builtin_actions.ContentType.TEXT, _('Text')),
      ],
      'gui_type': 'radio_button_box',
    },
    {
      'type': 'file',
      'name': 'image_file',
      'value': orig_image_file,
      'default_value': None,
      'action': Gimp.FileChooserAction.OPEN,
      'display_name': _('Image'),
      'none_ok': True,
    },
    {
      'type': 'name_pattern',
      'name': 'image_file_pattern',
      'value': '[image file]',
      'default_value': '[image file]',
      'display_name': _('Image pattern'),
      'description': _('This way, you can insert different overlays for each input.'),
      'gui_type_kwargs': {
        'regexes': ['image file'],
      },
    },
    {
      'type': 'string',
      'name': 'text',
      'value': '© Copyright',
      'default_value': '© Copyright',
      'display_name': _('Text'),
    },
    {
      'type': 'name_pattern',
      'name': 'text_pattern',
      'display_name': _('Text pattern'),
      'value': '© Copyright [current date]',
      'default_value': '© Copyright [current date]',
      'gui_type_kwargs': {
        'regexes': ['image file'],
      },
    },
    {
      'type': 'enum',
      'name': 'color_tag',
      'enum_type': Gimp.ColorTag,
      'excluded_values': [Gimp.ColorTag.NONE],
      'display_name': _('Color tag'),
      'value': orig_color_tag,
      'default_value': Gimp.ColorTag.BLUE,
    },
    {
      'type': 'bool',
      'name': 'use_pattern',
      'value': False,
      'default_value': False,
      'display_name': _('Use pattern'),
      'description': _('Using a pattern allows inserting different files or text for each input.'),
    },
    {
      'type': 'font',
      'name': 'text_font_family',
      'value': (
        Gimp.Font.get_by_name('Sans-serif') if Gimp.Font.get_by_name('Sans-serif') is not None
        else Gimp.fonts_get_list()[0]
      ),
      'default_value': None,
      'display_name': _('Font'),
    },
    {
      'type': 'dimension',
      'name': 'text_font_size',
      'value': {
        'pixel_value': 14.0,
        'percent_value': 5.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'default_value': {
        'pixel_value': 14.0,
        'percent_value': 5.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.pixel(),
        'percent_object': 'current_layer',
        'percent_property': {
          ('current_image',): 'width',
          ('current_layer', 'background_layer', 'foreground_layer'): 'width',
        },
      },
      'min_value': 0.0,
      'percent_placeholder_names': ['current_image', 'current_layer'],
      'display_name': _('Font size'),
    },
    {
      'type': 'color',
      'name': 'text_font_color',
      'value': [0.0, 0.0, 0.0, 1.0],
      'default_value': [0.0, 0.0, 0.0, 1.0],
      'display_name': _('Font color'),
    },
    {
      'type': 'dimension',
      'name': 'size',
      'value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
      },
      'default_value': {
        'pixel_value': 100.0,
        'percent_value': 100.0,
        'other_value': 1.0,
        'unit': Gimp.Unit.percent(),
      },
      'min_value': 0.0,
      'percent_placeholder_names': [],
      'display_name': _('Size'),
      'description': _(
        'Aspect ratio is preserved.'
        ' For absolute units, the inserted layer is scaled to fit'
        ' within the specified size (maximum width or height).'
      ),
    },
    {
      'type': 'double',
      'name': 'opacity',
      'value': 100.0,
      'default_value': 100.0,
      'min_value': 0.0,
      'max_value': 100.0,
      'display_name': _('Opacity'),
    },
    {
      'type': 'double',
      'name': 'rotation_angle',
      'value': 0.0,
      'default_value': 0.0,
      'min_value': 0.0,
      'max_value': 360.0,
      'display_name': _('Rotation angle (degrees)'),
      'tags': [commands_.MORE_OPTIONS_TAG],
    },
    {
      'type': 'bool',
      'name': 'adjust_placement',
      'value': adjust_placement,
      'default_value': True,
      'display_name': _('Adjust placement'),
    },
    {
      'type': 'anchor',
      'name': 'placement',
      # This is how images were placed in previous versions.
      'value': builtin_actions.AnchorPoints.TOP_LEFT,
      'default_value': builtin_actions.AnchorPoints.BOTTOM_RIGHT,
      'items': list(builtin_actions.ANCHOR_POINTS_ITEMS_AND_DISPLAY_NAMES),
      'display_name': _('Placement'),
    },
    {
      'type': 'coordinates',
      'name': 'offsets',
      'value': {
        'x': 0.0,
        'y': 0.0,
      },
      'default_value': {
        'x': 0.0,
        'y': 0.0,
      },
      'display_name': _('Offsets (X and Y)'),
      'tags': [commands_.MORE_OPTIONS_TAG],
    },
    {
      'type': 'int',
      'name': 'num_tiles',
      'value': 1,
      'default_value': 1,
      'display_name': _('Number of tiles'),
      'description': _('Set this to a value greater than 1 to enable tiling.'),
      'min_value': 1,
      'max_value': 6,
      'tags': [commands_.MORE_OPTIONS_TAG],
    },
    {
      'type': 'choice',
      'name': 'position',
      'value': position,
      'default_value': builtin_actions.InsertionPositions.FOREGROUND,
      'display_name': _('Position'),
      'items': [
        (builtin_actions.InsertionPositions.FOREGROUND, _('Foreground')),
        (builtin_actions.InsertionPositions.BACKGROUND, _('Background')),
      ],
      'gui_type': 'radio_button_box',
    },
  ]

  if orig_name_setting_dict['value'] == 'insert_overlay_for_layers':
    arguments_list[0]['items'] = [
      (builtin_actions.ContentType.FILE, _('File')),
      (builtin_actions.ContentType.TEXT, _('Text')),
      (builtin_actions.ContentType.LAYERS_WITH_COLOR_TAG, _('Layers with color tag')),
    ]
    arguments_list.extend([
      {
        'type': 'tagged_items',
        'name': 'tagged_items',
        'value': orig_tagged_items,
        'default_value': [],
        'gui_type': None,
        'tags': ['ignore_reset'],
      },
      {
        'type': 'string',
        'name': 'condition_name',
        'value': orig_condition_name,
        'default_value': '',
        'gui_type': None,
      },
    ])


def _merge_background_foreground_update_action(
      arguments_list, orig_name_setting_dict, action_dict):
  _merge_background_foreground_rename_action(orig_name_setting_dict)
  _merge_background_foreground_add_tags(action_dict)
  _merge_background_foreground_replace_arguments(arguments_list)


def _merge_background_foreground_rename_action(orig_name_setting_dict):
  orig_name = orig_name_setting_dict['value']
  new_orig_name = orig_name.replace('background', 'layer').replace('foreground', 'layer')

  orig_name_setting_dict['value'] = new_orig_name
  orig_name_setting_dict['default_value'] = new_orig_name


def _merge_background_foreground_add_tags(action_dict):
  for tag in ALL_PROCEDURE_GROUPS:
    if tag not in action_dict['tags']:
      action_dict['tags'].append(tag)


def _merge_background_foreground_replace_arguments(arguments_list):
  orig_merge_type = arguments_list[0]['value']

  arguments_list[:] = [
    {
      'type': 'placeholder_layer_without_current_layer',
      'name': 'layer',
      'display_name': _('Target Layer'),
      'value': 'foreground_layer',
      'default_value': 'foreground_layer',
    },
    {
      'type': 'enum',
      'name': 'merge_type',
      'enum_type': Gimp.MergeType,
      'value': orig_merge_type,
      'default_value': Gimp.MergeType.EXPAND_AS_NECESSARY,
      'excluded_values': [Gimp.MergeType.FLATTEN_IMAGE],
      'display_name': _('Merge type'),
    },
  ]


def _not_background_foreground_update_orig_name(orig_name_setting_dict):
  orig_name_setting_dict['value'] = 'without_color_tag'
  orig_name_setting_dict['default_value'] = 'without_color_tag'
