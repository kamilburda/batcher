"""Built-in "G'MIC Filter" action."""

from src.procedure_groups import *

from src.pypdb import pdb


__all__ = [
  'gmic_filter',
]


def gmic_filter(batcher, layers, command):
  if len(layers) == 1:
    input_ = 1
  else:
    input_ = 2

  pdb.plug_in_gmic_qt(
    image=batcher.current_image,
    drawables=layers,
    input=input_,
    output=0,
    command=command,
  )


GMIC_FILTER_DICT = {
  'name': 'gmic_filter',
  'function': gmic_filter,
  'display_name': _("G'MIC Filter"),
  'description': _(
    "Applies a G'MIC filter non-interactively.\n\n"
    "Select a filter in G'MIC and press Ctrl+C, or click the copy button. "
    "Then paste the text into the \"{}\" field."
  ).format(_('Command')),
  'display_options_on_create': True,
  'additional_tags': ALL_PROCEDURE_GROUPS,
  'arguments': [
    {
      'type': 'placeholder_layer_array',
      'name': 'layers',
      'element_type': 'layer',
      'default_value': 'current_layer_for_array',
      'display_name': _('Layers'),
    },
    {
      'type': 'string',
      'name': 'command',
      'default_value': '',
      'display_name': _('Command'),
    },
  ],
  'available': lambda _command_dict: 'plug_in_gmic_qt' in pdb,
}
