"""Widget for editing the contents of a command (action/condition)."""

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from src import commands as commands_
from src.gui import utils as gui_utils_
from src.gui import utils_grid as gui_utils_grid_
from src.gui import widgets as gui_widgets_
from src.pypdb import pdb


class CommandEditor(GimpUi.Dialog):

  _MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR = 650

  def __init__(self, command, *args, attach_editor_widget=True, **kwargs):
    super().__init__(*args, **kwargs)

    self.set_resizable(False)
    self.connect('delete-event', lambda *_args: self.hide_on_delete())

    self._scrolled_window_viewport = Gtk.Viewport(shadow_type=Gtk.ShadowType.NONE)

    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      propagate_natural_width=True,
      propagate_natural_height=True,
      max_content_height=self._MAX_HEIGHT_BEFORE_DISPLAYING_SCROLLBAR,
    )
    self._scrolled_window.add(self._scrolled_window_viewport)

    self._command_editor_widget = None

    if attach_editor_widget:
      self.attach_editor_widget(CommandEditorWidget(command, self))

    self._button_reset_response_id = 1
    self._button_reset = self.add_button(_('_Reset'), self._button_reset_response_id)
    self._button_reset.connect('clicked', self._on_button_reset_clicked, command)

    self._button_close = self.add_button(_('_Close'), Gtk.ResponseType.CLOSE)

    self.set_focus(self._button_close)

    command['display_name'].connect_event('value-changed', self._on_command_display_name_changed)

  @property
  def widget(self):
    return self._command_editor_widget

  def attach_editor_widget(self, widget):
    if self._command_editor_widget is not None:
      raise ValueError('a CommandEditorWidget is already attached to this CommandEditor')

    self._command_editor_widget = widget
    self._command_editor_widget.set_parent(self)

    self._scrolled_window_viewport.add(self._command_editor_widget.widget)

    self.vbox.pack_start(self._scrolled_window, False, False, 0)

  def _on_button_reset_clicked(self, _button, _command):
    self._command_editor_widget.reset()

  def _on_command_display_name_changed(self, display_name_setting):
    self.set_title(display_name_setting.value)


