# -*- coding: utf-8 -*-

"""Loading and saving settings."""

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *
import future.utils

import abc
import ast
import collections
import io
import os
import types

try:
  import cPickle as pickle
except ImportError:
  import pickle

try:
  import json
except ImportError:
  _json_module_found = False
else:
  _json_module_found = True

import gimp
import gimpenums
import gimpshelf

from .. import constants as pgconstants
from .. import utils as pgutils

from . import group as group_
from . import settings as settings_
from . import utils as utils_

from ._sources_errors import *

__all__ = [
  'Source',
  'GimpShelfSource',
  'GimpParasiteSource',
  'PickleFileSource',
  'JsonFileSource',
]


class Source(future.utils.with_metaclass(abc.ABCMeta, object)):
  """Abstract class for reading and writing settings to a source.
  
  Attributes:
  
  * `source_name` - A unique identifier to distinguish entries from different
    GIMP plug-ins or procedures.
  
  * `source_type` - If `'persistent'`, this indicates that the setting source
    should store settings permanently. If `'session'`, this indicates that the
    source should store settings within a single GIMP session (i.e. until the
    currently running GIMP instance is closed).
  """
  
  _MAX_LENGTH_OF_OBJECT_AS_STRING_ON_ERROR_OUTPUT = 512
  
  def __init__(self, source_name, source_type):
    self.source_name = source_name
    self.source_type = source_type
    
    self._settings_not_found = []
  
  @property
  def settings_not_found(self):
    return list(self._settings_not_found)
  
  def read(self, settings_or_groups):
    """Reads setting attributes from data and assigns them to existing settings
    specified in the `settings_or_groups` iterable, or creates settings within
    groups specified in `settings_or_groups`.
    
    If a setting value from the source is invalid, the setting will be reset to
    its default value.
    
    All settings that were not found in the source will be stored in the
    `settings_not_found` property. This property is reset on each call to
    `read()`.
    
    Raises:
    
    * `SourceNotFoundError` - Could not find the source.
    
    * `SourceInvalidFormatError` - Existing data in the source have an invalid
      format. This could happen if the source was edited manually.
    """
    data = self.read_data_from_source()
    if data is None:
      raise SourceNotFoundError(
        _('Could not find setting source "{}".').format(self.source_name))
    
    self._settings_not_found = []
    
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
          self._update_group(setting_or_group, setting_dict, setting_path, data_dict)
        else:
          raise TypeError('settings_or_groups must contain only Setting or Group instances')
      else:
        self._settings_not_found.append(setting_or_group)
  
  def _create_data_dict(self, data):
    # Creates a (setting/group path, dict/list representing the setting/group) mapping.
    # The entries in the mapping are listed in the depth-first order.
    data_dict = collections.OrderedDict()
    data_dict[None] = data
    
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
  
  def _update_group(self, group, group_dict, group_path, data_dict):
    matching_dicts = collections.OrderedDict(
      (path, dict_) for path, dict_ in data_dict.items()
      if path is not None and path.startswith(group_path) and path != group_path)
    
    matching_child_settings_or_groups = collections.OrderedDict(
      (child.get_path(), child) for child in group.walk(include_groups=True))
    matching_child_settings_or_groups[group_path] = group
    
    # `matching_dicts` is assumed to contain children in depth-first order,
    # which simplifies the algorithm quite a bit.
    for path, dict_ in matching_dicts.items():
      if 'value' in dict_:  # dict_ is a `Setting`
        if path in matching_child_settings_or_groups:
          self._update_setting(matching_child_settings_or_groups[path], dict_)
        else:
          self._add_setting_to_parent_group(dict_, path, matching_child_settings_or_groups)
      else:  # dict_ is a `Group`
        if path in matching_child_settings_or_groups:
          # Nothing to do. Group attributes will not be updated since setting
          # attributes are also not updated.
          pass
        else:
          self._add_group_to_parent_group(dict_, path, matching_child_settings_or_groups)
  
  def _update_setting(self, setting, setting_dict):
    try:
      setting.set_value(setting_dict['value'])
    except settings_.SettingValueError:
      setting.reset()
  
  def _add_setting_to_parent_group(self, dict_, path, matching_child_settings_or_groups):
    parent_path = path.rsplit(utils_.SETTING_PATH_SEPARATOR, 1)[0]
    
    # If the assertion fails, `matching_dicts` does not contain children
    # in depth-first order for some reason, which should not happen.
    assert parent_path in matching_child_settings_or_groups
    
    parent_group = matching_child_settings_or_groups[parent_path]
    
    child_setting_dict = dict(dict_)
    child_setting_dict.pop('value', None)
    
    parent_group.add([child_setting_dict])
    
    child_setting = parent_group[dict_['name']]
    
    if 'value' in dict_:
      self._update_setting(child_setting, dict_)
    
    matching_child_settings_or_groups[child_setting.get_path()] = child_setting
  
  def _add_group_to_parent_group(self, dict_, path, matching_child_settings_or_groups):
    parent_path = path.rsplit(utils_.SETTING_PATH_SEPARATOR, 1)[0]
    
    # If the assertion fails, `matching_dicts` does not contain children
    # in depth-first order for some reason, which should not happen.
    assert parent_path in matching_child_settings_or_groups
    
    parent_group = matching_child_settings_or_groups[parent_path]
    
    child_group_kwargs = dict(dict_)
    # Child settings will be created separately.
    child_group_kwargs.pop('settings')
    child_group = group_.Group(**child_group_kwargs)
    
    parent_group.add([child_group])
    
    matching_child_settings_or_groups[child_group.get_path()] = child_group
  
  def write(self, settings_or_groups):
    """Writes data representing settings specified in the `settings_or_groups`
    iterable.
    
    Settings in the source but not specified in `settings_or_groups` are kept
    intact.
    
    Raises:
    
    * `SourceInvalidFormatError` - Existing data in the source have an invalid
      format. This could happen if the source was edited manually.
    """
    data = self.read_data_from_source()
    if data is None:
      data = []
    
    self._update_data(settings_or_groups, data)
    
    self.write_data_to_source(data)
  
  def _update_data(self, settings_or_groups, data):
    for setting_or_group in settings_or_groups:
      # Create all parent groups if they do not exist.
      # `current_list` at the end of the loop will hold the immediate parent of
      # `setting_or_group`.
      current_list = data
      for parent in setting_or_group.parents:
        parent_dict = self._find_dict(current_list, parent)[0]
        
        if parent_dict is None:
          parent_dict = {'name': parent.name, 'settings': []}
          current_list.append(parent_dict)
        
        current_list = parent_dict['settings']
      
      if isinstance(setting_or_group, settings_.Setting):
        self._setting_to_data(current_list, setting_or_group)
      elif isinstance(setting_or_group, group_.Group):
        self._group_to_data(current_list, setting_or_group)
      else:
        raise TypeError('settings_or_groups must contain only Setting or Group instances')
  
  def _setting_to_data(self, group_list, setting):
    setting_dict, index = self._find_dict(group_list, setting)
    
    if setting_dict is not None:
      # Overwrite the original setting dict
      group_list[index] = setting.to_dict(source_type=self.source_type)
    else:
      group_list.append(setting.to_dict(source_type=self.source_type))
  
  def _group_to_data(self, group_list, group):
    settings_or_groups_and_dicts = [(group, group_list)]
    
    while settings_or_groups_and_dicts:
      setting_or_group, parent_list = settings_or_groups_and_dicts.pop(0)
      
      if isinstance(setting_or_group, settings_.Setting):
        self._setting_to_data(parent_list, setting_or_group)
      elif isinstance(setting_or_group, group_.Group):
        current_group_dict = self._find_dict(parent_list, setting_or_group)[0]
        
        if current_group_dict is None:
          current_group_dict = {'name': setting_or_group.name, 'settings': []}
          parent_list.append(current_group_dict)
        
        for child_setting_or_group in reversed(setting_or_group):
          settings_or_groups_and_dicts.insert(
            0, (child_setting_or_group, current_group_dict['settings']))
      else:
        raise TypeError('only Setting or Group instances are allowed as the first element')
  
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
    if (not isinstance(list_, collections.Iterable)
        or isinstance(list_, types.StringTypes)
        or isinstance(list_, dict)):
      raise SourceInvalidFormatError(
        'Error while parsing data from a source: Not a list: {}'.format(
          self._truncate_str(list_)))
  
  def _check_if_is_dict(self, dict_):
    if not isinstance(dict_, dict):
      raise SourceInvalidFormatError(
        'Error while parsing data from a source: Not a dictionary: {}'.format(
          self._truncate_str(dict_)))
  
  def _check_if_dict_has_required_keys(self, dict_):
    if 'name' not in dict_:
      raise SourceInvalidFormatError(
        'Error while parsing data from a source: every dictionary must always contain "name" key')
    
    if (('value' not in dict_ and 'settings' not in dict_)
        or ('value' in dict_ and 'settings' in dict_)):
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: every dictionary must always contain'
         ' either "value" or "settings" key'))
  
  def _check_if_setting_dict_has_value(self, setting_dict, setting_path):
    if 'value' not in setting_dict:
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: "value" not found in dictionary'
         ' representing setting "{}"').format(setting_path))
  
  def _check_if_setting_dict_has_settings(self, setting_dict, setting_path):
    if 'settings' not in setting_dict:
      raise SourceInvalidFormatError(
        ('Error while parsing data from a source: "settings" not found in dictionary'
         ' representing setting group "{}"').format(setting_path))
  
  @staticmethod
  def _truncate_str(obj, max_length=_MAX_LENGTH_OF_OBJECT_AS_STRING_ON_ERROR_OUTPUT):
    str_ = str(obj)
    if len(str_) > max_length:
      str_ = str_[:max_length] + '... (truncated)'
    
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
    """Returns `True` if the source contains data, `False` otherwise."""
    pass
  
  @abc.abstractmethod
  def read_data_from_source(self):
    """Reads data representing settings from the source.
    
    Usually you do not need to call this method. Use `read()` instead which
    assigns values to existing settings or creates settings dynamically from the
    data.
    
    If the source does not exist, `None` is returned.
    
    Raises:
    
    * `SourceInvalidFormatError` - Data could not be read due to being corrupt.
    """
    pass
  
  @abc.abstractmethod
  def write_data_to_source(self, data):
    """Writes data representing settings to the source.
    
    The entire setting source is overwritten by the specified data.
    Settings not specified thus will be removed.
    
    Usually you do not need to call this method. Use `write()` instead which
    creates an appropriate persistent representation of the settings that can
    later be loaded via `read()`.
    """
    pass


