"""Preview widget displaying the names of items to be batch-processed."""

from collections.abc import Iterable
from typing import List, Optional, Set

import bisect
import collections
import traceback

import gi
from gi.repository import GdkPixbuf
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import base as preview_base_

from src import builtin_actions
from src import exceptions
from src import itemtree
from src import utils
from src import utils_setting as utils_setting_
from src.gui import messages as messages_
from src.gui import utils as gui_utils_


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
    'preview-reordered-item': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    'preview-sorted-items': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'preview-removed-items': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
  }
  
  _COLUMNS = (
    _COLUMN_ICON_ITEM,
    _COLUMN_ICON_ITEM_VISIBLE,
    _COLUMN_ICON_COLOR_TAG,
    _COLUMN_ICON_COLOR_TAG_VISIBLE,
    _COLUMN_ITEM_NAME,
    _COLUMN_ITEM_KEY,
  ) = (
    [0, GdkPixbuf.Pixbuf],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_BOOLEAN],
    [4, GObject.TYPE_STRING],
    [5, GObject.TYPE_PYOBJECT],
  )

  _ICON_XPAD = 2
  _COLOR_TAG_BORDER_WIDTH = 1
  _COLOR_TAG_BORDER_COLOR = 0xdcdcdcff
  _COLOR_TAG_DEFAULT_COLOR = 0x7f7f7fff

  def __init__(
        self,
        batcher,
        settings,
        item_type,
        collapsed_items=None,
        selected_items=None,
        initial_cursor_item=None,
        show_original_name=False,
  ):
    super().__init__()
    
    self._batcher = batcher
    self._settings = settings
    self._item_type = item_type
    self._collapsed_items = collapsed_items if collapsed_items is not None else set()
    self._selected_items = selected_items if selected_items is not None else []
    self._initial_cursor_item = initial_cursor_item
    self._show_original_name = show_original_name

    self._tagged_items = set()
    
    # key: `Item.key`
    # value: `Gtk.TreeIter` instance
    self._tree_iters = collections.defaultdict(utils.return_none_func)
    # key: tuple of `Item.key` representing parents of an item
    # value: dict of (`Item.key`, None) pairs having the same parents (the key)
    self._cached_parent_and_item_keys = {}

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
  
  def update(self, full_update=False, scroll_to_first_selected_item=True):
    """Updates the preview (add/remove item, move item to a different parent
    group, etc.).

    If an exception was captured during the update, the method is terminated
    prematurely. It is the responsibility of the caller to handle the error
    (e.g. lock or clear the preview).

    If ``full_update`` is ``True``, the item tree is refreshed based on changes
    outside of this application (addition, removal, update of items).

    If ``scroll_to_first_selected_item`` is ``True``, the preview is scrolled
    to the first selected item.
    """
    update_locked = super().update()
    if update_locked:
      return

    error = self._process_items(full_update)

    if error:
      self.emit('preview-updated', error)
      return

    self._sync_new_items_with_tree_view()

    self._set_expanded_items()

    self._set_selection(scroll_to_first_selected_item)

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
    # `utils.timeout_add_strict()` to fail. We therefore wrap this function to
    # avoid the error.
    super().set_sensitive(sensitive)

  def set_collapsed_items(self, collapsed_items: Iterable):
    """Sets the collapsed state of items in the preview."""
    self._collapsed_items = set(collapsed_items)
    self._set_expanded_items()
    self.emit('preview-collapsed-items-changed')

  def set_selected_items(
        self,
        selected_items: Iterable,
        scroll_to_first_selected_item: bool = True,
  ):
    """Sets the selection of items in the preview.

    If ``scroll_to_first_selected_item`` is ``True``, the preview is scrolled
    to the first selected item.
    """
    self._selected_items = list(selected_items)
    self._set_selection(scroll_to_first_selected_item)
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

  def get_tree_view_column(self):
    return self._tree_view.get_column(0)

  def get_item_from_path(self, tree_path):
    item_key = self._get_key_from_tree_iter(self._tree_model.get_iter(tree_path))
    if item_key in self._batcher.item_tree:
      return self._batcher.item_tree[item_key]
    else:
      return None

  def set_show_original_name(self, show_original_name):
    self._show_original_name = show_original_name

  def add_items(self, objects):
    added_items = self._batcher.item_tree.add(objects)

    self.emit('preview-added-items', added_items)

  def reorder_item(self, item_key, reference_item, insertion_mode):
    item = self._batcher.item_tree[item_key]

    try:
      self._batcher.item_tree.reorder(item, reference_item, insertion_mode)
    except ValueError:
      # Ignore errors such as reordering folders to one of its children.
      pass

    self.emit('preview-reordered-item', item)

  def sort_items(self, key, ascending):
    self._batcher.item_tree.sort(key=key, ascending=ascending)

    self.emit('preview-sorted-items')

  def remove_selected_items(self):
    removed_items = self._batcher.item_tree.remove(
      [self._batcher.item_tree[item_key] for item_key in self._selected_items])

    self.emit('preview-removed-items', removed_items)

  def remove_all_items(self):
    removed_items = self._batcher.item_tree.clear(return_removed=True)

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
    self._folder_icon = gui_utils_.get_icon_pixbuf(
      'folder', self._tree_view, Gtk.IconSize.MENU)

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
    if color_tag != Gimp.ColorTag.NONE and color_tag in utils.get_enum_values(Gimp.ColorTag):
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
      item.delete_named_state(builtin_actions.EXPORT_NAME_ITEM_STATE)

    error = None

    try:
      self._batcher.run(
        refresh_item_tree=full_update,
        is_preview=True,
        process_contents=False,
        process_names=True,
        process_export=False,
        **utils_setting_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.CommandError as e:
      messages_.display_failure_message(
        messages_.get_failing_command_message(e),
        failure_message=str(e),
        details=e.traceback,
        parent=gui_utils_.get_toplevel_window(self))
      
      error = e
    except Exception as e:
      if self._item_type == 'layer':
        message = _('There was a problem with updating the list of input layers:')
      else:
        message = _('There was a problem with updating the list of input images:')

      messages_.display_failure_message(
        message,
        failure_message=str(e),
        details=traceback.format_exc(),
        parent=gui_utils_.get_toplevel_window(self))
      
      error = e
    
    return error

  def _sync_new_items_with_tree_view(self):
    self._row_select_interactive = False

    new_parent_and_item_keys = self._get_parent_and_item_keys()

    # Remove no longer existing folders or items moved to a different parent.
    # We are iterating in reverse so that we remove the innermost child iters
    # first. Iterating from the top would result in crashes when attempting
    # to remove a child iter whose parent was already removed.
    for original_parent_keys, original_item_keys in reversed(
          self._cached_parent_and_item_keys.items()):
      if original_parent_keys not in new_parent_and_item_keys:
        for key in original_item_keys:
          self._remove_item_if_exists(key)

    # Remove no longer existing items.
    for new_parent_keys, new_item_keys in reversed(new_parent_and_item_keys.items()):
      original_item_keys = self._cached_parent_and_item_keys.get(new_parent_keys, None)
      if original_item_keys:
        item_keys_to_remove = [key for key in original_item_keys if key not in new_item_keys]
        for item_key in item_keys_to_remove:
          self._remove_item_if_exists(item_key)
          del original_item_keys[item_key]

    # Move existing items within the same parent, add new items or re-add
    # existing items under a different parent.
    # We need to iterate in the normal order here so that we insert parents
    # first and then correctly insert children under the newly created parents.
    for new_parent_keys, new_item_keys in new_parent_and_item_keys.items():
      original_item_keys = self._cached_parent_and_item_keys.get(new_parent_keys, {})
      original_item_keys_list = list(original_item_keys)

      # Update existing items and add new items.
      for item_key in new_item_keys:
        item = self._batcher.item_tree[item_key]

        if item_key in original_item_keys:
          iter_from_item = self._tree_iters[item_key]

          self._update_item(iter_from_item, item)
        else:
          self._insert_item(item, None, 'before')
          original_item_keys_list.append(item_key)

      # Move items to the correct order. We are attempting to minimize the
      # number of moves to reduce the number of API calls to the GUI.
      new_item_keys_and_indexes = {item_key: index for index, item_key in enumerate(new_item_keys)}
      new_item_indexes_and_keys = {index: item_key for index, item_key in enumerate(new_item_keys)}
      original_item_key_indexes = [
        new_item_keys_and_indexes[item_key] for item_key in original_item_keys_list]

      longest_increasing_subsequence = self._find_longest_increasing_subsequence(
        original_item_key_indexes)
      longest_increasing_subsequence_set = set(longest_increasing_subsequence)

      for index, item_key in new_item_indexes_and_keys.items():
        if index in longest_increasing_subsequence_set:
          continue

        iter_from_item = self._tree_iters[item_key]

        if index == 0:
          reference_iter = None
        else:
          reference_iter = self._tree_iters[new_item_indexes_and_keys[index - 1]]

        self._move_item_within_parent(iter_from_item, reference_iter, 'after')

    self._cached_parent_and_item_keys = new_parent_and_item_keys

    self._row_select_interactive = True

  @staticmethod
  def _find_longest_increasing_subsequence(values):
    if not values:
      return []

    tail_values = []
    tail_indexes = []
    previous_indexes: List[Optional[int]] = [None] * len(values)

    for index, value in enumerate(values):
      index_of_leftmost_lowest_value = bisect.bisect_left(tail_values, value)

      if index_of_leftmost_lowest_value > 0:
        previous_indexes[index] = tail_indexes[index_of_leftmost_lowest_value - 1]
      else:
        previous_indexes[index] = None

      if index_of_leftmost_lowest_value == len(tail_values):
        tail_values.append(value)
        tail_indexes.append(index)
      else:
        tail_values[index_of_leftmost_lowest_value] = value
        tail_indexes[index_of_leftmost_lowest_value] = index

    longest_increasing_subsequence = []
    current_index = tail_indexes[len(tail_values) - 1]
    while current_index is not None:
      longest_increasing_subsequence.insert(0, values[current_index])
      current_index = previous_indexes[current_index]

    return longest_increasing_subsequence

  def _get_parent_and_item_keys(self):
    if self._batcher.matching_items_and_parents is not None:
      # We create the data structure below using `Batcher.matching_items`
      # rather than `Batcher.matching_items_and_parents` as the latter may
      # contain empty folders, which we do not want to display.
      new_items = self._batcher.matching_items
    else:
      new_items = self._batcher.item_tree

    # We use dictionaries instead of lists so that checking for the existence
    # of the original keys in the new keys is faster.
    visited_parents = set()
    parent_and_item_keys = collections.defaultdict(dict)
    for new_item in new_items:
      for parent in new_item.parents:
        if parent not in visited_parents:
          parent_keys = tuple(parent.key for parent in parent.parents)
          parent_and_item_keys[parent_keys][parent.key] = None
          visited_parents.add(parent)

      parent_keys = tuple(parent.key for parent in new_item.parents)
      parent_and_item_keys[parent_keys][new_item.key] = None

    return parent_and_item_keys

  def _insert_item(self, item, reference_iter, insertion_mode):
    if item.key in self._tree_iters:
      raise AssertionError(f'attempting to add the same item twice to the input list: {item.key}')

    if item.parent:
      parent_tree_iter = self._tree_iters[item.parent.key]
    else:
      parent_tree_iter = None

    item_icon = self._get_icon_from_item(item)
    color_tag_icon = self._get_color_tag_icon(item) if item.key in self._tagged_items else None

    if insertion_mode == 'before':
      insert_func = self._tree_model.insert_before
    elif insertion_mode == 'after':
      insert_func = self._tree_model.insert_after
    else:
      raise ValueError(f'insertion mode {insertion_mode} is not valid')

    tree_iter = insert_func(
      parent_tree_iter,
      reference_iter,
      [
        item_icon,
        item_icon is not None,
        color_tag_icon,
        color_tag_icon is not None,
        self._get_item_name(item),
        item.key,
      ],
    )

    self._expand_folder_item(tree_iter, item)

    self._tree_iters[item.key] = tree_iter

    return tree_iter

  def _expand_folder_item(self, tree_iter, item):
    if tree_iter is not None and item.type == itemtree.TYPE_FOLDER:
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
    if item.type == itemtree.TYPE_FOLDER:
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
    if not self._show_original_name:
      if not self._batcher.edit_mode:
        item_state = item.get_named_state(builtin_actions.EXPORT_NAME_ITEM_STATE)
        return item_state['name'] if item_state is not None else item.name
      else:
        return item.name
    else:
      return item.orig_name

  def _update_item(self, tree_iter, item):
    self._tree_model.set_value(
      tree_iter,
      self._COLUMN_ITEM_NAME[0],
      self._get_item_name(item))

  def _move_item_within_parent(self, tree_iter, reference_iter, insertion_mode):
    if insertion_mode == 'before':
      self._tree_model.move_before(tree_iter, reference_iter)
    elif insertion_mode == 'after':
      self._tree_model.move_after(tree_iter, reference_iter)
    else:
      raise ValueError(f'insertion mode {insertion_mode} is not valid')

  def _remove_item_if_exists(self, item_key):
    iter_to_remove = self._tree_iters.pop(item_key, None)

    if iter_to_remove is not None:
      self._tree_model.remove(iter_to_remove)

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
  
  def _set_selection(self, scroll_to_first_selected_item=True):
    self._row_select_interactive = False

    self._tree_view.get_selection().unselect_all()

    self._selected_items = [
      item_key for item_key in self._selected_items if item_key in self._tree_iters]

    for item_key in self._selected_items:
      tree_iter = self._tree_iters[item_key]
      if tree_iter is not None:
        self._tree_view.get_selection().select_iter(tree_iter)

    # We obtain the selected items again as there is no guarantee that the input
    # items are sorted according to their position in the tree.
    self._selected_items = self._get_keys_from_current_selection()

    if scroll_to_first_selected_item and self._selected_items:
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

    if self._selected_items and self._initial_cursor_item is not None:
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
