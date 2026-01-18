"""Widgets and functions to display GUI messages (particularly error messages).
"""

from collections.abc import Iterable
import functools
import sys
import traceback
from typing import Callable, Optional, Tuple, Union

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

from config import CONFIG
from src import core
from src import exceptions
from src import itemtree
from src import setting as setting_


ERROR_EXIT_STATUS = 1


def display_alert_message(
      title: Optional[str] = None,
      parent: Optional[Gtk.Window] = None,
      message_type: Gtk.MessageType = Gtk.MessageType.ERROR,
      modal: bool = True,
      destroy_with_parent: bool = True,
      message_markup: Optional[str] = None,
      message_secondary_markup: Optional[str] = None,
      details: Optional[str] = None,
      display_details_initially: bool = True,
      report_uri_list: Optional[Iterable[Tuple[str, str]]] = None,
      report_description: Optional[str] = None,
      button_texts_and_responses: Optional[Iterable[Tuple[str, Gtk.ResponseType]]] = None,
      response_id_of_button_to_focus: Optional[Gtk.ResponseType] = None,
) -> int:
  """Displays a message to alert the user about an error or an exception that
  occurred in the application.

  Args:
    title:
      Message dialog title.
    parent:
      Parent window.
    message_type:
      A `Gtk.MessageType` value.
    modal:
      If ``True``, the message dialog will be modal.
    destroy_with_parent:
      If ``True``, the message dialog will be destroyed if its parent is
      destroyed.
    message_markup:
      Primary message text to display as markup.
    message_secondary_markup:
      Secondary message text to display as markup.
    details:
      Text to display in a text box with details. If ``None``, no text box is
      displayed.
    display_details_initially:
      If ``True``, the details are displayed by default, otherwise they are
      hidden under an expander.
    report_uri_list:
      Sequence of (name, URL) pairs where the user can report the error. If no
      report list is desired, pass ``None`` or an empty sequence.
    report_description:
      Text accompanying ``report_uri_list``. If ``None``, default text is
      used. To suppress displaying the report description, pass an empty string.
    button_texts_and_responses:
      Buttons to display in the dialog as a list-like of (text, response ID).
    response_id_of_button_to_focus:
      If not ``None``, the default focus is set to the button (from
      ``button_texts_and_responses``) having this response ID.

  Returns:
    Response ID when closing the displayed dialog.
  """
  if message_markup is None:
    message_markup = (
      '<span font_size="large"><b>{}</b></span>'.format(
        _('Oops. Something went wrong.')))

  if message_secondary_markup is None:
    message_secondary_markup = _(
      'An unexpected error occurred and the plug-in has to close. Sorry about that!')

  if report_description is None:
    report_description = _(
      'You can help fix this error by sending a report with the text'
      ' in the details above to one of the following sites')

  if button_texts_and_responses is None:
    button_texts_and_responses = [(_('_Close'), Gtk.ResponseType.CLOSE)]

  dialog = GimpUi.Dialog(
    parent=parent,
    modal=modal,
    destroy_with_parent=destroy_with_parent,
    attached_to=parent,
    transient_for=parent,
  )

  if title is not None:
    dialog.set_title(title)
  else:
    dialog.set_title('')

  hbox_icon_and_messages = Gtk.Box(
    orientation=Gtk.Orientation.HORIZONTAL,
    spacing=12,
    border_width=12,
  )
  dialog.vbox.pack_start(hbox_icon_and_messages, False, False, 0)

  message_icon = _get_message_icon(message_type)
  if message_icon is not None:
    hbox_icon_and_messages.pack_start(message_icon, False, False, 0)

  vbox_messages = Gtk.Box(
    orientation=Gtk.Orientation.VERTICAL,
    spacing=5,
  )
  hbox_icon_and_messages.pack_start(vbox_messages, False, False, 0)

  if message_markup:
    primary_message = Gtk.Label(
      use_markup=True,
      label=message_markup,
      xalign=0.0,
      yalign=0.5,
      selectable=True,
      wrap=True,
      width_request=300,
      max_width_chars=50,
      wrap_mode=Pango.WrapMode.WORD_CHAR,
    )
    vbox_messages.pack_start(primary_message, False, False, 0)

  if message_secondary_markup:
    secondary_message = Gtk.Label(
      use_markup=True,
      label=message_secondary_markup,
      xalign=0.0,
      yalign=0.5,
      selectable=True,
      wrap=True,
      width_request=300,
      max_width_chars=50,
      wrap_mode=Pango.WrapMode.WORD_CHAR,
    )
    vbox_messages.pack_start(secondary_message, False, False, 0)

  if details is not None:
    expander = Gtk.Expander(
      use_markup=True,
      label='<b>{}</b>'.format(_('Details')),
    )
    expander.connect('activate', _on_details_expander_activate, dialog)

    vbox_details = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      spacing=6,
      margin_top=6,
    )

    details_widget = _get_details_widget(details)
    vbox_details.pack_start(details_widget, True, True, 0)

    label_plugin_version = Gtk.Label(
      label=_('Version of {}: {}').format(CONFIG.PLUGIN_TITLE, CONFIG.PLUGIN_VERSION),
      xalign=0.0,
      yalign=0.5,
      selectable=True,
    )

    vbox_details.pack_start(label_plugin_version, False, False, 0)

    if report_uri_list:
      vbox_labels_report = _get_report_link_buttons_and_copy_icon(
        report_uri_list, report_description, details)
      vbox_details.pack_start(vbox_labels_report, False, False, 0)

    if display_details_initially:
      expander.set_expanded(True)

    expander.add(vbox_details)

    vbox_expander = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      border_width=6,
    )
    vbox_expander.pack_start(expander, True, True, 0)

    dialog.vbox.pack_start(vbox_expander, True, True, 0)
  else:
    details_widget = None

  for button_text, button_response_id in button_texts_and_responses:
    dialog.add_button(button_text, button_response_id)

  if response_id_of_button_to_focus is not None:
    button = dialog.get_widget_for_response(response_id_of_button_to_focus)
    if button is not None:
      dialog.set_focus(button)
  else:
    if details_widget is not None and display_details_initially:
      dialog.set_focus(details_widget)

  dialog.show_all()
  response_id = dialog.run()
  dialog.destroy()

  return response_id