class GimpShelfSource(Source):
  """Class for reading and writing settings to the GIMP shelf.
  
  This class is appropriate to maintain settings within a single GIMP session
  as the GIMP shelf is reset when closing GIMP.
  """
  
  def __init__(self, source_name, source_type='session'):
    super().__init__(source_name, source_type)
  
  def clear(self):
    gimpshelf.shelf[self._get_key()] = None
  
  def has_data(self):
    return (
      gimpshelf.shelf.has_key(self._get_key())
      and gimpshelf.shelf[self._get_key()] is not None)
  
  def read_data_from_source(self):
    try:
      return gimpshelf.shelf[self._get_key()]
    except KeyError:
      return None
    except Exception:
      raise SourceInvalidFormatError(
        _('Session-wide settings for this plug-in may be corrupt.\n'
          'To fix this, save the settings again or reset them.'))
  
  def write_data_to_source(self, data):
    gimpshelf.shelf[self._get_key()] = data
  
  def _get_key(self):
    return pgutils.safe_encode_gimp(self.source_name)


class GimpParasiteSource(Source):
  """Class reading and writing settings to the `parasiterc` file maintained by
  GIMP.
  
  This class is useful as a persistent source (i.e. permanent storage) of
  settings.
  """
  
  def __init__(self, source_name, source_type='persistent'):
    super().__init__(source_name, source_type)
    
    self._parasite_filepath = os.path.join(gimp.directory, 'parasiterc')
  
  def clear(self):
    if gimp.parasite_find(self.source_name) is None:
      return
    
    gimp.parasite_detach(self.source_name)
  
  def has_data(self):
    return gimp.parasite_find(self.source_name) is not None
  
  def read_data_from_source(self):
    parasite = gimp.parasite_find(self.source_name)
    if parasite is None:
      return None
    
    try:
      data = pickle.loads(parasite.data)
    except Exception:
      raise SourceInvalidFormatError(
        _('Settings for this plug-in stored in "{}" may be corrupt.'
          ' This could happen if the file was edited manually.'
          '\nTo fix this, save the settings again or reset them.').format(
            self._parasite_filepath))
    
    return data
  
  def write_data_to_source(self, data):
    gimp.parasite_attach(
      gimp.Parasite(self.source_name, gimpenums.PARASITE_PERSISTENT, pickle.dumps(data)))


