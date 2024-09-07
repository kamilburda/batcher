"""Providing notifications when a plug-in is initialized."""

from gi.repository import GObject


class _PlugInInitializationNotifier(GObject.GObject):
  """Class providing a notification when a plug-in is properly initialized.

  Signals:
    start-procedure:
      A GIMP plug-in procedure is about to start. This signal is emitted
      immediately before a procedure function is executed.
  """

  __gsignals__ = {
    'start-procedure': (GObject.SignalFlags.RUN_FIRST, None, ()),
  }


notifier = _PlugInInitializationNotifier()
"""Singleton allowing to receive notifications when a plug-in is properly
initialized.

This is useful if you have code outside GIMP procedure functions that try to
access the GIMP API, such as ``Gimp.get_pdb()``, which is not initialized at
that point. With this singleton, you can delay executing that code until the
GIMP API is properly initialized.

In client code, you would use this singleton as follows:

  import pygimplib as pg

  def do_stuff_after_plugin_initialization(_notifier):
    print('initialized')
  
  pg.notifier.connect('start-procedure', do_stuff_after_plugin_initialization)
"""
