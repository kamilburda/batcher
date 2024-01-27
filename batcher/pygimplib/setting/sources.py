"""Loading and saving settings."""

import abc
from collections.abc import Iterable
import json
import os
import pickle
from typing import Any, Dict, List, Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

from .. import constants as pgconstants
from .. import utils as pgutils

from . import group as group_
from . import settings as settings_
from . import utils as utils_

from ._sources_errors import *

__all__ = [
  'Source',
  'GimpParasiteSource',
  'JsonFileSource',
]


class Source(metaclass=abc.ABCMeta):
  """Abstract class for reading and writing settings to a source."""
  
  _IGNORE_LOAD_TAG = 'ignore_load'
  _IGNORE_SAVE_TAG = 'ignore_save'
  
  _MAX_LENGTH_OF_OBJECT_AS_STRING_ON_ERROR_OUTPUT = 512
  
  def __init__(self, source_name: str):
    self.source_name = source_name
    """A unique identifier to distinguish sources from different GIMP plug-ins
    or procedures within a GIMP plug-in."""
    
    self._settings_not_loaded = []
  
  @property
  def settings_not_loaded(self) -> List[Union[settings_.Setting, group_.Group]]:
    """List of all `setting.Setting` and `setting.Group` instances that were not
    loaded.

    "Not loaded" means that such settings or groups were not found in the
    loaded data.

    This property is reset on each call to `read()`.
    """
    return list(self._settings_not_loaded)
  
  def read(self, settings_or_groups: Iterable[Union[settings_.Setting, group_.Group]]):
    """Assigns setting attributes from the source to the specified settings and
    creates any settings missing within the specified groups.
    
    If a setting value from the source is not valid, the setting will be reset
    to its default value.
    
    All settings that were not loaded in the source will be stored in the
    `settings_not_loaded` property. This property is reset on each call to
    `read()`.
    
    The following criteria determine whether a setting or group specified in
    ``setting_or_groups`` is not loaded:
    
    * The setting/group is not found in the source.
    * The setting/group or any of its parent groups contains ``'ignore_load'``
      in its ``tags`` attribute.
    
    Raises:
      SourceNotFoundError:
        Could not find the source having the `source_name` attribute as its
        name.
      SourceInvalidFormatError:
        Existing data in the source have an invalid format. This could happen if
        the source was edited manually.
    """
    data = self.read_data_from_source()
    if data is None:
      raise SourceNotFoundError
    
    self._settings_not_loaded = []
    
    self._update_settings(settings_or_groups, data)
  
  def _update_settings(self, settings_or_groups, data):
    data_dict = self._create_data_dict(data)
    
    for setting_or_group in settings_or_groups:
      setting_path = setting_or_group.get_path()
      
      if setting_path in data_dict:
        setting_dict = data_dict[setting_path]
        
        if isinstance(setting_or_group, settings_.Setting):
          self._check_if_setting_dict_has_value(setting_dict, setting_path)
          self._update_setting(setting_or_group, setting_dict)
        elif isinstance(setting_or_group, group_.Group):
          self._check_if_setting_dict_has_settings(setting_dict, setting_path)
          self._update_group(setting_or_group, setting_path, data_dict)
        else:
          raise TypeError('settings_or_groups must contain only Setting or Group instances')
      else:
        self._settings_not_loaded.append(setting_or_group)
  
  def _create_data_dict(self, data):
    """Creates a (setting/group path, dict/list representing the setting/group)
    mapping.

    The items in the mapping are listed in the depth-first order.
    """
    data_dict = {None: data}

    current_list_and_parents = []
    
    self._check_if_is_list(data)
    
    for dict_ in reversed(data):
      current_list_and_parents.insert(0, (dict_, []))
    
    while current_list_and_parents:
      current_dict, parents = current_list_and_parents.pop(0)
      
      self._check_if_is_dict(current_dict)
      self._check_if_dict_has_required_keys(current_dict)
      
      key = utils_.SETTING_PATH_SEPARATOR.join(parents + [current_dict['name']])
      data_dict[key] = current_dict
      
      if 'settings' in current_dict:
        parents.append(current_dict['name'])
        
        child_list = current_dict['settings']
        
        self._check_if_is_list(child_list)
        
        for child_dict in reversed(child_list):
          current_list_and_parents.insert(0, (child_dict, list(parents)))
    
    return data_dict
  
  def _update_group(self, group, group_path, data_dict):
    if not self._should_group_be_loaded(group):
      return
    
    matching_dicts = self._get_matching_dicts_for_group_path(data_dict, group_path)
    prefixes_to_ignore = set()
    matching_children = self._get_matching_children(
      group, group_path, matching_dicts, prefixes_to_ignore)
    matching_dicts = self._filter_matching_dicts(
      matching_dicts, matching_children, prefixes_to_ignore)
    
    # `matching_dicts` is assumed to contain children in depth-first order,
    # which simplifies the algorithm quite a bit.
    for path, dict_ in matching_dicts.items():
      if 'value' in dict_:  # dict_ is a `Setting`
        if path in matching_children:
          self._check_if_is_setting(matching_children[path], path)
          self._update_setting(matching_children[path], dict_)
        else:
          self._add_setting_to_parent_group(dict_, path, matching_children)
      elif 'settings' in dict_:  # dict_ is a `Group`
        if path in matching_children:
          # Nothing else to do. Group attributes will not be updated since
          # setting attributes are also not updated.
          self._check_if_is_group(matching_children[path], path)
        else:
          self._add_group_to_parent_group(dict_, path, matching_children)
      else:
        raise SourceInvalidFormatError(
          ('Error while parsing data from a source: every dictionary must always contain'
           ' either "value" or "settings" key'))
  
  @staticmethod
  def _get_matching_dicts_for_group_path(data_dict, group_path):
    return {
      path: dict_
      for path, dict_ in data_dict.items()
      if path is not None and path.startswith(group_path) and path != group_path
    }
  
  def _get_matching_children(self, group, group_path, matching_dicts, prefixes_to_ignore):
    matching_children = {}
    
    for child in group.walk(include_groups=True):
      child_path = child.get_path()
      
      if self._IGNORE_LOAD_TAG in child.tags:
        prefixes_to_ignore.add(child_path)
      
      if any(child_path.startswith(prefix) for prefix in prefixes_to_ignore):
        continue
      
      matching_children[child_path] = child
      
      if child_path not in matching_dicts:
        if isinstance(child, group_.Group):
          # Only append empty groups since non-empty groups are further descended.
          if len(child) == 0:
            self._settings_not_loaded.append(child)
        else:
          self._settings_not_loaded.append(child)
    
    matching_children[group_path] = group
    
    return matching_children
  
  def _filter_matching_dicts(self, matching_dicts, matching_children, prefixes_to_ignore):
    filtered_matching_dicts = {}
    
    for path, dict_ in matching_dicts.items():
      if self._IGNORE_LOAD_TAG in dict_.get('tags', []) and path not in matching_children:
        prefixes_to_ignore.add(path)
      
      if any(path.startswith(prefix) for prefix in prefixes_to_ignore):
        continue
      
      filtered_matching_dicts[path] = dict_
    
    return filtered_matching_dicts
  
  def _update_setting(self, setting, setting_dict):
    if not self._should_setting_be_loaded(setting):
      return
    
    setting.set_value(setting_dict['value'])
  
  def _should_setting_be_loaded(self, setting):
    if self._IGNORE_LOAD_TAG in setting.tags:
      return False
    
    return True
  
  def _should_group_be_loaded(self, group):
    return self._IGNORE_LOAD_TAG not in group.tags
  
  def _add_setting_to_parent_group(self, dict_, path, matching_children):
    parent_path = path.rsplit(utils_.SETTING_PATH_SEPARATOR, 1)[0]
    
    # If the assertion fails for some reason, then `matching_dicts` does not
    # contain children in depth-first order, or children of ignored parents are
    # not ignored.
    assert parent_path in matching_children
    
    parent_group = matching_children[parent_path]
    
    child_setting_dict = dict(dict_)
    child_setting_dict.pop('value', None)
    
    parent_group.add([child_setting_dict])
    
    child_setting = parent_group[dict_['name']]
    
    if 'value' in dict_:
      self._update_setting(child_setting, dict_)
    
    matching_children[child_setting.get_path()] = child_setting
  
  @staticmethod
  def _add_group_to_parent_group(dict_, path, matching_children):
    parent_path = path.rsplit(utils_.SETTING_PATH_SEPARATOR, 1)[0]
    
    # If the assertion fails for some reason, then `matching_dicts` does not
    # contain children in depth-first order, or children of ignored parents are
    # not ignored.
    assert parent_path in matching_children
    
    parent_group = matching_children[parent_path]
    
    child_group_kwargs = dict(dict_)
    # Child settings will be created separately.
    child_group_kwargs.pop('settings')
    child_group = group_.Group(**child_group_kwargs)
    
    parent_group.add([child_group])
    
    matching_children[child_group.get_path()] = child_group
  
  def write(self, settings_or_groups: Iterable[Union[settings_.Setting, group_.Group]]):
    """Writes attributes of the specified settings and groups to the source.

    Settings or groups present in the source but not specified in
    ``settings_or_groups`` are kept intact.
    
    Some settings or groups may not be saved. The following criteria
    determine whether a setting is not saved:
    
    * The setting/group or any of its parent groups contains ``'ignore_save'``
      in its ``tags`` attribute.
    
    Raises:
      SourceInvalidFormatError:
        Existing data in the source have an invalid format. This could happen if
        the source was edited manually.
    """
    data = self.read_data_from_source()
    if data is None:
      data = []
    
    self._update_data(settings_or_groups, data)
    
    self.write_data_to_source(data)
  
  def _update_data(self, settings_or_groups, data):
    for setting_or_group in settings_or_groups:
      immediate_parent_of_setting_or_group = self._create_all_parent_groups_if_they_do_not_exist(
        setting_or_group, data)

      if isinstance(setting_or_group, settings_.Setting):
        self._setting_to_data(immediate_parent_of_setting_or_group, setting_or_group)
      elif isinstance(setting_or_group, group_.Group):
        self._group_to_data(immediate_parent_of_setting_or_group, setting_or_group)
      else:
        raise TypeError('settings_or_groups must contain only Setting or Group instances')

  def _create_all_parent_groups_if_they_do_not_exist(self, setting_or_group, data):
    current_list = data
    for parent in setting_or_group.parents:
      parent_dict = self._find_dict(current_list, parent)[0]

      if parent_dict is None:
        parent_dict = dict(settings=[], **parent.to_dict())
        current_list.append(parent_dict)

      current_list = parent_dict['settings']

    immediate_parent_of_setting_or_group = current_list

    return immediate_parent_of_setting_or_group

  def _setting_to_data(self, group_list, setting):
    if not self._should_setting_be_saved(setting):
      return
    
    setting_dict, index = self._find_dict(group_list, setting)
    
    if setting_dict is not None:
      # Overwrite the original setting dict
      group_list[index] = setting.to_dict()
    else:
      group_list.append(setting.to_dict())
  
  def _group_to_data(self, group_list, group):
    if not self._should_group_be_saved(group):
      return
    
    # Clear the group in the source as its child settings may be reordered or
    # removed in the memory.
    self._clear_group_in_data(group, group_list)
    
    settings_or_groups_and_dicts = [(group, group_list)]
    
    while settings_or_groups_and_dicts:
      setting_or_group, parent_list = settings_or_groups_and_dicts.pop(0)
      
      if isinstance(setting_or_group, settings_.Setting):
        self._setting_to_data(parent_list, setting_or_group)
      elif isinstance(setting_or_group, group_.Group):
        if not self._should_group_be_saved(setting_or_group):
          continue
        
        current_group_dict = self._find_dict(parent_list, setting_or_group)[0]
        
        if current_group_dict is None:
          current_group_dict = dict(settings=[], **setting_or_group.to_dict())
          parent_list.append(current_group_dict)
        
        for child_setting_or_group in reversed(setting_or_group):
          settings_or_groups_and_dicts.insert(
            0, (child_setting_or_group, current_group_dict['settings']))
      else:
        raise TypeError('only Setting or Group instances are allowed as the first element')
  
  def _should_setting_be_saved(self, setting):
    if self._IGNORE_SAVE_TAG in setting.tags:
      return False
    
    return True
  
  def _should_group_be_saved(self, group):
    return self._IGNORE_SAVE_TAG not in group.tags
  
  def _clear_group_in_data(self, group, parent_list):
    group_in_parent, index = self._find_dict(parent_list, group)
    
    if group_in_parent is not None:
      parent_list[index]['settings'] = []
  
  def _find_dict(self, data_list, setting_or_group):
    self._check_if_is_list(data_list)
    
    if isinstance(setting_or_group, settings_.Setting):
      key = 'value'
    else:
      key = 'settings'
    
    for i, dict_ in enumerate(data_list):
      self._check_if_is_dict(dict_)
      
      if 'name' in dict_ and dict_['name'] == setting_or_group.name and key in dict_:
        return dict_, i
    
    return None, None
  
  def _check_if_is_list(self, list_):
    if not isinstance(list_, Iterable) or isinstance(list_, str) or isinstance(list_, dict):
      raise SourceInvalidFormatError(
        f'Error while parsing data from a source: Not a list: {self._truncate_str(list_)}')
  
  def _check_if_is_dict(self, dict_):
    if not isinstance(dict_, dict):
      raise SourceInvalidFormatError(
        f'Error while parsing data from a source: Not a dictionary: {self._truncate_str(dict_)}')

  @staticmethod
  def _check_if_dict_has_required_keys(dict_):
    if 'name' not in dict_:
      raise SourceInvalidFormatError(
        'Error while parsing data from a source: every dictionary must always contain "name" key')
    
    if (('value' not in dict_ and 'settings' not in dict_)
        or ('value' in dict_ and 'settings' in dict_)):
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: every dictionary must always contain'
         ' either "value" or "settings" key'))
  
  @staticmethod
  def _check_if_setting_dict_has_value(setting_dict, setting_path):
    if 'value' not in setting_dict:
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: "value" key not found in dictionary'
         f' representing setting "{setting_path}"'))
  
  @staticmethod
  def _check_if_setting_dict_has_settings(setting_dict, setting_path):
    if 'settings' not in setting_dict:
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: "settings" key not found in dictionary'
         f' representing group "{setting_path}"'))
  
  @staticmethod
  def _check_if_is_setting(setting, setting_path):
    if not isinstance(setting, settings_.Setting):
      raise SourceInvalidFormatError(
        f'expected a Setting instance, found Group instead: "{setting_path}"')
  
  @staticmethod
  def _check_if_is_group(group, group_path):
    if not isinstance(group, group_.Group):
      raise SourceInvalidFormatError(
        f'expected a Group instance, found Setting instead: "{group_path}"')
  
  @staticmethod
  def _truncate_str(obj, max_length=_MAX_LENGTH_OF_OBJECT_AS_STRING_ON_ERROR_OUTPUT):
    str_ = str(obj)
    if len(str_) > max_length:
      str_ = f'{str_[:max_length]}... (truncated)'
    
    return str_
  
  @abc.abstractmethod
  def clear(self):
    """Removes all settings from the source.
    
    Settings not belonging to `source_name` are kept intact.
    
    This method is useful if settings are renamed, since the old settings would
    not be removed and would thus lead to bloating the source.
    """
    pass
  
  @abc.abstractmethod
  def has_data(self):
    """Returns ``True`` if the source contains data, ``False`` otherwise."""
    pass
  
  @abc.abstractmethod
  def read_data_from_source(self):
    """Reads data representing settings from the source.
    
    Usually you do not need to call this method. Use `read()` instead which
    assigns values to existing settings or creates settings dynamically from the
    data.
    
    If the source does not exist, ``None`` is returned.
    
    Raises:
      SourceInvalidFormatError:
        Data could not be read due to being corrupt.
    """
    pass
  
  @abc.abstractmethod
  def write_data_to_source(self, data):
    """Writes data representing settings to the source.
    
    The entire setting source is overwritten by the specified data.
    Settings not specified thus will be removed.
    
    Usually you do not need to call this method. Use `write()` instead which
    creates an appropriate representation of the settings that can later be
    loaded via `read()`.
    """
    pass


