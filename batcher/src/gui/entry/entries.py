"""GTK text entries with enhanced features, including undo/redo history and a
customizable popup.
"""

from typing import List, Optional, Tuple

import gi
from gi.repository import GObject
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

import pygimplib as pg

from . import expander as entry_expander_
from . import popup as entry_popup_
from . import undo as entry_undo_

from src import fileformats
from src.gui import cell_renderers as cell_renderers_
from src.gui import popup_hide_context as popup_hide_context_
from src.path import pattern as pattern_


class ExtendedEntry(Gtk.Entry, Gtk.Editable):
  """Subclass of `Gtk.Entry` with additional capabilities.

  Additional features include:
    * undo/redo of text,
    * placeholder text,
    * expandable width of the entry.
  """

  _PLACEHOLDER_STYLE_CLASS_NAME = 'placeholder'
  
  def __init__(
        self,
        minimum_width_chars: int = -1,
        maximum_width_chars: int = -1,
        placeholder_text: Optional[str] = None,
        **kwargs,
  ):
    """Initializes an `ExtendedEntry` instance.

    Args:
      minimum_width_chars:
        Minimum width specified as a number of characters. The entry will not
        shrink below this width.
      maximum_width_chars:
        Maximum width specified as a number of characters. The entry will not
        expand above this width.
      placeholder_text:
        Text to display as a placeholder if the entry is empty. If ``None``,
        do not display any placeholder.
      **kwargs:
        Additional keyword arguments that can be passed to the `Gtk.Entry()`
        constructor.
    """
    Gtk.Entry.__init__(self, **kwargs)

    self._minimum_width_chars = minimum_width_chars
    self._maximum_width_chars = maximum_width_chars
    self._placeholder_text = placeholder_text

    self._undo_context = entry_undo_.EntryUndoContext(self)
    self._popup = None
    self._expander = entry_expander_.EntryExpander(
      self, self._minimum_width_chars, self._maximum_width_chars)
    
    self._has_placeholder_text_assigned = False

    self._placeholder_css_provider = Gtk.CssProvider()
    self._placeholder_css_provider.load_from_data(
      f'entry.{self._PLACEHOLDER_STYLE_CLASS_NAME} {{font-style: italic;}}'.encode())
    self.get_style_context().add_provider(
      self._placeholder_css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    self.connect('focus-in-event', self._on_extended_entry_focus_in_event)
    self.connect('focus-out-event', self._on_extended_entry_focus_out_event)
    self.connect_after('realize', self._on_after_extended_entry_realize)

  @property
  def undo_context(self) -> entry_undo_.EntryUndoContext:
    """`entry_undo.EntryUndoContext` instance to handle undo/redo actions."""
    return self._undo_context

  # HACK: Instead of connecting an 'insert-text' signal handler, we override the
  # `Gtk.Editable.do_insert_text` virtual method to avoid warnings related to
  # 'insert-text'.
  # More information: https://stackoverflow.com/a/38831655
  def do_insert_text(self, new_text: str, new_text_length: int, position: int) -> int:
    return self.undo_context.handle_insert_text(new_text, new_text_length, position)

  # For consistency with `do_insert_text`, we also override
  # `Gtk.Editable.do_delete_text` instead of connecting a 'delete-text' handler.
  def do_delete_text(self, start_pos: int, end_pos: int):
    self.undo_context.handle_delete_text(start_pos, end_pos)

  def assign_text(self, text: str, enable_undo: bool = False):
    """Replaces the current contents of the entry with the specified text.
    
    If the entry does not have focus and the text is empty or matches the
    placeholder text, the placeholder text is assigned.
     
    If ``enable_undo`` is ``True``, the replacement performed by this method is
    added to the undo history.
    """
    if self.has_focus() or not self._should_assign_placeholder_text(text):
      self._unassign_placeholder_text()
      self._do_assign_text(text, enable_undo)
    else:
      self._assign_placeholder_text()
  
  def get_text(self) -> str:
    """Returns the entry text if not matching the placeholder text, otherwise
    returns an empty string.

    The entry text is the return value of `Gtk.Entry.get_text()`.
    """
    if not self._has_placeholder_text_assigned:
      return super().get_text()
    else:
      return ''
  
  def _do_assign_text(self, text, enable_undo=False):
    """Use this method to set text instead of ``assign_text()`` if it is not
    desired to handle placeholder text assignment.
    """
    if self._popup is not None:
      self._popup.trigger_popup = False
    if not enable_undo:
      self.undo_context.undo_enabled = False

    self.set_text(text)
    
    if not enable_undo:
      self.undo_context.undo_enabled = True
    if self._popup is not None:
      self._popup.trigger_popup = True
  
  def _assign_placeholder_text(self):
    if self._placeholder_text is not None:
      self._has_placeholder_text_assigned = True
      
      # Delay font modification until after widget realization as the font may
      # have been different before the realization.
      if self.get_realized():
        self.get_style_context().add_class(self._PLACEHOLDER_STYLE_CLASS_NAME)
      
      self._do_assign_text(self._placeholder_text)
  
  def _unassign_placeholder_text(self):
    if self._has_placeholder_text_assigned:
      self._has_placeholder_text_assigned = False
      self.get_style_context().remove_class(self._PLACEHOLDER_STYLE_CLASS_NAME)
      self._do_assign_text('')
      if self._popup is not None:
        self._popup.save_last_value()
  
  def _should_assign_placeholder_text(self, text):
    return (
      not text
      or (self._placeholder_text is not None and text == self._placeholder_text))
  
  def _on_extended_entry_focus_in_event(self, entry, event):
    self._unassign_placeholder_text()
  
  def _on_extended_entry_focus_out_event(self, entry, event):
    if self._should_assign_placeholder_text(self.get_text()):
      self._assign_placeholder_text()

  def _on_after_extended_entry_realize(self, entry):
    if self._should_assign_placeholder_text(self.get_text()):
      self._assign_placeholder_text()


class FilenamePatternEntry(ExtendedEntry):
  """Subclass of `ExtendedEntry` used for typing a file name pattern.

  A popup displaying the list of suggested items (components of the pattern) is
  displayed while typing.
  """
  
  _BUTTON_MOUSE_LEFT = 1
  _TOOLTIP_WINDOW_BORDER_WIDTH = 3
  
  _COLUMNS = [
    _COLUMN_ITEM_NAMES,
    _COLUMN_ITEMS_TO_INSERT,
    _COLUMN_REGEX_TO_MATCH,
    _COLUMN_ITEM_DESCRIPTIONS] = (
      0, 1, 2, 3)
  
  _COLUMN_TYPES = [
    GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING, GObject.TYPE_STRING]
  
  def __init__(
        self,
        suggested_items: List[Tuple[str, str, str, str]],
        default_item: Optional[str] = None,
        **kwargs):
    """Initializes a `FilenamePatternEntry` instance.

    Args:
      suggested_items:
        List of `(item name displayed in popup, text to insert in entry,
        regular expression matching item name, description)` tuples
        describing each item.
      default_item:
        The second element of an item from the ``suggested_items`` that is
        displayed as placeholder text, or ``None`` for no default item. This
        argument replaces the ``placeholder_text`` parameter from
        `ExtendedEntry.__init__()`.
      **kwargs:
        Additional keyword arguments that can be passed to the parent class'
        `__init__()` method.
    """
    self._default_item_value = default_item
    
    self._item_regexes_and_descriptions = {item[2]: item[3] for item in suggested_items}
    
    suggested_item_values = [item[1] for item in suggested_items]
    if (self._default_item_value is not None
        and self._default_item_value not in suggested_item_values):
      raise ValueError(
        (f'default item "{self._default_item_value}" not in the list of'
         f' suggested items: {suggested_item_values}'))

    if (suggested_items
        and self._default_item_value is not None
        and self._default_item_value in suggested_item_values):
      kwargs['placeholder_text'] = (
        suggested_items[suggested_item_values.index(self._default_item_value)][0])
    
    super().__init__(**kwargs)

    self._cursor_position_before_assigning_from_row = None
    self._reset_cursor_position_before_assigning_from_row = True
    
    self._last_field_with_tooltip = ''
    
    self._pango_layout = Pango.Layout.new(self.get_pango_context())
    
    self._popup = entry_popup_.EntryPopup(self, self._COLUMN_TYPES, suggested_items)
    self._popup.filter_rows_func = self._filter_suggested_items
    self._popup.on_assign_from_selected_row = self._on_assign_from_selected_row
    self._popup.on_assign_last_value = self._assign_last_value
    self._popup.on_row_left_mouse_button_press = self._on_row_left_mouse_button_press
    self._popup.on_entry_changed_show_popup_condition = self._on_entry_changed_condition
    self._popup.on_entry_key_press = self._on_entry_key_press
    self._popup.on_entry_after_assign_by_key_press = (
      self._on_entry_after_assign_by_key_press)
    
    self._create_field_tooltip()
    
    self._add_columns()

    self._field_tooltip_hide_context = popup_hide_context_.PopupHideContext(
      self._field_tooltip_window,
      self,
      widgets_to_exclude_from_triggering_hiding=[
        self._field_tooltip_window,
        self,
      ],
    )
    self._field_tooltip_hide_context.enable()

    self.connect(
      'notify::cursor-position', self._on_filename_pattern_entry_notify_cursor_position)
    self.connect('changed', self._on_filename_pattern_entry_changed)
    self.connect('focus-out-event', self._on_filename_pattern_entry_focus_out_event)
    self.connect('realize', self._on_filename_pattern_entry_realize)

  @property
  def popup(self) -> entry_popup_.EntryPopup:
    """`entry_popup.EntryPopup` instance serving as the popup."""
    return self._popup
  
  def _should_assign_placeholder_text(self, text: str) -> bool:
    """Determines whether placeholder text should be set.

    Unlike the parent method, this method uses the value of the suggested
    item rather than its display name.
    """
    return (
      not text
      or (self._default_item_value is not None and text == self._default_item_value))
  
  def _create_field_tooltip(self):
    self._field_tooltip_window = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      type_hint=Gdk.WindowTypeHint.TOOLTIP,
      resizable=False,
    )
    self._field_tooltip_window.set_attached_to(self)
    
    self._field_tooltip_text = Gtk.Label(
      selectable=True,
    )
    
    self._field_tooltip_hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      border_width=self._TOOLTIP_WINDOW_BORDER_WIDTH,
    )
    self._field_tooltip_hbox.pack_start(self._field_tooltip_text, True, True, 0)

    self._field_tooltip_scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.NEVER,
      vscrollbar_policy=Gtk.PolicyType.NEVER,
      shadow_type=Gtk.ShadowType.ETCHED_IN,
    )
    self._field_tooltip_scrolled_window.add(self._field_tooltip_hbox)
    self._field_tooltip_scrolled_window.show_all()
    
    self._field_tooltip_window.add(self._field_tooltip_scrolled_window)
  
  def _add_columns(self):
    self._popup.tree_view.append_column(
      Gtk.TreeViewColumn(
        cell_renderer=Gtk.CellRendererText(),
        text=self._COLUMN_ITEM_NAMES,
      ),
    )
  
  def _on_filename_pattern_entry_notify_cursor_position(self, entry, property_spec):
    field = pattern_.StringPattern.get_field_at_position(self.get_text(), self.get_position())
    
    if field is None:
      self._hide_field_tooltip()
      return
    
    matching_field_regex = pattern_.StringPattern.get_first_matching_field_regex(
      field, self._item_regexes_and_descriptions)
    
    if matching_field_regex not in self._item_regexes_and_descriptions:
      self._hide_field_tooltip()
      return
    
    if field != self._last_field_with_tooltip:
      self._last_field_with_tooltip = field
      force_update_position = True
    else:
      force_update_position = False
    
    self._show_field_tooltip(
      self._item_regexes_and_descriptions[matching_field_regex], force_update_position)
  
  def _show_field_tooltip(self, tooltip_text=None, force_update_position=False):
    if not self._field_tooltip_window.get_mapped() or force_update_position:
      if tooltip_text is None:
        tooltip_text = ''
      self._field_tooltip_text.set_markup(tooltip_text)
      self._field_tooltip_window.show()
      self._field_tooltip_text.select_region(0, 0)  # Prevents selecting the entire text
      self._update_field_tooltip_position()
  
  def _hide_field_tooltip(self):
    if self._field_tooltip_window.get_mapped():
      self._field_tooltip_window.hide()
  
  def _update_field_tooltip_position(self):
    self._update_window_position(self._field_tooltip_window)
  
  def _update_window_position(self, tooltip_window):
    absolute_entry_position = pg.gui.utils.get_absolute_widget_position(self)

    if absolute_entry_position is not None:
      y = absolute_entry_position[1] - tooltip_window.get_allocation().height

      tooltip_window.move(absolute_entry_position[0], y)
  
  def _on_filename_pattern_entry_changed(self, entry):
    if self._reset_cursor_position_before_assigning_from_row:
      self._cursor_position_before_assigning_from_row = None
  
  def _on_filename_pattern_entry_focus_out_event(self, entry, event):
    self._hide_field_tooltip()

  def _on_filename_pattern_entry_realize(self, entry):
    self._field_tooltip_window.set_transient_for(pg.gui.utils.get_toplevel_window(self))

  def _filter_suggested_items(self, suggested_items, row_iter, data=None):
    item = suggested_items[row_iter][self._COLUMN_ITEMS_TO_INSERT]

    current_text = self.get_text()
    current_position = self.get_position()
    
    if (0 < current_position <= len(current_text)
        and current_text[current_position - 1] == '[' and item and item[0] != '['):
      return False
    else:
      return True
  
  def _on_assign_from_selected_row(self, tree_model, selected_tree_iter):
    if self._cursor_position_before_assigning_from_row is None:
      self._cursor_position_before_assigning_from_row = self.get_position()

    cursor_position = self._cursor_position_before_assigning_from_row
    
    suggested_item = str(tree_model[selected_tree_iter][self._COLUMN_ITEMS_TO_INSERT])
    last_assigned_entry_text = self._popup.last_assigned_entry_text
    
    if (0 < cursor_position <= len(last_assigned_entry_text)
        and last_assigned_entry_text[cursor_position - 1] == '['):
      suggested_item = suggested_item[1:]
    
    self.assign_text(
      (last_assigned_entry_text[:cursor_position] + suggested_item
       + last_assigned_entry_text[cursor_position:]))
    
    self.set_position(cursor_position + len(suggested_item))

    self._cursor_position_before_assigning_from_row = cursor_position
    
    return cursor_position, suggested_item
  
  def _assign_last_value(self, last_value):
    self._reset_cursor_position_before_assigning_from_row = False
    self._do_assign_text(last_value)
    self._reset_cursor_position_before_assigning_from_row = True
    
    if self._cursor_position_before_assigning_from_row is not None:
      self.set_position(self._cursor_position_before_assigning_from_row)
    self._cursor_position_before_assigning_from_row = None
  
  def _on_entry_changed_condition(self):
    current_text = self.get_text()
    current_position = self.get_position()

    if current_text:
      if len(current_text) > 1 and len(current_text) >= current_position:
        return (
          current_text[current_position - 1] == '['
          and current_text[current_position - 2] != '['
          and not pattern_.StringPattern.get_field_at_position(current_text, current_position - 1))
      else:
        return current_text[0] == '['
    else:
      return True
  
  def _on_row_left_mouse_button_press(self):
    self._cursor_position_before_assigning_from_row = None
    
    position, text = self._popup.assign_from_selected_row()
    if position is not None and text:
      self.undo_context.undo_push([('insert', position, text)])
  
  def _on_entry_key_press(self, key_name, tree_path, stop_event_propagation):
    if key_name in ['Return', 'KP_Enter', 'Escape']:
      self._hide_field_tooltip()
      self._cursor_position_before_assigning_from_row = None
    
    return stop_event_propagation
  
  def _on_entry_after_assign_by_key_press(
        self, previous_position, previous_text, position, text):
    undo_push_list = []
    
    if previous_text:
      undo_push_list.append(('delete', previous_position, previous_text))
    
    if position is not None and text:
      undo_push_list.append(('insert', position, text))
    
    if undo_push_list:
      self.undo_context.undo_push(undo_push_list)


