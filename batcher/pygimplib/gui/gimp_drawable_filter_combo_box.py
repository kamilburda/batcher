"""Widget for `Gimp.DrawableFilter` objects."""

from typing import Optional

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'GimpDrawableFilterComboBox',
]


class GimpDrawableFilterComboBox(Gtk.Box):
  """Class defining a GTK widget for `Gimp.DrawableFilter` instances.

  Signals:
    changed:
      The user changed the selection either in the combo box containing
      available drawables or in the combo box for the selected drawable filter.

      Signal arguments:
        selected_filter: The currently selected `Gimp.DrawableFilter` instance.
  """

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))}

  _COMBO_BOX_SPACING = 4

  def __init__(self, constraint=None, data=None, **kwargs):
    super().__init__(
      homogeneous=False,
      orientation=Gtk.Orientation.VERTICAL,
      spacing=self._COMBO_BOX_SPACING,
      **kwargs,
    )

    self._drawable_combo_box = GimpUi.DrawableComboBox.new(constraint=constraint, data=data)

    self.pack_start(self._drawable_combo_box, False, False, 0)

    self._model, self._filter_combo_box = self._create_filter_combo_box()

    self.pack_start(self._filter_combo_box, False, False, 0)

    Gtk.ComboBox.connect(self._drawable_combo_box, 'changed', self._on_drawable_changed)
    self._filter_combo_box.connect('changed', self._on_filter_changed)

  def get_active(self) -> Optional[int]:
    index = self._filter_combo_box.get_active()

    if 0 < index < len(self._model):
      return self._model[index][0]
    else:
      return -1

  def set_active(self, filter_id: int):
    for index, row in enumerate(self._model):
      if row[0] == filter_id:
        self._filter_combo_box.set_active(index)
        break

  def get_active_drawable(self):
    drawable_id = self._drawable_combo_box.get_active().value

    if Gimp.Drawable.id_is_valid(drawable_id):
      return Gimp.Drawable.get_by_id(drawable_id)
    else:
      return None

  def set_active_drawable(self, drawable):
    self._drawable_combo_box.set_active(drawable.get_id())

  @staticmethod
  def _create_filter_combo_box():
    model = Gtk.ListStore(GObject.TYPE_INT, GObject.TYPE_STRING)

    combo_box = Gtk.ComboBox(model=model, active=0)

    renderer_text = Gtk.CellRendererText()
    combo_box.pack_start(renderer_text, True)
    combo_box.add_attribute(renderer_text, 'text', 1)

    return model, combo_box

  def _on_drawable_changed(self, _combo_box):
    self._model.clear()

    drawable = self.get_active_drawable()

    for drawable_filter in drawable.get_filters():
      drawable_filter_id = drawable_filter.get_id()
      self._model.append((drawable_filter_id, f'{drawable_filter.get_name()}-{drawable_filter_id}'))

    self._filter_combo_box.set_active(0)

  def _on_filter_changed(self, _combo_box):
    self.emit('changed', self.get_active())


GObject.type_register(GimpDrawableFilterComboBox)