class GimpParasiteSource(Source):
  """Class reading and writing settings to a persistent source.

  A persistent source stores settings permanently, i.e. the settings are
  retained after ending a GIMP session.

  The ``parasiterc`` file maintained by GIMP is used as the persistent source.
  """
  
  def __init__(self, source_name: str):
    super().__init__(source_name)

    self._parasite_filepath = os.path.join(Gimp.directory(), 'parasiterc')

  @property
  def filepath(self):
    """Path to the file containing saved settings."""
    return self._parasite_filepath

  def clear(self):
    if Gimp.get_parasite(self.source_name) is None:
      return
    
    Gimp.detach_parasite(self.source_name)
  
  def has_data(self):
    return Gimp.get_parasite(self.source_name) is not None
  
  def read_data_from_source(self):
    parasite = Gimp.get_parasite(self.source_name)
    if parasite is None:
      return None

    parasite_data = pgutils.signed_bytes_to_bytes(parasite.get_data())
    try:
      data = pickle.loads(parasite_data)
    except Exception:
      raise SourceInvalidFormatError
    
    return data
  
  def write_data_to_source(self, data):
    Gimp.attach_parasite(
      Gimp.Parasite.new(
        self.source_name,
        Gimp.PARASITE_PERSISTENT,
        pgutils.bytes_to_signed_bytes(pickle.dumps(data))))


