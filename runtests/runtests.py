#!/usr/bin/env python3

"""Running automated tests.

By default, all modules starting with the `'test_'` prefix will be run.

To run tests in GIMP:

1. Open up the Python-Fu console (Filters -> Python-Fu -> Console).
2. Choose ``Browse...`` and find the ``'plug-in-run-tests'`` procedure.
3. Hit ``Apply``. The procedure call is copied to the console with placeholder
   arguments.
4. Adjust the arguments as needed. The run mode does not matter as the procedure
   is always non-interactive. Make sure to wrap the ``modules`` and
  ``ignored-modules`` arguments in
  ``GObject.Value(GObject.TYPE_STRV, [<module names...>])``, otherwise the
  procedure fails with an error.
5. Run the command.

To repeat the tests, simply call the procedure again.
"""
from typing import List, Optional

import importlib
import inspect
import os
import pkgutil
import sys
import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

PLUGIN_DIRPATH = os.path.dirname(os.path.dirname(os.path.abspath(
  inspect.getfile(inspect.currentframe()))))
if PLUGIN_DIRPATH not in sys.path:
  sys.path.append(PLUGIN_DIRPATH)

from batcher import pygimplib as pg


def plug_in_run_tests(
      procedure: Gimp.Procedure,
      run_mode: Gimp.RunMode,
      config: Gimp.ProcedureConfig):
  run_tests(
    config.get_property('dirpath'),
    config.get_property('prefix'),
    config.get_property('modules'),
    config.get_property('ignored-modules'),
    config.get_property('output-stream'),
  )


def run_tests(
      dirpath: str,
      test_module_name_prefix: str = 'test_',
      modules: Optional[List[str]] = None,
      ignored_modules: Optional[List[str]] = None,
      output_stream: str = 'stderr'):
  """Runs all modules containing tests located in the specified directory path.

  Modules containing tests are considered those that contain the
  ``test_module_name_prefix`` prefix.

  ``ignored_modules`` is a list of prefixes matching test modules or packages
  to ignore.
  
  If ``modules`` is ``None`` or empty, all modules are included, except those
  specified in ``ignored_modules``. If ``modules`` is not ``None``,
  only modules matching the prefixes specified in ``modules`` are included.
  ``ignored_modules`` can be used to exclude submodules in ``modules``.
  
  ``output_stream`` is the name of the stream to print the output to -
  ``'stdout'``, ``'stderr'`` or a file path.
  """
  module_names = []
  
  if not modules:
    modules = []

  if not ignored_modules:
    ignored_modules = []
  
  if not modules:
    should_append = (
      lambda name: not any(name.startswith(ignored_module) for ignored_module in ignored_modules))
  else:
    should_append = (
      lambda name: (
        any(name.startswith(module) for module in modules)
        and not any(name.startswith(ignored_module) for ignored_module in ignored_modules)))

  for importer, module_name, is_package in pkgutil.walk_packages(path=[dirpath]):
    if should_append(module_name):
      if is_package:
        sys.path.append(importer.path)

      module_names.append(module_name)

  stream = _get_output_stream(output_stream)

  for module_name in module_names:
    if module_name.split('.')[-1].startswith(test_module_name_prefix):
      module = importlib.import_module(module_name)
      run_test(module, stream=stream)

  stream.close()


def run_test(module, stream=sys.stderr):
  test_suite = unittest.TestLoader().loadTestsFromModule(module)
  test_runner = unittest.TextTestRunner(stream=stream)
  test_runner.run(test_suite)


def _get_output_stream(stream_or_filepath):
  if hasattr(sys, stream_or_filepath):
    return _Stream(getattr(sys, stream_or_filepath))
  else:
    return open(stream_or_filepath, 'w')
  

class _Stream:
  
  def __init__(self, stream):
    self.stream = stream
  
  def write(self, data):
    self.stream.write(data)
  
  def flush(self):
    if hasattr(self.stream, 'flush'):
      self.stream.flush()
  
  def close(self):
    pass


pg.register_procedure(
  plug_in_run_tests,
  arguments=[
    dict(
      name='run-mode',
      type=Gimp.RunMode,
      default=Gimp.RunMode.NONINTERACTIVE,
      nick='Run mode',
      blurb='The run mode'),
    dict(
      name='dirpath',
      type=str,
      default=PLUGIN_DIRPATH,
      nick='_Directory',
      blurb='Directory path containing test modules'),
    dict(
      name='prefix',
      type=str,
      default='test_',
      nick='_Prefix of test modules',
      blurb='Prefix of test modules'),
    dict(
      name='modules',
      type=GObject.TYPE_STRV,
      default=[],
      nick='Modules to _include',
      blurb='Modules to include'),
    dict(
      name='ignored_modules',
      type=GObject.TYPE_STRV,
      default=[],
      nick='Modules to i_gnore',
      blurb='Modules to ignore'),
    dict(
      name='output_stream',
      type=str,
      default='stderr',
      nick='_Output stream',
      blurb='Output stream or file path to write output to'),
  ],
  documentation=('Runs automated tests in the specified directory path', ''),
)


pg.main()
