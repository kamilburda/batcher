"""Preview widget displaying the names of items to be batch-processed."""

from collections.abc import Iterable
from typing import Set

import collections
import traceback

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import GdkPixbuf
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import exceptions
from src import utils as utils_
from src.gui import messages as messages_
from src.gui import preview_base as preview_base_


class NamePreview(preview_base_.Preview):
  """A widget displaying a preview of batch-processed items - names and their
  folder structure.
  
  Additional features:
  * toggling "filter mode" - unselected items are not sensitive.
  
  Signals:
  
  * ``'preview-selection-changed'`` - The selection in the preview was modified
    by the user or by calling `set_selected_items()`.
  * ``'preview-updated'`` - The preview was updated by calling `update()`. This
    signal is not emitted if the update is locked.
    
    Arguments:
    
    * error: If ``None``, the preview was updated successfully. Otherwise,
      this is an `Exception` instance describing the error that occurred during
      the update.
  """
  
  __gsignals__ = {
    'preview-selection-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'preview-updated': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
  }
  
  _COLUMNS = (
    _COLUMN_ICON_ITEM,
    _COLUMN_ICON_ITEM_VISIBLE,
    _COLUMN_ICON_COLOR_TAG,
    _COLUMN_ICON_COLOR_TAG_VISIBLE,
    _COLUMN_ITEM_NAME_SENSITIVE,
    _COLUMN_ITEM_NAME,
    _COLUMN_ITEM_ID,
    _COLUMN_ITEM_TYPE) = (
    [0, GdkPixbuf.Pixbuf],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_BOOLEAN],
    [4, GObject.TYPE_BOOLEAN],
    [5, GObject.TYPE_STRING],
    [6, GObject.TYPE_INT],
    [7, GObject.TYPE_INT])
  
  def __init__(
        self,
        batcher,
        settings,
        initial_item_tree=None,
        collapsed_items=None,
        selected_items=None,
        selected_items_filter_name='selected_in_preview'):
    super().__init__()
    
    self._batcher = batcher
    self._settings = settings
    self._initial_item_tree = initial_item_tree
    self._collapsed_items = collapsed_items if collapsed_items is not None else set()
    self._selected_items = selected_items if selected_items is not None else []
    self._selected_items_filter_name = selected_items_filter_name
    
    self.is_filtering = False
    """If ``True``, unselected items are not sensitive."""
    
    # key: ID of `Item.raw` or (ID of `Item.raw`, 'folder') instance
    # value: `Gtk.TreeIter` instance
    self._tree_iters = collections.defaultdict(pg.utils.return_none_func)
    
    self._row_expand_collapse_interactive = True
    self._clearing_preview = False
    self._row_select_interactive = True
    self._initial_scroll_to_selection = True
    
    self._init_gui()
  
  @property
  def batcher(self):
    return self._batcher
  
  @property
  def tree_view(self):
    return self._tree_view
  
  @property
  def collapsed_items(self):
    return self._collapsed_items
  
  @property
  def selected_items(self):
    return self._selected_items
  
  def update(self, reset_items: bool = False, update_existing_contents_only: bool = False):
    """Updates the preview (add/remove item, move item to a different parent
    item group, etc.).
    
    If ``reset_items`` is ``True``, full update is perform - new items are
    added, non-existent items are removed, etc. Note that setting this to
    ``True`` may introduce a performance penalty for hundreds of items.
    
    If ``update_existing_contents_only`` is ``True``, only the contents of
    the existing items are updated. Note that the items will not be
    reparented, expanded/collapsed or added/removed even if they need to be.
    This option is useful if you know the item structure will be preserved.
    
    If an exception was captured during the update, the method is terminated
    prematurely. It is the responsibility of the caller to handle the error
    (e.g. lock or clear the preview).
    """
    update_locked = super().update()
    if update_locked:
      return
    
    if not update_existing_contents_only:
      self.clear()
    
    error = self._process_items(reset_items=reset_items)
    
    if error:
      self.emit('preview-updated', error)
      return
    
    items = self._get_items_to_process()
    
    if not update_existing_contents_only:
      self._insert_items(items)
      self._set_expanded_items()
    else:
      self._update_items(items)
    
    self._set_selection()
    self._set_item_tree_sensitive_for_selected(items)
    
    self._tree_view.columns_autosize()
    
    self.emit('preview-updated', None)
  
  def clear(self):
    """Clears the entire preview."""
    self._clearing_preview = True
    self._tree_model.clear()
    self._tree_iters.clear()
    self._clearing_preview = False

  def set_sensitive(self, sensitive):
    # Functions created via GObject introspection are not hashable, causing
    # functions in `pg.invocation` to fail. We therefore wrap this function to
    # avoid the error.
    super().set_sensitive(sensitive)

  def set_collapsed_items(self, collapsed_items: Set):
    """Sets the collapsed state of items in the preview."""
    self._collapsed_items = collapsed_items
    self._set_expanded_items()
  
  def set_selected_items(self, selected_items: Iterable):
    """Sets the selection of items in the preview."""
    self._selected_items = list(selected_items)
    self._set_selection()
    self.emit('preview-selection-changed')
  
  def get_items_from_selected_rows(self):
    return [self._batcher.item_tree[item_key]
            for item_key in self._get_keys_from_current_selection()]
  
  def get_item_from_cursor(self):
    tree_path, _unused = self._tree_view.get_cursor()
    if tree_path is not None:
      item_key = self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path))
      return self._batcher.item_tree[item_key]
    else:
      return None
  
  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.VERTICAL)

    self._tree_model = Gtk.TreeStore(*[column[1] for column in self._COLUMNS])
    
    self._tree_view = Gtk.TreeView(
      model=self._tree_model,
      headers_visible=False,
      enable_search=False,
      enable_tree_lines=True,
    )
    self._tree_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    
    self._init_icons()
    
    column = Gtk.TreeViewColumn()
    
    cell_renderer_icon_item = Gtk.CellRendererPixbuf()
    column.pack_start(cell_renderer_icon_item, False)
    column.set_attributes(
      cell_renderer_icon_item,
      pixbuf=self._COLUMN_ICON_ITEM[0],
      visible=self._COLUMN_ICON_ITEM_VISIBLE[0],
    )

    cell_renderer_icon_color_tag = Gtk.CellRendererPixbuf()
    column.pack_start(cell_renderer_icon_color_tag, False)
    column.set_attributes(
      cell_renderer_icon_color_tag,
      pixbuf=self._COLUMN_ICON_COLOR_TAG[0],
      visible=self._COLUMN_ICON_COLOR_TAG_VISIBLE[0],
    )
    
    cell_renderer_item_name = Gtk.CellRendererText()
    column.pack_start(cell_renderer_item_name, False)
    column.set_attributes(
      cell_renderer_item_name,
      text=self._COLUMN_ITEM_NAME[0],
      sensitive=self._COLUMN_ITEM_NAME_SENSITIVE[0])
    
    self._tree_view.append_column(column)
    
    self._scrolled_window = Gtk.ScrolledWindow(
      hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
      vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    )
    self._scrolled_window.add(self._tree_view)
    
    self.pack_start(self._scrolled_window, True, True, 0)
    
    self._tree_view.connect('row-collapsed', self._on_tree_view_row_collapsed)
    self._tree_view.connect('row-expanded', self._on_tree_view_row_expanded)
    self._tree_view.get_selection().connect('changed', self._on_tree_selection_changed)
  
  def _init_icons(self):
    self._icons = {
      'folder': self._tree_view.render_icon_pixbuf(Gtk.STOCK_DIRECTORY, Gtk.IconSize.MENU),
    }
  
  def _on_tree_view_row_collapsed(self, tree_view, tree_iter, tree_path):
    if self._row_expand_collapse_interactive:
      self._collapsed_items.add(self._get_key_from_tree_iter(tree_iter))
      self._tree_view.columns_autosize()
  
  def _on_tree_view_row_expanded(self, tree_view, tree_iter, tree_path):
    if self._row_expand_collapse_interactive:
      item_key = self._get_key_from_tree_iter(tree_iter)
      if item_key in self._collapsed_items:
        self._collapsed_items.remove(item_key)
      
      self._set_expanded_items(tree_path)
      
      self._tree_view.columns_autosize()
  
  def _on_tree_selection_changed(self, tree_selection):
    if not self._clearing_preview and self._row_select_interactive:
      previous_selected_items = self._selected_items
      self._selected_items = self._get_keys_from_current_selection()
      
      self.emit('preview-selection-changed')
      
      if self.is_filtering and self._selected_items != previous_selected_items:
        self.update()
  
  def _get_keys_from_current_selection(self):
    _unused, tree_paths = self._tree_view.get_selection().get_selected_rows()
    return [
      self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path))
      for tree_path in tree_paths]
  
  @staticmethod
  def _get_key(item):
    if item.type != pg.itemtree.TYPE_FOLDER:
      return item.raw.get_id()
    else:
      return item.raw.get_id(), pg.itemtree.FOLDER_KEY
  
  def _get_key_from_tree_iter(self, tree_iter):
    item_id = self._tree_model.get_value(tree_iter, column=self._COLUMN_ITEM_ID[0])
    item_type = self._tree_model.get_value(tree_iter, column=self._COLUMN_ITEM_TYPE[0])
    
    if item_type != pg.itemtree.TYPE_FOLDER:
      return item_id
    else:
      return item_id, pg.itemtree.FOLDER_KEY
  
  def _get_items_to_process(self):
    if self.is_filtering:
      with self._batcher.item_tree.filter.remove_temp(name=self._selected_items_filter_name):
        return list(self._batcher.item_tree)
    else:
      return list(self._batcher.item_tree)
  
  def _process_items(self, reset_items=False):
    if not reset_items:
      if self._initial_item_tree is not None:
        item_tree = self._initial_item_tree
        self._initial_item_tree = None
      else:
        item_tree = self._batcher.item_tree
    else:
      item_tree = None
    
    if item_tree is not None:
      # We need to reset item attributes explicitly before processing since
      # existing item trees are not automatically refreshed.
      for item in item_tree.iter_all():
        item.reset()
    
    error = None
    
    try:
      self._batcher.run(
        item_tree=item_tree,
        is_preview=True,
        process_contents=False,
        process_names=True,
        process_export=False,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError as e:
      pass
    except exceptions.ActionError as e:
      messages_.display_failure_message(
        messages_.get_failing_action_message(e),
        failure_message=str(e),
        details=traceback.format_exc(),
        parent=pg.gui.get_toplevel_window(self))
      
      error = e
    except Exception as e:
      messages_.display_failure_message(
        _('There was a problem with updating the name preview:'),
        failure_message=str(e),
        details=traceback.format_exc(),
        parent=pg.gui.get_toplevel_window(self))
      
      error = e
    
    return error
  
  def _update_items(self, items):
    updated_parents = set()
    for item in items:
      self._update_parent_items(item, updated_parents)
      self._update_item(item)
  
  def _insert_items(self, items):
    inserted_parents = set()
    for item in items:
      self._insert_parent_items(item, inserted_parents)
      self._insert_item(item)
  
  def _insert_item(self, item):
    if item.parent:
      parent_tree_iter = self._tree_iters[self._get_key(item.parent)]
    else:
      parent_tree_iter = None

    item_icon = self._get_icon_from_item(item)
    color_tag_icon = self._get_color_tag_icon(item)
    
    tree_iter = self._tree_model.append(
      parent_tree_iter,
      [item_icon,
       item_icon is not None,
       color_tag_icon,
       color_tag_icon is not None,
       True,
       item.name,
       item.raw.get_id(),
       item.type])
    
    self._tree_iters[self._get_key(item)] = tree_iter
    
    return tree_iter
  
  def _update_item(self, item):
    self._tree_model.set(
      self._tree_iters[self._get_key(item)],
      self._COLUMN_ITEM_NAME_SENSITIVE[0],
      True,
      self._COLUMN_ITEM_NAME[0],
      item.name)
  
  def _insert_parent_items(self, item, inserted_parents):
    for parent in item.parents:
      if parent not in inserted_parents:
        self._insert_item(parent)
        inserted_parents.add(parent)
  
  def _update_parent_items(self, item, updated_parents):
    for parent in item.parents:
      if parent not in updated_parents:
        self._update_item(parent)
        updated_parents.add(parent)
  
  def _set_item_tree_sensitive_for_selected(self, items):
    if self.is_filtering:
      self._set_items_sensitive(items, False)
      self._set_items_sensitive(
        [self._batcher.item_tree[item_key] for item_key in self._selected_items], True)
  
  def _get_item_sensitive(self, item):
    return self._tree_model.get_value(
      self._tree_iters[self._get_key(item)], self._COLUMN_ITEM_NAME_SENSITIVE[0])
  
  def _set_items_sensitive(self, items, sensitive):
    processed_parents = set()
    for item in items:
      self._set_item_sensitive(item, sensitive)
      self._set_parent_items_sensitive(item, processed_parents)
  
  def _set_item_sensitive(self, item, sensitive):
    if self._get_key(item) in self._tree_iters:
      self._tree_model.set_value(
        self._tree_iters[self._get_key(item)],
        self._COLUMN_ITEM_NAME_SENSITIVE[0],
        sensitive)
  
  def _set_parent_items_sensitive(self, item, processed_parents):
    for parent in reversed(list(item.parents)):
      if parent not in processed_parents:
        parent_sensitive = any(
          self._get_item_sensitive(child) for child in parent.children
          if self._get_key(child) in self._tree_iters)
        self._set_item_sensitive(parent, parent_sensitive)
        
        processed_parents.add(parent)
  
  def _get_icon_from_item(self, item):
    if item.type == pg.itemtree.TYPE_FOLDER:
      return self._icons['folder']
    else:
      return None

  @staticmethod
  def _get_color_tag_icon(item):
    color_tag = item.raw.get_color_tag()

    if color_tag in _COLOR_TAGS_AND_PREMADE_PIXBUFS:
      return _COLOR_TAGS_AND_PREMADE_PIXBUFS[color_tag]
    else:
      return None

  def _set_expanded_items(self, tree_path=None):
    """Sets the expanded state of items in the tree view.
    
    If ``tree_path`` is specified, set the states only for the child elements in
    the tree path, otherwise set the states in the whole tree view.
    """
    self._row_expand_collapse_interactive = False
    
    if tree_path is None:
      self._tree_view.expand_all()
    else:
      self._tree_view.expand_row(tree_path, True)
    
    self._remove_no_longer_valid_collapsed_items()
    
    for item_key in self._collapsed_items:
      if item_key in self._tree_iters:
        item_tree_iter = self._tree_iters[item_key]
        if item_tree_iter is None:
          continue
        
        item_tree_path = self._tree_model.get_path(item_tree_iter)
        if tree_path is None or self._tree_view.row_expanded(item_tree_path):
          self._tree_view.collapse_row(item_tree_path)
    
    self._row_expand_collapse_interactive = True
  
  def _remove_no_longer_valid_collapsed_items(self):
    if self._batcher.item_tree is None:
      return
    
    self._collapsed_items = set(
      [item_key for item_key in self._collapsed_items if item_key in self._batcher.item_tree])
  
  def _set_selection(self):
    self._row_select_interactive = False
    
    self._selected_items = [
      item_key for item_key in self._selected_items if item_key in self._tree_iters]
    
    for item_key in self._selected_items:
      tree_iter = self._tree_iters[item_key]
      if tree_iter is not None:
        self._tree_view.get_selection().select_iter(tree_iter)
    
    if self._initial_scroll_to_selection and self._selected_items:
      self._set_initial_scroll_to_selection()
      self._initial_scroll_to_selection = False
    
    self._row_select_interactive = True
  
  def _set_initial_scroll_to_selection(self):
    if self._selected_items:
      tree_iter = self._tree_iters[self._selected_items[0]]
      if tree_iter is not None:
        first_selected_item_path = (
          self._tree_model.get_path(self._tree_iters[self._selected_items[0]]))
        if first_selected_item_path is not None:
          self._tree_view.scroll_to_cell(first_selected_item_path, None, True, 0.5, 0.0)


def _get_color_tag_pixbuf(color_tag):
  border_color = 0xd0d0d0ff
  default_color = 0x7f7f7fff

  border_color_padding = 2
  tag_color_padding = 3

  if color_tag != Gimp.ColorTag.NONE and color_tag in Gimp.ColorTag.__enum_values__:
    icon_size = Gtk.icon_size_lookup(Gtk.IconSize.MENU)

    color_tag_pixbuf = GdkPixbuf.Pixbuf.new(
      GdkPixbuf.Colorspace.RGB, True, 8, icon_size.width, icon_size.height)

    color_tag_border_subpixbuf = color_tag_pixbuf.new_subpixbuf(
      border_color_padding + 1,
      border_color_padding + 1,
      icon_size.width - border_color_padding * 2,
      icon_size.height - border_color_padding * 2)

    color_tag_border_subpixbuf.fill(border_color)

    color_tag_color_subpixbuf = color_tag_pixbuf.new_subpixbuf(
      tag_color_padding + 1,
      tag_color_padding + 1,
      icon_size.width - tag_color_padding * 2,
      icon_size.height - tag_color_padding * 2)

    color_tag_color_subpixbuf.fill(_COLOR_TAGS_AND_COLORS.get(color_tag, default_color))

    return color_tag_pixbuf
  else:
    return None


# Colors taken from:
#  https://gitlab.gnome.org/GNOME/gimp/-/blob/master/app/widgets/gimpwidgets-utils.c
_COLOR_TAGS_AND_COLORS = {
  Gimp.ColorTag.BLUE: 0x54669fff,
  Gimp.ColorTag.GREEN: 0x6f8f30ff,
  Gimp.ColorTag.YELLOW: 0xd2b62dff,
  Gimp.ColorTag.ORANGE: 0xd97a26ff,
  Gimp.ColorTag.BROWN: 0x573519ff,
  Gimp.ColorTag.RED: 0xaa2a2fff,
  Gimp.ColorTag.VIOLET: 0x6342aeff,
  Gimp.ColorTag.GRAY: 0x575757ff,
}

_COLOR_TAGS_AND_PREMADE_PIXBUFS = {
  color_tag: _get_color_tag_pixbuf(color_tag) for color_tag in _COLOR_TAGS_AND_COLORS}


GObject.type_register(NamePreview)
