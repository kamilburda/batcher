"""Class that groups settings for easier setting creation and management."""

from __future__ import annotations

from collections.abc import Iterable
import inspect
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Union

from .. import utils as pgutils

from . import meta as meta_
from . import persistor as persistor_
from . import settings as settings_
from . import utils as utils_

__all__ = [
  'Group',
  'create_groups',
  'GroupWalkCallbacks',
]


class Group(utils_.SettingParentMixin, utils_.SettingEventsMixin, metaclass=meta_.GroupMeta):
  """Class grouping related plug-in settings (`setting.Setting` instances).

  `Group`s are a convenient way to manipulate multiple settings at once, such as
  loading, saving, or modifying setting attributes. Additionally, `Group` makes
  use of specific values from the `setting.Setting.tag` attribute to skip
  iterating or processing particular settings.

  Groups can be organized in a hierarchy, i.e. `Group` instances can be nested.
  """
  
  def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        setting_attributes: Optional[Dict[str, Any]] = None,
        recurse_setting_attributes: bool = True,
  ):
    utils_.SettingParentMixin.__init__(self)
    utils_.SettingEventsMixin.__init__(self)
    
    utils_.check_setting_name(name)
    self._name = name
    
    self._display_name = utils_.get_processed_display_name(display_name, self._name)
    self._description = utils_.get_processed_description(description, self._display_name)
    self._tags = set(tags) if tags is not None else set()
    self._setting_attributes = setting_attributes
    self._recurse_setting_attributes = recurse_setting_attributes

    # We rely on the ordered nature of Python dictionaries.
    self._settings = {}

    self._setting_list = []
    
    # Used in `_next()`
    self._settings_iterator = None
  
  @property
  def name(self) -> str:
    """A string that identifies the group.

    The name must be unique among all settings or groups within a parent group.
    """
    return self._name
  
  @property
  def display_name(self) -> str:
    """Group name in a human-readable format."""
    return self._display_name
  
  @property
  def description(self) -> str:
    """A more detailed description of the group.

    By default, the description is derived from `display_name`. In that case,
    any underscores are removed when deriving the description.
    """
    return self._description
  
  @property
  def tags(self) -> Set[str]:
    """A mutable set of arbitrary tags attached to the setting.

    Tags can be used to e.g. ignore loading, saving or iterating over an entire
    nested group.
    """
    return self._tags
  
  @property
  def setting_attributes(self) -> Dict[str, Any]:
    """Dictionary of (setting attribute, value) pairs to assign to each new
    setting created in the group via `add()`.

    These attributes are not applied to already created settings that are
    later added to the group via `add()`.

    Attributes in individual settings override these attributes.
    """
    # Return a copy to prevent modification.
    return dict(self._setting_attributes) if self._setting_attributes is not None else None
  
  @property
  def recurse_setting_attributes(self) -> bool:
    """If ``True``, `setting_attributes` is recursively applied to child
    settings of any depth. If ``False``, `setting_attributes` will only be
    applied to immediate child settings.

    If ``True`` and a child group defines its own `setting_attributes`,
    it will override its parent's `setting_attributes`.
    """
    return self._recurse_setting_attributes
  
  def __str__(self) -> str:
    return pgutils.stringify_object(self, self.name)
  
  def __repr__(self) -> str:
    return pgutils.reprify_object(self, self.name)
  
  def __getitem__(self, setting_name_or_path: str) -> Union[settings_.Setting, Group]:
    """Returns a setting or group given its name or full path.
    
    If a setting is inside a nested group, you can access the setting as
    follows:
      
      settings['main']['file_extension']
    
    As a more compact alternative, you may specify a setting path:
    
      settings['main/file_extension']
    
    If the name or path does not exist, `KeyError` is raised.
    """
    if utils_.SETTING_PATH_SEPARATOR in setting_name_or_path:
      return self._get_setting_from_path(setting_name_or_path)
    else:
      try:
        return self._settings[setting_name_or_path]
      except KeyError:
        raise KeyError(f'"{setting_name_or_path}" not found in group "{self.name}"')
  
  def __contains__(self, setting_name_or_path: str) -> bool:
    """Returns ``True`` if a setting or group given its name or full path exists
    within this group, ``False`` otherwise.

    For more information on the full path, see `__getitem__()`.
    """
    if utils_.SETTING_PATH_SEPARATOR in setting_name_or_path:
      try:
        self._get_setting_from_path(setting_name_or_path)
      except KeyError:
        return False
      else:
        return True
    else:
      return setting_name_or_path in self._settings
  
  def _get_setting_from_path(self, setting_path):
    setting_path_components = setting_path.split(utils_.SETTING_PATH_SEPARATOR)
    current_group = self
    for group_name in setting_path_components[:-1]:
      if group_name in current_group:
        current_group = current_group._settings[group_name]
      else:
        raise KeyError(f'group "{group_name}" in path "{setting_path}" does not exist')
    
    try:
      setting = current_group[setting_path_components[-1]]
    except KeyError:
      raise KeyError(f'setting "{setting_path_components[-1]}" not found in path "{setting_path}"')

    return setting
  
  def __iter__(self) -> Generator[Union[settings_.Setting, Group], None, None]:
    """Iterates over child settings and groups.
    
    This method does not iterate over nested groups. Use `walk()` in that case.
    
    By default, the children are iterated in the order they were created or
    added into the group. The order of children can be modified via `reorder()`.
    """
    for setting in self._setting_list:
      yield setting
  
  def __len__(self) -> int:
    return len(self._settings)
  
  def __reversed__(self):
    return reversed(self._setting_list)
  
  def get_path(self, relative_path_group: Optional[str] = None) -> str:
    """Returns the full path of this group.

    This is a wrapper method for `setting.utils.get_setting_path()`. Consult
    the method for more information.
    """
    return utils_.get_setting_path(self, relative_path_group)
  
  def add(self, settings_groups_or_dicts, uniquify_name=False):
    """Adds settings and groups to this group.

    `settings_groups_or_dicts` is a list or list-like that can contain
    existing `setting.Setting` instances, `Group` instances or dictionaries
    representing `setting.Setting` instances to be created.
    
    The order of items in `settings_groups_or_dicts` corresponds to the order
    in which the items are iterated.

    If `settings_groups_or_dicts` is a dictionary, it must contain (attribute
    name, value) pairs. ``attribute name`` is a string that
    represents an argument passed when instantiating the setting. The
    following attributes must always be specified:
    * ``'type'``: Type of the `setting.Setting` instance to instantiate.
    * ``'name'``: Name of the `setting.Setting` instance. The name must not
      contain forward slashes (``'/'``) which are used to access settings as
      paths.
    
    For more attributes, check the documentation of `setting.Setting` and its
    subclasses. Some ``setting.Setting`` subclasses may require specifying
    additional attributes (corresponding to positional parameters to
    `__init__()` in the respective subclasses).
    
    Multiple settings with the same name and in different nested groups are
    possible. Each such setting can be accessed like any other:
    
      settings['main/file_extension']
      settings['advanced/file_extension']
    
    Settings created from dictionaries are by default assigned setting
    attributes specified during the initialization of this class via
    `setting_attributes`. These attributes can be overridden by attributes in
    individual settings.

    If ``uniquify_name`` is ``True``, then the ``name`` attribute is made unique
    within the group. Otherwise, `ValueError` is raised if a setting with the
    same name already exists in the group.
    """
    for setting in settings_groups_or_dicts:
      if isinstance(setting, (settings_.Setting, Group)):
        setting = self._add_setting(setting, uniquify_name)
      else:
        setting = self._create_setting(setting, uniquify_name)
      
      self._set_as_parent_for_setting(setting)
  
  def _add_setting(self, setting, uniquify_name):
    if setting.name in self._settings:
      if uniquify_name:
        setting.uniquify_name(self)
      else:
        raise ValueError(f'{setting} already exists in {self}')
    
    if setting == self:
      raise ValueError(f'cannot add {setting} as a child of itself')
    
    self._settings[setting.name] = setting
    self._setting_list.append(setting)
    
    return setting
  
  def _create_setting(self, setting_data, uniquify_name):
    try:
      setting_type = setting_data['type']
    except KeyError:
      raise TypeError(self._get_missing_required_attributes_message(['type']))
    
    setting_type = meta_.process_setting_type(setting_type)
    
    # Do not modify the original `setting_data` in case it is expected to be
    # reused.
    setting_data_copy = {key: setting_data[key] for key in setting_data if key != 'type'}
    
    try:
      setting_data_copy['name']
    except KeyError:
      raise TypeError(self._get_missing_required_attributes_message(['name']))
    
    if utils_.SETTING_PATH_SEPARATOR in setting_data_copy['name']:
      raise ValueError(
        (f'setting name "{setting_data_copy["name"]}" must not contain'
         f' path separator "{utils_.SETTING_PATH_SEPARATOR}"'))
    
    if setting_data_copy['name'] in self._settings:
      if uniquify_name:
        setting_data_copy['name'] = utils_.get_unique_setting_name(setting_data_copy['name'], self)
      else:
        raise ValueError(f'setting "{setting_data_copy["name"]}" already exists')
    
    for setting_attribute, setting_attribute_value in self._get_setting_attributes().items():
      if setting_attribute not in setting_data_copy:
        setting_data_copy[setting_attribute] = setting_attribute_value
    
    setting = self._instantiate_setting(setting_type, setting_data_copy)
    
    return setting
  
  def _get_setting_attributes(self):
    setting_attributes = self._setting_attributes
    
    if setting_attributes is None:
      for group_or_parent in reversed(self.parents):
        if not group_or_parent.recurse_setting_attributes:
          break
        
        if group_or_parent.setting_attributes is not None:
          setting_attributes = group_or_parent.setting_attributes
          break
    
    if setting_attributes is None:
      setting_attributes = {}
    
    return setting_attributes
  
  def _instantiate_setting(self, setting_type, setting_data_copy):
    try:
      setting = setting_type(**setting_data_copy)
    except TypeError as e:
      missing_required_arguments = self._get_missing_required_arguments(
        setting_type, setting_data_copy)
      if missing_required_arguments:
        message = self._get_missing_required_attributes_message(missing_required_arguments)
      else:
        message = str(e)
      raise TypeError(message)
    
    self._settings[setting_data_copy['name']] = setting
    self._setting_list.append(setting)
    
    return setting
  
  def _get_missing_required_arguments(self, setting_type, setting_data):
    required_arg_names = self._get_required_argument_names(setting_type.__init__)
    return [arg_name for arg_name in required_arg_names if arg_name not in setting_data]
  
  @staticmethod
  def _get_required_argument_names(func):
    arg_spec = inspect.getfullargspec(func)
    arg_default_values = arg_spec[3] if arg_spec[3] is not None else []
    num_required_args = len(arg_spec[0]) - len(arg_default_values)
    
    required_args = arg_spec[0][0:num_required_args]
    if required_args[0] == 'self':
      del required_args[0]
    
    return required_args
  
  @staticmethod
  def _get_missing_required_attributes_message(attribute_names):
    return f'missing the following required setting attributes: {", ".join(attribute_names)}'
  
  def get_value(self, setting_name_or_path: str, default_value=None):
    """Returns the value of the setting specified by its name or path.

    If the setting does not exist, ``default_value`` is returned instead.
    """
    try:
      setting = self[setting_name_or_path]
    except KeyError:
      return default_value
    else:
      return setting.value
  
  def get_attributes(self, setting_attributes: List[str]) -> Dict[str, Any]:
    """Returns a dictionary of ``(setting_path.attribute_name, value)`` pairs
    given a list of setting attribute names.

    If the ``attribute_name`` part is omitted in a list item, the setting value
    is returned (i.e. `setting.Setting.value`).
    
    If any attribute does not exist, `AttributeError` is raised. If any
    setting does not exist, `KeyError` is raised. If the key has more than
    one separator for attributes (`setting.utils.SETTING_ATTRIBUTE_SEPARATOR`),
    `ValueError` is raised.
    
    Example:

      group.get_attributes([
        'main/file_extension',
        'main/file_extension.display_name'])
    
    returns

      {
        'main/file_extension': 'png',
        'main/file_extension.display_name': 'File Extension'
      }
    """
    setting_attributes_and_values = {}
    
    for setting_path_and_attribute in setting_attributes:
      setting_path, attribute_name = self._get_setting_path_and_attribute_name(
        setting_path_and_attribute)
      
      value = getattr(self[setting_path], attribute_name)
      setting_attributes_and_values[setting_path_and_attribute] = value
    
    return setting_attributes_and_values

  @staticmethod
  def _get_setting_path_and_attribute_name(setting_path_and_attribute):
    parts = setting_path_and_attribute.split(utils_.SETTING_ATTRIBUTE_SEPARATOR)
    if len(parts) == 1:
      setting_path = setting_path_and_attribute
      attribute_name = 'value'
    elif len(parts) == 2:
      setting_path, attribute_name = parts
    else:
      raise ValueError(
        (f'"{setting_path_and_attribute}" cannot have more than'
         f' one "{utils_.SETTING_ATTRIBUTE_SEPARATOR}" character'))

    return setting_path, attribute_name
  
  def get_values(self) -> Dict[str, Any]:
    """Returns a dictionary of ``(setting name, value)`` pairs for all settings
    and nested groups of any depth.

    The order of key-value pairs corresponds to the iteration order within the
    group.
    """
    return {setting.get_path('root'): setting.value for setting in self.walk()}
  
  def set_values(self, settings_and_values: Dict[str, Any]):
    """Sets values for multiple settings at once specified via a dictionary of
    `(setting name, value)` pairs.
    
    If any setting does not exist, `KeyError` is raised.

    Example:
      group.set_values({
        'main/file_extension': 'png',
        'main/output_directory': '/sample/directory',
      })
    """
    for setting_name, value in settings_and_values.items():
      self[setting_name].set_value(value)
  
  def reorder(self, setting_name: str, new_position: int):
    """Reorders a child setting to the new position.
    
    ``setting_name`` is the name of the child setting.
    
    A negative position functions as an n-th to last position (-1 for last, -2
    for second to last, etc.).

    If ``setting_name`` does not match any child setting, `ValueError` is
    raised.
    """
    try:
      setting = self._settings[setting_name]
    except KeyError:
      raise KeyError(f'setting "{setting_name}" not found')
    
    self._setting_list.remove(setting)
    
    if new_position < 0:
      new_position = max(len(self._setting_list) + new_position + 1, 0)
    
    self._setting_list.insert(new_position, setting)
  
  def remove(self, setting_names: Iterable[str]):
    """Removes child settings from the group specified by their names.
    
    If any setting does not exist, `KeyError` is raised.
    """
    for setting_name in setting_names:
      if setting_name in self._settings:
        setting = self._settings[setting_name]
        del self._settings[setting_name]
        self._setting_list.remove(setting)
      else:
        raise KeyError(f'setting "{setting_name}" not found')
  
  def walk(
        self,
        include_setting_func: Optional[Callable] = None,
        include_groups: bool = False,
        include_if_parent_skipped: bool = False,
        walk_callbacks: Optional[GroupWalkCallbacks] = None,
  ) -> Generator[Union[settings_.Setting, Group], None, None]:
    """Recursively iterates over all child settings and optionally groups.

    The method uses the pre-order traversal.

    ``include_setting_func`` is a function that should return ``True`` if a
    child should be yielded and ``False`` if a child should be skipped. The
    function must accept one positional parameter - the current setting or
    group. If ``include_setting_func`` is ``None``, all child settings and
    groups are returned.

    If ``include_groups`` is ``True``, child groups are also yielded.

    If ``include_if_parent_skipped`` is ``False``, settings or groups within
    a parent group not matching ``include_setting_func`` are skipped. If
    ``True``, settings or groups within a parent group are yielded regardless
    of whether the parent groups matches ``include_setting_func`` or not.
    
    ``walk_callbacks`` is a `GroupWalkCallbacks` instance that invokes
    additional commands during the walk of the group. By default,
    the callbacks do nothing. For more information, see the
    `GroupWalkCallbacks` class.
    """
    if include_setting_func is None:
      include_setting_func = pgutils.create_empty_func(return_value=True)
    
    if walk_callbacks is None:
      walk_callbacks = GroupWalkCallbacks()
    
    groups = [self]
    
    while groups:
      try:
        setting_or_group = groups[0]._next()
      except StopIteration:
        if groups[0] != self:
          walk_callbacks.on_end_group_walk(groups[0])
        
        groups.pop(0)
        continue
      
      if isinstance(setting_or_group, Group):
        if include_setting_func(setting_or_group):
          groups.insert(0, setting_or_group)
          
          if include_groups:
            walk_callbacks.on_visit_group(setting_or_group)
            yield setting_or_group
        elif include_if_parent_skipped:
          groups.insert(0, setting_or_group)
          continue
        else:
          continue
      else:
        if include_setting_func(setting_or_group):
          walk_callbacks.on_visit_setting(setting_or_group)
          yield setting_or_group
        else:
          continue
  
  def _next(self):
    """Returns the next item when iterating the settings. Used by `walk()`."""
    if self._settings_iterator is None:
      self._settings_iterator = iter(self._setting_list)
    
    try:
      next_item = next(self._settings_iterator)
    except StopIteration:
      self._settings_iterator = None
      raise StopIteration
    else:
      return next_item
  
  def reset(self):
    """Resets all child settings recursively.

    Child settings with the ``'ignore_reset'`` tag are ignored.
    """
    def _has_ignore_reset_tag(setting):
      return 'ignore_reset' not in setting.tags
    
    for setting in self.walk(include_setting_func=_has_ignore_reset_tag):
      setting.reset()
  
  def load(self, *args, **kwargs):
    """Loads child settings from the specified source(s).
    
    See `setting.persistor.Persistor.load()` for information about parameters.
    
    If the `tags` property in this group contains ``'ignore_load'``,
    this method will have no effect.
    """
    return persistor_.Persistor.load([self], *args, **kwargs)
  
  def save(self, *args, **kwargs):
    """Saves values of settings to the specified source(s).
    
    See `setting.persistor.Persistor.save()` for information about parameters.

    If the `tags` property in this group contains ``'ignore_save'``,
    this method will have no effect.
    """
    return persistor_.Persistor.save([self], *args, **kwargs)
  
  def initialize_gui(self, custom_gui: Optional[Dict[str, List]] = None):
    """Initializes GUI for all child settings.

    Child settings with the ``'ignore_initialize_gui'`` tag are ignored.
    
    Settings that are not provided with a readily available GUI can have
    their GUI initialized using the ``custom_gui`` dictionary. ``custom_gui``
    contains (setting name, list of arguments to `setting.Setting.set_gui()`)
    key-value pairs. For more information about parameters in the list,
    see `setting.Setting.set_gui()`.
    
    Example:
    
      file_extension_entry = Gtk.Entry()
      ...
      main_settings.initialize_gui({
        'file_extension': [
          setting.SETTING_GUI_TYPES.entry, file_extension_entry]
        ...
      })
    """
    def _should_not_ignore(setting):
      return 'ignore_initialize_gui' not in setting.tags
    
    if custom_gui is None:
      custom_gui = {}
    
    for setting in self.walk(include_setting_func=_should_not_ignore):
      if setting.get_path('root') not in custom_gui:
        setting.set_gui()
      else:
        set_gui_args = custom_gui[setting.get_path('root')]
        setting.set_gui(*set_gui_args)
  
  def apply_gui_values_to_settings(self, force: bool = False):
    """Applies GUI widget values, entered by the user, to settings.

    Child settings with the ``'ignore_apply_gui_value_to_setting'`` tag are
    ignored.
    
    If ``force`` is ``False``, this method will have no effect on settings
    with automatic GUI-to-setting value updating. Otherwise, each setting
    will be updated regardless of whether the automatic GUI-to-setting update
    is enabled or not. Passing ``force=True`` is useful if some GUI widgets
    are internally assigned a valid value on instantiation while the
    corresponding settings retain their own value.
    """
    def _should_not_ignore(setting_):
      return 'ignore_apply_gui_value_to_setting' not in setting_.tags
    
    for setting in self.walk(include_setting_func=_should_not_ignore):
      setting.gui.update_setting_value()
  
  def to_dict(self):
    """Returns a dictionary representing the group, appropriate for saving it
    (e.g. via `Group.save()`).
    
    The dictionary contains (attribute name, attribute value) pairs.
    Specifically, the dictionary contains:
    * the `name` property
    * all keyword argument names and values passed to `__init__()` that were
      used to instantiate the group.
    
    The list of child settings is not included in the returned dictionary.
    """
    group_dict = dict(self._dict_on_init)
    
    if 'tags' in group_dict:
      group_dict['tags'] = list(group_dict['tags'])
    
    if 'name' not in group_dict:
      # Make sure `name` is always included (which it should be anyway as it is
      # a required parameter in `__init__()`).
      group_dict['name'] = self.name
    
    return group_dict


