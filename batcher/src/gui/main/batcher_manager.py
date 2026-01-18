import contextlib
import traceback

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import builtin_actions
from src import exceptions
from src import overwrite
from src import utils_setting as utils_setting_

from src.gui import messages as messages_
from src.gui import overwrite_chooser as overwrite_chooser_
from src.gui import progress_updater as progress_updater_

from . import _utils as gui_main_utils_


class BatcherInteractiveMixin:

  def __init__(self):
    self._prompted_to_continue_on_error = False

  def _prompt_to_continue_on_error(self, exc, parent_widget):
    failure_message = '{}\n\n{}'.format(
      str(exc),
      _('Do you want to continue processing and ignore any subsequent errors?'
        ' You can permanently ignore errors by checking "{}" in the settings.').format(
        _('Continue on Error'),
      ),
    )

    response_id = messages_.display_failure_message(
      messages_.get_failing_message(exc),
      failure_message=failure_message,
      details=exc.traceback if hasattr(exc, 'traceback') else traceback.format_exc(),
      parent=parent_widget,
      button_texts_and_responses=[
        (_('Continue'), Gtk.ResponseType.YES), (_('Stop'), Gtk.ResponseType.NO)],
      response_id_of_button_to_focus=Gtk.ResponseType.NO,
    )

    self._prompted_to_continue_on_error = True

    return response_id == Gtk.ResponseType.YES

  @staticmethod
  def _get_interactive_overwrite_chooser(parent_widget):
    return overwrite_chooser_.GtkDialogOverwriteChooser(
      builtin_actions.INTERACTIVE_OVERWRITE_MODES,
      default_value=overwrite.OverwriteModes.RENAME_NEW,
      default_response=overwrite.OverwriteModes.CANCEL,
      parent=parent_widget)

  @staticmethod
  def _stop_batcher(batcher):
    if batcher is not None:
      batcher.queue_stop()
      return True
    else:
      return False

  @staticmethod
  def _update_output_directory_and_recent_dirpaths(settings):
    if 'output_directory' in settings['main']:
      if hasattr(settings['main/output_directory'].gui, 'add_to_recent_dirpaths'):
        settings['main/output_directory'].gui.add_to_recent_dirpaths()

      if hasattr(
            settings['main/output_directory'].gui,
            'set_current_recent_dirpath_as_current_directory'):
        settings['main/output_directory'].gui.set_current_recent_dirpath_as_current_directory()


class BatcherManager(BatcherInteractiveMixin):

  _PREVIEWS_BATCHER_RUN_KEY = 'batcher_run'

  def __init__(self, item_tree, settings):
    super().__init__()

    self._item_tree = item_tree
    self._settings = settings

    self._batcher = None

  def run_batcher(
        self,
        mode,
        item_type,
        command_lists,
        previews,
        settings_manager,
        parent_widget,
        progress_bar,
  ):
    self._update_output_directory_and_recent_dirpaths(self._settings)

    self._settings.apply_gui_values_to_settings()

    self._prompted_to_continue_on_error = False

    self._batcher, overwrite_chooser, progress_updater = self._set_up_batcher(
      mode, item_type, parent_widget, progress_bar)

    success = True

    previews.lock(self._PREVIEWS_BATCHER_RUN_KEY)

    try:
      self._batcher.run(
        prompt_to_continue_on_error_func=(
          lambda exc: self._prompt_to_continue_on_error(exc, parent_widget)),
        **utils_setting_.get_settings_for_batcher(self._settings['main']),
      )
    except exceptions.BatcherCancelError:
      success = False
    except exceptions.CommandError as e:
      success = False
      if not self._prompted_to_continue_on_error:
        messages_.display_failure_message(
          messages_.get_failing_message(e),
          failure_message=str(e),
          details=e.traceback,
          parent=parent_widget)
    except exceptions.BatcherError as e:
      success = False
      if not self._prompted_to_continue_on_error:
        messages_.display_processing_failure_message(e, parent=parent_widget)
    except Exception as e:
      success = False
      if not self._prompted_to_continue_on_error:
        messages_.display_invalid_image_failure_message(e, parent=parent_widget)
    finally:
      previews.unlock(self._PREVIEWS_BATCHER_RUN_KEY, update=False)

      if mode == 'edit':
        previews.image_preview.update()
        previews.name_preview.update()

      command_lists.set_command_status_and_deactivate_failed_commands(self._batcher)

      message = self._batcher.get_finished_processing_message()

      self._batcher = None

    if (mode == 'export'
        and overwrite_chooser.overwrite_mode
          in self._settings['main/overwrite_mode'].items.values()):
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)

    settings_manager.save_settings()

    progress_updater.reset()

    return success, message

  def stop_batcher(self):
    self._stop_batcher(self._batcher)

  def _set_up_batcher(self, mode, item_type, parent_widget, progress_bar):
    overwrite_chooser = self._get_interactive_overwrite_chooser(parent_widget)

    progress_updater = progress_updater_.GtkProgressUpdater(progress_bar)

    batcher = gui_main_utils_.get_batcher_class(item_type)(
      item_tree=self._item_tree,
      actions=self._settings['main/actions'],
      conditions=self._settings['main/conditions'],
      edit_mode=mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.INTERACTIVE,
      overwrite_chooser=overwrite_chooser,
      progress_updater=progress_updater,
      export_context_manager=_handle_gui_in_export,
      export_context_manager_args=[parent_widget])

    return batcher, overwrite_chooser, progress_updater


