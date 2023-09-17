"""Stubs for GIMP objects, classes, etc. usable in automated tests."""

import itertools

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio


class ParasiteFunctionsStubMixin:
  
  def __init__(self):
    self._parasites = {}
  
  def get_parasite(self, name):
    if name in self._parasites:
      return self._parasites[name]
    else:
      return None
  
  def get_parasite_list(self):
    return list(self._parasites)
  
  def attach_parasite(self, parasite):
    self._parasites[parasite.get_name()] = parasite
  
  def detach_parasite(self, parasite_name):
    if parasite_name in self._parasites:
      del self._parasites[parasite_name]


class Image(ParasiteFunctionsStubMixin):

  _image_id_counter = itertools.count(start=1)

  _images_and_ids = {}

  def __init__(self, name=None, id_=None, filepath=None):
    super().__init__()
    
    self.name = name
    
    if id_ is None:
      self.id_ = next(self._image_id_counter)
    else:
      self.id_ = id_

    self._images_and_ids[self.id_] = self

    self.width = 0
    self.height = 0
    self.base_type = None
    self.layers = []

    if filepath is not None:
      self._file = Gio.file_new_for_path(filepath)
    else:
      self._file = None

    self.valid = True

  @classmethod
  def get_by_id(cls, id_):
    return cls._images_and_ids[id_]

  def get_name(self):
    return self.name

  def get_id(self):
    return self.id_

  def get_width(self):
    return self.width

  def get_height(self):
    return self.height

  def get_base_type(self):
    return self.base_type

  def list_layers(self):
    return self.layers

  def get_file(self):
    return self._file

  def set_file(self, value):
    self._file = value

  def is_valid(self):
    return self.valid


class Item(ParasiteFunctionsStubMixin):
  
  _item_id_counter = itertools.count(start=1)

  _items_and_ids = {}
  
  def __init__(self, name=None, id_=None, visible=True, image=None, parent=None, is_group=False):
    super().__init__()
    
    self.name = name
    
    if id_ is None:
      self.id_ = next(self._item_id_counter)
    else:
      self.id_ = id_

    self._items_and_ids[self.id_] = self

    self._is_group = is_group
    self.width = 0
    self.height = 0
    self.visible = visible
    self.offsets = (0, 0)
    self.image = image
    self.children = []
    self.parent = parent
    self.valid = True

  @classmethod
  def get_by_id(cls, id_):
    return cls._items_and_ids[id_]

  def get_name(self):
    return self.name

  def get_id(self):
    return self.id_

  def is_group(self):
    return self._is_group

  def get_width(self):
    return self.width

  def get_height(self):
    return self.height

  def get_visible(self):
    return self.visible

  def get_offsets(self):
    return (True, *self.offsets)

  def get_image(self):
    return self.image

  def list_children(self):
    return self.children

  def get_parent(self):
    return self.parent

  def is_valid(self):
    return self.valid


class Layer(Item):
  pass


class Channel(Item):
  pass


class Vectors(Item):
  pass


class Display(ParasiteFunctionsStubMixin):
  
  def __init__(self, id_=None):
    super().__init__()

    self.id_ = id_


class GimpModuleStub(ParasiteFunctionsStubMixin):

  Parasite = Gimp.Parasite
  Image = Image
  Item = Item
  Layer = Layer
  Channel = Channel
  Vectors = Vectors
  Display = Display
