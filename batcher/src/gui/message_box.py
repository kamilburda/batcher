"""Button to accumulate and display messages in a dialog when clicked."""

import gi
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src.gui import messages


class SettingValueNotValidMessageBox(Gtk.Box):
  """Class displaying a button containing warnings if an invalid value was
  assigned to any `pygimplib.Setting` instance.
  """

  def __init__(self, message_type=Gtk.MessageType.WARNING, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self._messages = []
    self._details_list = []
    self._message_type = message_type

    self._init_gui()

    self._set_up_setting_value_not_valid_handler()

  def add_message(self, setting, message, details):
    self._button.show()

    self._messages.append(f'Setting "{setting.get_path()}": {message}')
    self._details_list.append(details)

  def clear_messages(self):
    self._messages = []
    self._details_list = []

    self._button.hide()

  def _init_gui(self):
    if self._message_type == Gtk.MessageType.WARNING:
      icon_name = GimpUi.ICON_DIALOG_WARNING
    elif self._message_type == Gtk.MessageType.ERROR:
      icon_name = GimpUi.ICON_DIALOG_ERROR
    else:
      icon_name = GimpUi.ICON_DIALOG_INFORMATION

    self._button = Gtk.Button(
      tooltip_text=_('Plug-in errors occurred'),
      no_show_all=True,
    )
    self._button.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))

    self._button.connect('clicked', self._on_button_clicked)

    self.pack_start(self._button, False, False, 0)

    self.show_all()

  def _on_button_clicked(self, _button):
    message_contents_list = []

    for message, details in zip(self._messages, self._details_list):
      message_contents_list.append('\n'.join([message, details]))

    message_contents = f'\n{"=" * 80}\n'.join(message_contents_list)

    messages.display_alert_message(
      title=pg.config.PLUGIN_TITLE,
      parent=pg.gui.get_toplevel_window(self),
      message_type=self._message_type,
      message_markup=_('The plug-in encountered one or more errors.'),
      message_secondary_markup=_(
        'The errors should not cause crashes,'
        ' but you should exercise caution nonetheless.'),
      details=message_contents,
      report_description=_(
        'You can help fix these errors by sending a report with the text'
        ' in the details above to one of the following sites'),
      report_uri_list=pg.config.BUG_REPORT_URL_LIST,
    )

  def _set_up_setting_value_not_valid_handler(self):
    pg.setting.Setting.connect_event_global('value-not-valid', self._on_setting_value_not_valid)

  def _on_setting_value_not_valid(self, setting, message, _message_id, details):
    self.add_message(setting, message, details)


GObject.type_register(SettingValueNotValidMessageBox)
