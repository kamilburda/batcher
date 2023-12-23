"""Custom GTK cell renderers."""

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

__all__ = [
  'CellRendererTextList',
]


class CellRendererTextList(Gtk.CellRendererText):
  """Custom text-based cell renderer that can accept a list of strings."""
  
  __gproperties__ = {
    'text-list': (
      GObject.TYPE_STRV,
      'list of strings',
      'List of strings to render',
      GObject.PARAM_READWRITE,
    ),
    'markup-list': (
      GObject.TYPE_STRV,
      'list of strings in markup',
      'List of strings with markup to render',
      GObject.PARAM_WRITABLE,
    ),
    'text-list-separator': (
      GObject.TYPE_STRING,
      'separator for list of strings',
      'Text separator for the list of strings ("text-list" and "markup-list" properties)',
      ', ',     # Default value
      GObject.PARAM_READWRITE,
    ),
  }
  
  def __init__(self):
    super().__init__()
    
    self.text_list = []
    self.markup_list = []
    self.text_list_separator = ', '
  
  def do_get_property(self, property_):
    attr_name = self._property_name_to_attr(property_.name)
    if hasattr(self, attr_name):
      return getattr(self, attr_name)
    else:
      return Gtk.CellRendererText.get_property(self, property_.name)
  
  def do_set_property(self, property_, value):
    attr_name = self._property_name_to_attr(property_.name)
    if hasattr(self, attr_name):
      if (property_.name in ['text-list', 'markup-list']
          and not (isinstance(value, list) or isinstance(value, tuple))):
        raise AttributeError('not a list or tuple')
      
      setattr(self, attr_name, value)
      
      self._evaluate_text_property(property_.name)
  
  def _evaluate_text_property(self, property_name):
    """Changes the ``'text'`` or ``'markup'`` property according to the value of
    ``'text-list'``, ``'markup-list'`` and ``'text-list-separator'`` properties.
    """
    def _set_text():
      new_text = self.text_list_separator.join(self.text_list)
      Gtk.CellRendererText.set_property(self, 'text', new_text)
    
    def _set_markup():
      new_text = self.text_list_separator.join(self.markup_list)
      Gtk.CellRendererText.set_property(self, 'markup', new_text)
    
    if property_name == 'text-list':
      _set_text()
      self.markup_list = []
    elif property_name == 'markup-list':
      _set_markup()
      self.text_list = []
    elif property_name == 'text-list-separator':
      if self.text_list:
        _set_text()
      elif self.markup_list:
        _set_markup()
  
  @staticmethod
  def _property_name_to_attr(property_name):
    return property_name.replace('-', '_')


GObject.type_register(CellRendererTextList)
