"""Metaclasses for settings and mappings of types."""

import collections
import functools
import inspect
import re

from gi.repository import GObject


class _TypeMap:
  
  def __init__(self, description=None):
    self._description = description
    
    self._name_to_type_map = {}
    self._type_to_names_map = collections.defaultdict(list)
  
  def __getitem__(self, type_or_name):
    if isinstance(type_or_name, str):
      try:
        return self._name_to_type_map[type_or_name]
      except KeyError:
        raise TypeError(self._get_error_message(type_or_name))
    else:
      return_all_names = False
      
      if isinstance(type_or_name, (list, tuple)):
        type_ = type_or_name[0]
        if len(type_or_name) > 1:
          return_all_names = type_or_name[1]
      else:
        type_ = type_or_name
      
      if type_ not in self._type_to_names_map:
        raise TypeError(self._get_error_message(type_))
      
      names = self._type_to_names_map[type_]
      
      if return_all_names:
        return names
      else:
        return names[0]
  
  def __contains__(self, key):
    if isinstance(key, str):
      return key in self._name_to_type_map
    else:
      return key in self._type_to_names_map
  
  def __getattr__(self, name):
    try:
      return self._name_to_type_map[name]
    except KeyError:
      raise TypeError(self._get_error_message(name))
  
  def __hasattr__(self, name):
    return name in self._name_to_type_map

  def __iter__(self):
    return self.keys()

  def keys(self):
    for name in self._name_to_type_map:
      yield name

  def values(self):
    for type_ in self._name_to_type_map.values():
      yield type_

  def items(self):
    for name, type_ in self._name_to_type_map.items():
      yield name, type_
  
  def _get_error_message(self, value):
    error_message = f'unrecognized type "{value}"'
    if self._description:
      error_message += f'; are you sure this is a {self._description}?'
    
    return error_message


SETTING_TYPES = _TypeMap(description='setting type')
"""Mapping of `setting.Setting` subclass names to `setting.Setting` subclasses.

The names are a more human-readable alternative to `setting.Setting` subclass 
names and are used as strings when saving or loading setting data from a 
persistent source.
"""

SETTING_GUI_TYPES = _TypeMap(description='setting GUI type')
"""Mapping of `setting.Presenter` subclass names to `setting.Presenter`
subclasses.

The names are a more human-readable alternative to `setting.Presenter` 
subclass names and are used as strings when saving or loading setting data 
from a persistent source.
"""

GOBJECT_TYPES_AND_SETTING_TYPES = collections.defaultdict(list)
"""Mapping of `GObject.GType` instances, representing GIMP POB argument types,
to `setting.Setting` subclasses.

This mapping is automatically generated from `setting.Setting` subclasses based
on their allowed PDB types.

Be aware that this mapping is incomplete - for example, it does not contain
enumerated types (GObject types derived from `GObject.GEnum`) or array types
(e.g. `Gimp.FloatArray`). If you need to obtain a setting type for all supported
GObject types, use `get_setting_type_from_gobject_type()`.
"""


class SettingMeta(type):
  """Metaclass for the `setting.Setting` class and its subclasses.
  
  The metaclass is responsible for the following:

  * Creating a mapping of `setting.Setting` subclasses and human-readable
    names for easier specification of the `'type'` field when creating settings
    via `setting.Group.add()`.

  * Tracking names and values of arguments passed to instantiation of a setting.
    The names and values are then passed to `setting.Setting.to_dict()` to allow
    persisting the setting with the arguments it was instantiated with.

  * Ensuring that `setting.Setting` classes documented as abstract cannot be
    initialized (`TypeError` is raised on `setting.Setting.__init__()`).
  """
  
  def __new__(mcls, name, bases, namespace):
    _handle_abstract_attribute(namespace)
    
    _set_init_wrapper(mcls, namespace)
    
    cls = super().__new__(mcls, name, bases, namespace)
    
    _register_type_and_aliases(namespace, cls, name, SETTING_TYPES, 'Setting')

    _update_gobject_types(namespace, cls, GOBJECT_TYPES_AND_SETTING_TYPES)
    
    return cls
  
  @staticmethod
  def _get_init_wrapper(orig_init):
    
    @functools.wraps(orig_init)
    def init_wrapper(self, *args, **kwargs):
      if getattr(self, '_ABSTRACT', False):
        raise TypeError(f'cannot initialize abstract setting class "{type(self).__qualname__}"')
      
      # This check prevents a parent class' `__init__()` from overriding the
      # contents of `_dict_on_init`, which may have different arguments.
      if not hasattr(self, '_dict_on_init'):
        if inspect.getfullargspec(orig_init).varargs is not None:
          raise TypeError(
            ('__init__ in Setting subclasses cannot accept variable positional arguments'
             f' (found in "{type(self).__qualname__}")'))

        self._dict_on_init = {}

        # Exclude `self` as the first argument
        arg_names = inspect.getfullargspec(orig_init).args[1:]
        for arg_name, arg in zip(arg_names, args):
          self._dict_on_init[arg_name] = arg

        self._dict_on_init.update(kwargs)
      
      orig_init(self, *args, **kwargs)
    
    return init_wrapper