def create_groups(setting_dict: Dict) -> Group:
  """Creates a hierarchy of groups (`Group` instances) from a dictionary
  containing attributes for the groups.

  This function simplifies adding groups via `Group.add()`.

  Groups are specified under the ``'groups'`` key as a list of dictionaries.

  Only ``'groups'`` and the names of parameters for `Group.__init__()` are valid
  keys for ``setting_dict``. Other keys raise `TypeError`.

  Example:
    settings = create_groups({
      'name': 'main',
      'groups': [
        {
          'name': 'procedures'
        },
        {
          'name': 'constraints'
        }
      ]
    })
  """
  group_dicts = setting_dict.pop('groups', None)

  if group_dicts is None:
    group_dicts = []

  group = Group(**setting_dict)

  for group_dict in group_dicts:
    group.add([create_groups(group_dict)])

  return group


class GroupWalkCallbacks:
  """Callbacks invoked within `Group.walk()`.

  By default, the callbacks do nothing.
  
  `on_visit_setting` is called before the current `setting.Setting` instance
  is yielded. `on_visit_group` is called before the current `Group` instance
  is yielded. `on_end_group_walk` is called after all children of the current
  `Group` instance are visited.
  """
  
  def __init__(self):
    self.on_visit_setting = pgutils.empty_func
    self.on_visit_group = pgutils.empty_func
    self.on_end_group_walk = pgutils.empty_func
