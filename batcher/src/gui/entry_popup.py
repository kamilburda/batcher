"""Custom popup usable for GTK text entries."""

from typing import Callable, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from . import popup_hide_context as popup_hide_context_


class EntryPopup:
  
  # Implementation of the popup is loosely based on the implementation of
  # `Gtk.EntryCompletion`:
  # https://gitlab.gnome.org/GNOME/gtk/-/blob/gtk-3-24/gtk/gtkentrycompletion.c
  
  _BUTTON_MOUSE_LEFT = 1
  
  def __init__(
        self,
        entry: Gtk.Entry,
        column_types,
        rows,
        width: int = -1,
        height: int = 200,
        max_num_visible_rows: int = 8):
    self._entry = entry
    self._width = width
    self._height = height
    self._max_num_visible_rows = max_num_visible_rows
    
    self.on_assign_from_selected_row = pg.utils.create_empty_func(return_value=(None, None))
    self.on_assign_last_value = self._entry.assign_text
    self.on_row_left_mouse_button_press = self.assign_from_selected_row
    self.on_entry_left_mouse_button_press_func = pg.utils.empty_func
    self.on_entry_key_press_before_show_popup = pg.utils.empty_func
    self.on_entry_key_press = (
      lambda key_name, tree_path, stop_event_propagation: stop_event_propagation)
    self.on_entry_after_assign_by_key_press = pg.utils.empty_func
    self.on_entry_changed_show_popup_condition = pg.utils.create_empty_func(return_value=True)
    
    self.trigger_popup = True
    
    self._filter_rows_func = None
    
    self._last_assigned_entry_text = ''
    self._previous_assigned_entry_text_position = None
    self._previous_assigned_entry_text = None
    
    self._show_popup_first_time = True
    
    self._clear_filter = False

    self._init_gui(column_types, rows)
    
    self._popup_hide_context = popup_hide_context_.PopupHideContext(
      self._popup,
      self._entry,
      hide_callback=self.hide,
      widgets_to_exclude_from_triggering_hiding=[
        self._entry,
        self._popup,
        self._scrolled_window.get_vscrollbar(),
      ],
    )
    self._popup_hide_context.enable()
    
    self._connect_events()
  
  @property
  def rows(self):
    return self._rows
  
  @property
  def rows_filtered(self):
    return self._rows_filtered
  
  @property
  def filter_rows_func(self) -> Callable:
    return self._filter_rows_func
  
  @filter_rows_func.setter
  def filter_rows_func(self, func: Callable):
    self._filter_rows_func = func
    if func is not None:
      self._rows_filtered.set_visible_func(self._filter_rows)
    else:
      self._rows_filtered.set_visible_func(pg.utils.create_empty_func(return_value=True))
  
  @property
  def popup(self) -> Gtk.Window:
    return self._popup
  
  @property
  def tree_view(self) -> Gtk.TreeView:
    return self._tree_view
  
  @property
  def last_assigned_entry_text(self) -> str:
    return self._last_assigned_entry_text
  
  def assign_last_value(self):
    self.on_assign_last_value(self._last_assigned_entry_text)
  
  def show(self):
    if not self.is_shown() and len(self._rows_filtered) > 0:
      self._popup.set_screen(self._entry.get_screen())
      
      self._popup.show()
      
      self._update_position()
      
      if self._show_popup_first_time:
        self.save_last_value()
        self._show_popup_first_time = False
  
  def hide(self):
    if self.is_shown():
      self._popup.hide()
  
  def is_shown(self) -> bool:
    return self._popup.get_mapped()
  
  def resize(self, num_rows: int):
    """Resizes the tree view in the popup.
    
    The height of the tree view is updated according to the number of rows.
    If the number of rows is 0, the entire popup is hidden.
    """
    columns = self._tree_view.get_columns()
    if columns:
      cell_height = max(column.cell_get_size()[3] for column in columns)
    else:
      cell_height = 0
    
    vertical_spacing = self._tree_view.style_get_property('vertical-separator')
    row_height = cell_height + vertical_spacing
    num_visible_rows = min(num_rows, self._max_num_visible_rows)

    self._tree_view.set_size_request(-1, row_height * num_visible_rows)
    
    if num_rows == 0:
      self.hide()
  
  def refresh_row(self, row_path, is_path_filtered: bool = True):
    if not is_path_filtered:
      row_path = self._rows_filtered.convert_child_path_to_path(row_path)
    
    if row_path is not None:
      self._rows_filtered.emit('row-changed', row_path, self._rows_filtered.get_iter(row_path))
  
  def select_row(self, row_num: int):
    self._tree_view.set_cursor(Gtk.TreePath.new_from_indices([row_num]))
  
  def unselect(self):
    # Select an invalid row so that `get_cursor` returns None on the next call.
    self.tree_view.set_cursor(Gtk.TreePath.new_from_indices([len(self._rows_filtered)]))
    self.tree_view.get_selection().unselect_all()
  
  def assign_from_selected_row(self):
    tree_model, tree_iter = self._tree_view.get_selection().get_selected()
    if tree_iter is None:     # No row is selected
      return None, None
    
    return self.on_assign_from_selected_row(tree_model, tree_iter)
  
  def select_and_assign_row(self, row_num: int):
    self.select_row(row_num)
    return self.assign_from_selected_row()
  
  def select_and_assign_row_after_key_press(
        self,
        tree_path,
        next_row: Union[Callable, int],
        next_row_if_no_current_selection: int,
        current_row_before_unselection: Union[Callable, int],
        row_to_scroll_before_unselection: int = 0):
    """Select the row specified by ``tree_path`` after a particular key is
    pressed, and assigns the value from the selected row to the entry.
    
    One can pass functions for ``next_row`` and
    ``current_row_before_unselection`` parameters if ``tree_path`` is
    ``None`` and ``tree_path`` is used to compute these parameters.
    """
    if tree_path is None:
      position, text = self.select_and_assign_row(next_row_if_no_current_selection)
    else:
      if callable(current_row_before_unselection):
        current_row_before_unselection = current_row_before_unselection(tree_path)
      
      if tree_path[0] == current_row_before_unselection:
        self._tree_view.scroll_to_cell((row_to_scroll_before_unselection,))
        self.unselect()
        self.assign_last_value()
        
        position, text = None, None
      else:
        if callable(next_row):
          next_row = next_row(tree_path)
        position, text = self.select_and_assign_row(next_row)
    
    self.on_entry_after_assign_by_key_press(
      self._previous_assigned_entry_text_position,
      self._previous_assigned_entry_text,
      position,
      text)
    
    self._previous_assigned_entry_text_position = position
    self._previous_assigned_entry_text = text
  
  def save_last_value(self):
    self._last_assigned_entry_text = self._entry.get_text()
  
  def _init_gui(self, column_types, rows):
    self._rows = Gtk.ListStore(*column_types)
    
    for row in rows:
      self._rows.append(row)
    
    self._rows_filtered = self._rows.filter_new()
    
    self._tree_view = Gtk.TreeView(
      model=self._rows_filtered,
      hover_selection=True,
      headers_visible=False,
      enable_search=False,
      width_request=self._width,
      height_request=self._height,
    )
    
    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.NEVER,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      shadow_type=Gtk.ShadowType.ETCHED_IN,
      max_content_width=self._width,
      max_content_height=self._height,
      propagate_natural_width=True,
      propagate_natural_height=True,
    )
    self._scrolled_window.add(self._tree_view)
    
    # HACK: Make sure the height of the tree view can be set properly. Source:
    # https://gitlab.gnome.org/GNOME/gtk/-/blob/gtk-3-24/gtk/gtkentrycompletion.c#L573
    self._scrolled_window.get_vscrollbar().set_size_request(-1, 0)
    
    # `Gtk.WindowType.POPUP` prevents the popup from stealing focus from the text entry.
    self._popup = Gtk.Window(
      type=Gtk.WindowType.POPUP,
      type_hint=Gdk.WindowTypeHint.TOOLTIP,
      resizable=False,
    )
    self._popup.add(self._scrolled_window)
    
    self._scrolled_window.show_all()
  
  def _connect_events(self):
    self._entry.connect('changed', self._on_entry_changed)
    self._entry.connect('button-press-event', self._on_entry_left_mouse_button_press)
    self._entry.connect('key-press-event', self._on_entry_key_press_event)
    
    self._entry.connect('focus-out-event', self._on_entry_focus_out_event)
    
    self._tree_view.connect_after('realize', self._on_after_tree_view_realize)
    self._tree_view.connect('button-press-event', self._on_tree_view_button_press_event)
  
  def _update_position(self):
    position = pg.gui.utils.get_position_below_widget(self._entry)
    if position is not None:
      self._popup.move(*position)

  def _filter_rows(self, rows, row_iter, data):
    if self._clear_filter:
      return True
    else:
      return self._filter_rows_func(rows, row_iter, data)
  
  def _on_entry_key_press_event(self, entry, event):
    key_name = Gdk.keyval_name(event.keyval)
    
    if (not self.is_shown()
        and key_name in [
          'Up', 'KP_Up', 'Down', 'KP_Down',
          'Page_Up', 'KP_Page_Up', 'Page_Down', 'KP_Page_Down']):
      self.on_entry_key_press_before_show_popup()
      
      show_popup_first_time = self._show_popup_first_time
      self.show()
      
      # This prevents the navigation keys to select the first row.
      if show_popup_first_time:
        self.unselect()
      
      return True
    
    if self.is_shown():
      tree_path, _unused = self._tree_view.get_cursor()
      stop_event_propagation = True
      
      if key_name in ['Up', 'KP_Up']:
        self.select_and_assign_row_after_key_press(
          tree_path,
          next_row=lambda tree_path: tree_path[0] - 1,
          next_row_if_no_current_selection=len(self._rows_filtered) - 1,
          current_row_before_unselection=0)
      elif key_name in ['Down', 'KP_Down']:
        self.select_and_assign_row_after_key_press(
          tree_path,
          next_row=lambda tree_path: tree_path[0] + 1,
          next_row_if_no_current_selection=0,
          current_row_before_unselection=len(self._rows_filtered) - 1)
      elif key_name in ['Page_Up', 'KP_Page_Up']:
        self.select_and_assign_row_after_key_press(
          tree_path,
          next_row=lambda tree_path: max(tree_path[0] - self._max_num_visible_rows, 0),
          next_row_if_no_current_selection=len(self._rows_filtered) - 1,
          current_row_before_unselection=0)
      elif key_name in ['Page_Down', 'KP_Page_Down']:
        self.select_and_assign_row_after_key_press(
          tree_path,
          next_row=lambda tree_path: min(
            tree_path[0] + self._max_num_visible_rows, len(self._rows_filtered) - 1),
          next_row_if_no_current_selection=0,
          current_row_before_unselection=len(self._rows_filtered) - 1)
      elif key_name in ['Return', 'KP_Enter']:
        self.save_last_value()
        self.hide()
      elif key_name == 'Escape':
        self.assign_last_value()
        self.hide()
      else:
        stop_event_propagation = False
      
      return self.on_entry_key_press(key_name, tree_path, stop_event_propagation)
    else:
      return False
  
  def _on_entry_changed(self, entry):
    if self.trigger_popup:
      self.save_last_value()
      
      self._previous_assigned_entry_text_position = None
      self._previous_assigned_entry_text = None
      
      if not self.on_entry_changed_show_popup_condition():
        self.hide()
        return
      
      show_popup_first_time = self._show_popup_first_time
      if not show_popup_first_time:
        self._rows_filtered.refilter()
        self.resize(num_rows=len(self._rows_filtered))
      
      self.unselect()
      
      self.show()
      
      # If the popup is shown for the first time, filtering after showing the
      # popup makes sure that the correct width is assigned to the tree view.
      if show_popup_first_time:
        self._rows_filtered.refilter()
        self.resize(num_rows=len(self._rows_filtered))
  
  def _on_entry_left_mouse_button_press(self, entry, event):
    if event.button == self._BUTTON_MOUSE_LEFT:
      # If the user clicks on the edge of the entry (where the text cursor is not
      # displayed yet), set the focus on the entry, since the popup will be displayed.
      if not self._entry.has_focus():
        self._entry.grab_focus()
        self._entry.set_position(-1)
      
      self._clear_filter = True
      self._rows_filtered.refilter()
      self._clear_filter = False
      
      show_popup_first_time = self._show_popup_first_time
      if not show_popup_first_time:
        self.resize(num_rows=len(self._rows_filtered))
      
      # No need to resize the tree view after showing the popup for the first
      # time - the 'realize' signal handler automatically resizes the tree view.
      self.show()
      
      self.unselect()
      
      self.on_entry_left_mouse_button_press_func()
  
  def _on_tree_view_button_press_event(self, tree_view, event):
    if event.button == self._BUTTON_MOUSE_LEFT:
      self.on_row_left_mouse_button_press()
      
      self.save_last_value()
      
      self.hide()
  
  def _on_entry_focus_out_event(self, entry, event):
    self.save_last_value()

  def _on_after_tree_view_realize(self, tree_view):
    # Set the correct initial width and height of the tree view.
    self.resize(num_rows=len(self._rows_filtered))
