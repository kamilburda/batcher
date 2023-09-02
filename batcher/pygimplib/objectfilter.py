"""Class to filter objects according to the specified rules."""

from __future__ import annotations

import collections
from collections.abc import Generator, Iterable
import contextlib
import itertools
from typing import Callable, Dict, List, Optional, Union, Tuple


_Rule = collections.namedtuple(
  '_Rule', ['function', 'args', 'kwargs', 'name', 'id'])


class ObjectFilter:
  """Class containing a list of rules determining whether an object matches
  given rules.
  
  A rule can be a callable (function) or a nested ``ObjectFilter`` instance with
  its own rules and a different match type.
  """
  
  _MATCH_TYPES = MATCH_ALL, MATCH_ANY = (0, 1)
  
  _rule_id_counter = itertools.count(start=1)
  
  def __init__(self, match_type: int = MATCH_ALL, name: str = ''):
    self._match_type = match_type
    self._name = name
    
    # Key: rule/nested filter ID
    # Value: `_Rule` or `ObjectFilter` instance
    self._rules = {}
  
  @property
  def match_type(self) -> int:
    """Match type.

    Possible values:
    * MATCH_ALL - For ``is_match()`` to return ``True``, an object must match
      all rules.
    * MATCH_ANY - For ``is_match()`` to return ``True``, an object must match
      at least one rule.
    """
    return self._match_type
  
  @property
  def name(self) -> str:
    """Name of the filter.

    The name does not have to be unique and can be used to manipulate
    multiple rules (functions or nested filters) with the same name at once
    (e.g. by removing them with ``remove()``).
    """
    return self._name
  
  def __bool__(self) -> bool:
    """Returns ``True`` if the filter is not empty, ``False`` otherwise."""
    return bool(self._rules)
  
  def __contains__(self, rule_id: int) -> bool:
    """Returns ``True`` if the filter contains a rule specified by its ID,
    ``False`` otherwise.

    ``rule_id`` is returned by `add()`.
    """
    return rule_id in self._rules
  
  def __getitem__(self, rule_id: int) -> Union[_Rule, ObjectFilter]:
    """Returns the specified ``_Rule`` instance or a nested filter given the ID.
    
    ``rule_id`` is returned by `add()`.
    
    Raises:
      KeyError: ``rule_id`` is not found in the filter.
    """
    return self._rules[rule_id]
  
  def __len__(self):
    """Returns the number of rules in the filter.
    
    Rules within nested filters do not count.
    """
    return len(self._rules)
  
  def add(
        self,
        func_or_filter: Union[Callable, ObjectFilter],
        args: Optional[Iterable] = None,
        kwargs: Optional[Dict] = None,
        name: str = '',
  ) -> Union[_Rule, int]:
    """Adds the specified callable or a nested filter as a rule to the filter.
    
    Args:
      func_or_filter:
        A callable (function) or a nested filter to filter objects by. If a
        callable, it must have at least one argument - the object to match
        (used by `is_match()`). args:
      args:
        Arguments for ``func_or_filter`` if it is a callable.
      kwargs:
        Keyword arguments for `func_or_filter` if it is a callable.
      name:
        Name of the added rule if `func_or_filter` is a callable. If this an
        empty string, the ``__name__`` attribute is used if it exists. ``name``
        does not have to be unique and can be used to manipulate multiple rules
        with the same name at once (e.g. by removing them with ``remove()``).
    
    Returns:
      If ``func_or_filter`` is a callable, a ``_Rule`` instance is returned,
      containing the input parameters and a unique identifier. If
      ``func_or_filter`` is a nested filter, a unique identifier is returned.
      The identifier can be used to e.g. access (via ``__getitem__``) or
      remove a rule.
    
    Raises:
      TypeError: ``func_or_filter`` is not a callable or an ``ObjectFilter``
        instance.
    """
    args = args if args is not None else ()
    kwargs = kwargs if kwargs is not None else {}
    
    rule_id = self._get_rule_id()
    
    if isinstance(func_or_filter, ObjectFilter):
      self._rules[rule_id] = func_or_filter
      
      return rule_id
    elif callable(func_or_filter):
      func = func_or_filter
      rule = _Rule(
        func,
        args,
        kwargs,
        self._get_rule_name_for_func(func, name),
        rule_id)
      self._rules[rule_id] = rule
      
      return rule
    else:
      raise TypeError(f'"{func_or_filter}": not a callable or ObjectFilter instance')
  
  @staticmethod
  def _get_rule_name_for_func(func, name):
    if not name and hasattr(func, '__name__'):
      return func.__name__
    else:
      return name
  
  def _get_rule_id(self):
    return next(self._rule_id_counter)
  
  def remove(
        self,
        rule_id: Optional[int] = None,
        name: Optional[str] = None,
        func_or_filter: Optional[Union[Callable, ObjectFilter]] = None,
        count: int = 0,
  ) -> Tuple[List[Union[Callable, ObjectFilter]], List[int]]:
    """Removes rules from the filter matching one or more criteria specified as
    arguments.

    Args:
      rule_id: Rule ID as returned by `add()`.
      name: See `find()`.
      func_or_filter: See `find()`.
      count: See `find()`.
    
    Raises:
      ValueError: If ``rule_id``, ``name`` and ``func_or_filter`` are all
        ``None``.
    
    Returns:
      A list of removed rules (callables or nested filters) and a list of the
      corresponding IDs.
    """
    if rule_id is None and name is None and func_or_filter is None:
      raise ValueError('at least one removal criterion must be specified')
    
    matching_ids = []
    
    if name is not None or func_or_filter is not None:
      matching_ids = self.find(name=name, func_or_filter=func_or_filter, count=count)
    
    if rule_id in self and rule_id not in matching_ids:
      matching_ids.append(rule_id)
    
    matching_rules = [self._rules.pop(id_) for id_ in matching_ids]
    
    return matching_rules, matching_ids

  @contextlib.contextmanager
  def add_temp(
        self,
        func_or_filter: Union[Callable, ObjectFilter],
        args: Optional[Iterable] = None,
        kwargs: Optional[Dict] = None,
        name: str = '',
  ) -> Generator[Union[_Rule, int], None, None]:
    """Temporarily adds a callable or nested filter as a rule to the filter.
    
    Use this function as a context manager:
    
      with filter.add_temp(func_or_filter) as rule_or_id:
        # do stuff
    
    See `add()` for further information about parameters and exceptions.
    """
    args = args if args is not None else ()
    kwargs = kwargs if kwargs is not None else {}
    
    rule_or_id = self.add(func_or_filter, args, kwargs, name)
    
    try:
      yield rule_or_id
    finally:
      if isinstance(rule_or_id, _Rule):
        self.remove(rule_or_id.id)
      else:
        self.remove(rule_or_id)
  
  @contextlib.contextmanager
  def remove_temp(
        self,
        rule_id: Optional[int] = None,
        name: Optional[str] = None,
        func_or_filter: Optional[Union[Callable, ObjectFilter]] = None,
        count: int = 0,
  ) -> Generator[Tuple[List[Union[Callable, ObjectFilter]], List[int]], None, None]:
    """Temporarily removes rules from the filter matching one or more criteria.
    
    Use as a context manager:
      
      rule_id = filter.add(...)
      
      with filter.remove_temp(rule_id=rule_id) as rules_and_ids:
        # do stuff
    
    The identifiers (IDs) of the temporarily removed rules are preserved once
    added back.
    
    See `remove()` for further information about parameters and exceptions.
    """
    matching_rules, matching_ids = self.remove(
      rule_id=rule_id, name=name, func_or_filter=func_or_filter, count=count)
    
    try:
      yield matching_rules, matching_ids
    finally:
      for rule_id, rule in zip(matching_ids, matching_rules):
        self._rules[rule_id] = rule
  
  def is_match(self, obj) -> bool:
    """Returns ``True`` if the specified object matches the rules, ``False``
    otherwise.
    
    If ``match_type`` is ``MATCH_ALL``, ``True`` is returned if the object
    matches all rules and all top-level nested filters return ``True``.
    Otherwise, ``False`` is returned.
    
    If ``match_type`` is ``MATCH_ANY``, ``True`` is returned if the object
    matches at least one rule or at least one top-level nested filter returns
    ``True``. Otherwise, ``False`` is returned.
    
    If no rules are specified, ``True`` is returned.
    """
    if not self._rules:
      return True
    
    if self._match_type == self.MATCH_ALL:
      return self._is_match_all(obj)
    elif self._match_type == self.MATCH_ANY:
      return self._is_match_any(obj)
  
  def _is_match_all(self, obj):
    is_match = True
    
    for value in self._rules.values():
      if isinstance(value, ObjectFilter):
        is_match = is_match and value.is_match(obj)
      else:
        rule = value
        is_match = is_match and rule.function(obj, *rule.args, **rule.kwargs)
      if not is_match:
        break
    
    return is_match
  
  def _is_match_any(self, obj):
    is_match = False
    
    for value in self._rules.values():
      if isinstance(value, ObjectFilter):
        is_match = is_match or value.is_match(obj)
      else:
        rule = value
        is_match = is_match or rule.function(obj, *rule.args, **rule.kwargs)
      if is_match:
        break
    
    return is_match
  
  def find(
        self,
        name: Optional[str] = None,
        func_or_filter: Optional[Union[Callable, ObjectFilter]] = None,
        count: int = 0,
  ) -> List[int]:
    """Finds rule IDs matching the specified name or object (callable or nested
    filter).
    
    Both ``name`` and ``func_or_filter`` can be specified at the same time.
    
    Args:
      name:
        Name of the added rule (callable or nested filter).
      func_or_filter:
        Callable (e.g. a function) or a nested ``ObjectFilter`` instance.
      count:
        If 0, return all occurrences. If greater than 0, return up to the
        first ``count`` occurrences. If less than 0, return up to the last
        ``count`` occurrences.
    
    Returns:
      List of IDs of matching ``_Rule`` instances or nested filters, or an empty
      list if there is no match.
    
    Raises:
      ValueError: If both ``name`` and ``func_or_filter`` are ``None``.
    """
    if name is None and func_or_filter is None:
      raise ValueError('at least a name or object must be specified')

    # We are exploiting the ordered nature of Python dictionaries to list IDs
    # in the order they were found.
    matching_rule_ids = {}
    
    for rule_id, rule_or_filter in self._rules.items():
      if name is not None:
        if rule_or_filter.name == name:
          matching_rule_ids[rule_id] = None
      
      if func_or_filter is not None:
        if isinstance(rule_or_filter, _Rule):
          if rule_or_filter.function == func_or_filter:
            matching_rule_ids[rule_id] = None
        else:
          if rule_or_filter == func_or_filter:
            matching_rule_ids[rule_id] = None
    
    matching_rule_ids = list(matching_rule_ids)
    
    if count == 0:
      return matching_rule_ids
    elif count > 0:
      return matching_rule_ids[:count]
    else:
      return matching_rule_ids[count:]
  
  def list_rules(self) -> Dict[int, _Rule]:
    """Returns a dictionary of (rule ID, rule) pairs.

    A copy is returned to prevent modifying the original dictionary.
    """
    return dict(self._rules)
  
  def reset(self):
    """Resets the filter, removing all rules.

    The match type is preserved.
    """
    self._rules.clear()

