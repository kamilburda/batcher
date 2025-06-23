import gi
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from . import _base


__all__ = [
  'CheckButtonLabelPresenter',
  'EntryPresenter',
  'LabelPresenter',
]


class CheckButtonLabelPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.CheckButton` widgets.

  Value: Label of the check button.
  """

  _VALUE_CHANGED_SIGNAL = 'notify::text'

  def get_value(self):
    return self._widget.get_child().get_text()

  def _set_value(self, value):
    self._widget.get_child().set_text(value if value is not None else '')


class EntryPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Entry` widgets.

  Value: Text in the entry.
  """

  _VALUE_CHANGED_SIGNAL = 'changed'

  def _create_widget(self, setting, **kwargs):
    return Gtk.Entry()

  def get_value(self):
    return self._widget.get_text()

  def _set_value(self, value):
    self._widget.set_text(value if value is not None else '')
    # Place the cursor at the end of the text entry.
    self._widget.set_position(-1)


class LabelPresenter(_base.GtkPresenter):
  """`setting.Presenter` subclass for `Gtk.Label` widgets.

  Value: Label text.
  """

  _VALUE_CHANGED_SIGNAL = 'notify::text'

  def _create_widget(
        self,
        setting,
        use_markup=True,
        xalign=0.0,
        yalign=0.5,
        max_width_chars=50,
        ellipsize=Pango.EllipsizeMode.END,
        **kwargs,
  ):
    label = Gtk.Label(
      use_markup=use_markup,
      max_width_chars=max_width_chars,
      xalign=xalign,
      yalign=yalign,
      ellipsize=ellipsize,
      **kwargs,
    )
    label.set_markup(GLib.markup_escape_text(setting.display_name))
    return label

  def get_value(self):
    return self._widget.get_label()

  def _set_value(self, value):
    self._widget.set_markup(value if value is not None else '')
