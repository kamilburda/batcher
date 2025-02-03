"""Management of version numbers (particularly incrementing)."""

from __future__ import annotations

import re
from typing import Optional


class Version:
  """Class for holding and incrementing a version."""

  def __init__(
        self,
        major: Optional[int] = None,
        minor: Optional[int] = None,
        patch: Optional[int] = None,
        prerelease: Optional[str] = None,
        prerelease_patch: Optional[int] = None):
    self.major = major
    self.minor = minor
    self.patch = patch
    self.prerelease = prerelease
    self.prerelease_patch = prerelease_patch
  
  def __str__(self):
    version_str = [f'{self.major}.{self.minor}']
    
    if self.patch is not None:
      version_str.append(f'.{self.patch}')
    
    if self.prerelease is not None:
      version_str.append(f'-{self.prerelease}')
      if self.prerelease_patch is not None:
        version_str.append(f'.{self.prerelease_patch}')
    
    return ''.join(version_str)
  
  def __repr__(self):
    class_ = type(self).__qualname__
    prerelease = f'"{self.prerelease}"' if self.prerelease is not None else self.prerelease
    return (
      f'{class_}({self.major}, {self.minor}, {self.patch}, {prerelease}, {self.prerelease_patch})')
  
  def __lt__(self, other_version):
    this_version_main_components = self._get_main_components_tuple(self)
    other_version_main_components = self._get_main_components_tuple(other_version)
    
    if this_version_main_components < other_version_main_components:
      return True
    elif this_version_main_components > other_version_main_components:
      return False
    else:
      if self.prerelease is not None and other_version.prerelease is None:
        return True
      elif self.prerelease is not None and other_version.prerelease is not None:
        if self.prerelease < other_version.prerelease:
          return True
        elif self.prerelease > other_version.prerelease:
          return False
        else:
          return (
            self._get_default_number(self.prerelease_patch)
            < self._get_default_number(other_version.prerelease_patch))
      else:
        return False
  
  def __le__(self, other_version):
    return self.__lt__(other_version) or self.__eq__(other_version)
  
  def __eq__(self, other_version):
    return (
      (self._get_main_components_tuple(self)
       == self._get_main_components_tuple(other_version))
      and self.prerelease == other_version.prerelease
      and (self._get_default_number(self.prerelease_patch)
           == self._get_default_number(other_version.prerelease_patch)))
  
  def __ne__(self, other_version):
    return not self.__eq__(other_version)
  
  def __gt__(self, other_version):
    return not self.__le__(other_version)
  
  def __ge__(self, other_version):
    return not self.__lt__(other_version)
  
  def increment(self, component_to_increment: str, prerelease: Optional[str] = None):
    """Increments the version.
    
    ``component_to_increment`` can be ``'major'``, ``'minor'`` or
    ``'patch'``. Given the format ``X.Y.Z``, ``'major'`` increments ``X``,
    ``'minor'`` increments ``Y`` and ``'patch'`` increments ``Z``. If the
    ``patch`` attribute is ``None`` and ``'patch'`` is specified, ``'1'``
    will be assigned (e.g. ``'3.3'`` becomes ``'3.3.1'``).
    
    If the ``prerelease`` string is not ``None`` and non-empty,
    the pre-release is appended. For example, ``'3.3'`` with ``'major'``
    component and ``'alpha'`` as the pre-release string becomes ``'4.0-alpha'``.
    
    If the version already has the same pre-release, a number to the
    pre-release is appended (e.g. ``'4.0-alpha'`` becomes ``'4.0-alpha.2'``).
    
    If the version already has a different pre-release (lexically earlier than
    ``prerelease``), replace the existing pre-release with ``prerelease`` (e.g.
    ``'4.0-alpha'`` with the ``'beta'`` pre-release becomes ``'4.0-beta'``).
    
    Raises:
      ValueError:
        * Value of ``component_to_increment`` is not valid.
        * The specified ``prerelease`` contains non-alphanumeric characters or
          is lexically earlier than the existing ``prerelease`` attribute.
    """
    available_components_to_increment = ['major', 'minor', 'patch', 'release']

    if component_to_increment not in available_components_to_increment:
      raise ValueError(f'invalid version component "{component_to_increment}"')
    
    if prerelease:
      if not re.search(r'^[a-zA-Z0-9]+$', prerelease):
        raise ValueError(f'invalid pre-release format "{prerelease}"')
      
      if self.prerelease is not None and prerelease < self.prerelease:
        raise ValueError(
          f'the specified pre-release "{prerelease}" is lexically earlier than'
          f' the existing pre-release "{self.prerelease}"')

    if component_to_increment == 'release':
      if prerelease:
        raise ValueError('cannot specify prerelease if the increment is "release"')

      if not self.prerelease:
        raise ValueError('if the increment is "release", the existing version must be a prerelease')
    
    if not prerelease:
      prerelease = None
    
    def increment_major():
      self.major += 1
      self.minor = 0
      self.patch = None
    
    def increment_minor():
      self.minor += 1
      self.patch = None
    
    def increment_patch():
      if self.patch is None:
        self.patch = 0
      self.patch += 1

    def increment_release():
      pass

    def clear_prerelease():
      self.prerelease = None
      self.prerelease_patch = None
    
    def set_new_prerelease():
      self.prerelease = prerelease
      self.prerelease_patch = None
    
    def increment_prerelease():
      if self.prerelease_patch is None:
        self.prerelease_patch = 1
      self.prerelease_patch += 1
    
    if component_to_increment == 'major':
      increment_component_func = increment_major
    elif component_to_increment == 'minor':
      increment_component_func = increment_minor
    elif component_to_increment == 'patch':
      increment_component_func = increment_patch
    elif component_to_increment == 'release':
      increment_component_func = increment_release
    else:
      raise ValueError((
        'increment can only be one of the following:'
        f' {", ".join(available_components_to_increment)}'))

    if prerelease is None:
      increment_component_func()
      clear_prerelease()
    else:
      if self.prerelease is None:
        increment_component_func()
        set_new_prerelease()
      else:
        if prerelease == self.prerelease:
          increment_prerelease()
        else:
          set_new_prerelease()
  
  @classmethod
  def parse(cls, version_str: str) -> Version:
    """Parses the specified string and returns a ``Version`` instance.
    
    Raises:
      InvalidVersionFormatError: ``version_str`` does not have a valid format.
      TypeError: ``version_str`` is not a string.
    """
    if not isinstance(version_str, str):
      raise TypeError('version string must be a string type')

    ver = Version()
    cls._fill_version_components(ver, version_str)
    return ver
  
  @classmethod
  def _fill_version_components(cls, version_obj, version_str):
    version_str_components = version_str.split('-')
    
    if len(version_str_components) > 2:
      raise InvalidVersionFormatError
    
    cls._set_main_version_components(version_obj, version_str_components[0])
    
    if len(version_str_components) == 2:
      cls._set_prerelease_version_components(version_obj, version_str_components[1])
  
  @classmethod
  def _set_main_version_components(cls, version_obj, main_str_components):
    match = re.search(r'^([0-9]+?)\.([0-9]+?)$', main_str_components)
    
    if match is None:
      match = re.search(r'^([0-9]+?)\.([0-9]+?)\.([1-9][0-9]*)$', main_str_components)
      if match is None:
        raise InvalidVersionFormatError
    
    match_groups = match.groups()
    version_obj.major = int(match_groups[0])
    version_obj.minor = int(match_groups[1])
    if len(match_groups) == 3:
      version_obj.patch = int(match_groups[2])
  
  @classmethod
  def _set_prerelease_version_components(cls, version_obj, prerelease_str_components):
    match = re.search(r'^([a-zA-Z0-9]+?)$', prerelease_str_components)
    
    if match is None:
      match = re.search(
        r'^([a-zA-Z0-9]+?)\.([2-9]|[1-9][0-9]+)$', prerelease_str_components)
      if match is None:
        raise InvalidVersionFormatError
    
    match_groups = match.groups()
    version_obj.prerelease = match_groups[0]
    if len(match_groups) == 2:
      version_obj.prerelease_patch = int(match_groups[1])
  
  @staticmethod
  def _get_main_components_tuple(ver):
    return tuple(
      number if number is not None else -1
      for number in [ver.major, ver.minor, ver.patch])
  
  @staticmethod
  def _get_default_number(component):
    return component if component is not None else -1


class InvalidVersionFormatError(Exception):
  pass