class PickleFileSource(Source):
  """Class reading and writing settings to a file, formatted using the Python
  `pickle` module.
  
  This class is useful as a persistent source (i.e. permanent storage) of
  settings. This class is appropriate to use when saving settings to a file path
  chosen by the user.
  """
  
  _SOURCE_NAME_CONTENTS_SEPARATOR = ' '
  
  def __init__(self, source_name, filepath, source_type='persistent'):
    super().__init__(source_name, source_type)
    
    self._filepath = filepath
  
  @property
  def filepath(self):
    return self._filepath
  
  def clear(self):
    all_data = self.read_all_data()
    if all_data is not None and self.source_name in all_data:
      del all_data[self.source_name]
      
      self.write_all_data(all_data)
  
  def has_data(self):
    """Returns `True` if the source contains data and the data have a valid
    format, `'invalid_format'` if the source contains some data, but the data
    have an invalid format, and `False` otherwise.
    
    `'invalid_format'` represents an ambiguous value since there is no way to
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
      return self._get_settings_from_pickled_data(all_data[self.source_name])
    else:
      return None
  
  def write_data_to_source(self, data):
    raw_data = self._pickle_settings(data)
    
    all_data = self.read_all_data()
    if all_data is None:
      all_data = collections.OrderedDict([(self.source_name, raw_data)])
    else:
      all_data[self.source_name] = raw_data
    
    self.write_all_data(all_data)
  
  def read_all_data(self):
    """Reads the contents of the entire file into a dictionary of
    (source name, contents) pairs.
    
    The dictionary also contains contents from other source names if they exist.
    """
    if not os.path.isfile(self._filepath):
      return None
    
    all_data = collections.OrderedDict()
    
    try:
      with io.open(self._filepath, 'r', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        for line in f:
          split = line.split(self._SOURCE_NAME_CONTENTS_SEPARATOR, 1)
          if len(split) == 2:
            source_name, contents = split
            all_data[source_name] = contents
    except Exception as e:
      raise SourceReadError(str(e))
    else:
      return all_data
  
  def write_all_data(self, all_data):
    """Writes `all_data` into the file, overwriting the entire file contents.
    
    `all_data` is a dictionary of (source name, contents) pairs.
    """
    try:
      with io.open(self._filepath, 'w', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        for source_name, contents in all_data.items():
          f.write(source_name + self._SOURCE_NAME_CONTENTS_SEPARATOR + contents + '\n')
    except Exception as e:
      raise SourceWriteError(str(e))
  
  def _get_settings_from_pickled_data(self, contents):
    try:
      return pickle.loads(ast.literal_eval(contents))
    except Exception as e:
      raise SourceInvalidFormatError(str(e))
  
  def _pickle_settings(self, settings):
    try:
      return repr(pickle.dumps(settings))
    except Exception as e:
      raise SourceInvalidFormatError(str(e))


class JsonFileSource(Source):
  """Class reading and writing settings to a JSON file.
  
  This class is useful as a persistent source (i.e. permanent storage) of
  settings. This class is appropriate to use when saving settings to a file path
  chosen by the user.
  
  Compared to `PickleFileSource`, JSON files are more readable and, if need be,
  easy to modify by hand.
  """
  
  def __init__(self, source_name, filepath, source_type='persistent'):
    if not _json_module_found:
      raise RuntimeError('"json" module not found')
    
    super().__init__(source_name, source_type)
    
    self._filepath = filepath
  
  @property
  def filepath(self):
    return self._filepath
  
  def clear(self):
    all_data = self.read_all_data()
    if all_data is not None and self.source_name in all_data:
      del all_data[self.source_name]
      
      self.write_all_data(all_data)
  
  def has_data(self):
    """Returns `True` if the source contains data and the data have a valid
    format, `'invalid_format'` if the source contains some data, but the data
    have an invalid format, and `False` otherwise.
    
    `'invalid_format'` represents an ambiguous value since there is no way to
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
      all_data = collections.OrderedDict([(self.source_name, data)])
    else:
      all_data[self.source_name] = data
    
    self.write_all_data(all_data)
  
  def read_all_data(self):
    """Reads the contents of the entire file into a dictionary of
    (source name, contents) pairs.
    
    The dictionary also contains contents from other source names if they exist.
    """
    if not os.path.isfile(self._filepath):
      return None
    
    all_data = collections.OrderedDict()
    
    try:
      with io.open(self._filepath, 'r', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        all_data = json.load(f)
    except Exception as e:
      raise SourceReadError(str(e))
    else:
      return all_data
  
  def write_all_data(self, all_data):
    """Writes `all_data` into the file, overwriting the entire file contents.
    
    `all_data` is a dictionary of (source name, contents) pairs.
    """
    try:
      with io.open(self._filepath, 'w', encoding=pgconstants.TEXT_FILE_ENCODING) as f:
        # Workaround for Python 2 code to properly handle Unicode strings
        raw_data = json.dumps(all_data, f, sort_keys=False, indent=4, separators=(',', ': '))
        f.write(unicode(raw_data))
    except Exception as e:
      raise SourceWriteError(str(e))
