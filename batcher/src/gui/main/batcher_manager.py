import contextlib

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from src import builtin_procedures
from src import core
from src import exceptions
from src import overwrite
from src import utils as utils_

from src.gui import messages as messages_
from src.gui import overwrite_chooser as overwrite_chooser_
from src.gui import progress_updater as progress_updater_


class BatcherManager:

  _PREVIEWS_BATCHER_RUN_KEY = 'batcher_run'

  def __init__(self, item_tree, settings):
    self._item_tree = item_tree
    self._settings = settings

    self._batcher = None

  def run_batcher(
        self,
        mode,
        image,
        action_lists,
        previews,
        settings_manager,
        parent_widget,
        progress_bar,
  ):
    self._settings.apply_gui_values_to_settings()

    self._batcher, overwrite_chooser, progress_updater = self._set_up_batcher(
      mode, parent_widget, progress_bar)

    should_quit = True

    previews.lock(self._PREVIEWS_BATCHER_RUN_KEY)

    try:
      self._batcher.run(**utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      should_quit = False
    except exceptions.ActionError as e:
      messages_.display_failure_message(
        messages_.get_failing_action_message(e),
        failure_message=str(e),
        details=e.traceback,
        parent=parent_widget)
      should_quit = False
    except exceptions.BatcherError as e:
      messages_.display_processing_failure_message(e, parent=parent_widget)
      should_quit = False
    except Exception:
      if image.is_valid():
        raise
      else:
        messages_.display_invalid_image_failure_message(parent=parent_widget)
    else:
      if mode == 'export' and not self._batcher.exported_items:
        should_quit = False
        messages_.display_message(
          _('No layers were exported.'), Gtk.MessageType.INFO, parent=parent_widget)
    finally:
      previews.unlock(self._PREVIEWS_BATCHER_RUN_KEY, update=False)

      if mode == 'edit':
        previews.image_preview.update()
        previews.name_preview.update()

      action_lists.set_warning_on_actions(self._batcher)

      self._batcher = None

    if (mode == 'export'
        and overwrite_chooser.overwrite_mode
          in self._settings['main/overwrite_mode'].items.values()):
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)

    settings_manager.save_settings()

    progress_updater.reset()

    return should_quit

  def stop_batcher(self):
    _stop_batcher(self._batcher)

  def _set_up_batcher(self, mode, parent_widget, progress_bar):
    overwrite_chooser = _get_interactive_overwrite_chooser(parent_widget)

    progress_updater = progress_updater_.GtkProgressUpdater(progress_bar)

    batcher = core.LayerBatcher(
      item_tree=self._item_tree,
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=mode == 'edit',
      initial_export_run_mode=Gimp.RunMode.INTERACTIVE,
      overwrite_chooser=overwrite_chooser,
      progress_updater=progress_updater,
      export_context_manager=_handle_gui_in_export,
      export_context_manager_args=[parent_widget])

    return batcher, overwrite_chooser, progress_updater


class BatcherManagerQuick:

  def __init__(self, item_tree, settings):
    self._item_tree = item_tree
    self._settings = settings

    self._batcher = None

  def run_batcher(
        self,
        mode,
        image,
        item_tree,
        parent_widget,
        progress_bar,
  ):
    self._settings.apply_gui_values_to_settings()

    self._batcher, overwrite_chooser, progress_updater = self._set_up_batcher(
      mode, parent_widget, progress_bar)

    try:
      self._batcher.run(
        item_tree=item_tree,
        **utils_.get_settings_for_batcher(self._settings['main']))
    except exceptions.BatcherCancelError:
      pass
    except exceptions.BatcherError as e:
      messages_.display_processing_failure_message(e, parent=parent_widget)
    except Exception:
      if image.is_valid():
        raise
      else:
        messages_.display_invalid_image_failure_message(parent=parent_widget)
    else:
      if mode == 'export' and not self._batcher.exported_items:
        messages_.display_message(
          _('No layers were exported.'), Gtk.MessageType.INFO, parent=parent_widget)

    if (mode == 'export'
        and overwrite_chooser.overwrite_mode
          in self._settings['main/overwrite_mode'].items.values()):
      self._settings['main/overwrite_mode'].set_value(overwrite_chooser.overwrite_mode)

  def stop_batcher(self):
    _stop_batcher(self._batcher)

  def _set_up_batcher(self, mode, parent_widget, progress_bar):
    if mode == 'export':
      if self._settings['gui/show_quick_settings'].value:
        overwrite_chooser = _get_interactive_overwrite_chooser(parent_widget)
        initial_export_run_mode = Gimp.RunMode.INTERACTIVE
      else:
        overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
          self._settings['main/overwrite_mode'].value)
        initial_export_run_mode = Gimp.RunMode.WITH_LAST_VALS
    else:
      overwrite_chooser = _get_interactive_overwrite_chooser(parent_widget)
      initial_export_run_mode = Gimp.RunMode.INTERACTIVE

    progress_updater = progress_updater_.GtkProgressUpdater(progress_bar)

    batcher = core.LayerBatcher(
      item_tree=self._item_tree,
      procedures=self._settings['main/procedures'],
      constraints=self._settings['main/constraints'],
      edit_mode=mode == 'edit',
      initial_export_run_mode=initial_export_run_mode,
      overwrite_chooser=overwrite_chooser,
      progress_updater=progress_updater,
      export_context_manager=_handle_gui_in_export,
      export_context_manager_args=[parent_widget])

    return batcher, overwrite_chooser, progress_updater


def _get_interactive_overwrite_chooser(parent_widget):
  return overwrite_chooser_.GtkDialogOverwriteChooser(
    builtin_procedures.INTERACTIVE_OVERWRITE_MODES,
    default_value=overwrite.OverwriteModes.RENAME_NEW,
    default_response=overwrite.OverwriteModes.CANCEL,
    parent=parent_widget)


def _stop_batcher(batcher):
  if batcher is not None:
    batcher.queue_stop()
    return True
  else:
    return False


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