def _get_message_icon(message_type=None):
  if message_type == Gtk.MessageType.WARNING:
    return Gtk.Image(
      icon_name=GimpUi.ICON_DIALOG_WARNING,
      icon_size=Gtk.IconSize.DIALOG,
    )
  elif message_type == Gtk.MessageType.ERROR:
    return Gtk.Image(
      icon_name=GimpUi.ICON_DIALOG_ERROR,
      icon_size=Gtk.IconSize.DIALOG,
    )
  else:
    return None


def _on_details_expander_activate(expander, window):
  if expander.get_expanded():
    window.resize(window.get_allocation().width, 100)


def _get_details_widget(details_text):
  scrolled_window = Gtk.ScrolledWindow(
    width_request=300,
    max_content_width=300,
    height_request=200,
    shadow_type=Gtk.ShadowType.IN,
    hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
    vexpand=True,
  )

  exception_text_view = Gtk.TextView(
    buffer=Gtk.TextBuffer(text=details_text),
    editable=False,
    wrap_mode=Gtk.WrapMode.WORD,
    cursor_visible=False,
    pixels_above_lines=1,
    pixels_below_lines=1,
    pixels_inside_wrap=0,
    left_margin=5,
    right_margin=5,
  )

  scrolled_window.add(exception_text_view)

  return scrolled_window


def _get_report_link_buttons_and_copy_icon(report_uri_list, report_description, details):
  if not report_uri_list:
    return None

  vbox = Gtk.Box(
    orientation=Gtk.Orientation.VERTICAL,
    homogeneous=False,
    spacing=6,
  )

  if report_description:
    label_report_text = report_description
    label_report_text += ':'

    label_report = Gtk.Label(
      label=label_report_text,
      xalign=0,
      yalign=0.5,
      wrap=True,
      wrap_mode=Pango.WrapMode.WORD,
      max_width_chars=50,
    )

    button_copy_to_clipboard = Gtk.Button(
      relief=Gtk.ReliefStyle.NONE,
      tooltip_text=_('Copy details to clipboard'),
    )
    button_copy_to_clipboard.set_image(
      Gtk.Image.new_from_icon_name(GimpUi.ICON_EDIT_COPY, Gtk.IconSize.BUTTON))
    button_copy_to_clipboard.connect(
      'clicked',
      _set_clipboard_text,
      details)

    hbox_label_report_and_copy_icon = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=3,
    )
    hbox_label_report_and_copy_icon.pack_start(
      label_report, True, True, 0)
    hbox_label_report_and_copy_icon.pack_start(
      button_copy_to_clipboard, False, False, 0)

    vbox.pack_start(hbox_label_report_and_copy_icon, False, False, 0)

  for name, uri in report_uri_list:
    linkbutton = Gtk.LinkButton(
      uri=uri,
      label=name,
      xalign=0,
      yalign=0.5,
    )
    vbox.pack_start(linkbutton, False, False, 0)

  return vbox


