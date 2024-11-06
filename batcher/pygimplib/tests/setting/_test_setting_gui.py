"""Test GUI for all available setting types.

The GUI also exercises 'setting value changed' events connected to the GUI
elements.
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ...setting import meta as meta_
from ...setting import settings as settings_


_SETTING_WIDGET_WIDTH = 450
_SETTING_VALUE_LABEL_WIDTH = 150


def test_settings_and_gui():
  setting_data = _get_setting_data()

  value_not_valid_event_id = settings_.Setting.connect_event_global(
    'value-not-valid', _on_setting_value_not_valid)
  
  settings = []
  
  for item in setting_data.values():
    setting_type_name = item.pop('type')
    setting_type = meta_.SETTING_TYPES[setting_type_name]
    
    for gui_type in setting_type.get_allowed_gui_types():
      item['gui_type'] = gui_type
      settings.append(setting_type(**item))
  
  dialog = Gtk.Dialog(
    border_width=5,
  )
  
  setting_type_title_label = Gtk.Label(
    label='<b>Type</b>',
    use_markup=True,
    xalign=0.0,
    yalign=0.5,
  )
  
  setting_gui_title_label = Gtk.Label(
    label='<b>GUI</b>',
    use_markup=True,
    xalign=0.0,
    yalign=0.5,
  )
  
  setting_value_title_label = Gtk.Label(
    label='<b>Value</b>',
    use_markup=True,
    xalign=0.0,
    yalign=0.5,
  )
  
  setting_call_count_title_label = Gtk.Label(
    label='<b>Call count</b>',
    use_markup=True,
    xalign=0.0,
    yalign=0.5,
  )
  
  grid = Gtk.Grid(
    row_spacing=6,
    column_spacing=5,
  )

  grid.attach(setting_type_title_label, 0, 0, 1, 1)
  grid.attach(setting_gui_title_label, 1, 0, 1, 1)
  grid.attach(setting_value_title_label, 2, 0, 1, 1)
  grid.attach(setting_call_count_title_label, 3, 0, 1, 1)
  
  for row_index, setting in enumerate(settings):
    setting_type_label = Gtk.Label(
      label=setting.display_name,
      xalign=0.0,
      yalign=0.5,
    )
    
    setting.set_gui()
    setting.gui.widget.set_property('width-request', _SETTING_WIDGET_WIDTH)
    
    _check_setting_gui_interface(setting)
    
    setting_value_label = Gtk.Label(
      xalign=0.0,
      yalign=0.5,
      width_request=_SETTING_VALUE_LABEL_WIDTH,
    )
    
    setting_value_changed_call_count_label = Gtk.Label(
      label='0',
      xalign=0.0,
      yalign=0.5,
    )
    
    _set_setting_value_label(setting, setting_value_label)
    
    setting.connect_event(
      'value-changed',
      _on_setting_value_changed,
      setting_value_label,
      setting_value_changed_call_count_label)
    
    grid.attach(setting_type_label, 0, row_index + 1, 1, 1)
    grid.attach(setting.gui.widget, 1, row_index + 1, 1, 1)
    grid.attach(setting_value_label, 2, row_index + 1, 1, 1)
    grid.attach(setting_value_changed_call_count_label, 3, row_index + 1, 1, 1)
  
  reset_button = dialog.add_button('Reset', Gtk.ResponseType.OK)
  reset_button.connect('clicked', _on_reset_button_clicked, settings)

  update_settings_button = dialog.add_button('Update Settings', Gtk.ResponseType.OK)
  update_settings_button.connect('clicked', _on_update_settings_button_clicked, settings)
  
  scrolled_window = Gtk.ScrolledWindow(
    hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    shadow_type=Gtk.ShadowType.NONE,
  )
  scrolled_window.add(grid)
  
  dialog.vbox.pack_start(scrolled_window, True, True, 0)
  dialog.set_default_size(850, 800)
  
  dialog.show_all()

  settings_.Setting.remove_event_global(value_not_valid_event_id)


def _get_setting_data():
  setting_data = {}

  added_types = set()

  for name, setting_type in meta_.SETTING_TYPES.items():
    # Prevent the same setting type from being created multiple times (which can
    # occur if a setting type name has aliases).
    if setting_type not in added_types:
      added_types.add(setting_type)
    else:
      continue

    # Arrays are handled separately.
    if name == 'array':
      continue

    # Skip stub settings that could theoretically have been registered.
    if name.startswith('stub_'):
      continue

    setting_data[name] = {
      'name': name,
      'type': name,
    }

  setting_data['choice']['items'] = [
    ('skip', 'SKIP'),
    ('overwrite', 'OVERWRITE'),
  ]
  setting_data['choice']['default_value'] = 'skip'

  setting_data['enum']['enum_type'] = Gimp.RunMode

  setting_data['string']['default_value'] = 'Test'

  setting_data.update(**_get_array_settings())

  return setting_data


def _get_array_settings():
  return {
    'array_of_booleans': {
     'name': 'array_of_booleans',
     'type': 'array',
     'default_value': (True, False, True),
     'element_type': 'bool',
     'element_default_value': True,
     'min_size': 3,
     'max_size': 10,
    },
    'array_of_doubles': {
     'name': 'array_of_doubles',
     'type': 'array',
     'default_value': (5.0, 10.0, 30.0),
     'element_type': 'double',
     'element_default_value': 1.0,
     'min_size': 3,
     'max_size': 10,
    },
    '2D_array_of_doubles': {
     'name': '2D_array_of_doubles',
     'type': 'array',
     'display_name': '2D array of doubles',
     'default_value': ((1.0, 5.0, 10.0), (2.0, 15.0, 25.0), (-5.0, 10.0, 40.0)),
     'element_type': 'array',
     'element_default_value': (0.0, 0.0, 0.0),
     'min_size': 3,
     'max_size': 10,
     'element_element_type': 'double',
     'element_element_default_value': 1.0,
     'element_min_size': 1,
     'element_max_size': 3,
    },
    'array_of_layers': {
     'name': 'array_of_layers',
     'type': 'array',
     'element_type': 'layer',
    },
  }


def _on_setting_value_changed(
      setting, setting_value_label, setting_value_changed_call_count_label):
  _set_setting_value_label(setting, setting_value_label)
  
  setting_value_changed_call_count_label.set_label(
    str(int(setting_value_changed_call_count_label.get_label()) + 1))


def _on_setting_value_not_valid(_setting, message, _message_id, details):
  dialog = Gtk.Dialog()

  dialog.vbox.pack_start(
    Gtk.Label(
      use_markup=True,
      label='<b>Warning:</b>',
      xalign=0.0,
      yalign=0.5,
      selectable=True,
      wrap=True,
      max_width_chars=50,
    ),
    False,
    False,
    0,
  )

  dialog.vbox.pack_start(
    Gtk.Label(
      label=message,
      xalign=0.0,
      yalign=0.5,
      selectable=True,
      wrap=True,
      max_width_chars=50,
    ),
    False,
    False,
    0,
  )

  dialog.vbox.pack_start(
    Gtk.Label(
      use_markup=True,
      label='<b>Details:</b>',
      xalign=0.0,
      yalign=0.5,
      selectable=True,
      wrap=True,
      max_width_chars=50,
    ),
    False,
    False,
    0,
  )

  details_window = Gtk.ScrolledWindow(
    width_request=300,
    max_content_width=300,
    height_request=200,
    shadow_type=Gtk.ShadowType.IN,
    hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
  )

  text_view = Gtk.TextView(
    buffer=Gtk.TextBuffer(text=details),
    editable=False,
    wrap_mode=Gtk.WrapMode.WORD,
    cursor_visible=False,
    pixels_above_lines=1,
    pixels_below_lines=1,
    pixels_inside_wrap=0,
    left_margin=5,
    right_margin=5,
  )

  details_window.add(text_view)

  dialog.vbox.pack_start(details_window, True, True, 0)

  dialog.vbox.set_spacing(5)
  dialog.set_border_width(8)

  close_button = dialog.add_button('_Close', Gtk.ResponseType.CLOSE)

  close_button.connect('clicked', lambda *args: dialog.destroy())

  dialog.show_all()


def _on_reset_button_clicked(button, settings):
  for setting in settings:
    setting.reset()


def _on_update_settings_button_clicked(button, settings):
  for setting in settings:
    setting.gui.update_setting_value(force=True)


def _set_setting_value_label(setting, setting_value_label):
  setting_value_label.set_label(str(setting.to_dict()['value']))


def _check_setting_gui_interface(setting):
  setting.gui.set_sensitive(True)
  setting.gui.set_visible(True)
  
  assert setting.gui.get_sensitive()
  assert setting.gui.get_visible()
