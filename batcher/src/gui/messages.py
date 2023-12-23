"""Functions to display message dialogs."""

import traceback
from typing import Optional, Tuple, Union

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg

from src import exceptions


def display_message(
      message: str,
      message_type: Gtk.MessageType = Gtk.MessageType.ERROR,
      parent: Optional[Gtk.Window] = None,
      buttons: Gtk.ButtonsType = Gtk.ButtonsType.OK,
      message_in_text_view: bool = False,
      button_response_id_to_focus: int = None,
      message_markup: bool = False,
):
  return pg.gui.display_message(
    message,
    message_type,
    parent=parent,
    buttons=buttons,
    message_in_text_view=message_in_text_view,
    button_response_id_to_focus=button_response_id_to_focus,
    message_markup=message_markup)


def display_failure_message(
      main_message: str,
      failure_message: str,
      details: Optional[str] = None,
      parent: Optional[Gtk.Window] = None,
      report_description: Optional[str] = None,
      display_details_initially: bool = False,
):
  if report_description is None:
    report_description = _(
      'If you believe this is an error in the plug-in, you can help fix it'
      ' by sending a report with the text in the details to one of the sites below')
  
  pg.gui.display_alert_message(
    parent=parent,
    message_type=Gtk.MessageType.WARNING,
    message_markup=main_message,
    message_secondary_markup=failure_message,
    details=details,
    display_details_initially=display_details_initially,
    report_uri_list=pg.config.BUG_REPORT_URL_LIST,
    report_description=report_description,
    focus_on_button=True)


def display_processing_failure_message(
      exception: Exception,
      parent: Optional[Gtk.Window] = None,
):
  display_failure_message(
    _('There was a problem during processing:'),
    failure_message=str(exception),
    details=traceback.format_exc(),
    parent=parent)


def display_invalid_image_failure_message(parent: Optional[Gtk.Window] = None):
  display_failure_message(
    _('There was a problem during processing.'
      ' Do not close the image during processing,'
      ' keep it open until the processing is finished successfully.'),
    failure_message='',
    details=traceback.format_exc(),
    parent=parent)


def display_import_export_settings_failure_message(
      main_message: str,
      details: str,
      parent: Optional[Gtk.Window] = None,
):
  display_failure_message(
    main_message,
    failure_message='',
    details=details,
    parent=parent,
    report_description=_(
      'If you believe this is an error in the plug-in, you can help fix it'
      ' by sending a report with the file and the text in the details to one of the sites below'))


def get_failing_action_message(
      action_and_item_or_action_error: Union[
        Tuple[pg.setting.Group, pg.itemtree.Item], exceptions.ActionError],
):
  if isinstance(action_and_item_or_action_error, exceptions.ActionError):
    action, item = action_and_item_or_action_error.action, action_and_item_or_action_error.item
  else:
    action, item = action_and_item_or_action_error
  
  if 'procedure' not in action.tags and 'constraint' not in action.tags:
    raise ValueError('an action must have the "procedure" or "constraint" tag')

  message_template = None

  if item is not None:
    if 'procedure' in action.tags:
      message_template = _('Failed to apply procedure "{}" on "{}" because:')
    elif 'constraint' in action.tags:
      message_template = _('Failed to apply constraint "{}" on "{}" because:')

    if message_template is not None:
      return message_template.format(action['display_name'].value, item.orig_name)
  else:
    if 'procedure' in action.tags:
      message_template = _('Failed to apply procedure "{}" because:')
    elif 'constraint' in action.tags:
      message_template = _('Failed to apply constraint "{}" because:')

    if message_template is not None:
      return message_template.format(action['display_name'].value)

  return action['display_name'].value
