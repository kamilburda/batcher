"""Widget for editing the contents of a command (action/condition)."""

import os
import traceback

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import commands as commands_
from src import gimp_config as gimp_config_
from src import setting as setting_
from src.gui import messages as messages_
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

  _TOP_HORIZONTAL_SPACING = 3
  _TOP_VERTICAL_SPACING = 9
  _CONTENTS_BORDER_WIDTH = 6
  _CONTENTS_SPACING = 3

  _GRID_ROW_SPACING = 3
  _GRID_COLUMN_SPACING = 8

  _HBOX_ADDITIONAL_SETTINGS_SPACING = 6
  _HBOX_ADDITIONAL_SETTINGS_BOTTOM_MARGIN = 3

  _MORE_OPTIONS_SPACING = 3
  _MORE_OPTIONS_LABEL_TOP_MARGIN = 6
  _MORE_OPTIONS_LABEL_BOTTOM_MARGIN = 6

  _COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_COMMAND_INFO = 50
  _COMMAND_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_COMMAND_INFO = 6
  _COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_COMMAND_INFO = 60
  _COMMAND_ARGUMENT_LABEL_WIDTH_CHARS = 20

  def __init__(self, command, parent, is_in_browser=False):
    self._command = command
    self._parent = parent

    self._is_in_browser = is_in_browser

    if (self._command['origin'].value in ['gimp_pdb', 'gegl']
        and self._command['function'].value
        and self._command['function'].value in pdb):
      self._pdb_procedure = pdb[self._command['function'].value]
    else:
      self._pdb_procedure = None

    self._info_popup = None
    self._info_popup_text = None

    self._command_argument_indexes_in_grid = {}
    self._command_more_options_indexes_in_grid = {}

    self._label_width_chars_for_arguments = self._COMMAND_ARGUMENT_LABEL_WIDTH_CHARS

    self._init_gui()

    self._button_preview.connect('clicked', self._on_button_preview_clicked)
    self._button_reset.connect('clicked', self._on_button_reset_clicked)

  @property
  def command(self):
    return self._command

  @property
  def widget(self):
    return self._vbox

  @property
  def is_in_browser(self):
    return self._is_in_browser

  @is_in_browser.setter
  def is_in_browser(self, value):
    self._is_in_browser = value

    self._show_hide_additional_gui()

  def reset(self):
    self._command['display_name'].reset()
    self._command['arguments'].reset()
    self._command['more_options'].reset()

  def set_parent(self, parent):
    self._parent = parent

    self._info_popup, self._info_popup_text = (
      _create_command_info_popup(self._command_info, self._parent))

  def _init_gui(self):
    self._set_up_top_widgets(self._command, self._parent)

    self._button_preview = Gtk.CheckButton(label=_('_Preview'), use_underline=True)
    self._button_preview.show_all()

    self._button_reset = Gtk.Button(label=_('_Reset'), use_underline=True)
    self._button_reset.show_all()

    self._hbox_additional_settings = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_ADDITIONAL_SETTINGS_SPACING,
      margin_bottom=self._HBOX_ADDITIONAL_SETTINGS_BOTTOM_MARGIN,
    )
    self._hbox_additional_settings.set_no_show_all(True)
    self._hbox_additional_settings.pack_start(self._button_preview, False, False, 0)
    self._hbox_additional_settings.pack_start(self._button_reset, False, False, 0)

    self._label_command_name = Gtk.Label(
      use_markup=True,
      selectable=True,
      can_focus=False,
      ellipsize=True,
      xalign=0.0,
      yalign=0.5,
    )
    self._label_command_name.set_markup(f'<b>{self._command["display_name"].value}</b>')
    self._label_command_name.show_all()
    self._label_command_name.set_no_show_all(True)

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

    self._vbox.pack_start(self._label_command_name, False, False, 0)
    if self._hbox_top.get_children():
      self._vbox.pack_start(self._vbox_top, False, False, 0)
    self._vbox.pack_start(self._hbox_additional_settings, False, False, 0)
    self._vbox.pack_start(self._grid_command_arguments, False, False, 0)
    self._vbox.pack_start(self._command['more_options_expanded'].gui.widget, False, False, 0)

    self._set_arguments(self._command)

    self._set_more_options(self._command)

    self._set_grids_to_update_according_to_visible_state(self._command)

    self._show_hide_additional_gui()

  def _set_up_top_widgets(self, command, parent):
    self._button_preset = None
    self._button_info = None
    self._command_info = None
    self._info_popup = None
    self._info_popup_text = None

    self._hbox_top = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._TOP_HORIZONTAL_SPACING,
    )

    self._vbox_top = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._TOP_VERTICAL_SPACING,
    )
    self._vbox_top.pack_start(self._hbox_top, False, False, 0)

    self._command_info = _get_command_info_from_pdb_procedure(self._pdb_procedure)

    if self._command_info:
      max_width_chars = self._COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITH_COMMAND_INFO
    else:
      max_width_chars = self._COMMAND_SHORT_DESCRIPTION_MAX_WIDTH_CHARS_WITHOUT_COMMAND_INFO

    description_lines = []

    if command['description'].value:
      description_lines = [line.strip() for line in command['description'].value.splitlines()]
      description_lines = [line for line in description_lines if line]

      for index, line in enumerate(description_lines):
        if index == 0:
          box = self._hbox_top
        else:
          box = self._vbox_top

        label = Gtk.Label(
          label=line,
          use_markup=False,
          selectable=True,
          wrap=True,
          max_width_chars=max_width_chars,
          xalign=0.0,
        )
        box.pack_start(label, True, True, 0)

    if self._command_info:
      self._info_popup, self._info_popup_text = (
        _create_command_info_popup(self._command_info, parent))

      self._button_info = Gtk.Button(
        image=Gtk.Image.new_from_icon_name(GimpUi.ICON_DIALOG_INFORMATION, Gtk.IconSize.BUTTON),
        relief=Gtk.ReliefStyle.NONE,
        tooltip_text=_('Show more information'),
        valign=Gtk.Align.START,
      )
      self._hbox_top.pack_end(self._button_info, False, False, 0)

      self._button_info.connect('clicked', self._on_button_info_clicked)
      self._button_info.connect('focus-out-event', self._on_button_info_focus_out_event)

    display_preset_management = self._get_button_preset_status()

    if display_preset_management:
      self._menu_preset = Gtk.Menu()

      self._menu_item_load_preset = Gtk.MenuItem(label=_('Load Preset from File...'))
      self._menu_preset.append(self._menu_item_load_preset)

      self._menu_item_save_preset = Gtk.MenuItem(label=_('Save Preset to File...'))
      self._menu_preset.append(self._menu_item_save_preset)

      self._menu_preset.show_all()

      self._button_preset = Gtk.Button(
        relief=Gtk.ReliefStyle.NONE,
        image=Gtk.Image.new_from_icon_name(GimpUi.ICON_MENU_LEFT, Gtk.IconSize.BUTTON),
        valign=Gtk.Align.START,
      )

      if commands_.DISABLE_MANAGE_PRESETS_TAG not in self._command.tags:
        self._button_preset.set_tooltip_text(_('Manage presets'))
      else:
        self._button_preset.set_tooltip_text(_(
          'Use the built-in {} to load or save a preset.'
          ' If not available, upgrade to the latest version of GIMP.'
        ).format(self._command['display_name'].default_value))

        self._button_preset.set_sensitive(False)

      self._button_preset.connect('clicked', self._on_button_preset_clicked)
      self._menu_item_load_preset.connect('activate', self._on_menu_item_load_preset_activate)
      self._menu_item_save_preset.connect('activate', self._on_menu_item_save_preset_activate)

      self._hbox_top.pack_end(self._button_preset, False, False, 0)

    if not self._command_info or not self._button_preset or len(description_lines) >= 2:
      self._vbox_top.set_margin_bottom(
        self._COMMAND_SHORT_DESCRIPTION_LABEL_BOTTOM_MARGIN_WITHOUT_COMMAND_INFO)

  def _get_button_preset_status(self):
    if self._pdb_procedure is None:
      if self._command['origin'].value != 'builtin':
        return False
    else:
      if not self._pdb_procedure.raw_arguments:
        return False

    if len(self._command['arguments']) == 1 and self._has_run_mode_argument():
      return False

    if self._command['origin'].value == 'gimp_pdb':
      is_procedure_internal = self._pdb_procedure.proc.get_proc_type() == Gimp.PDBProcType.INTERNAL

      return not is_procedure_internal
    elif self._command['origin'].value == 'gegl':
      return True
    elif self._command['origin'].value == 'builtin':
      return commands_.CAN_MANAGE_PRESETS_TAG in self._command.tags
    else:
      return False

  def _on_button_info_clicked(self, _button):
    self._info_popup.show()
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

    self._label_width_chars_for_arguments = gui_utils_grid_.get_max_label_width_from_settings(
      command['arguments'])

    for setting in command['arguments']:
      if not setting.gui.get_visible():
        continue

      grid, indexes_in_grid = self._get_grid_and_indexes_in_grid(setting)

      self._set_must_be_merged(setting)

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
        width_chars=self._label_width_chars_for_arguments,
        max_width_chars=self._label_width_chars_for_arguments,
        include_name_in_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
      )

      gui_utils_grid_.attach_widget_to_grid(
        grid,
        setting,
        row_index,
        include_name_in_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
      )

      indexes_in_grid[setting] = row_index

  @staticmethod
  def _set_must_be_merged(setting):
    if commands_.FILTER_MUST_BE_MERGED_TAG in setting.tags:
      setting.gui.set_sensitive(False)

  def _set_more_options(self, command):
    row_index = len(self._command_more_options_indexes_in_grid)

    label_width_chars = gui_utils_grid_.get_max_label_width_from_settings(command['more_options'])

    for setting in command['more_options']:
      if not setting.gui.get_visible():
        continue

      gui_utils_grid_.attach_label_to_grid(
        self._grid_more_options,
        setting,
        row_index,
        width_chars=label_width_chars,
        max_width_chars=label_width_chars,
        include_name_in_tooltip=False,
      )

      gui_utils_grid_.attach_widget_to_grid(
        self._grid_more_options,
        setting,
        row_index,
        include_name_in_tooltip=False,
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
      width_chars=self._label_width_chars_for_arguments,
      max_width_chars=self._label_width_chars_for_arguments,
      include_name_in_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
    )

    gui_utils_grid_.attach_widget_to_grid(
      grid,
      setting,
      row_index,
      include_name_in_tooltip=self._command['origin'].value in ['gimp_pdb', 'gegl'],
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

  def _show_hide_additional_gui(self):
    if self._is_in_browser:
      self._label_command_name.show()
      self._hbox_additional_settings.show()
    else:
      self._label_command_name.hide()
      self._hbox_additional_settings.hide()

  def _on_button_preset_clicked(self, button):
    self._menu_preset.popup_at_widget(
      button,
      Gdk.Gravity.NORTH_WEST,
      Gdk.Gravity.NORTH_EAST,
      None,
    )

  def _on_menu_item_load_preset_activate(self, _menu_item):
    file_dialog = Gtk.FileChooserNative(
      title=_('Load Preset from File'),
      action=Gtk.FileChooserAction.OPEN,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self._parent),
    )

    file_dialog.connect('response', self._on_load_preset_file_dialog_response)

    file_dialog.show()

  def _on_load_preset_file_dialog_response(self, file_dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
      filepath = file_dialog.get_filename()

      if not filepath or not os.path.exists(filepath):
        gui_utils_.display_popover(self._button_preset, _('Preset file not found.'))

      try:
        parsed_data = gimp_config_.parse(filepath)
      except gimp_config_.GimpConfigParseError:
        gui_utils_.display_popover(
          self._button_preset,
          _('The specified preset file is not valid.'),
          icon_name=GimpUi.ICON_DIALOG_WARNING,
          max_width_chars=35,
        )
      else:
        self._load_parsed_config_to_command_arguments(parsed_data)

  def _load_parsed_config_to_command_arguments(self, parsed_data):
    if 'load_preset_preprocessor' in self._command:
      parsed_data_dict = dict(
        self._command['load_preset_preprocessor'].value(self._command, parsed_data))
    else:
      parsed_data_dict = dict(parsed_data)

    error_messages = []

    for name, value in parsed_data_dict.items():
      if name in self._command['arguments'] and not self._is_run_mode_argument(name):
        # HACK: There is no clean way within `ArraySetting` to distinguish
        # whether the input list comes from a GIMP config or elsewhere. Since
        # arrays always have a length argument from the GIMP config and not
        # from other sources, the argument could be mistakenly treated as a
        # regular array element. We therefore remove the length here. Also,
        # each element must be enclosed in a list to match the format accepted
        # by the underlying setting type.
        # There should be a place outside the GUI to handle this.
        processed_value = value

        if isinstance(self._command[f'arguments/{name}'], setting_.ArraySetting):
          if len(processed_value) >= 1:
            processed_value = [[val] for val in processed_value[1:]]

        try:
          self._command[f'arguments/{name}'].set_value(processed_value)
        except Exception as e:
          error_messages.append((name, str(e), traceback.format_exc()))

    if error_messages:
      messages_.display_failure_message(
        _('Some values could not be loaded from the preset file:'),
        failure_message='\n'.join(
          [f'{message_data[0]}: {message_data[1]}' for message_data in error_messages]),
        details=error_messages[-1][2],
        parent=gui_utils_.get_toplevel_window(self._parent),
      )

  def _on_menu_item_save_preset_activate(self, _menu_item):
    file_dialog = Gtk.FileChooserNative(
      title=_('Load Preset from File'),
      action=Gtk.FileChooserAction.SAVE,
      do_overwrite_confirmation=True,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self._parent),
    )

    file_dialog.connect('response', self._on_save_preset_file_dialog_response)

    file_dialog.show()

  def _on_save_preset_file_dialog_response(self, file_dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
      self._save_command_arguments_to_config(file_dialog.get_filename())

  def _save_command_arguments_to_config(self, config_filepath):
    contents = []
    error_messages = []

    if self._pdb_procedure is not None:
      pdb_argument_names = set(arg.name for arg in self._pdb_procedure.raw_arguments)
    else:
      pdb_argument_names = None

    for setting in self._command['arguments']:
      if self._is_run_mode_argument(setting.name):
        continue

      if pdb_argument_names is not None and setting.name not in pdb_argument_names:
        continue

      try:
        value_as_string = setting.value_to_string()
      except NotImplementedError:
        pass
      except Exception as e:
        error_messages.append((setting.name, str(e), traceback.format_exc()))
      else:
        contents.append((setting.name, value_as_string))

    if 'save_preset_preprocessor' in self._command:
      processed_contents = self._command['save_preset_preprocessor'].value(self._command, contents)
    else:
      processed_contents = contents

    try:
      gimp_config_.serialize(processed_contents, config_filepath)
    except Exception as e:
      messages_.display_failure_message(
        _(f'Could not save preset file "{config_filepath}":'),
        failure_message=str(e),
        details=traceback.format_exc(),
        parent=gui_utils_.get_toplevel_window(self._parent),
      )
    else:
      if not error_messages:
        gui_utils_.display_popover(self._button_preset, _('Preset successfully saved.'))
      else:
        messages_.display_failure_message(
          _('Some values could not be saved to the preset file:'),
          failure_message='\n'.join(
            [f'{message_data[0]}: {message_data[1]}' for message_data in error_messages]),
          details=error_messages[-1][2],
          parent=gui_utils_.get_toplevel_window(self._parent),
        )

  def _on_button_preview_clicked(self, _button):
    self._command['enabled'].set_value(self._button_preview.get_active())

  def _on_button_reset_clicked(self, _button):
    self.reset()

  def _has_run_mode_argument(self):
    return (
      'run-mode' in self._command['arguments']
      and isinstance(self._command['arguments/run-mode'], setting_.EnumSetting))

  def _is_run_mode_argument(self, argument_name):
    return (
      argument_name == 'run-mode'
      and isinstance(self._command['arguments/run-mode'], setting_.EnumSetting))


def _get_command_info_from_pdb_procedure(pdb_procedure):
  if pdb_procedure is None:
    return None

  if pdb_procedure is not None:
    command_info = ''

    command_main_info = []

    help_text = pdb_procedure.help
    if help_text:
      if command_info:
        command_info += '\n\n'
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


def _create_command_info_popup(command_info, parent_widget, max_width_chars=70, border_width=3):
  info_popup = Gtk.Window(
    type=Gtk.WindowType.POPUP,
    type_hint=Gdk.WindowTypeHint.TOOLTIP,
    resizable=False,
    attached_to=parent_widget,
    transient_for=gui_utils_.get_toplevel_window(parent_widget),
  )

  info_popup_text = Gtk.Label(
    label=command_info,
    use_markup=False,
    selectable=True,
    can_focus=False,
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

  return info_popup, info_popup_text
