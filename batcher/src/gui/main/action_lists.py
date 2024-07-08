from typing import Dict, List

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import builtin_actions_common
from src import builtin_constraints
from src import builtin_procedures

from src.gui import messages as messages_
from src.gui.actions import list as action_list_


class ActionLists:

  _ACTION_LABEL_BOX_SPACING = 5

  _CONSTRAINTS_TOP_MARGIN = 5

  def __init__(self, settings, plugin_procedure, dialog):
    self._settings = settings
    self._dialog = dialog

    self._procedure_list = action_list_.ActionList(
      self._settings['main/procedures'],
      builtin_actions=builtin_actions_common.get_filtered_builtin_actions(
        builtin_procedures.BUILTIN_PROCEDURES, [plugin_procedure]),
      add_action_text=_('Add P_rocedure...'),
      allow_custom_actions=True,
      add_custom_action_text=_('Add Custom Procedure...'),
      action_browser_text=_('Add Custom Procedure'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._constraint_list = action_list_.ActionList(
      self._settings['main/constraints'],
      builtin_actions=builtin_actions_common.get_filtered_builtin_actions(
        builtin_constraints.BUILTIN_CONSTRAINTS, [plugin_procedure]),
      add_action_text=_('Add C_onstraint...'),
      allow_custom_actions=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._init_gui()

    self._init_setting_gui()

  def _init_gui(self):
    self._label_procedures = Gtk.Label(
      label='<b>{}</b>'.format(_('Procedures')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_procedures = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
    )
    self._vbox_procedures.pack_start(self._label_procedures, False, False, 0)
    self._vbox_procedures.pack_start(self._procedure_list, True, True, 0)

    self._label_constraints = Gtk.Label(
      label='<b>{}</b>'.format(_('Constraints')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._vbox_constraints = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
      margin_top=self._CONSTRAINTS_TOP_MARGIN,
    )
    self._vbox_constraints.pack_start(self._label_constraints, False, False, 0)
    self._vbox_constraints.pack_start(self._constraint_list, True, True, 0)

    self._procedure_list.connect(
      'action-list-item-added-interactive',
      _on_insert_background_foreground_procedure_item_added,
      self._constraint_list,
    )

  def _init_setting_gui(self):
    self._settings['gui/procedure_browser/paned_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.paned_position,
      widget=self._procedure_list.browser.paned,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_position'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_position,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )
    self._settings['gui/procedure_browser/dialog_size'].set_gui(
      gui_type=pg.setting.SETTING_GUI_TYPES.window_size,
      widget=self._procedure_list.browser.widget,
      copy_previous_visible=False,
      copy_previous_sensitive=False,
    )

  @property
  def procedure_list(self):
    return self._procedure_list

  @property
  def constraint_list(self):
    return self._constraint_list

  @property
  def vbox_procedures(self):
    return self._vbox_procedures

  @property
  def vbox_constraints(self):
    return self._vbox_constraints

  def display_warnings_and_tooltips_for_actions(self, batcher, clear_previous=True):
    self.set_warning_on_actions(batcher, clear_previous=clear_previous)

    self._set_action_skipped_tooltips(
      self._procedure_list,
      batcher.skipped_procedures,
      _('This procedure is skipped. Reason: {}'),
      clear_previous=clear_previous)

    self._set_action_skipped_tooltips(
      self._constraint_list,
      batcher.skipped_constraints,
      _('This constraint is skipped. Reason: {}'),
      clear_previous=clear_previous)

  def set_warning_on_actions(self, batcher, clear_previous=True):
    action_lists = [self._procedure_list, self._constraint_list]
    failed_actions_dict = [batcher.failed_procedures, batcher.failed_constraints]

    for action_list, failed_actions in zip(action_lists, failed_actions_dict):
      for action_item in action_list.items:
        if action_item.action.name in failed_actions:
          action_item.set_warning(
            True,
            messages_.get_failing_action_message(
              (action_item.action, failed_actions[action_item.action.name][0][0])),
            failed_actions[action_item.action.name][0][1],
            failed_actions[action_item.action.name][0][2],
            parent=self._dialog)
        else:
          if clear_previous:
            action_item.set_warning(False)

  def reset_action_tooltips_and_indicators(self):
    for action_list in [self._procedure_list, self._constraint_list]:
      for action_item in action_list.items:
        action_item.reset_tooltip()
        action_item.set_warning(False)

  def close_action_edit_dialogs(self):
    for action_list in [self._procedure_list, self._constraint_list]:
      for action_item in action_list.items:
        action_item.editor.hide()

  @staticmethod
  def _set_action_skipped_tooltips(
        action_list: action_list_.ActionList,
        skipped_actions: Dict[str, List],
        message: str,
        clear_previous: bool = True,
  ):
    for action_item in action_list.items:
      if not action_item.has_warning():
        if action_item.action.name in skipped_actions:
          skipped_message = skipped_actions[action_item.action.name][0][1]
          action_item.set_tooltip(message.format(skipped_message))
        else:
          if clear_previous:
            action_item.reset_tooltip()


def _on_insert_background_foreground_procedure_item_added(procedure_list, item, constraint_list):
  if item.action['orig_name'].value in ['insert_background', 'insert_foreground']:
    procedure_list.reorder_item(item, 0)

    item.action['arguments/last_enabled_value_for_merge'].gui.set_visible(False)
    item.action['arguments/last_enabled_value_for_constraint'].gui.set_visible(False)

    merge_item = _add_merge_background_foreground_procedure(procedure_list, item)

    constraint_item = _add_not_background_foreground_constraint(item, constraint_list)

    item.action['enabled'].connect_event(
      'value-changed',
      _on_insert_background_foreground_procedure_enabled_changed,
      item,
      merge_item,
      constraint_item,
    )

    procedure_list.connect(
      'action-list-item-removed',
      _on_insert_background_foreground_procedure_removed,
      item,
      merge_item,
      constraint_list,
      constraint_item,
    )


def _add_merge_background_foreground_procedure(procedure_list, item):
  merge_procedure_orig_name_mapping = {
    'insert_background': 'merge_background',
    'insert_foreground': 'merge_foreground',
  }
  insert_procedure_name = merge_procedure_orig_name_mapping[item.action['orig_name'].value]

  merge_item = procedure_list.add_item(
    builtin_procedures.BUILTIN_PROCEDURES[insert_procedure_name])

  export_procedure_index = next(
    iter(index for index, item in enumerate(procedure_list.items)
         if item.action['orig_name'].value == 'export'),
    None)

  if export_procedure_index is not None:
    procedure_list.reorder_item(merge_item, export_procedure_index)

  _set_buttons_for_action_item_sensitive(merge_item, False)

  return merge_item


def _add_not_background_foreground_constraint(item, constraint_list):
  def _on_insert_background_foreground_color_tag_changed(color_tag_setting):
    constraint_item.action['arguments/color_tag'].set_value(color_tag_setting.value)

  constraint_orig_name_mapping = {
    'insert_background': 'not_background',
    'insert_foreground': 'not_foreground',
  }
  constraint_name = constraint_orig_name_mapping[item.action['orig_name'].value]

  constraint_item = constraint_list.add_item(
    builtin_constraints.BUILTIN_CONSTRAINTS[constraint_name])

  constraint_item.action['arguments/color_tag'].gui.set_visible(False)

  item.action['arguments/color_tag'].connect_event(
    'value-changed', _on_insert_background_foreground_color_tag_changed)
  _on_insert_background_foreground_color_tag_changed(item.action['arguments/color_tag'])

  _set_buttons_for_action_item_sensitive(constraint_item, False)

  return constraint_item


def _on_insert_background_foreground_procedure_enabled_changed(
      enabled_setting,
      insert_back_foreground_item,
      merge_item,
      constraint_item,
):
  if not enabled_setting.value:
    insert_back_foreground_item.action['arguments/last_enabled_value_for_merge'].set_value(
      merge_item.action['enabled'].value)
    merge_item.action['enabled'].set_value(False)

    insert_back_foreground_item.action['arguments/last_enabled_value_for_constraint'].set_value(
      constraint_item.action['enabled'].value)
    constraint_item.action['enabled'].set_value(False)
  else:
    merge_item.action['enabled'].set_value(
      insert_back_foreground_item.action['arguments/last_enabled_value_for_merge'].value)
    constraint_item.action['enabled'].set_value(
      insert_back_foreground_item.action['arguments/last_enabled_value_for_constraint'].value)

  merge_item.action['enabled'].gui.set_sensitive(enabled_setting.value)
  constraint_item.action['enabled'].gui.set_sensitive(enabled_setting.value)


def _on_insert_background_foreground_procedure_removed(
      procedure_list,
      removed_item,
      insert_back_foreground_item,
      merge_item,
      constraint_list,
      constraint_item):
  if removed_item == insert_back_foreground_item:
    if merge_item in procedure_list.items:
      procedure_list.remove_item(merge_item)
    if constraint_item in constraint_list.items:
      constraint_list.remove_item(constraint_item)


def _set_buttons_for_action_item_sensitive(item, sensitive):
  item.button_remove.set_sensitive(sensitive)
