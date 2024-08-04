"""Widget for editing the contents of an action (procedure/constraint)."""

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg
from pygimplib import pdb

from . import utils as action_utils_

from src.gui import editable_label as editable_label_
from src.gui import placeholders as gui_placeholders_
from src.gui import popup_hide_context as popup_hide_context_


class ActionEditor(GimpUi.Dialog):

  def __init__(self, action, *args, attach_editor_widget=True, **kwargs):
    super().__init__(*args, **kwargs)

    self.set_resizable(False)
    self.connect('delete-event', lambda *_args: self.hide_on_delete())

    self._action_editor_widget = None

    if attach_editor_widget:
      self.attach_editor_widget(ActionEditorWidget(action, self))

    self._button_reset_response_id = 1
    self._button_reset = self.add_button(_('_Reset'), self._button_reset_response_id)
    self._button_reset.connect('clicked', self._on_button_reset_clicked, action)

    self._button_close = self.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self.set_focus(self._button_close)

    action['display_name'].connect_event('value-changed', self._on_action_display_name_changed)

  @property
  def widget(self):
    return self._action_editor_widget

  def attach_editor_widget(self, widget):
    if self._action_editor_widget is not None:
      raise ValueError('an ActionEditorWidget is already attached to this ActionEditor')

    self._action_editor_widget = widget
    self._action_editor_widget.set_parent(self)

    self.vbox.pack_start(self._action_editor_widget.widget, False, False, 0)

  def _on_button_reset_clicked(self, _button, _action):
    self._action_editor_widget.reset()

  def _on_action_display_name_changed(self, display_name_setting):
    self.set_title(display_name_setting.value)


