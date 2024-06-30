import contextlib
import os

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GLib
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pygimplib as pg


@contextlib.contextmanager
def handle_gui_in_export(run_mode, _image, _layer, _output_filepath, window):
  should_manipulate_window = run_mode == Gimp.RunMode.INTERACTIVE

  if should_manipulate_window:
    window_position = window.get_position()
    window.hide()
  else:
    window_position = None

  while Gtk.events_pending():
    Gtk.main_iteration()

  try:
    yield
  finally:
    if window_position is not None:
      window.move(*window_position)
      window.show()

    while Gtk.events_pending():
      Gtk.main_iteration()


def display_reset_prompt(parent=None):
  dialog = Gtk.MessageDialog(
    parent=parent,
    message_type=Gtk.MessageType.WARNING,
    modal=True,
    destroy_with_parent=True,
    buttons=Gtk.ButtonsType.YES_NO,
  )

  dialog.set_transient_for(parent)
  dialog.set_markup(GLib.markup_escape_text(_('Are you sure you want to reset settings?')))
  dialog.set_focus(dialog.get_widget_for_response(Gtk.ResponseType.NO))

  dialog.show_all()
  response_id = dialog.run()
  dialog.destroy()

  return response_id


def set_up_output_directory_settings(settings, current_image):
  _set_up_images_and_directories_and_initial_output_directory(
    settings, settings['main/output_directory'], current_image)
  _set_up_output_directory_changed(settings, current_image)


def _set_up_images_and_directories_and_initial_output_directory(
      settings, output_directory_setting, current_image):
  """Sets up the initial directory path for the current image.

  The path is set according to the following priority list:

    1. Last export directory path of the current image
    2. Import directory path of the current image
    3. Last export directory path of any image (i.e. the current value of
       ``'main/output_directory'``)
    4. The default directory path (default value) for
       ``'main/output_directory'``

  Notes:

    Directory 3. is set upon loading ``'main/output_directory'``.
    Directory 4. is set upon the instantiation of ``'main/output_directory'``.
  """
  settings['gui/images_and_directories'].update_images_and_dirpaths()

  _update_directory(
    output_directory_setting,
    current_image,
    settings['gui/images_and_directories'].value[current_image])


def _update_directory(setting, current_image, current_image_dirpath):
  """Sets the directory path to the ``setting``.

  The path is set according to the following priority list:

  1. ``current_image_dirpath`` if not ``None``
  2. ``current_image`` - import path of the current image if not ``None``

  If update was performed, ``True`` is returned, ``False`` otherwise.
  """
  if current_image_dirpath is not None:
    setting.set_value(current_image_dirpath)
    return True

  if current_image.get_file() is not None and current_image.get_file().get_path() is not None:
    setting.set_value(os.path.dirname(current_image.get_file().get_path()))
    return True

  return False


def _set_up_output_directory_changed(settings, current_image):
  def on_output_directory_changed(output_directory, images_and_directories, current_image_):
    images_and_directories.update_dirpath(current_image_, output_directory.value)

  settings['main/output_directory'].connect_event(
    'value-changed',
    on_output_directory_changed,
    settings['gui/images_and_directories'],
    current_image)


def get_help_button(reference_button):
  button_help = Gtk.LinkButton(
    uri=(
      pg.config.LOCAL_DOCS_PATH if os.path.isfile(pg.config.LOCAL_DOCS_PATH)
      else pg.config.DOCS_URL),
    label=_('_Help'),
    use_underline=True,
  )
  # Make the button appear like a regular button
  button_help_style_context = button_help.get_style_context()

  for style_class in button_help_style_context.list_classes():
    button_help_style_context.remove_class(style_class)

  for style_class in reference_button.get_style_context().list_classes():
    button_help_style_context.add_class(style_class)

  button_help.unset_state_flags(Gtk.StateFlags.LINK)

  # Make sure the button retains the style of a regular button when clicked.
  button_help.connect(
    'clicked',
    lambda button, *args: button.unset_state_flags(Gtk.StateFlags.VISITED | Gtk.StateFlags.LINK))

  return button_help
