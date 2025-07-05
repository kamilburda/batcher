import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from src import setting as setting_


def assert_contents(test_case, settings, _orig_setting_values):
  test_case.assertEqual(
    settings['main/output_directory'].gui_type, setting_.FileChooserPresenter)
  test_case.assertIsInstance(settings['main/output_directory'].value, Gio.File)
  test_case.assertEqual(
    settings['main/output_directory'].action, Gimp.FileChooserAction.SELECT_FOLDER)
