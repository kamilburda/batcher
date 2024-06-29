import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import actions as actions_
from src import builtin_constraints
from src import builtin_procedures

from src.gui import messages as messages_
from src.gui.actions import list as action_list_


class ActionLists:

  _ACTION_LABEL_BOX_SPACING = 5

  _CONSTRAINTS_TOP_MARGIN = 5

  def __init__(self, settings, dialog):
    self._settings = settings
    self._dialog = dialog

    self._init_gui()

    self._init_setting_gui()

  def _init_gui(self):
    self._label_procedures = Gtk.Label(
      label='<b>{}</b>'.format(_('Procedures')),
      use_markup=True,
      xalign=0.0,
      yalign=0.5,
    )

    self._procedure_list = action_list_.ActionList(
      self._settings['main/procedures'],
      builtin_actions=builtin_procedures.BUILTIN_PROCEDURES,
      add_action_text=_('Add P_rocedure...'),
      allow_custom_actions=True,
      add_custom_action_text=_('Add Custom Procedure...'),
      action_browser_text=_('Add Custom Procedure'),
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
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

    self._constraint_list = action_list_.ActionList(
      self._settings['main/constraints'],
      builtin_actions=builtin_constraints.BUILTIN_CONSTRAINTS,
      add_action_text=_('Add C_onstraint...'),
      allow_custom_actions=False,
      propagate_natural_height=True,
      propagate_natural_width=True,
      hscrollbar_policy=Gtk.PolicyType.NEVER,
    )

    self._vbox_constraints = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._ACTION_LABEL_BOX_SPACING,
      margin_top=self._CONSTRAINTS_TOP_MARGIN,
    )
    self._vbox_constraints.pack_start(self._label_constraints, False, False, 0)
    self._vbox_constraints.pack_start(self._constraint_list, True, True, 0)

    self._procedure_list.connect(
      'action-list-item-added-interactive', self._on_procedure_list_item_added)

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
  def _set_action_skipped_tooltips(action_list, skipped_actions, message, clear_previous=True):
    for action_item in action_list.items:
      if not action_item.has_warning():
        if action_item.action.name in skipped_actions:
          skipped_message = skipped_actions[action_item.action.name][0][1]
          action_item.set_tooltip(message.format(skipped_message))
        else:
          if clear_previous:
            action_item.reset_tooltip()

  def _on_procedure_list_item_added(self, _procedure_list, item):
    if any(item.action['orig_name'].value == name
           for name in ['insert_background', 'insert_foreground']):
      actions_.reorder(self._settings['main/procedures'], item.action.name, 0)