class BatcherManagerQuick(BatcherInteractiveMixin):

  def __init__(self, item_tree, settings):
    super().__init__()

    self._item_tree = item_tree
    self._settings = settings

    self._batcher = None

  def run_batcher(
        self,
        mode,
        item_type,
        item_tree,
        parent_widget,
        progress_bar,
  ):
    self._update_output_directory_and_recent_dirpaths(self._settings)

    self._settings.apply_gui_values_to_settings()

    self._prompted_to_continue_on_error = False

    self._batcher, overwrite_chooser, progress_updater = self._set_up_batcher(
      mode, item_type, parent_widget, progress_bar)

    try:
      self._batcher.run(
        item_tree=item_tree,
        prompt_to_continue_on_error_func=(
          lambda exc: self._prompt_to_continue_on_error(exc, parent_widget)),
        **utils_setting_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.BatcherError as e:
      if not self._prompted_to_continue_on_error:
        messages_.display_processing_failure_message(e, parent=parent_widget)
    except Exception as e:
      if not self._prompted_to_continue_on_error:
        messages_.display_invalid_image_failure_message(e, parent=parent_widget)

    if (mode == 'export'
        and overwrite_chooser.overwrite_mode
          in self._settings['main/overwrite_mode'].items.values()):
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)

  def stop_batcher(self):
    self._stop_batcher(self._batcher)

  def _set_up_batcher(self, mode, item_type, parent_widget, progress_bar):
    if mode == 'export':
      if self._settings['gui/show_quick_settings'].value:
        overwrite_chooser = self._get_interactive_overwrite_chooser(parent_widget)
        initial_export_run_mode = Gimp.RunMode.INTERACTIVE
      else:
        overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
          self._settings['main/overwrite_mode'].value)
        initial_export_run_mode = Gimp.RunMode.WITH_LAST_VALS
    else:
      overwrite_chooser = self._get_interactive_overwrite_chooser(parent_widget)
      initial_export_run_mode = Gimp.RunMode.INTERACTIVE

    progress_updater = progress_updater_.GtkProgressUpdater(progress_bar)

    batcher = gui_main_utils_.get_batcher_class(item_type)(
      item_tree=self._item_tree,
      actions=self._settings['main/actions'],
      conditions=self._settings['main/conditions'],
      edit_mode=mode == 'edit',
      initial_export_run_mode=initial_export_run_mode,
      overwrite_chooser=overwrite_chooser,
      progress_updater=progress_updater,
      export_context_manager=_handle_gui_in_export,
      export_context_manager_args=[parent_widget])

    return batcher, overwrite_chooser, progress_updater


@contextlib.contextmanager
def _handle_gui_in_export(run_mode, _image, _layer, _output_filepath, window):
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
