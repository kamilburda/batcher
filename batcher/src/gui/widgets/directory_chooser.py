"""Widget for choosing a directory."""

from collections.abc import Iterable
from typing import Optional

import gi
from gi.repository import GdkPixbuf
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from src import directory as directory_
from src.gui import utils as gui_utils_

__all__ = [
  'DirectoryChooser',
]


class DirectoryChooser(Gtk.Box):
  """Class defining a widget for choosing a single directory.

  The widget can store recently used directories and also allows defining
  special entries that can be used in the client code to dynamically resolve
  a directory.

  Signals:
    changed:
      The user changed the selected directory.
  """

  _ROW_SEPARATOR = type('RowSeparator', (), {})()

  _HBOX_SPACING = 3
  _ICON_XPAD = 2

  _ROW_CURRENT_DIRECTORY = 0

  _COLUMNS = (
    _COLUMN_NAME,
    _COLUMN_VISIBLE,
    _COLUMN_ICON,
    _COLUMN_ICON_VISIBLE,
    _COLUMN_DIRECTORY,
  ) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_BOOLEAN],
    [4, GObject.TYPE_PYOBJECT],
  )

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        initial_directory: Optional[directory_.Directory] = None,
        procedure_groups: Optional[Iterable[str]] = None,
        max_width_chars: Optional[int] = None,
        max_recent_dirpaths: int = 5,
        *args,
        **kwargs,
  ):
    super().__init__(*args, **kwargs)

    self._procedure_groups = procedure_groups
    self._max_width_chars = max_width_chars if max_width_chars is not None else -1
    self._max_recent_dirpaths = max(max_recent_dirpaths, 0)

    self._recent_dirpaths_separator_tree_iter = None
    self._recent_dirpaths_tree_iters = []
    self._recent_dirpaths = []

    self._can_emit_changed_signal = True

    self._special_values_and_indexes = {}

    self._init_gui()

    self._can_emit_changed_signal = False

    self.set_directory(initial_directory)

    self._can_emit_changed_signal = True

    self._combo_box.connect('changed', self._on_combo_box_changed)
    self._button_browse.connect('clicked', self._on_button_browse_clicked)

  def get_recent_dirpaths(self):
    return self._recent_dirpaths

  def set_recent_dirpaths(self, recent_dirpaths):
    self._can_emit_changed_signal = False

    self._recent_dirpaths = recent_dirpaths[:self._max_recent_dirpaths]

    if not self._recent_dirpaths and self._recent_dirpaths_separator_tree_iter is not None:
      self._model.remove(self._recent_dirpaths_separator_tree_iter)
      self._recent_dirpaths_separator_tree_iter = None

    if self._recent_dirpaths and self._recent_dirpaths_separator_tree_iter is None:
      self._recent_dirpaths_separator_tree_iter = self._model.append(
        ['', True, None, False, self._ROW_SEPARATOR])

    for tree_iter in self._recent_dirpaths_tree_iters:
      self._model.remove(tree_iter)

    self._recent_dirpaths_tree_iters = []

    for dirpath in self._recent_dirpaths:
      tree_iter = self._model.append(
        [dirpath, True, self._folder_icon, True, directory_.Directory(dirpath)])
      self._recent_dirpaths_tree_iters.append(tree_iter)

    self._can_emit_changed_signal = True

    if self._combo_box.get_active() == -1:
      self._combo_box.set_active(self._ROW_CURRENT_DIRECTORY)

  def add_to_recent_dirpaths(self, dirpath):
    if dirpath in self._recent_dirpaths:
      return

    self._can_emit_changed_signal = False

    if self._recent_dirpaths_separator_tree_iter is None:
      self._recent_dirpaths_separator_tree_iter = self._model.append(
        ['', True, None, False, self._ROW_SEPARATOR])

    if len(self._recent_dirpaths) == self._max_recent_dirpaths:
      dirpath_to_remove_iter = self._recent_dirpaths_tree_iters.pop()
      self._model.remove(dirpath_to_remove_iter)

      self._recent_dirpaths.pop()

    self._recent_dirpaths.insert(0, dirpath)

    tree_iter = self._model.insert_after(
      self._recent_dirpaths_separator_tree_iter,
      [dirpath, True, self._folder_icon, True, directory_.Directory(dirpath)],
    )
    self._recent_dirpaths_tree_iters.insert(0, tree_iter)

    self._can_emit_changed_signal = True

    if self._combo_box.get_active() == -1:
      self._combo_box.set_active(self._ROW_CURRENT_DIRECTORY)

  def set_current_recent_dirpath_as_current_directory(self, set_active=True):
    if self._combo_box.get_active() != self._ROW_CURRENT_DIRECTORY:
      directory = self._model[self._combo_box.get_active()][self._COLUMN_DIRECTORY[0]]
      if directory.type_ == directory_.DirectoryTypes.DIRECTORY:
        self.set_directory(directory_.Directory(directory.value), set_active=set_active)

  def set_most_recent_dirpath_as_current_directory(self, set_active=True):
    if (self._combo_box.get_active() != self._ROW_CURRENT_DIRECTORY
        and self._recent_dirpaths_tree_iters):
      directory = self._model[self._recent_dirpaths_tree_iters[0]][self._COLUMN_DIRECTORY[0]]
      self.set_directory(directory_.Directory(directory.value), set_active=set_active)

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._HBOX_SPACING)

    self._model = Gtk.ListStore(*[column[1] for column in self._COLUMNS])

    self._combo_box = Gtk.ComboBox(
      model=self._model,
      active=0,
      id_column=0,
    )
    self._combo_box.set_row_separator_func(self._is_row_separator)

    self._folder_icon = gui_utils_.get_icon_pixbuf('folder', self._combo_box, Gtk.IconSize.MENU)

    special_values = directory_.get_special_values(self._procedure_groups)
    default_directory = directory_.Directory()

    self._model.append([default_directory.value, True, self._folder_icon, True, default_directory])

    if special_values:
      self._model.append(['', True, None, False, self._ROW_SEPARATOR])

    for name, special_value in special_values.items():
      self._model.append([
        special_value.display_name,
        True,
        None,
        False,
        directory_.Directory(name, type_=directory_.DirectoryTypes.SPECIAL),
      ])
      self._special_values_and_indexes[name] = len(self._model) - 1

    self._renderer_icon = Gtk.CellRendererPixbuf(
      xpad=self._ICON_XPAD,
    )
    self._combo_box.pack_start(self._renderer_icon, False)
    self._combo_box.add_attribute(self._renderer_icon, 'pixbuf', self._COLUMN_ICON[0])
    self._combo_box.add_attribute(self._renderer_icon, 'visible', self._COLUMN_ICON_VISIBLE[0])

    self._renderer_name = Gtk.CellRendererText(
      ellipsize=Pango.EllipsizeMode.START,
      max_width_chars=self._max_width_chars,
    )
    self._combo_box.pack_start(self._renderer_name, True)
    self._combo_box.add_attribute(self._renderer_name, 'text', self._COLUMN_NAME[0])

    self._combo_box.set_active(self._ROW_CURRENT_DIRECTORY)

    self._combo_box.show_all()

    self._button_browse = Gtk.Button(
      image=Gtk.Image.new_from_icon_name('folder', Gtk.IconSize.BUTTON),
      tooltip_text=_('Browse'),
    )

    self.pack_start(self._combo_box, True, True, 0)
    self.pack_start(self._button_browse, False, False, 0)

    self.show_all()

  def _is_row_separator(self, model, tree_iter):
    return model[tree_iter][self._COLUMN_DIRECTORY[0]] == self._ROW_SEPARATOR

  def _on_combo_box_changed(self, _combo_box):
    self._set_tooltip()

    if self._can_emit_changed_signal:
      self.emit('changed')

  def _on_button_browse_clicked(self, _button):
    file_dialog = Gtk.FileChooserNative(
      title=_('Select a Folder'),
      action=Gtk.FileChooserAction.SELECT_FOLDER,
      do_overwrite_confirmation=True,
      modal=True,
      transient_for=gui_utils_.get_toplevel_window(self),
    )

    response_id = file_dialog.run()

    if response_id == Gtk.ResponseType.ACCEPT:
      dirpath = file_dialog.get_filename()
      if dirpath:
        self.set_directory(directory_.Directory(dirpath))

    file_dialog.destroy()

  def get_directory(self) -> directory_.Directory:
    selected_row_index = self._combo_box.get_active()
    if selected_row_index == -1:
      selected_row_index = self._ROW_CURRENT_DIRECTORY

    row = self._model[selected_row_index]

    return row[self._COLUMN_DIRECTORY[0]]

  def set_directory(self, directory: Optional[directory_.Directory], set_active=True):
    can_emit_changed_signal = self._can_emit_changed_signal

    self._can_emit_changed_signal = False

    if directory is None:
      directory = directory_.Directory()

    if directory.type_ == directory_.DirectoryTypes.DIRECTORY:
      self._model[self._ROW_CURRENT_DIRECTORY][self._COLUMN_DIRECTORY[0]] = directory
      self._model[self._ROW_CURRENT_DIRECTORY][self._COLUMN_NAME[0]] = directory.value

      if set_active:
        self._combo_box.set_active(self._ROW_CURRENT_DIRECTORY)
    elif directory.type_ == directory_.DirectoryTypes.SPECIAL:
      if set_active:
        self._combo_box.set_active(self._special_values_and_indexes[directory.value])

    self._can_emit_changed_signal = can_emit_changed_signal

    if self._can_emit_changed_signal:
      self.emit('changed')

    self._set_tooltip()

  def _set_tooltip(self):
    directory = self.get_directory()

    if directory.type_ == directory_.DirectoryTypes.SPECIAL:
      index = self._special_values_and_indexes[directory.value]
      self._combo_box.set_tooltip_text(self._model[index][self._COLUMN_NAME[0]])
    else:
      self._combo_box.set_tooltip_text(directory.value)


GObject.type_register(DirectoryChooser)
