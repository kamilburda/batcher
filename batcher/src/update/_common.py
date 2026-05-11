"""Functions shared across multiple update handlers."""

from src import placeholders as placeholders_


def update_dimension_arguments(arguments_list):
  def _update_percent_property_for_layers(value_dict):
    if 'percent_property' in value_dict:
      if previous_layer_placeholders_str in value_dict['percent_property']:
        percent_property = value_dict['percent_property'][previous_layer_placeholders_str]
        del value_dict['percent_property'][previous_layer_placeholders_str]
        layer_placeholders_str = ','.join(placeholders_.ALL_LAYER_PLACEHOLDERS)
        value_dict['percent_property'][layer_placeholders_str] = percent_property

      if previous_layer_placeholders in value_dict['percent_property']:
        percent_property = value_dict['percent_property'][previous_layer_placeholders]
        del value_dict['percent_property'][previous_layer_placeholders]
        value_dict['percent_property'][placeholders_.ALL_LAYER_PLACEHOLDERS] = percent_property

  previous_layer_placeholders_str = 'current_layer,background_layer,foreground_layer'
  previous_layer_placeholders = ('current_layer', 'background_layer', 'foreground_layer')
  previous_percent_placeholder_names = [
    'current_image', 'current_layer', 'background_layer', 'foreground_layer']

  for argument_dict in arguments_list:
    if argument_dict['type'] == 'dimension':
      _update_percent_property_for_layers(argument_dict['default_value'])
      _update_percent_property_for_layers(argument_dict['value'])

      if ('percent_placeholder_names' in argument_dict
          and argument_dict['percent_placeholder_names'] == previous_percent_placeholder_names):
        argument_dict['percent_placeholder_names'] = [
          *placeholders_.ALL_IMAGE_PLACEHOLDERS,
          *placeholders_.ALL_LAYER_PLACEHOLDERS,
        ]
