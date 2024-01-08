import unittest

from ...setting import meta as meta_
from ...setting import settings as settings_
from ...setting import presenters_gtk


class TestSettingTypeFunctions(unittest.TestCase):

  def test_process_setting_type_with_name(self):
    self.assertEqual(meta_.process_setting_type('int'), settings_.IntSetting)

  def test_process_setting_type_with_type(self):
    self.assertEqual(meta_.process_setting_type(settings_.IntSetting), settings_.IntSetting)

  def test_process_setting_type_with_invalid_name(self):
    with self.assertRaises(TypeError):
      meta_.process_setting_type('invalid_type')

  def test_process_setting_type_with_invalid_type(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      meta_.process_setting_type(object())


class TestSettingGuiTypeFunctions(unittest.TestCase):

  def test_process_setting_gui_type_with_name(self):
    self.assertEqual(
      meta_.process_setting_gui_type('check_button'),
      presenters_gtk.CheckButtonPresenter)

  def test_process_setting_gui_type_with_type(self):
    self.assertEqual(
      meta_.process_setting_gui_type(presenters_gtk.CheckButtonPresenter),
      presenters_gtk.CheckButtonPresenter)

  def test_process_setting_gui_type_with_invalid_name(self):
    with self.assertRaises(TypeError):
      meta_.process_setting_gui_type('invalid_type')

  def test_process_setting_gui_type_with_invalid_type(self):
    with self.assertRaises(TypeError):
      # noinspection PyTypeChecker
      meta_.process_setting_gui_type(object())
