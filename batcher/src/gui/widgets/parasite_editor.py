"""Widget for `Gimp.Parasite` instances."""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib

from src import utils

__all__ = [
  'ParasiteEditor',
]


class ParasiteEditor(Gtk.Grid):
  """Subclass of `Gtk.Grid` to edit `Gimp.Parasite` instances interactively.

  The class allows adjusting the following `Gimp.Parasite` attributes: name,
  flags and data. In the text box provided by this class, the data attribute is
  treated as a sequence of characters having ordinal value between 0-255. Any
  Unicode characters entered by the user having ordinal value of 256 or higher
  will be ignored when calling ``get_parasite()``.

  Signals:
    parasite-changed: The parasite was modified by the user.
  """
  
  __gsignals__ = {'parasite-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}
  
  _ROW_SPACING = 5
  _COLUMN_SPACING = 5
  
  def __init__(self, parasite: Gimp.Parasite, default_parasite_name: str):
    super().__init__()

    self._should_invoke_parasite_changed_signal = True
    self._default_parasite_name = default_parasite_name
    
    self._init_gui(parasite)

  def get_parasite(self) -> Gimp.Parasite:
    """Returns a `Gimp.Parasite` instance based on the values in the parasite
    box.

    Any characters with ordinal value of 256 or higher are ignored.
    """
    return Gimp.Parasite.new(*self._get_values())
  
  def set_parasite(self, parasite: Gimp.Parasite):
    """Fills the parasite box with attributes from the specified `Gimp.Parasite`
    instance.
    """
    self._set_values(parasite)

  def _init_gui(self, parasite):
    self.set_row_spacing(self._ROW_SPACING)
    self.set_column_spacing(self._COLUMN_SPACING)

    self._label_name = Gtk.Label(
      label=_('Name'),
    )
    self.attach(self._label_name, 0, 0, 1, 1)

    self._parasite_name_entry = Gtk.Entry(
      hexpand=True,
    )
    self.attach(self._parasite_name_entry, 1, 0, 1, 1)

    self._label_flags = Gtk.Label(
      label=_('Flags'),
    )
    self.attach(self._label_flags, 0, 1, 1, 1)

    self._parasite_flags_spin_button = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=parasite.get_flags(),
        lower=0,
        upper=GLib.MAXINT,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
      hexpand=True,
    )
    self.attach(self._parasite_flags_spin_button, 1, 1, 1, 1)

    self._label_data = Gtk.Label(
      label=_('Data'),
    )
    self.attach(self._label_data, 0, 2, 1, 1)

    self._parasite_data_entry = Gtk.Entry(
      hexpand=True,
    )
    self.attach(self._parasite_data_entry, 1, 2, 1, 1)

    self._set_values(parasite)
    self._connect_changed_events()
  
  def _get_values(self):
    parasite_name = self._parasite_name_entry.get_text()

    return (
      parasite_name if parasite_name else self._default_parasite_name,
      self._parasite_flags_spin_button.get_value_as_int(),
      utils.bytes_to_signed_bytes(
        utils.escaped_string_to_bytes(
          self._parasite_data_entry.get_text(), remove_overflow=True)))
  
  def _set_values(self, parasite):
    self._should_invoke_parasite_changed_signal = False
    
    self._parasite_name_entry.set_text(parasite.get_name())
    self._parasite_flags_spin_button.set_value(parasite.get_flags())
    self._parasite_data_entry.set_text(
      utils.bytes_to_escaped_string(utils.signed_bytes_to_bytes(parasite.get_data())))
    
    self._should_invoke_parasite_changed_signal = True
  
  def _connect_changed_events(self):
    self._parasite_name_entry.connect('changed', self._on_parasite_changed)
    self._parasite_flags_spin_button.connect('value-changed', self._on_parasite_changed)
    self._parasite_data_entry.connect('changed', self._on_parasite_changed)

  def _on_parasite_changed(self, widget, *args, **kwargs):
    if self._should_invoke_parasite_changed_signal:
      self.emit('parasite-changed')


GObject.type_register(ParasiteEditor)