class FileExtensionEntry(ExtendedEntry):
  """Subclass of `ExtendedEntry` used for typing a file extension.
  
  A popup displaying the list of available file formats in GIMP and the
  corresponding file extensions is displayed. If a row contains multiple file
  extensions, the user is able to select a particular file extension. By
  default, the first file extension in the row is used.
  """
  
  _COLUMNS = [_COLUMN_DESCRIPTION, _COLUMN_EXTENSIONS] = (0, 1)
  _COLUMN_TYPES = [GObject.TYPE_STRING, GObject.TYPE_STRV]
  
  def __init__(self, **kwargs):
    """Initializes a `FileExtensionEntry` instance.

    Args:
      **kwargs:
        Additional keyword arguments that can be passed to the parent class'
        `__init__()` method.
    """
    super().__init__(**kwargs)
    
    self._tree_view_columns_rects = []
    
    self._cell_renderer_description = None
    self._cell_renderer_extensions = None
    
    self._highlighted_extension_row = None
    self._highlighted_extension_index = None
    self._highlighted_extension = ''
    self._is_modifying_highlight = False
    
    self._extensions_separator_text_pixel_size = None
    self._extensions_text_pixel_rects = []
    
    self._popup = entry_popup_.EntryPopup(
      self, self._COLUMN_TYPES, self._get_file_formats(fileformats.FILE_FORMATS))
    self._popup.filter_rows_func = self._filter_file_formats
    self._popup.on_assign_from_selected_row = self._on_assign_from_selected_row
    self._popup.on_assign_last_value = self._do_assign_text
    self._popup.on_row_left_mouse_button_press = self._on_row_left_mouse_button_press
    self._popup.on_entry_key_press_before_show_popup = (
      self._on_key_press_before_show_popup)
    self._popup.on_entry_key_press = self._on_tab_keys_pressed
    self._popup.on_entry_after_assign_by_key_press = (
      self._on_entry_after_assign_by_key_press)
    
    self._add_columns()
    
    self._popup.tree_view.connect(
      'motion-notify-event', self._on_tree_view_motion_notify_event)
    self._popup.tree_view.connect_after('realize', self._on_after_tree_view_realize)
    self._popup.tree_view.get_selection().connect('changed', self._on_tree_selection_changed)

  @property
  def popup(self) -> entry_popup_.EntryPopup:
    """`entry_popup.EntryPopup` instance serving as the popup."""
    return self._popup
  
  def _do_assign_text(self, *args, **kwargs):
    super()._do_assign_text(*args, **kwargs)
    self.set_position(-1)
  
  def _add_columns(self):
    def _add_column(cell_renderer, cell_renderer_property, column_number, column_title=None):
      self._popup.tree_view.append_column(Gtk.TreeViewColumn(
        title=column_title,
        cell_renderer=cell_renderer,
        **{cell_renderer_property: column_number},
      ))
    
    self._cell_renderer_description = Gtk.CellRendererText()
    self._cell_renderer_extensions = cell_renderers_.CellRendererTextList()
    _add_column(self._cell_renderer_description, 'text', self._COLUMN_DESCRIPTION)
    _add_column(self._cell_renderer_extensions, 'markup-list', self._COLUMN_EXTENSIONS)
  
  def _on_tree_view_motion_notify_event(self, tree_view, event):
    self._highlight_extension_at_pos(int(event.x), int(event.y))
  
  def _on_after_tree_view_realize(self, tree_view):
    self._extensions_separator_text_pixel_size = self._get_text_pixel_size(
      self._cell_renderer_extensions.get_property('text-list-separator'),
      Pango.Layout.new(self._popup.tree_view.get_pango_context()))
    
    self._fill_extensions_text_pixel_rects()
    
    self._tree_view_columns_rects = [
      self._popup.tree_view.get_cell_area(
        Gtk.TreePath.new_from_indices([0]), self._popup.tree_view.get_column(column))
      for column in self._COLUMNS]
  
  def _fill_extensions_text_pixel_rects(self):
    pango_layout = Pango.Layout.new(self._popup.tree_view.get_pango_context())
    
    for file_format in self._popup.rows:
      file_extensions = file_format[1]
      
      if len(file_extensions) > 1:
        text_pixel_rects = self._get_text_pixel_rects(
          file_extensions, pango_layout, self._extensions_separator_text_pixel_size[0])
        for rect in text_pixel_rects:
          rect.x += self._cell_renderer_extensions.get_property('xpad')
          rect.x += self._popup.tree_view.style_get_property('horizontal-separator')
          rect.x += self._popup.tree_view.get_column(self._COLUMN_EXTENSIONS).get_spacing()
          
          # Occupy the space of the separator so that extension highlighting is
          # continuous.
          if rect == text_pixel_rects[0]:
            rect.width += self._extensions_separator_text_pixel_size[0] // 2
          elif rect == text_pixel_rects[-1]:
            rect.x -= self._extensions_separator_text_pixel_size[0] // 2
            rect.width += self._extensions_separator_text_pixel_size[0] // 2
          else:
            rect.x -= self._extensions_separator_text_pixel_size[0] // 2
            rect.width += self._extensions_separator_text_pixel_size[0]
          
        self._extensions_text_pixel_rects.append(text_pixel_rects)
      else:
        self._extensions_text_pixel_rects.append([])
  
  def _on_tree_selection_changed(self, tree_selection):
    self._unhighlight_extension()
  
  def _filter_file_formats(self, file_formats, row_iter, data=None):
    return self._entry_text_matches_row(self.get_text(), file_formats, row_iter)
  
  def _entry_text_matches_row(self, entry_text, file_formats, row_iter, full_match=False):
    if self._is_modifying_highlight:
      return True

    extensions = file_formats[row_iter][self._COLUMN_EXTENSIONS]

    if full_match:
      return any(entry_text.lower() == extension.lower() for extension in extensions)
    else:
      return any(entry_text.lower() in extension.lower() for extension in extensions)
  
  def _on_assign_from_selected_row(self, tree_model, selected_tree_iter, extension_index=0):
    extensions = tree_model[selected_tree_iter][self._COLUMN_EXTENSIONS]
    if extension_index > len(extensions):
      extension_index = len(extensions) - 1
    self._do_assign_text(extensions[extension_index])
    
    return 0, extensions[extension_index]
  
  def _on_row_left_mouse_button_press(self):
    previous_position, previous_text = 0, self.get_text()
    
    if self._highlighted_extension_index is None:
      position, text = self._popup.assign_from_selected_row()
    else:
      self._do_assign_text(self._highlighted_extension)
      position, text = 0, self._highlighted_extension
    
    self._undo_push(previous_position, previous_text, position, text)
  
  def _on_key_press_before_show_popup(self):
    self._unhighlight_extension()
  
  def _on_tab_keys_pressed(self, key_name, selected_tree_path, stop_event_propagation):
    if key_name in ['Tab', 'KP_Tab', 'ISO_Left_Tab']:
      # Tree paths can sometimes point at the first row even though no row is
      # selected, hence the `tree_iter` usage.
      _unused, tree_iter = self._popup.tree_view.get_selection().get_selected()
      
      if tree_iter is not None:
        if key_name in ['Tab', 'KP_Tab']:
          self._highlight_extension_next(selected_tree_path)
        elif key_name == 'ISO_Left_Tab':    # Shift + Tab
          self._highlight_extension_previous(selected_tree_path)
        
        previous_position, previous_text = 0, self.get_text()
        
        self._do_assign_text(self._highlighted_extension)
        
        self._on_entry_after_assign_by_key_press(
          previous_position, previous_text, 0, self._highlighted_extension)
        
        return True
    
    return stop_event_propagation
  
  def _on_entry_after_assign_by_key_press(self, previous_position, previous_text, position, text):
    self._undo_push(previous_position, previous_text, position, text)
  
  def _undo_push(self, previous_position, previous_text, position, text):
    undo_push_list = []
    
    if previous_text:
      undo_push_list.append(('delete', previous_position, previous_text))
    
    if position is not None and text:
      undo_push_list.append(('insert', position, text))
    
    if undo_push_list:
      self.undo_context.undo_push(undo_push_list)
  
  def _highlight_extension_next(self, selected_row_path):
    def _select_next_extension(highlighted_extension_index, len_extensions):
      return (highlighted_extension_index + 1) % len_extensions
    
    self._highlight_extension(selected_row_path, _select_next_extension)
  
  def _highlight_extension_previous(self, selected_row_path):
    def _select_previous_extension(highlighted_extension_index, len_extensions):
      return (highlighted_extension_index - 1) % len_extensions
    
    self._highlight_extension(selected_row_path, _select_previous_extension)
  
  def _highlight_extension(self, selected_row_path, extension_index_selection_func):
    if selected_row_path is not None:
      self._do_unhighlight_extension()
      
      row_path = self._popup.rows_filtered.convert_path_to_child_path(selected_row_path)
      self._highlighted_extension_row = row_path[0]
      
      extensions = self._popup.rows[row_path][self._COLUMN_EXTENSIONS]
      if len(extensions) <= 1:
        # Do not highlight any extension.
        if not extensions:
          self._highlighted_extension = ''
        elif len(extensions) == 1:
          self._highlighted_extension = extensions[0]
        
        return
      
      if self._highlighted_extension_index is None:
        self._highlighted_extension_index = 0
      
      self._highlighted_extension_index = extension_index_selection_func(
        self._highlighted_extension_index, len(extensions))
      
      self._do_highlight_extension()
      
      self._popup.refresh_row(selected_row_path)
  
  def _highlight_extension_at_pos(self, x, y):
    is_in_extensions_column = x >= self._tree_view_columns_rects[self._COLUMN_EXTENSIONS].x
    if not is_in_extensions_column:
      if self._highlighted_extension:
        self._unhighlight_extension()
      return
    
    path_params = self._popup.tree_view.get_path_at_pos(x, y)
    if path_params is None:
      return
    
    selected_path_unfiltered = self._popup.rows_filtered.convert_path_to_child_path(path_params[0])
    extension_index = self._get_extension_index_at_pos(path_params[2], selected_path_unfiltered[0])
    
    if extension_index == self._highlighted_extension_index:
      return
    
    if extension_index is not None:
      self._highlight_extension_at_index(path_params[0], extension_index)
    else:
      self._unhighlight_extension()
  
  def _get_extension_index_at_pos(self, cell_x, selected_row):
    extension_rects = self._extensions_text_pixel_rects[selected_row]
    
    if not extension_rects:
      return None
    
    extension_index = 0
    for extension_rect in extension_rects:
      if extension_rect.x <= cell_x <= extension_rect.x + extension_rect.width:
        break
      extension_index += 1
    
    matches_extension = extension_index < len(extension_rects)
    
    if matches_extension:
      return extension_index
    else:
      return None
  
  def _highlight_extension_at_index(self, selected_row_path, extension_index):
    if selected_row_path is not None:
      self._do_unhighlight_extension()
      
      row_path = self._popup.rows_filtered.convert_path_to_child_path(selected_row_path)
      
      self._highlighted_extension_row = row_path[0]
      self._highlighted_extension_index = extension_index
      
      self._do_highlight_extension()
      
      self._popup.refresh_row(selected_row_path)
  
  def _do_highlight_extension(self):
    self._is_modifying_highlight = True

    highlighted_row = self._highlighted_extension_row
    highlighted_extension_index = self._highlighted_extension_index
    extensions = self._popup.rows[highlighted_row][self._COLUMN_EXTENSIONS]
    
    self._highlighted_extension = extensions[highlighted_extension_index]

    extensions[highlighted_extension_index] = f'<b>{extensions[highlighted_extension_index]}</b>'

    self._popup.rows[highlighted_row][self._COLUMN_EXTENSIONS] = extensions

    self._is_modifying_highlight = False

  def _unhighlight_extension(self):
    self._do_unhighlight_extension()
    
    if self._highlighted_extension_row is not None:
      self._popup.refresh_row(
        Gtk.TreePath.new_from_indices([self._highlighted_extension_row]), is_path_filtered=False)
    
    self._highlighted_extension_row = None
    self._highlighted_extension_index = None
  
  def _do_unhighlight_extension(self):
    if (self._highlighted_extension_row is not None
        and self._highlighted_extension_index is not None):
      extensions = self._popup.rows[self._highlighted_extension_row][self._COLUMN_EXTENSIONS]
      if self._highlighted_extension:
        self._is_modifying_highlight = True

        extensions[self._highlighted_extension_index] = self._highlighted_extension
        self._popup.rows[self._highlighted_extension_row][self._COLUMN_EXTENSIONS] = extensions

        self._is_modifying_highlight = False
        self._highlighted_extension = ''

  @staticmethod
  def _get_file_formats(file_formats):
    return [[file_format.description, file_format.file_extensions]
            for file_format in file_formats if file_format.is_installed()]
  
  @staticmethod
  def _get_text_pixel_size(text, pango_layout):
    pango_layout.set_text(text)
    return pango_layout.get_pixel_size()
  
  def _get_text_pixel_rects(self, file_extensions, pango_layout, separator_pixel_width):
    text_pixel_rects = []
    
    extension_x = 0
    for extension in file_extensions:
      extension_pixel_size = self._get_text_pixel_size(extension, pango_layout)

      rectangle = Gdk.Rectangle()
      rectangle.x = extension_x
      rectangle.y = 0
      rectangle.width = extension_pixel_size[0]
      rectangle.height = extension_pixel_size[1]

      text_pixel_rects.append(rectangle)
      
      extension_x += extension_pixel_size[0] + separator_pixel_width
    
    return text_pixel_rects


GObject.type_register(ExtendedEntry)
GObject.type_register(FilenamePatternEntry)
GObject.type_register(FileExtensionEntry)
