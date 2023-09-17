"""Utility functions for the ``test_itemtree`` module."""

from . import stubs_gimp


def parse_layers(tree_string: str) -> stubs_gimp.Image:
  """Parses layer names from a given string and returns an image stub containing
  layer stubs.
  
  The string must contain layer names separated by lines and curly braces (each
  on a separate line). Leading or trailing spaces in each line in the string are
  truncated.
  """
  image = stubs_gimp.Image()
  
  tree_string = tree_string.strip()
  lines = tree_string.splitlines(False)
  
  num_lines = len(lines)
  parents = [image]
  current_parent = image
  
  for i in range(num_lines):
    current_symbol = lines[i].strip()
    
    layer = None
    
    if current_symbol.endswith(' {'):
      layer = stubs_gimp.Layer(current_symbol.rstrip(' {'), is_group=True)
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
      layer = stubs_gimp.Layer(current_symbol)
      if isinstance(current_parent, stubs_gimp.Image):
        current_parent.layers.append(layer)
      else:
        current_parent.children.append(layer)
    
    if layer is not None:
      layer.parent = current_parent
  
  return image