class JsonFileSource(Source):
  """Class reading and writing settings to a JSON file.
  
  This class is useful as a persistent source (i.e. permanent storage) of
  settings. This class is appropriate to use when saving settings to a file path
  chosen by the user.
  """
  
  def __init__(self, source_name: str, filepath: str):
    super().__init__(source_name)
    
    self._filepath = filepath
  
  @property
  def filepath(self):
    """Path to the file containing saved settings."""
    return self._filepath
  
  def clear(self):
    all_data = self.read_all_data()
    if all_data is not None and self.source_name in all_data:
      del all_data[self.source_name]
      
      self.write_all_data(all_data)

  def has_data(self) -> Union[bool, str]:
    """Returns ``True`` if the source contains data and the data have a valid
    format, ``'invalid_format'`` if the source contains some data, but the data
    do not have a valid format, and ``False`` otherwise.

    ``'invalid_format'`` represents an ambiguous value since there is no way to
    determine if there are data under `source_name` or not.
    """
    try:
      data = self.read_data_from_source()
    except SourceError:
      return 'invalid_format'
    else:
      return data is not None
  
  def read_data_from_source(self):
    all_data = self.read_all_data()
    if all_data is not None and self.source_name in all_data:
      return all_data[self.source_name]
    else:
      return None
  
  def write_data_to_source(self, data):
    all_data = self.read_all_data()
    if all_data is None:
      all_data = {self.source_name: data}
    else:
      all_data[self.source_name] = data
    
    self.write_all_data(all_data)
  
  def read_all_data(self) -> Union[Dict[str, Any], None]:
    """Reads the contents of the entire file into a dictionary of
    (source name, contents) pairs.

    The dictionary also contains contents from other source names if they exist.

    If the `filepath` property does not point to a valid file, ``None`` is
    returned.
    """
    if not os.path.isfile(self._filepath):
      return None
    
    all_data = {}
    
    try:
      with open(self._filepath, 'r', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        all_data = json.load(f)
    except Exception as e:
      raise SourceReadError from e
    else:
      return all_data
  
  def write_all_data(self, all_data: Dict[str, Any]):
    """Writes ``all_data`` into the file, overwriting the entire file contents.

    ``all_data`` is a dictionary of (source name, contents) pairs.
    """
    try:
      with open(self._filepath, 'w', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        json.dump(all_data, f, indent=4)
    except Exception as e:
      raise SourceWriteError from e
