"""Utility functions related to the `update` package.

These functions are defined in a separate module so that scripts in the `dev`
package can run without needing to import modules from `gi.repository`. This is
convenient as otherwise one would have to install GIMP and manually add paths
containing `gi.repository` to ``PYTHONPATH``.
"""

import importlib
import pkgutil
import sys

from src import version as version_


HANDLERS_PACKAGE_NAME = '_handlers'
UPDATE_HANDLER_MODULE_PREFIX = 'update_'
UPDATE_HANDLER_MODULE_NEXT_VERSION_SUFFIX = '_next'
UPDATE_HANDLER_FUNC_NAME = 'update'
ASSERT_UPDATE_HANDLER_MODULE_PREFIX = 'assert_update_'
ASSERT_UPDATE_HANDLER_FUNC_NAME = 'assert_contents'


def get_versions_and_functions(
      minimum_version: version_.Version,
      maximum_version: version_.Version,
      package_dirpath: str,
      package_path: str,
      module_prefix: str,
      next_version_suffix: str,
      function_name: str,
      include_next: bool,
      match_minimum_version: bool = False,
):
  functions_and_versions = []
  next_function = None

  for _module_info, module_name, is_package in pkgutil.walk_packages(path=[package_dirpath]):
    if is_package:
      continue

    if module_name.startswith(module_prefix):
      module_path = f'{package_path}.{module_name}'

      if module_name.endswith(next_version_suffix):
        if include_next:
          next_module = importlib.import_module(module_path)
          next_function = getattr(next_module, function_name)
      else:
        try:
          version_from_module = _get_version_from_module_name(module_name, module_prefix)
        except Exception as e:
          print(f'could not parse version from module {module_name}; reason: {e}', file=sys.stderr)
        else:
          if match_minimum_version:
            matches_version = minimum_version <= version_from_module <= maximum_version
          else:
            matches_version = minimum_version < version_from_module <= maximum_version

          if matches_version:
            module = importlib.import_module(module_path)

            functions_and_versions.append((getattr(module, function_name), version_from_module))

  functions_and_versions.sort(key=lambda item: item[1])
  functions = [item[0] for item in functions_and_versions]

  if next_function is not None:
    functions.append(next_function)

  return functions


def _get_version_from_module_name(
      module_name: str,
      module_prefix: str,
) -> version_.Version:
  version_str = module_name[len(module_prefix):]

  version_numbers_and_prerelease_components = version_str.split('__')
  if len(version_numbers_and_prerelease_components) > 1:
    version_numbers_str, prerelease_str = version_numbers_and_prerelease_components[:2]
  else:
    version_numbers_str = version_numbers_and_prerelease_components[0]
    prerelease_str = None

  version_number_components_str = version_numbers_str.split('_')
  major_number = int(version_number_components_str[0])
  minor_number = None
  patch_number = None
  prerelease = None
  prerelease_patch_number = None

  if len(version_number_components_str) == 2:
    minor_number = int(version_number_components_str[1])
  elif len(version_number_components_str) > 2:
    minor_number = int(version_number_components_str[1])
    patch_number = int(version_number_components_str[2])

  if prerelease_str is not None:
    prerelease_components_str = prerelease_str.split('_')
    prerelease = prerelease_components_str[0]

    if len(prerelease_components_str) > 1:
      prerelease_patch_number = int(prerelease_components_str[1])

  return version_.Version(
    major=major_number,
    minor=minor_number,
    patch=patch_number,
    prerelease=prerelease,
    prerelease_patch=prerelease_patch_number,
  )
