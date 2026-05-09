"""Built-in "G'MIC Filter" action."""

from src import builtin_commands_common
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


def _on_after_add_gmic_filter_action(_actions, action, _orig_action_dict, _settings):
  builtin_commands_common.set_up_display_name_change_for_command(
    _set_display_name_for_gmic_filter,
    action['arguments/command'],
    action,
  )


def _set_display_name_for_gmic_filter(gmic_command_setting, action):
  if gmic_command_setting.value:
    filter_name = gmic_command_setting.value.strip().split(' ')[0]
    action['display_name'].set_value(_("G'MIC Filter: {}").format(filter_name))
  else:
    action['display_name'].set_value(_("G'MIC Filter"))


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
  'after_add_handler': _on_after_add_gmic_filter_action,
}
