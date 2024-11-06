"""Utility functions for the ``test_itemtree`` module."""

from typing import Dict, Tuple, Union

from . import stubs_gimp


def parse_layers(
      tree_string: str,
) -> Tuple[stubs_gimp.Image, Dict[Tuple[str, ...], Union[int, Tuple[int, str]]]]:
  """Parses layer names from a given string and returns an image stub containing
  layer stubs, along with a path-to-ID mapping for easier testing.

  ``tree_string`` must contain layer names separated by lines and curly
  braces (each on a separate line). Leading or trailing spaces in each line
  in the string are truncated.
  """
  image = stubs_gimp.Image()
  layer_path_to_id_mapping = {}

  tree_string = tree_string.strip()
  lines = tree_string.splitlines(False)

  parents = [image]
  current_parent = image

  for i in range(len(lines)):
    current_symbol = lines[i].strip()

    if current_symbol.endswith(' {'):
      layer = stubs_gimp.GroupLayer(name=current_symbol.rstrip(' {'))
      if current_parent != image:
        layer.parent = current_parent

      layer_path_to_id_mapping[_get_layer_path(layer)] = layer.get_id()

      if isinstance(current_parent, stubs_gimp.Image):
        current_parent.layers.append(layer)
      else:
        current_parent.children.append(layer)

      current_parent = layer
      parents.append(current_parent)
    elif current_symbol == '}':
      parents.pop()
      current_parent = parents[-1]
    else:
      layer = stubs_gimp.Layer(name=current_symbol)
      if current_parent != image:
        layer.parent = current_parent

      layer_path_to_id_mapping[_get_layer_path(layer)] = layer.get_id()

      if isinstance(current_parent, stubs_gimp.Image):
        current_parent.layers.append(layer)
      else:
        current_parent.children.append(layer)
  
  return image, layer_path_to_id_mapping


def _get_layer_path(layer):
  path = []

  parent = layer.parent

  while parent is not None:
    path.insert(0, parent.get_name())

    parent = parent.parent

  path.append(layer.get_name())

  return tuple(path)