class ActionEditorWidget:

  _CONTENTS_BORDER_WIDTH = 6
  _CONTENTS_SPACING = 3

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  _HBOX_ADDITIONAL_SETTINGS_SPACING = 6
  _HBOX_ADDITIONAL_SETTINGS_TOP_MARGIN = 3
  _HBOX_ADDITIONAL_SETTINGS_BOTTOM_MARGIN = 3

  _MORE_OPTIONS_SPACING = 3
  _MORE_OPTIONS_LABEL_TOP_MARGIN = 6
  _MORE_OPTIONS_LABEL_BOTTOM_MARGIN = 3

  _LABEL_ACTION_NAME_MAX_WIDTH_CHARS = 50

  _ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_ACTION_INFO = 50
  _ACTION_SHORT_DESCRIPTION_LABEL_RIGHT_MARGIN_WITHOUT_ACTION_INFO = 8
  _ACTION_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_ACTION_INFO = 6
  _ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_ACTION_INFO = 60
  _ACTION_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING = 3
  _ACTION_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS = 40

  def __init__(self, action, parent, show_additional_settings=False):
    self._action = action
    self._parent = parent

    self._show_additional_settings = show_additional_settings

    if self._action['origin'].is_item('gimp_pdb') and self._action['function'].value:
      self._pdb_procedure = pdb[self._action['function'].value]
    else:
      self._pdb_procedure = None

    self._info_popup = None
    self._info_popup_text = None
    self._parent_widget_realize_event_id = None

    self._pdb_argument_names_and_blurbs = None
    self._action_argument_indexes_in_grid = {}

    self._init_gui()

    self._button_preview.connect('clicked', self._on_button_preview_clicked)
    self._button_reset.connect('clicked', self._on_button_reset_clicked)

    self._action['display_name'].connect_event(
      'value-changed', self._on_action_display_name_changed)

  @property
  def action(self):
    return self._action

  @property
  def widget(self):
    return self._vbox

  @property
  def show_additional_settings(self):
    return self._show_additional_settings

  @show_additional_settings.setter
  def show_additional_settings(self, value):
    self._show_additional_settings = value

    self._show_hide_additional_settings()

  def reset(self):
    self._action['display_name'].reset()
    self._action['arguments'].reset()
    self._action['more_options'].reset()

  def set_parent(self, parent):
    if self._info_popup is not None and self._parent_widget_realize_event_id is not None:
      parent_widget = self._info_popup.get_attached_to()
      parent_widget.disconnect(self._parent_widget_realize_event_id)

    self._info_popup, self._info_popup_text, self._parent_widget_realize_event_id = (
      _create_action_info_popup(self._action_info, parent))

  def _init_gui(self):
    self._set_up_editable_name(self._action)

    self._set_up_action_info(self._action, self._parent)

    self._button_preview = Gtk.CheckButton(label=_('_Preview'), use_underline=True)
    self._button_preview.show_all()

    self._button_reset = Gtk.Button(label=_('_Reset'), use_underline=True)
    self._button_reset.show_all()

    self._hbox_additional_settings = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_ADDITIONAL_SETTINGS_SPACING,
      margin_top=self._HBOX_ADDITIONAL_SETTINGS_TOP_MARGIN,
      margin_bottom=self._HBOX_ADDITIONAL_SETTINGS_BOTTOM_MARGIN,
    )
    self._hbox_additional_settings.set_no_show_all(True)
    self._hbox_additional_settings.pack_start(self._button_preview, False, False, 0)
    self._hbox_additional_settings.pack_start(self._button_reset, False, False, 0)

    self._grid_action_arguments = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )

    self._vbox_more_options = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._MORE_OPTIONS_SPACING,
      margin_top=self._MORE_OPTIONS_LABEL_BOTTOM_MARGIN,
    )
    self._vbox_more_options.pack_start(
      self._action['more_options/enabled_for_previews'].gui.widget, False, False, 0)
    if 'also_apply_to_parent_folders' in self._action['more_options']:
      self._vbox_more_options.pack_start(
        self._action['more_options/also_apply_to_parent_folders'].gui.widget, False, False, 0)

    self._action['more_options_expanded'].gui.widget.add(self._vbox_more_options)
    self._action['more_options_expanded'].gui.widget.set_margin_top(
      self._MORE_OPTIONS_LABEL_TOP_MARGIN)

    self._vbox = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      border_width=self._CONTENTS_BORDER_WIDTH,
      spacing=self._CONTENTS_SPACING,
    )

    self._vbox.pack_start(self._label_editable_action_name, False, False, 0)
    if self._action_info_hbox is not None:
      self._vbox.pack_start(self._action_info_hbox, False, False, 0)
    self._vbox.pack_start(self._hbox_additional_settings, False, False, 0)
    self._vbox.pack_start(self._grid_action_arguments, False, False, 0)
    self._vbox.pack_start(self._action['more_options_expanded'].gui.widget, False, False, 0)

    self._set_arguments(self._action, self._pdb_procedure)

    self._set_grid_action_arguments_to_update_according_to_visible_state(self._action)

    self._show_hide_additional_settings()

  def _set_up_editable_name(self, action):
    self._label_editable_action_name = editable_label_.EditableLabel()

    self._label_editable_action_name.label.set_use_markup(True)
    self._label_editable_action_name.label.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_editable_action_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(action['display_name'].value)))
    self._label_editable_action_name.label.set_max_width_chars(
      self._LABEL_ACTION_NAME_MAX_WIDTH_CHARS)

    self._label_editable_action_name.button_edit.set_tooltip_text(_('Edit Name'))

    self._label_editable_action_name.connect(
      'changed', self._on_label_editable_action_name_changed, action)

  @staticmethod
  def _on_label_editable_action_name_changed(editable_label, action):
    action['display_name'].set_value(editable_label.label.get_text())

  def _on_action_display_name_changed(self, display_name_setting):
    self._set_editable_label_text(display_name_setting.value)

  def _set_editable_label_text(self, text):
    self._label_editable_action_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(text)))

  def _set_up_action_info(self, action, parent):
    self._action_info = None
    self._label_short_description = None
    self._info_popup = None
    self._info_popup_text = None
    self._button_info = None
    self._action_info_hbox = None

    if self._pdb_procedure is not None:
      short_description = action_utils_.get_action_description(action, self._pdb_procedure.proc)
    else:
      short_description = action_utils_.get_action_description(action, self._pdb_procedure)

    if short_description is None:
      return

    self._action_info = _get_action_info_from_pdb_procedure(self._pdb_procedure)

    if self._action_info is not None:
      max_width_chars = self._ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_ACTION_INFO
    else:
      max_width_chars = self._ACTION_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_ACTION_INFO

    self._label_short_description = Gtk.Label(
      label=short_description,
      use_markup=False,
      selectable=True,
      wrap=True,
      max_width_chars=max_width_chars,
      xalign=0.0,
    )

    self._action_info_hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._ACTION_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING,
    )
    self._action_info_hbox.pack_start(self._label_short_description, False, False, 0)

    if self._action_info is not None:
      self._info_popup, self._info_popup_text, self._parent_widget_realize_event_id = (
        _create_action_info_popup(self._action_info, parent))

      self._button_info = Gtk.Button(
        image=Gtk.Image.new_from_icon_name(GimpUi.ICON_DIALOG_INFORMATION, Gtk.IconSize.BUTTON),
        relief=Gtk.ReliefStyle.NONE,
      )
      self._button_info.set_tooltip_text(_('Show More Information'))

      self._button_info.connect('clicked', self._on_button_info_clicked)
      self._button_info.connect('focus-out-event', self._on_button_info_focus_out_event)

      self._action_info_hbox.pack_start(self._button_info, False, False, 0)
    else:
      self._action_info_hbox.set_margin_end(
        self._ACTION_SHORT_DESCRIPTION_LABEL_RIGHT_MARGIN_WITHOUT_ACTION_INFO)
      self._action_info_hbox.set_margin_bottom(
        self._ACTION_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_ACTION_INFO)

  def _on_button_info_clicked(self, _button):
    self._info_popup.show()
    self._info_popup_text.select_region(0, 0)  # Prevents selecting the entire text
    self._update_info_popup_position()

  def _on_button_info_focus_out_event(self, _button, _event):
    self._info_popup.hide()

  def _update_info_popup_position(self):
    if self._button_info is not None:
      position = pg.gui.utils.get_position_below_widget(self._button_info)
      if position is not None:
        self._info_popup.move(*position)

  def _set_arguments(self, action, pdb_procedure):
    if pdb_procedure is not None:
      self._pdb_argument_names_and_blurbs = {
        arg.name: arg.blurb for arg in pdb_procedure.proc.get_arguments()}

    row_index = 0

    for setting in action['arguments']:
      if not setting.gui.get_visible():
        continue

      self._attach_label_to_grid(setting, row_index)
      self._attach_widget_to_grid(setting, row_index)

      self._action_argument_indexes_in_grid[setting] = row_index

      row_index += 1

  def _attach_action_argument_to_grid(self, setting, row_index):
    self._attach_label_to_grid(setting, row_index)
    self._attach_widget_to_grid(setting, row_index)

  def _attach_label_to_grid(self, setting, row_index):
    if self._pdb_argument_names_and_blurbs is not None:
      argument_description = self._pdb_argument_names_and_blurbs[setting.name]
    else:
      argument_description = setting.display_name

    if argument_description is None or not argument_description.strip():
      argument_description = setting.name
      should_set_tooltip = False
    else:
      should_set_tooltip = True

    label = Gtk.Label(
      label=argument_description,
      xalign=0.0,
      yalign=0.5,
      max_width_chars=self._ACTION_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS,
      wrap=True,
    )

    if should_set_tooltip:
      label.set_tooltip_text(setting.name)

    self._grid_action_arguments.attach(label, 0, row_index, 1, 1)

  def _attach_widget_to_grid(self, setting, row_index):
    widget_to_attach = setting.gui.widget

    if isinstance(setting.gui, pg.setting.SETTING_GUI_TYPES.null):
      widget_to_attach = gui_placeholders_.create_placeholder_widget()
    else:
      if (isinstance(setting, pg.setting.ArraySetting)
          and not setting.element_type.get_allowed_gui_types()):
        widget_to_attach = gui_placeholders_.create_placeholder_widget()

    self._grid_action_arguments.attach(widget_to_attach, 1, row_index, 1, 1)

  def _set_grid_action_arguments_to_update_according_to_visible_state(self, action):
    for setting in action['arguments']:
      setting.connect_event('gui-visible-changed', self._on_action_argument_gui_visible_changed)

  def _on_action_argument_gui_visible_changed(self, setting):
    if setting.gui.get_visible():
      self._add_action_argument_to_grid(setting)
    else:
      self._remove_action_argument_from_grid(setting)

  def _add_action_argument_to_grid(self, setting):
    if setting in self._action_argument_indexes_in_grid:
      return

    previous_settings = []

    for setting_in_arguments in self._action['arguments']:
      if setting_in_arguments.name == setting.name:
        break

      previous_settings.insert(0, setting_in_arguments)

    last_visible_previous_setting = next(
      iter(
        previous_setting for previous_setting in previous_settings
        if previous_setting in self._action_argument_indexes_in_grid),
      None)

    if last_visible_previous_setting is not None:
      row_index = self._action_argument_indexes_in_grid[last_visible_previous_setting] + 1
    else:
      row_index = 0

    self._grid_action_arguments.insert_row(row_index)
    self._attach_action_argument_to_grid(setting, row_index)

    if last_visible_previous_setting is not None:
      new_action_argument_indexes_in_grid = {}

      for setting_in_grid, row_index in self._action_argument_indexes_in_grid.items():
        new_action_argument_indexes_in_grid[setting_in_grid] = row_index

        if setting_in_grid == last_visible_previous_setting:
          # The row indexes will be refreshed anyway, so any value is OK at this point.
          new_action_argument_indexes_in_grid[setting] = 0

      self._action_argument_indexes_in_grid = new_action_argument_indexes_in_grid
    else:
      self._action_argument_indexes_in_grid = dict(
        {setting: 0}, **self._action_argument_indexes_in_grid)

    self._refresh_action_argument_indexes_in_grid()

    # This is necessary to show the newly attached widgets.
    self._grid_action_arguments.show_all()

  def _remove_action_argument_from_grid(self, setting):
    row_index = self._action_argument_indexes_in_grid.pop(setting, None)
    if row_index is not None:
      self._grid_action_arguments.remove_row(row_index)

    self._refresh_action_argument_indexes_in_grid()

  def _refresh_action_argument_indexes_in_grid(self):
    self._action_argument_indexes_in_grid = {
      setting: index for index, setting in enumerate(self._action_argument_indexes_in_grid)
    }

  def _show_hide_additional_settings(self):
    if self._show_additional_settings:
      self._hbox_additional_settings.show()
    else:
      self._hbox_additional_settings.hide()

  def _on_button_preview_clicked(self, _button):
    self._action['enabled'].set_value(self._button_preview.get_active())

  def _on_button_reset_clicked(self, _button):
    self.reset()