def _set_clipboard_text(button, text):
  Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, len(text))


_gui_excepthook_parent = None
# Once this is set to True, it prevents the exception dialog from being
# displayed again if an exception occurred during `display_alert_message` (which
# is used to create and display the exception dialog). This prevents potential
# infinite loops and the inability of the user to close the dialog.
_gui_excepthook_invoked = False


def add_gui_excepthook(
      title: Optional[str] = None,
      report_uri_list: Optional[Iterable[Tuple[str, str]]] = None,
      parent: Optional[Gtk.Window] = None,
) -> Callable:
  """Returns a `sys.excepthook` wrapper that displays an error dialog for
  unhandled exceptions and terminates the application.

  `sys.excepthook` is restored after the decorated function is finished.

  The dialog will not be displayed for exceptions which are not subclasses of
  `Exception` (such as `SystemExit` or `KeyboardInterrupt`).

  For the description of parameters, see `display_alert_message()`.
  """
  global _gui_excepthook_parent

  _gui_excepthook_parent = parent

  def gui_excepthook(func):
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
      def _gui_excepthook(exc_type, exc_value, exc_traceback):
        _gui_excepthook_generic(
          exc_type,
          exc_value,
          exc_traceback,
          title,
          _gui_excepthook_parent,
          report_uri_list)

      sys.excepthook = _gui_excepthook

      func(*args, **kwargs)

      sys.excepthook = sys.__excepthook__

    return func_wrapper

  return gui_excepthook


def set_gui_excepthook(
      title: Optional[str] = None,
      report_uri_list: Optional[Iterable[Tuple[str, str]]] = None,
      parent: Optional[Gtk.Window] = None,
):
  """Modifies `sys.excepthook` to display an error dialog for unhandled
  exceptions.

  The dialog will not be displayed for exceptions which are not subclasses of
  `Exception` (such as `SystemExit` or `KeyboardInterrupt`).

  For information about parameters, see `add_gui_excepthook()`.
  """
  global _gui_excepthook_parent

  _gui_excepthook_parent = parent

  def gui_excepthook(exc_type, exc_value, exc_traceback):
    _gui_excepthook_generic(
      exc_type,
      exc_value,
      exc_traceback,
      title,
      _gui_excepthook_parent,
      report_uri_list)

  sys.excepthook = gui_excepthook


def set_gui_excepthook_parent(parent: Optional[Gtk.Window]):
  """Set the parent window to attach the exception dialog to when using
  `add_gui_excepthook()`.

  This function allows to modify the parent dynamically even after decorating
  a function with `add_gui_excepthook()`.
  """
  global _gui_excepthook_parent

  _gui_excepthook_parent = parent


def _gui_excepthook_generic(
      exc_type,
      exc_value,
      exc_traceback,
      title,
      parent,
      report_uri_list):
  global _gui_excepthook_invoked

  sys.__excepthook__(exc_type, exc_value, exc_traceback)

  if issubclass(exc_type, Exception):
    if not _gui_excepthook_invoked:
      _gui_excepthook_invoked = True

      exception_message = ''.join(
        traceback.format_exception(exc_type, exc_value, exc_traceback))

      display_alert_message(
        title=title,
        parent=parent,
        details=exception_message,
        report_uri_list=report_uri_list)

    sys.exit(ERROR_EXIT_STATUS)