class CommandEditorWidget:

  _CONTENTS_BORDER_WIDTH = 6
  _CONTENTS_SPACING = 3

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  _HBOX_ADDITIONAL_SETTINGS_SPACING = 6
  _HBOX_ADDITIONAL_SETTINGS_TOP_MARGIN = 3
  _HBOX_ADDITIONAL_SETTINGS_BOTTOM_MARGIN = 3

  _MORE_OPTIONS_SPACING = 3
  _MORE_OPTIONS_LABEL_TOP_MARGIN = 6
  _MORE_OPTIONS_LABEL_BOTTOM_MARGIN = 6

  _LABEL_COMMAND_NAME_MAX_WIDTH_CHARS = 50

  _COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_COMMAND_INFO = 50
  _COMMAND_SHORT_DESCRIPTION_LABEL_RIGHT_MARGIN_WITHOUT_COMMAND_INFO = 8
  _COMMAND_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_COMMAND_INFO = 6
  _COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_COMMAND_INFO = 60
  _COMMAND_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING = 3
  _COMMAND_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS = 40

  def __init__(self, command, parent, show_additional_settings=False):
    self._command = command
    self._parent = parent

    self._show_additional_settings = show_additional_settings

    if (self._command['origin'].value in ['gimp_pdb', 'gegl']
        and self._command['function'].value
        and self._command['function'].value in pdb):
      self._pdb_procedure = pdb[self._command['function'].value]
    else:
      self._pdb_procedure = None

    self._info_popup = None
    self._info_popup_text = None
    self._parent_widget_realize_event_id = None

    self._command_argument_indexes_in_grid = {}
    self._command_more_options_indexes_in_grid = {}

    self._init_gui()

    self._button_preview.connect('clicked', self._on_button_preview_clicked)
    self._button_reset.connect('clicked', self._on_button_reset_clicked)

    self._command['display_name'].connect_event(
      'value-changed', self._on_command_display_name_changed)

  @property
  def command(self):
    return self._command

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
    self._command['display_name'].reset()
    self._command['arguments'].reset()
    self._command['more_options'].reset()

  def set_parent(self, parent):
    if self._info_popup is not None and self._parent_widget_realize_event_id is not None:
      parent_widget = self._info_popup.get_attached_to()
      parent_widget.disconnect(self._parent_widget_realize_event_id)

    self._info_popup, self._info_popup_text, self._parent_widget_realize_event_id = (
      _create_command_info_popup(self._command_info, parent))

  def _init_gui(self):
    self._set_up_editable_name(self._command)

    self._set_up_command_info(self._command, self._parent)

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

    self._grid_command_arguments = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
    )

    self._grid_more_options = Gtk.Grid(
      row_spacing=self._GRID_ROW_SPACING,
      column_spacing=self._GRID_COLUMN_SPACING,
      margin_top=self._MORE_OPTIONS_LABEL_BOTTOM_MARGIN,
    )

    self._command['more_options_expanded'].gui.widget.add(self._grid_more_options)
    self._command['more_options_expanded'].gui.widget.set_margin_top(
      self._MORE_OPTIONS_LABEL_TOP_MARGIN)

    self._vbox = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      border_width=self._CONTENTS_BORDER_WIDTH,
      spacing=self._CONTENTS_SPACING,
    )

    self._vbox.pack_start(self._label_editable_command_name, False, False, 0)
    if self._command_info_hbox is not None:
      self._vbox.pack_start(self._command_info_hbox, False, False, 0)
    self._vbox.pack_start(self._hbox_additional_settings, False, False, 0)
    self._vbox.pack_start(self._grid_command_arguments, False, False, 0)
    self._vbox.pack_start(self._command['more_options_expanded'].gui.widget, False, False, 0)

    self._set_arguments(self._command)

    self._set_more_options(self._command)

    self._set_grids_to_update_according_to_visible_state(self._command)

    self._show_hide_additional_settings()

  def _set_up_editable_name(self, command):
    self._label_editable_command_name = gui_widgets_.EditableLabel()

    self._label_editable_command_name.label.set_use_markup(True)
    self._label_editable_command_name.label.set_ellipsize(Pango.EllipsizeMode.END)
    self._label_editable_command_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(command['display_name'].value)))
    self._label_editable_command_name.label.set_max_width_chars(
      self._LABEL_COMMAND_NAME_MAX_WIDTH_CHARS)

    self._label_editable_command_name.button_edit.set_tooltip_text(_('Edit Name'))

    self._label_editable_command_name.connect(
      'changed', self._on_label_editable_command_name_changed, command)

  @staticmethod
  def _on_label_editable_command_name_changed(editable_label, command):
    command['display_name'].set_value(editable_label.label.get_text())

  def _on_command_display_name_changed(self, display_name_setting):
    self._set_editable_label_text(display_name_setting.value)

  def _set_editable_label_text(self, text):
    self._label_editable_command_name.label.set_markup(
      '<b>{}</b>'.format(GLib.markup_escape_text(text)))

  def _set_up_command_info(self, command, parent):
    self._command_info = None
    self._label_short_description = None
    self._info_popup = None
    self._info_popup_text = None
    self._button_info = None
    self._command_info_hbox = None

    if command['description'].value is None:
      return

    self._command_info = _get_command_info_from_pdb_procedure(self._pdb_procedure)

    if self._command_info:
      max_width_chars = self._COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_COMMAND_INFO
    else:
      max_width_chars = self._COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_COMMAND_INFO

    self._label_short_description = Gtk.Label(
      label=command['description'].value,
      use_markup=False,
      selectable=True,
      wrap=True,
      max_width_chars=max_width_chars,
      xalign=0.0,
    )

    self._command_info_hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._COMMAND_SHORT_DESCRIPTION_LABEL_BUTTON_SPACING,
    )
    self._command_info_hbox.pack_start(self._label_short_description, True, True, 0)

    if self._command_info:
      self._info_popup, self._info_popup_text, self._parent_widget_realize_event_id = (
        _create_command_info_popup(self._command_info, parent))

      self._button_info = Gtk.Button(
        image=Gtk.Image.new_from_icon_name(GimpUi.ICON_DIALOG_INFORMATION, Gtk.IconSize.BUTTON),
        relief=Gtk.ReliefStyle.NONE,
      )
      self._button_info.set_tooltip_text(_('Show More Information'))

      self._button_info.connect('clicked', self._on_button_info_clicked)
      self._button_info.connect('focus-out-event', self._on_button_info_focus_out_event)

      self._command_info_hbox.pack_start(self._button_info, False, False, 0)
    else:
      self._command_info_hbox.set_margin_end(
        self._COMMAND_SHORT_DESCRIPTION_LABEL_RIGHT_MARGIN_WITHOUT_COMMAND_INFO)
      self._command_info_hbox.set_margin_bottom(
        self._COMMAND_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_COMMAND_INFO)

  def _on_button_info_clicked(self, _button):
    self._info_popup.show()
    self._info_popup_text.select_region(0, 0)  # Prevents selecting the entire text
    self._update_info_popup_position()

  def _on_button_info_focus_out_event(self, _button, _event):
    self._info_popup.hide()

  def _update_info_popup_position(self):
    if self._button_info is not None:
      position = gui_utils_.get_position_below_widget(self._button_info)
      if position is not None:
        self._info_popup.move(*position)

  def _set_arguments(self, command):
    row_index_for_arguments = -1
    row_index_for_more_options = -1

    for setting in command['arguments']:
      if not setting.gui.get_visible():
        continue

      grid, indexes_in_grid = self._get_grid_and_indexes_in_grid(setting)

      if commands_.MORE_OPTIONS_TAG in setting.tags:
        row_index_for_more_options += 1
        row_index = row_index_for_more_options
      else:
        row_index_for_arguments += 1
        row_index = row_index_for_arguments

      gui_utils_grid_.attach_label_to_grid(
        grid,
        setting,
        row_index,
        max_width_chars=self._COMMAND_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS,
        set_name_as_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
      )

      gui_utils_grid_.attach_widget_to_grid(
        grid,
        setting,
        row_index,
        set_name_as_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
      )

      indexes_in_grid[setting] = row_index

  def _set_more_options(self, command):
    row_index = len(self._command_more_options_indexes_in_grid)

    for setting in command['more_options']:
      if not setting.gui.get_visible():
        continue

      gui_utils_grid_.attach_label_to_grid(
        self._grid_more_options,
        setting,
        row_index,
        max_width_chars=self._COMMAND_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS,
        set_name_as_tooltip=False,
      )

      gui_utils_grid_.attach_widget_to_grid(
        self._grid_more_options,
        setting,
        row_index,
        set_name_as_tooltip=False,
      )

      row_index += 1

  def _get_grid_and_indexes_in_grid(self, setting):
    if commands_.MORE_OPTIONS_TAG in setting.tags:
      return self._grid_more_options, self._command_more_options_indexes_in_grid
    else:
      return self._grid_command_arguments, self._command_argument_indexes_in_grid

  def _set_grids_to_update_according_to_visible_state(self, command):
    for setting in command['arguments']:
      setting.connect_event('gui-visible-changed', self._on_command_argument_gui_visible_changed)

  def _on_command_argument_gui_visible_changed(self, setting):
    if setting.gui.get_visible():
      self._add_command_argument_to_grid(setting)
    else:
      self._remove_command_argument_from_grid(setting)

  def _add_command_argument_to_grid(self, setting):
    grid, indexes_in_grid = self._get_grid_and_indexes_in_grid(setting)

    if setting in indexes_in_grid:
      return

    previous_settings_for_arguments = []
    previous_settings_for_more_options = []

    for setting_in_arguments in self._command['arguments']:
      if setting_in_arguments.name == setting.name:
        break

      if commands_.MORE_OPTIONS_TAG in setting_in_arguments.tags:
        previous_settings = previous_settings_for_more_options
      else:
        previous_settings = previous_settings_for_arguments

      previous_settings.insert(0, setting_in_arguments)

    if commands_.MORE_OPTIONS_TAG in setting.tags:
      previous_settings = previous_settings_for_more_options
    else:
      previous_settings = previous_settings_for_arguments

    last_visible_previous_setting = next(
      iter(
        previous_setting for previous_setting in previous_settings
        if previous_setting in indexes_in_grid),
      None)

    if last_visible_previous_setting is not None:
      row_index = indexes_in_grid[last_visible_previous_setting] + 1
    else:
      row_index = 0

    grid.insert_row(row_index)
    self._attach_command_argument_to_grid(setting, grid, row_index)

    if last_visible_previous_setting is not None:
      new_indexes_in_grid = {}

      for setting_in_grid, row_index in indexes_in_grid.items():
        new_indexes_in_grid[setting_in_grid] = row_index

        if setting_in_grid == last_visible_previous_setting:
          # The row indexes will be refreshed anyway, so any value is OK at this point.
          new_indexes_in_grid[setting] = 0

      indexes_in_grid = new_indexes_in_grid
    else:
      indexes_in_grid = dict({setting: 0}, **indexes_in_grid)

    indexes_in_grid = self._refresh_indexes_in_grid(indexes_in_grid)

    if commands_.MORE_OPTIONS_TAG in setting.tags:
      self._command_more_options_indexes_in_grid = indexes_in_grid
    else:
      self._command_argument_indexes_in_grid = indexes_in_grid

    # This is necessary to show the newly attached widgets.
    grid.show_all()

  def _attach_command_argument_to_grid(self, setting, grid, row_index):
    gui_utils_grid_.attach_label_to_grid(
      grid,
      setting,
      row_index,
      max_width_chars=self._COMMAND_ARGUMENT_DESCRIPTION_MAX_WIDTH_CHARS,
      set_name_as_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
    )

    gui_utils_grid_.attach_widget_to_grid(
      grid,
      setting,
      row_index,
      set_name_as_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
    )

  def _remove_command_argument_from_grid(self, setting):
    grid, indexes_in_grid = self._get_grid_and_indexes_in_grid(setting)

    row_index = indexes_in_grid.pop(setting, None)
    if row_index is not None:
      grid.remove_row(row_index)

    indexes_in_grid = self._refresh_indexes_in_grid(indexes_in_grid)

    if commands_.MORE_OPTIONS_TAG in setting.tags:
      self._command_more_options_indexes_in_grid = indexes_in_grid
    else:
      self._command_argument_indexes_in_grid = indexes_in_grid

  @staticmethod
  def _refresh_indexes_in_grid(indexes_in_grid):
    return {setting: index for index, setting in enumerate(indexes_in_grid)}

  def _show_hide_additional_settings(self):
    if self._show_additional_settings:
      self._hbox_additional_settings.show()
    else:
      self._hbox_additional_settings.hide()

  def _on_button_preview_clicked(self, _button):
    self._command['enabled'].set_value(self._button_preview.get_active())

  def _on_button_reset_clicked(self, _button):
    self.reset()