def _get_action_info_from_pdb_procedure(pdb_procedure):
  if pdb_procedure is None:
    return None

  if pdb_procedure is not None:
    action_info = ''
    action_main_info = []

    help_text = pdb_procedure.proc.get_help()
    if help_text:
      action_main_info.append(help_text)

    action_info += '\n\n'.join(action_main_info)

    action_author_info = []
    authors = pdb_procedure.proc.get_authors()
    if authors:
      action_author_info.append(authors)

    date_text = pdb_procedure.proc.get_date()
    if date_text:
      action_author_info.append(date_text)

    copyright_text = pdb_procedure.proc.get_copyright()
    if copyright_text:
      if not authors.startswith(copyright_text):
        action_author_info.append(f'\u00a9 {copyright_text}')
      else:
        if authors:
          action_author_info[0] = f'\u00a9 {action_author_info[0]}'

    if action_author_info:
      if action_info:
        action_info += '\n\n'
      action_info += ', '.join(action_author_info)

    return action_info


def _create_action_info_popup(action_info, parent_widget, max_width_chars=100, border_width=3):
  info_popup = Gtk.Window(
    type=Gtk.WindowType.POPUP,
    type_hint=Gdk.WindowTypeHint.TOOLTIP,
    resizable=False,
  )
  info_popup.set_attached_to(parent_widget)

  parent_widget_realize_event_id = parent_widget.connect(
    'realize',
    lambda *args: info_popup.set_transient_for(pg.gui.utils.get_toplevel_window(parent_widget)))

  info_popup_text = Gtk.Label(
    label=action_info,
    use_markup=False,
    selectable=True,
    wrap=True,
    max_width_chars=max_width_chars,
  )

  info_popup_hbox = Gtk.Box(
    orientation=Gtk.Orientation.HORIZONTAL,
    homogeneous=False,
    border_width=border_width,
  )
  info_popup_hbox.pack_start(info_popup_text, True, True, 0)

  info_popup_hide_context = popup_hide_context_.PopupHideContext(
    info_popup,
    parent_widget,
    widgets_to_exclude_from_triggering_hiding=[
      info_popup,
      parent_widget,
    ],
  )
  info_popup_hide_context.enable()

  info_popup_scrolled_window = Gtk.ScrolledWindow(
    hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    shadow_type=Gtk.ShadowType.ETCHED_IN,
    propagate_natural_width=True,
    propagate_natural_height=True,
  )
  info_popup_scrolled_window.add(info_popup_hbox)
  info_popup_scrolled_window.show_all()

  info_popup.add(info_popup_scrolled_window)

  return info_popup, info_popup_text, parent_widget_realize_event_id
