"""Stubs for GIMP objects, classes, etc. usable in automated tests."""

import collections
import itertools

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject


def _get_result_tuple_type(arg_name) -> collections.namedtuple:
  return collections.namedtuple(
    f'ResultTuple_{arg_name}', ['success', arg_name])


class PdbStub:

  _PROCEDURES = {}

  @classmethod
  def add_procedure(cls, proc):
    """Adds a fake PDB procedure."""
    cls._PROCEDURES[proc.get_name()] = proc

  @classmethod
  def clear_procedures(cls):
    cls._PROCEDURES = {}

  @classmethod
  def procedure_exists(cls, proc_name):
    return proc_name in cls._PROCEDURES

  @classmethod
  def lookup_procedure(cls, proc_name):
    return cls._PROCEDURES.get(proc_name, None)


class PdbProcedureStub:

  def __init__(
        self,
        name,
        proc_type=Gimp.PDBProcType.PLUGIN,
        function=None,
        arguments_spec=None,
        return_vals_spec=None,
        blurb='',
        menu_label=None,
  ):
    self.function = function

    self._name = name
    self._proc_type = proc_type
    self._blurb = blurb
    self._menu_label = menu_label

    if arguments_spec is None:
      arguments_spec = []

    self._arguments_spec = [GParamStub(**kwargs) for kwargs in arguments_spec]

    if return_vals_spec is None:
      return_vals_spec = []

    self._return_vals_spec = [GParamStub(**kwargs) for kwargs in return_vals_spec]

  def get_name(self):
    return self._name

  def get_proc_type(self):
    return self._proc_type

  def get_blurb(self):
    return self._blurb

  def get_arguments(self):
    return self._arguments_spec

  def get_return_values(self):
    return self._return_vals_spec

  def get_menu_label(self):
    return self._menu_label

  def run(self, config):
    pass


class GParamStub:

  def __init__(self, value_type, name, blurb='', default_value=None):
    self.value_type = value_type
    self.name = name
    self.blurb = blurb
    self.default_value = default_value


class ParasiteFunctionsStubMixin:
  
  def __init__(self):
    self.parasites = {}
  
  def get_parasite(self, name):
    if name in self.parasites:
      return self.parasites[name]
    else:
      return None
  
  def get_parasite_list(self):
    return list(self.parasites)
  
  def attach_parasite(self, parasite):
    self.parasites[parasite.get_name()] = parasite
  
  def detach_parasite(self, parasite_name):
    if parasite_name in self.parasites:
      del self.parasites[parasite_name]


class Parasite(GObject.GObject):

  def __init__(self, name, flags, data):
    self.name = name
    self.flags = flags
    self.data = data

  @classmethod
  def new(cls, name, flags, data):
    return Parasite(name, flags, data)

  def get_name(self):
    return self.name

  def get_flags(self):
    return self.flags

  def get_data(self):
    return list(self.data)


class Image(GObject.GObject, ParasiteFunctionsStubMixin):

  _image_id_counter = itertools.count(start=1)

  _images_and_ids = {}

  def __init__(self, name=None, id_=None, filepath=None, width=0, height=0, base_type=None):
    GObject.GObject.__init__(self)
    ParasiteFunctionsStubMixin.__init__(self)
    
    self.name = name
    
    if id_ is None:
      self.id_ = next(self._image_id_counter)
    else:
      self.id_ = id_

    self._images_and_ids[self.id_] = self

    self.width = width
    self.height = height
    self.base_type = base_type
    self.layers = []

    if filepath is not None:
      self._file = Gio.file_new_for_path(filepath)
    else:
      self._file = None

    self.valid = True

  @classmethod
  def get_by_id(cls, id_):
    try:
      return cls._images_and_ids[id_]
    except KeyError:
      return None

  @classmethod
  def id_is_valid(cls, id_):
    return id_ in cls._images_and_ids

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

  def get_layers(self):
    return self.layers

  def get_file(self):
    return self._file

  def set_file(self, value):
    self._file = value

  def is_valid(self):
    return self.valid

  def delete(self):
    pass