class GroupMeta(type):
  """Metaclass for the `setting.Group` class.
  
  The metaclass is responsible for the following:
  
  * Tracking names and values of arguments passed to instantiation of a group.
    The names and values are then passed to `setting.Group.to_dict()` to allow
    persisting the group with the arguments it was instantiated with.
  """
  
  def __new__(mcls, name, bases, namespace):
    _set_init_wrapper(mcls, namespace)
    
    cls = super(GroupMeta, mcls).__new__(mcls, name, bases, namespace)
    
    return cls
  
  @staticmethod
  def _get_init_wrapper(orig_init):
    
    @functools.wraps(orig_init)
    def init_wrapper(self, *args, **kwargs):
      # This check prevents a parent class' `__init__()` from overriding the
      # contents of `_dict_on_init`, which may have different arguments.
      if not hasattr(self, '_dict_on_init'):
        if inspect.getfullargspec(orig_init).varargs is not None:
          raise TypeError('Group.__init__() cannot accept variable positional arguments')

        self._dict_on_init = {}

        # Exclude `self` as the first argument
        arg_names = inspect.getfullargspec(orig_init).args[1:]
        for arg_name, arg in zip(arg_names, args):
          self._dict_on_init[arg_name] = arg

        self._dict_on_init.update(kwargs)
      
      orig_init(self, *args, **kwargs)
    
    return init_wrapper


class PresenterMeta(type):
  """Metaclass for the `setting.Presenter` class and its subclasses.
  
  The metaclass is responsible for the following:
  
  * Creating a mapping of `setting.Presenter` subclasses and human-readable
    names for easier specification of the ``gui_type`` field when creating
    settings via `setting.Group.add()`.
  
  * Ensuring that `setting.Presenter` classes documented as abstract cannot be
    initialized (`TypeError` is raised on `__init__()`).
  """
  
  def __new__(mcls, name, bases, namespace):
    _handle_abstract_attribute(namespace)
    
    _set_init_wrapper(mcls, namespace)
    
    cls = super(PresenterMeta, mcls).__new__(mcls, name, bases, namespace)
    
    _register_type_and_aliases(namespace, cls, name, SETTING_GUI_TYPES, 'Presenter')
    
    return cls
  
  @staticmethod
  def _get_init_wrapper(orig_init):
    
    @functools.wraps(orig_init)
    def init_wrapper(self, *args, **kwargs):
      if getattr(self, '_ABSTRACT', False):
        raise TypeError(f'cannot initialize abstract presenter class "{type(self).__qualname__}"')
      
      orig_init(self, *args, **kwargs)
    
    return init_wrapper


# noinspection PyProtectedMember
def _set_init_wrapper(mcls, namespace):
  # Only wrap `__init__` if the (sub)class defines or overrides it.
  # Otherwise, the argument list of `__init__` for a subclass would be
  # overridden the parent class' `__init__` argument list.
  if '__init__' in namespace:
    namespace['__init__'] = mcls._get_init_wrapper(namespace['__init__'])


def _handle_abstract_attribute(namespace):
  if '_ABSTRACT' not in namespace:
    namespace['_ABSTRACT'] = False


# noinspection PyProtectedMember
def _register_type_and_aliases(namespace, cls, type_name, type_map, base_class_name):
  human_readable_name = _get_human_readable_class_name(type_name, base_class_name)
  
  if human_readable_name not in type_map._name_to_type_map:
    if not namespace['_ABSTRACT']:
      type_map._name_to_type_map[human_readable_name] = cls
      type_map._type_to_names_map[cls].append(human_readable_name)
      
      if '_ALIASES' in namespace:
        for alias in namespace['_ALIASES']:
          if alias not in type_map._name_to_type_map:
            type_map._name_to_type_map[alias] = cls
          else:
            raise TypeError(
              f'alias "{alias}" matches a {base_class_name} class name or is already specified')
          
          type_map._type_to_names_map[cls].append(alias)
  else:
    raise TypeError(
      (f'Setting subclass with the name "{cls.__qualname__}"'
       f' already exists ({type_map._name_to_type_map[human_readable_name]})'))


def _get_human_readable_class_name(name, suffix_to_strip=None):
  processed_name = name
  
  if suffix_to_strip and processed_name.endswith(suffix_to_strip):
    processed_name = processed_name[:-len(suffix_to_strip)]
  
  # Converts the class name in CamelCase to snake_case.
  # Source: https://stackoverflow.com/a/1176023
  processed_name = re.sub(r'(?<!^)(?=[A-Z])', '_', processed_name).lower()
  
  return processed_name


def _update_gobject_types(namespace, cls, gobject_and_setting_types):
  if '_ALLOWED_PDB_TYPES' in namespace:
    for pdb_type in namespace['_ALLOWED_PDB_TYPES']:
      if isinstance(pdb_type, GObject.GType):
        gobject_type = pdb_type
      elif hasattr(pdb_type, '__gtype__'):
        gobject_type = pdb_type.__gtype__
      else:
        raise TypeError(
          f'PDB type "{pdb_type}" for Setting subclass {cls} is not valid,'
          ' it must be a GObject.GObject subclass or a GType instance')

      gobject_and_setting_types[gobject_type].append(cls)