def display_failure_message(
      main_message: str,
      failure_message: str,
      details: Optional[str] = None,
      parent: Optional[Gtk.Window] = None,
      report_description: Optional[str] = None,
      display_details_initially: bool = False,
      button_texts_and_responses: Optional[Iterable[Tuple[str, Gtk.ResponseType]]] = None,
      response_id_of_button_to_focus: Optional[Gtk.ResponseType] = None,
) -> int:
  if report_description is None:
    report_description = _(
      'If you believe this is an error in the plug-in, you can help fix it'
      ' by sending a report with the text in the details to one of the sites below')
  
  response_id = display_alert_message(
    parent=parent,
    message_type=Gtk.MessageType.WARNING,
    message_markup=main_message,
    message_secondary_markup=failure_message,
    details=details,
    display_details_initially=display_details_initially,
    report_uri_list=CONFIG.BUG_REPORT_URL_LIST,
    report_description=report_description,
    button_texts_and_responses=button_texts_and_responses,
    response_id_of_button_to_focus=response_id_of_button_to_focus,
  )

  return response_id


def display_processing_failure_message(
      exception: Exception,
      parent: Optional[Gtk.Window] = None,
):
  display_failure_message(
    _('There was a problem during processing:'),
    failure_message=str(exception),
    details=traceback.format_exc(),
    parent=parent)


def display_invalid_image_failure_message(
      exception: Exception,
      parent: Optional[Gtk.Window] = None,
):
  display_failure_message(
    _('There was a problem during processing:'),
    failure_message=str(exception),
    report_description=_(
      'If you closed an image during processing, do not close it and instead'
      ' keep it open until the processing is finished successfully.'
      '\n\nIf you believe this is an error in the plug-in, you can help fix it'
      ' by sending a report with the text in the details to one of the sites below'
    ),
    details=traceback.format_exc(),
    parent=parent)


def get_failing_message(
      command_and_item_or_error: Union[Tuple[setting_.Group, itemtree.Item], Exception],
):
  if isinstance(command_and_item_or_error, exceptions.CommandError):
    command, item = command_and_item_or_error.command, command_and_item_or_error.item
  elif isinstance(command_and_item_or_error, (tuple, list)):
    command, item = command_and_item_or_error
  elif isinstance(command_and_item_or_error, exceptions.BatcherFileLoadError):
    return _('Failed to load image file "{}":').format(command_and_item_or_error.filepath)
  else:
    return _('There was a problem during processing:')

  if 'action' not in command.tags and 'condition' not in command.tags:
    raise ValueError('a command must have the "action" or "condition" tag')

  if item is not None:
    if core.DEFAULT_EXPORT_ACTION_TAG in command.tags:
      message_template = _('Could not export "{}" because:')
      return message_template.format(item.orig_name)
    elif core.DEFAULT_RENAME_ACTION_TAG in command.tags:
      message_template = _('Could not rename "{}" because:')
      return message_template.format(item.orig_name)
    elif 'action' in command.tags:
      message_template = _('Failed to apply action "{}" on "{}" because:')
      return message_template.format(command['display_name'].value, item.orig_name)
    elif 'condition' in command.tags:
      message_template = _('Failed to apply condition "{}" on "{}" because:')
      return message_template.format(command['display_name'].value, item.orig_name)
  else:
    if 'action' in command.tags:
      message_template = _('Failed to apply action "{}" because:')
      return message_template.format(command['display_name'].value)
    elif 'condition' in command.tags:
      message_template = _('Failed to apply condition "{}" because:')
      return message_template.format(command['display_name'].value)

  return command['display_name'].value


def display_popover(widget, text, icon_name=None, icon_size=Gtk.IconSize.LARGE_TOOLBAR):
  """Displays a simple message as a popover attached to ``widget``, optionally
  with an icon.
  """
  hbox = Gtk.Box(
    orientation=Gtk.Orientation.HORIZONTAL,
    spacing=8,
    border_width=6,
  )

  if icon_name is not None:
    icon = Gtk.Image(
      icon_name=icon_name,
      icon_size=icon_size,
    )

    hbox.pack_start(icon, False, False, 0)

  label = Gtk.Label(
    label=text,
    xalign=0.0,
    yalign=0.5,
    max_width_chars=60,
    wrap=True,
  )

  hbox.pack_start(label, False, False, 0)

  hbox.show_all()

  popover_message = Gtk.Popover()
  popover_message.add(hbox)
  popover_message.set_constrain_to(Gtk.PopoverConstraint.NONE)
  popover_message.set_relative_to(widget)

  popover_message.popup()
