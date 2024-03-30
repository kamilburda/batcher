"""Widget displaying a list of available actions (procedures/constraints).

The list includes GIMP PDB procedures.
"""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg


class ActionBrowser:

  def __init__(self, title=None):
    self._title = title

    self._init_gui()

  @property
  def widget(self):
    return self._dialog

  def _init_gui(self):
    self._dialog = GimpUi.ProcBrowserDialog(
      title=self._title,
      role=pg.config.PLUGIN_NAME,
    )

    self._dialog.add_buttons(
      Gtk.STOCK_ADD, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL,
      Gtk.ResponseType.CANCEL)

    self._dialog.set_default_response(Gtk.ResponseType.OK)
