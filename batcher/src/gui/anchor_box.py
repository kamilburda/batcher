"""Widget for setting an anchor point, e.g. "top left"."""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Gtk


__all__ = [
  'AnchorBox',
]


class AnchorBox(Gtk.Box):

  __gsignals__ = {'value-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}

  def __init__(
        self,
        anchor_names_and_display_names,
        default_anchor_name,
        widget_spacing=8,
  ):
    super().__init__()

    self._anchor_names_and_display_names = dict(anchor_names_and_display_names.items())
    self._default_anchor_name = default_anchor_name
    self._widget_spacing = widget_spacing

    self._active_button = None

    self._init_gui()

  def get_value(self):
    return self._buttons_and_names[self._active_button]

  def set_value(self, anchor_name):
    button = self._names_and_buttons[anchor_name]
    self._set_button_active(button)

  def _init_gui(self):
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_spacing(self._widget_spacing)

    self._grid = Gtk.Grid()

    self._n_rows = 3
    self._n_cols = 3
    self._icon_names = [
      GimpUi.ICON_GRAVITY_NORTH_WEST,
      GimpUi.ICON_GRAVITY_NORTH,
      GimpUi.ICON_GRAVITY_NORTH_EAST,
      GimpUi.ICON_GRAVITY_WEST,
      GimpUi.ICON_CENTER,
      GimpUi.ICON_GRAVITY_EAST,
      GimpUi.ICON_GRAVITY_SOUTH_WEST,
      GimpUi.ICON_GRAVITY_SOUTH,
      GimpUi.ICON_GRAVITY_SOUTH_EAST,
    ]

    buttons = []

    for row_index in range(self._n_rows):
      for col_index in range(self._n_cols):
        button = Gtk.ToggleButton.new()

        icon_index = row_index * self._n_rows + col_index
        image = Gtk.Image.new_from_icon_name(
          self._icon_names[icon_index],
          Gtk.IconSize.BUTTON,
        )
        button.add(image)

        self._grid.attach(button, col_index, row_index, 1, 1)

        buttons.append(button)

    self._button_clicked_handler_ids = {}
    self._buttons_and_names = dict(zip(buttons, self._anchor_names_and_display_names))
    self._names_and_buttons = dict(zip(self._anchor_names_and_display_names, buttons))

    self._active_button = self._names_and_buttons[self._default_anchor_name]
    self._active_button.set_active(True)

    self._label = Gtk.Label(
      label=self._anchor_names_and_display_names[self._default_anchor_name],
      width_chars=max(
        [len(display_name) for display_name in self._anchor_names_and_display_names.values()]),
      xalign=0.0,
      yalign=0.5,
    )

    self.pack_start(self._grid, False, False, 0)
    self.pack_start(self._label, False, False, 0)

    for button in self._buttons_and_names:
      self._button_clicked_handler_ids[button] = button.connect('toggled', self._on_button_toggled)

  def _on_button_toggled(self, button):
    self._set_button_active(button)

    self.emit('value-changed')

  def _set_button_active(self, button):
    if self._active_button is not None:
      active_button_handler_id = self._button_clicked_handler_ids[self._active_button]
      with GObject.signal_handler_block(self._active_button, active_button_handler_id):
        self._active_button.set_active(False)

    handler_id = self._button_clicked_handler_ids[button]
    with GObject.signal_handler_block(button, handler_id):
      button.set_active(True)

    anchor_name = self._buttons_and_names[button]
    self._label.set_text(self._anchor_names_and_display_names[anchor_name])

    self._active_button = button


GObject.type_register(AnchorBox)