def _get_command_info_from_pdb_procedure(pdb_procedure):
  if pdb_procedure is None:
    return None

  if pdb_procedure is not None:
    command_info = ''
    command_main_info = []

    help_text = pdb_procedure.help
    if help_text:
      command_main_info.append(help_text)

    command_info += '\n\n'.join(command_main_info)

    command_author_info = []
    authors = pdb_procedure.authors
    if authors:
      command_author_info.append(authors)

    date_text = pdb_procedure.date
    if date_text:
      command_author_info.append(date_text)

    copyright_text = pdb_procedure.copyright
    if copyright_text:
      if not authors.startswith(copyright_text):
        command_author_info.append(f'\u00a9 {copyright_text}')
      else:
        if authors:
          command_author_info[0] = f'\u00a9 {command_author_info[0]}'

    if command_author_info:
      if command_info:
        command_info += '\n\n'
      command_info += ', '.join(command_author_info)

    return command_info


def _create_command_info_popup(command_info, parent_widget, max_width_chars=100, border_width=3):
  info_popup = Gtk.Window(
    type=Gtk.WindowType.POPUP,
    type_hint=Gdk.WindowTypeHint.TOOLTIP,
    resizable=False,
  )
  info_popup.set_attached_to(parent_widget)

  parent_widget_realize_event_id = parent_widget.connect(
    'realize',
    lambda *args: info_popup.set_transient_for(gui_utils_.get_toplevel_window(parent_widget)))

  info_popup_text = Gtk.Label(
    label=command_info,
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

  info_popup_hide_context = gui_widgets_.PopupHideContext(
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
