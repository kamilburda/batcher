"""Widget for choosing a directory."""

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
  _ROW_CURRENT_DIRECTORY_SPECIAL_VALUES_SEPARATOR = 1

  _COLUMNS = (
    _COLUMN_NAME,
    _COLUMN_VISIBLE,
    _COLUMN_ICON,
    _COLUMN_DIRECTORY,
  ) = (
    [0, GObject.TYPE_STRING],
    [1, GObject.TYPE_BOOLEAN],
    [2, GdkPixbuf.Pixbuf],
    [3, GObject.TYPE_PYOBJECT],
  )

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        initial_directory: Optional[directory_.Directory] = None,
        *args,
        **kwargs,
  ):
    super().__init__(*args, **kwargs)

    self._can_emit_changed_signal = True

    self._special_values_and_indexes = {}

    self._init_gui()

    self._can_emit_changed_signal = False

    self.set_directory(initial_directory)

    self._can_emit_changed_signal = True

    self._combo_box.connect('changed', self._on_combo_box_changed)
    self._button_browse.connect('clicked', self._on_button_browse_clicked)

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

    special_values = directory_.get_special_values()
    default_directory = directory_.Directory()

    self._model.append([default_directory.value, True, self._folder_icon, default_directory])
    self._model.append(['', bool(special_values), None, self._ROW_SEPARATOR])

    for name, special_value in special_values.items():
      self._model.append([
        special_value.display_name,
        True,
        None,
        directory_.Directory(name, type_=directory_.DirectoryTypes.SPECIAL),
      ])
      self._special_values_and_indexes[name] = len(self._model) - 1

    self._renderer_icon = Gtk.CellRendererPixbuf(
      xpad=self._ICON_XPAD,
    )
    self._combo_box.pack_start(self._renderer_icon, False)
    self._combo_box.add_attribute(self._renderer_icon, 'pixbuf', self._COLUMN_ICON[0])

    self._renderer_name = Gtk.CellRendererText(
      ellipsize=Pango.EllipsizeMode.START,
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

  def set_directory(self, directory: Optional[directory_.Directory]):
    if directory is None:
      directory = directory_.Directory()

    if directory.type_ == directory_.DirectoryTypes.DIRECTORY:
      self._model[self._ROW_CURRENT_DIRECTORY][self._COLUMN_DIRECTORY[0]] = directory
      self._model[self._ROW_CURRENT_DIRECTORY][self._COLUMN_NAME[0]] = directory.value

      self._combo_box.set_active(self._ROW_CURRENT_DIRECTORY)
    elif directory.type_ == directory_.DirectoryTypes.SPECIAL:
      self._combo_box.set_active(self._special_values_and_indexes[directory.value])

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
