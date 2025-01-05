"""Preview widget displaying the names of items to be batch-processed."""

from collections.abc import Iterable
from typing import Set

import collections
import traceback

import gi
from gi.repository import GdkPixbuf
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from . import base as preview_base_

from src import exceptions
from src import export as export_
from src import utils as utils_
from src.gui import messages as messages_


class NamePreview(preview_base_.Preview):
  """A widget displaying a preview of batch-processed items - names and their
  folder structure.
  
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
    'preview-updated': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'preview-selection-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'preview-collapsed-items-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'preview-added-items': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'preview-removed-items': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
  }
  
  _COLUMNS = (
    _COLUMN_ICON_ITEM,
    _COLUMN_ICON_ITEM_VISIBLE,
    _COLUMN_ICON_COLOR_TAG,
    _COLUMN_ICON_COLOR_TAG_VISIBLE,
    _COLUMN_ITEM_NAME,
    _COLUMN_ITEM_KEY) = (
    [0, GdkPixbuf.Pixbuf],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_BOOLEAN],
    [4, GObject.TYPE_STRING],
    [5, GObject.TYPE_PYOBJECT])

  _ICON_XPAD = 2
  _COLOR_TAG_BORDER_WIDTH = 1
  _COLOR_TAG_BORDER_COLOR = 0xdcdcdcff
  _COLOR_TAG_DEFAULT_COLOR = 0x7f7f7fff
  
  def __init__(
        self,
        batcher,
        settings,
        collapsed_items=None,
        selected_items=None,
        initial_cursor_item=None,
  ):
    super().__init__()
    
    self._batcher = batcher
    self._settings = settings
    self._collapsed_items = collapsed_items if collapsed_items is not None else set()
    self._selected_items = selected_items if selected_items is not None else []
    self._initial_cursor_item = initial_cursor_item

    self._tagged_items = set()
    
    # key: `Item.key`
    # value: `Gtk.TreeIter` instance
    self._tree_iters = collections.defaultdict(pg.utils.return_none_func)
    
    self._row_expand_collapse_interactive = True
    self._clearing_preview = False
    self._row_select_interactive = True
    
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
  
  def update(self, full_update=False):
    """Updates the preview (add/remove item, move item to a different parent
    group, etc.).

    If an exception was captured during the update, the method is terminated
    prematurely. It is the responsibility of the caller to handle the error
    (e.g. lock or clear the preview).

    If ``full_update`` is ``True``, the item tree is refreshed based on changes
    outside of this application (addition, removal, update of items).
    """
    update_locked = super().update()
    if update_locked:
      return

    existing_items_parents_and_previous = self._get_items()

    error = self._process_items(full_update)

    if error:
      self.emit('preview-updated', error)
      return

    self._sync_new_items_with_tree_view(existing_items_parents_and_previous)

    self._set_expanded_items()

    self._set_selection()

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

  def set_collapsed_items(self, collapsed_items: Iterable):
    """Sets the collapsed state of items in the preview."""
    self._collapsed_items = set(collapsed_items)
    self._set_expanded_items()
    self.emit('preview-collapsed-items-changed')

  def set_selected_items(self, selected_items: Iterable):
    """Sets the selection of items in the preview."""
    self._selected_items = list(selected_items)
    self._set_selection()
    self.emit('preview-selection-changed')

  def set_tagged_items(self, tagged_items: Set):
    """Assigns color tags to the specified items in the preview.

    Existing items not present in ``tagged_items`` will have their color tags
    removed if they have one.
    """
    for item_key in self._tagged_items:
      if item_key in self._tree_iters:
        self._remove_color_tag(item_key)

    self._tagged_items = tagged_items

    for item_key in self._tagged_items:
      if item_key in self._tree_iters:
        self._set_color_tag(item_key)

  def get_items_from_selected_rows(self):
    return [self._batcher.item_tree[item_key]
            for item_key in self._get_keys_from_current_selection()
            if item_key in self._batcher.item_tree]
  
  def get_item_from_cursor(self):
    tree_path, _unused = self._tree_view.get_cursor()
    if tree_path is not None:
      item_key = self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path))
      if item_key in self._batcher.item_tree:
        return self._batcher.item_tree[item_key]
      else:
        return None
    else:
      return None

  def add_items(self, objects):
    added_items = self._batcher.item_tree.add(objects)

    self.emit('preview-added-items', added_items)

  def remove_selected_items(self):
    removed_items = self._batcher.item_tree.remove(
      [self._batcher.item_tree[item_key] for item_key in self._selected_items])

    self.emit('preview-removed-items', removed_items)

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
    
    cell_renderer_icon_item = Gtk.CellRendererPixbuf(
      xpad=self._ICON_XPAD,
    )
    column.pack_start(cell_renderer_icon_item, False)
    column.set_attributes(
      cell_renderer_icon_item,
      pixbuf=self._COLUMN_ICON_ITEM[0],
      visible=self._COLUMN_ICON_ITEM_VISIBLE[0],
    )

    cell_renderer_icon_color_tag = Gtk.CellRendererPixbuf(
      xpad=self._ICON_XPAD,
    )
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
      text=self._COLUMN_ITEM_NAME[0])
    
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
    self._folder_icon = pg.gui.utils.get_icon_pixbuf('folder', self._tree_view, Gtk.IconSize.MENU)

    # Colors taken from:
    #  https://gitlab.gnome.org/GNOME/gimp/-/blob/master/app/widgets/gimpwidgets-utils.c
    self._color_tags_and_icons = {
      Gimp.ColorTag.BLUE: 0x54669fff,
      Gimp.ColorTag.GREEN: 0x6f8f30ff,
      Gimp.ColorTag.YELLOW: 0xd2b62dff,
      Gimp.ColorTag.ORANGE: 0xd97a26ff,
      Gimp.ColorTag.BROWN: 0x573519ff,
      Gimp.ColorTag.RED: 0xaa2a2fff,
      Gimp.ColorTag.VIOLET: 0x6342aeff,
      Gimp.ColorTag.GRAY: 0x575757ff,
    }

    self._color_tags_and_premade_pixbufs = {
      color_tag: self._get_color_tag_pixbuf(color_tag) for color_tag in
      self._color_tags_and_icons}

  def _get_color_tag_pixbuf(self, color_tag):
    if color_tag != Gimp.ColorTag.NONE and color_tag in Gimp.ColorTag.__enum_values__:
      icon_size = Gtk.icon_size_lookup(Gtk.IconSize.MENU)

      color_tag_pixbuf = GdkPixbuf.Pixbuf.new(
        GdkPixbuf.Colorspace.RGB, True, 8, icon_size.width, icon_size.height)
      color_tag_pixbuf.fill(self._COLOR_TAG_BORDER_COLOR)

      color_tag_color_subpixbuf = color_tag_pixbuf.new_subpixbuf(
        self._COLOR_TAG_BORDER_WIDTH,
        self._COLOR_TAG_BORDER_WIDTH,
        icon_size.width - self._COLOR_TAG_BORDER_WIDTH * 2,
        icon_size.height - self._COLOR_TAG_BORDER_WIDTH * 2)
      color_tag_color_subpixbuf.fill(
        self._color_tags_and_icons.get(color_tag, self._COLOR_TAG_DEFAULT_COLOR))

      return color_tag_pixbuf
    else:
      return None

  def _on_tree_view_row_collapsed(self, _tree_view, _tree_iter, tree_path):
    if self._row_expand_collapse_interactive:
      self._collapsed_items.add(self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path)))
      self._tree_view.columns_autosize()

      self.emit('preview-collapsed-items-changed')
  
  def _on_tree_view_row_expanded(self, _tree_view, tree_iter, tree_path):
    if self._row_expand_collapse_interactive:
      item_key = self._get_key_from_tree_iter(tree_iter)
      self._collapsed_items.discard(item_key)

      self._set_expanded_items(tree_path)

      self._tree_view.columns_autosize()

      self.emit('preview-collapsed-items-changed')
  
  def _on_tree_selection_changed(self, _tree_selection):
    if not self._clearing_preview and self._row_select_interactive:
      previous_selected_items = self._selected_items
      self._selected_items = self._get_keys_from_current_selection()

      # According to the docs for `Gtk.TreeSelection`, the 'changed' signal can
      # be emitted even if the selection did not change. We thus check whether
      # the selection really changed.
      if previous_selected_items != self._selected_items:
        self.emit('preview-selection-changed')

  def _get_keys_from_current_selection(self):
    _unused, tree_paths = self._tree_view.get_selection().get_selected_rows()
    return [
      self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path))
      for tree_path in tree_paths]
  
  def _get_key_from_tree_iter(self, tree_iter):
    return self._tree_model.get_value(tree_iter, column=self._COLUMN_ITEM_KEY[0])
  
  def _process_items(self, full_update=False):
    # We need to reset item attributes explicitly before processing as some
    # items will not be refreshed (removed and re-added) by the tree.
    # The performance hit of doing this is negligible.
    for item in self._batcher.item_tree.iter_all():
      item.reset()
      item.delete_named_state(export_.EXPORT_NAME_ITEM_STATE)

    error = None

    try:
      self._batcher.run(
        refresh_item_tree=full_update,
        is_preview=True,
        process_contents=False,
        process_names=True,
        process_export=False,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.ActionError as e:
      messages_.display_failure_message(
        messages_.get_failing_action_message(e),
        failure_message=str(e),
        details=e.traceback,
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

  def _get_items(self):
    items = {}
    previous_items = {}
    parents = {}

    previous_item_per_parent = collections.defaultdict(lambda: None)
    visited_parents = set()

    if self._batcher.matching_items is not None:
      item_tree_items = self._batcher.matching_items
    else:
      item_tree_items = self._batcher.item_tree

    for item in item_tree_items:
      # We also explicitly insert parents as they would be omitted due to not
      # matching constraints.
      for parent_item in item.parents:
        if parent_item not in visited_parents:
          items[parent_item.key] = parent_item
          previous_items[parent_item.key] = previous_item_per_parent[parent_item.parent]
          parents[parent_item.key] = parent_item.parent

          previous_item_per_parent[parent_item.parent] = parent_item
          visited_parents.add(parent_item)

      items[item.key] = item
      previous_items[item.key] = previous_item_per_parent[item.parent]
      parents[item.key] = item.parent

      previous_item_per_parent[item.parent] = item

    return items, previous_items, parents

  def _sync_new_items_with_tree_view(self, existing_items_parents_and_previous):
    existing_items, previous_existing_items, existing_parents = existing_items_parents_and_previous
    new_items, previous_new_items, new_parents = self._get_items()

    parents_to_remove = {}

    for new_item_key, new_item in new_items.items():
      previous_new_item = previous_new_items[new_item_key]

      if new_item_key in existing_items and new_item_key in self._tree_iters:
        previous_existing_item = previous_existing_items[new_item_key]
        existing_parent = existing_parents[new_item_key]
        new_parent = new_parents[new_item_key]

        parents_are_equal = (
          (new_parent is None and existing_parent is None)
          or (
            new_parent is not None
            and existing_parent is not None
            and new_parent.key not in parents_to_remove
            and new_parent.key == existing_parent.key))

        if not parents_are_equal:
          # We cannot use `Gtk.TreeStore.move_after()` here as that method only
          # works within the same parent. Hence, we remove and insert the
          # item under a new parent.

          if new_item.type != pg.itemtree.TYPE_FOLDER:
            self._remove_item_by_key(new_item_key)
          else:
            # We cannot remove a parent from the `Gtk.TreeStore` at this
            # point as all child `Gtk.TreeIter`s would be removed as well. We
            # remove all obsoleted parents at tne end.
            parent_iter = self._tree_iters.pop(new_item_key, None)
            if parent_iter is not None:
              parents_to_remove[new_item_key] = parent_iter

          self._insert_item(new_item, previous_new_item)
        else:
          previous_items_are_equal = (
            (previous_new_item is None and previous_existing_item is None)
            or (
              previous_new_item is not None
              and previous_existing_item is not None
              and previous_new_item.key == previous_existing_item.key))

          if not previous_items_are_equal:
            self._move_item(new_item, previous_new_item)
            self._update_item(new_item)
          else:
            self._update_item(new_item)

        del existing_items[new_item_key]
      else:
        self._insert_item(new_item, previous_new_item)

        if new_item_key in existing_items:
          del existing_items[new_item_key]

    # We need to delete children first to avoid crashes (accessing child
    # `Gtk.TreeIter`s that no longer exist), hence the reversed iteration.
    for no_longer_existing_item_key in reversed(existing_items):
      self._remove_item_by_key(no_longer_existing_item_key)

    for tree_iter in reversed(parents_to_remove.values()):
      self._remove_item_by_iter(tree_iter)
  
  def _insert_item(self, item, previous_item):
    if item.key in self._tree_iters:
      return None

    if item.parent:
      parent_tree_iter = self._tree_iters[item.parent.key]
    else:
      parent_tree_iter = None

    if previous_item:
      previous_tree_iter = self._tree_iters[previous_item.key]
    else:
      previous_tree_iter = None

    item_icon = self._get_icon_from_item(item)
    color_tag_icon = self._get_color_tag_icon(item) if item.key in self._tagged_items else None

    tree_iter = self._tree_model.insert_after(
      parent_tree_iter,
      previous_tree_iter,
      [item_icon,
       item_icon is not None,
       color_tag_icon,
       color_tag_icon is not None,
       self._get_item_name(item),
       item.key])

    self._expand_folder_item(tree_iter, item)

    self._tree_iters[item.key] = tree_iter

    return tree_iter

  def _expand_folder_item(self, tree_iter, item):
    if tree_iter is not None and item.type == pg.itemtree.TYPE_FOLDER:
      self._row_expand_collapse_interactive = False
      self._tree_view.expand_row(self._tree_model[tree_iter].path, True)
      self._row_expand_collapse_interactive = True

  def _set_color_tag(self, item_key):
    if item_key not in self._batcher.item_tree:
      return

    item = self._batcher.item_tree[item_key]

    color_tag_icon = self._get_color_tag_icon(item)

    self._tree_model.set(
      self._tree_iters[item_key],
      [
        self._COLUMN_ICON_COLOR_TAG[0],
        self._COLUMN_ICON_COLOR_TAG_VISIBLE[0],
      ],
      [
        color_tag_icon,
        color_tag_icon is not None,
      ])

  def _remove_color_tag(self, item_key):
    self._tree_model.set(
      self._tree_iters[item_key],
      [
        self._COLUMN_ICON_COLOR_TAG[0],
        self._COLUMN_ICON_COLOR_TAG_VISIBLE[0],
      ],
      [
        None,
        False,
      ])

  def _get_icon_from_item(self, item):
    if item.type == pg.itemtree.TYPE_FOLDER:
      return self._folder_icon
    else:
      return None

  def _get_color_tag_icon(self, item):
    if item.raw is None:
      return None

    color_tag = item.raw.get_color_tag()

    if color_tag in self._color_tags_and_premade_pixbufs:
      return self._color_tags_and_premade_pixbufs[color_tag]
    else:
      return None

  def _get_item_name(self, item):
    if not self._batcher.edit_mode:
      item_state = item.get_named_state(export_.EXPORT_NAME_ITEM_STATE)
      return item_state['name'] if item_state is not None else item.name
    else:
      return item.name

  def _update_item(self, item):
    self._tree_model.set_value(
      self._tree_iters[item.key],
      self._COLUMN_ITEM_NAME[0],
      self._get_item_name(item))

  def _move_item(self, item, previous_item):
    item_tree_iter = self._tree_iters[item.key]
    if previous_item is not None:
      previous_item_tree_iter = self._tree_iters[previous_item.key]
    else:
      previous_item_tree_iter = None

    self._tree_model.move_after(item_tree_iter, previous_item_tree_iter)

  def _remove_item_by_key(self, item_key):
    tree_iter = self._tree_iters.pop(item_key, None)
    if tree_iter is not None:
      self._tree_model.remove(tree_iter)

  def _remove_item_by_iter(self, tree_iter):
    self._tree_model.remove(tree_iter)

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
    self._collapsed_items = set(
      item_key for item_key in self._collapsed_items if item_key in self._batcher.item_tree)
  
  def _set_selection(self):
    self._row_select_interactive = False

    self._selected_items = [
      item_key for item_key in self._selected_items if item_key in self._tree_iters]

    for item_key in self._selected_items:
      tree_iter = self._tree_iters[item_key]
      if tree_iter is not None:
        self._tree_view.get_selection().select_iter(tree_iter)

    if self._selected_items:
      if self._initial_cursor_item is None:
        first_selected_tree_iter = self._tree_iters.get(self._selected_items[0], None)
        if first_selected_tree_iter is not None:
          first_selected_tree_path = self._tree_model.get_path(first_selected_tree_iter)
          if first_selected_tree_path is not None:
            tree_path_with_cursor = self._set_cursor_to_item_if_not_set(first_selected_tree_path)
            self._scroll_to_cursor(tree_path_with_cursor)
      else:
        tree_iter = self._tree_iters.get(self._initial_cursor_item, None)
        if tree_iter is not None:
          tree_path = self._tree_model.get_path(tree_iter)
          if tree_path is not None:
            tree_path_with_cursor = self._set_cursor_to_item_if_not_set(tree_path)
            self._scroll_to_cursor(tree_path_with_cursor)
        self._initial_cursor_item = None

    self._row_select_interactive = True

  def _set_cursor_to_item_if_not_set(self, tree_path):
    tree_path_with_cursor, _unused = self._tree_view.get_cursor()

    if tree_path_with_cursor is None:
      self._tree_view.set_cursor(tree_path, None, False)
      tree_path_with_cursor = tree_path

    return tree_path_with_cursor

  def _scroll_to_cursor(self, tree_path):
    if tree_path is not None:
      self._tree_view.scroll_to_cell(tree_path, None, True, 0.5, 0.0)


GObject.type_register(NamePreview)