class Item(GObject.GObject, ParasiteFunctionsStubMixin):
  
  _item_id_counter = itertools.count(start=1)

  _items_and_ids = {}
  
  def __init__(self, name=None, id_=None, visible=True, image=None, parent=None, is_group=False):
    GObject.GObject.__init__(self)
    ParasiteFunctionsStubMixin.__init__(self)
    
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
    try:
      return cls._items_and_ids[id_]
    except KeyError:
      return None

  @classmethod
  def id_is_valid(cls, id_):
    return id_ in cls._items_and_ids

  def get_name(self):
    return self.name

  def get_id(self):
    return self.id_

  def is_group(self):
    return self._is_group

  def is_layer(self):
    return False

  def is_layer_mask(self):
    return False

  def is_drawable(self):
    return False

  def is_channel(self):
    return False

  def is_path(self):
    return False

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

  def get_children(self):
    return self.children

  def get_parent(self):
    return self.parent

  def is_valid(self):
    return self.valid


class Layer(Item):

  def __init__(self, mask=None, **kwargs):
    super().__init__(**kwargs)

    self.mask = mask

  def is_layer(self):
    return True

  def is_drawable(self):
    return True

  def get_mask(self):
    return self.mask


class LayerMask(Item):

  def is_layer_mask(self):
    return True


class Channel(Item):

  def is_channel(self):
    return True


class Path(Item):

  def is_path(self):
    return True


class Display(GObject.GObject):

  _display_id_counter = itertools.count(start=1)

  _displays_and_ids = {}
  
  def __init__(self, id_=None):
    super().__init__()

    if id_ is None:
      self.id_ = next(self._display_id_counter)
    else:
      self.id_ = id_

    self._displays_and_ids[self.id_] = self

    self.valid = True

  @classmethod
  def get_by_id(cls, id_):
    return cls._displays_and_ids[id_]

  def get_id(self):
    return self.id_

  def is_valid(self):
    return self.valid


class Resource(GObject.GObject):

  _resources = {}

  def __init__(self, name=None):
    super().__init__()
    
    self.name = name

    if name is not None:
      self._resources[name] = self

    self.valid = True

  @classmethod
  def get_by_name(cls, name):
    return cls._resources[name]

  def get_name(self):
    return self.name

  def is_valid(self):
    return self.valid


class Brush(Resource):

  def __init__(
        self,
        name=None,
        angle=0.0,
        aspect_ratio=0.0,
        hardness=0.0,
        radius=0.0,
        shape=0,
        spacing=0,
        spikes=0,
  ):
    super().__init__(name=name)

    self.angle = angle
    self.aspect_ratio = aspect_ratio
    self.hardness = hardness
    self.radius = radius
    self.shape = shape
    self.spacing = spacing
    self.spikes = spikes

  def get_angle(self):
    return _get_result_tuple_type('angle')(True, self.angle)

  def get_aspect_ratio(self):
    return _get_result_tuple_type('aspect_ratio')(True, self.aspect_ratio)

  def get_hardness(self):
    return _get_result_tuple_type('hardness')(True, self.hardness)

  def get_radius(self):
    return _get_result_tuple_type('radius')(True, self.radius)

  def get_shape(self):
    return _get_result_tuple_type('shape')(True, self.shape)

  def get_spacing(self):
    return self.spacing

  def get_spikes(self):
    return _get_result_tuple_type('spikes')(True, self.spikes)

  def set_angle(self, value):
    self.angle = value

  def set_aspect_ratio(self, value):
    self.aspect_ratio = value

  def set_hardness(self, value):
    self.hardness = value

  def set_radius(self, value):
    self.radius = value

  def set_shape(self, value):
    self.shape = Gimp.BrushGeneratedShape(value)

  def set_spacing(self, value):
    self.spacing = value

  def set_spikes(self, value):
    self.spikes = value


class Font(Resource):
  pass


class Gradient(Resource):
  pass


class Palette(Resource):

  def __init__(self, name=None, columns=0):
    super().__init__(name=name)

    self.columns = columns

  def get_columns(self):
    return self.columns

  def set_columns(self, value):
    self.columns = value


class Pattern(Resource):
  pass


class ObjectArray:

  __gtype__ = Gimp.ObjectArray.__gtype__


class GimpModuleStub(ParasiteFunctionsStubMixin):

  Parasite = Parasite

  Image = Image

  Item = Item
  Layer = Layer
  LayerMask = LayerMask
  Channel = Channel
  Path = Path

  Display = Display

  Resource = Resource
  Brush = Brush
  Font = Font
  Gradient = Gradient
  Palette = Palette
  Pattern = Pattern

  ObjectArray = ObjectArray

  RunMode = Gimp.RunMode
  PDBStatusType = Gimp.PDBStatusType

  PARASITE_PERSISTENT = Gimp.PARASITE_PERSISTENT

  _PDB_INSTANCE = PdbStub()

  @classmethod
  def get_pdb(cls):
    return cls._PDB_INSTANCE
