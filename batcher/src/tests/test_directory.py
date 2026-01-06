import os
import unittest
import unittest.mock as mock

from gi.repository import Gio

from config import CONFIG
from src import directory as directory_
from src.procedure_groups import *


_TEST_SPECIAL_VALUES = {
  'some_value': directory_.SpecialValue(
    'some_value', 'Some value', lambda *args: 'resolved_value', ALL_PROCEDURE_GROUPS),
}


class TestDirectory(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    CONFIG.PROCEDURE_GROUP = CONVERT_GROUP

  @classmethod
  def tearDownClass(cls):
    CONFIG.PROCEDURE_GROUP = CONFIG.PLUGIN_NAME

  def test_default_directory(self):
    directory = directory_.Directory()

    self.assertIsNotNone(directory.value)
    self.assertEqual(directory.type_, directory_.DirectoryTypes.DIRECTORY)

  def test_directory_from_string(self):
    directory = directory_.Directory('some_directory')

    self.assertEqual(directory.value, 'some_directory')
    self.assertEqual(directory.type_, directory_.DirectoryTypes.DIRECTORY)

  def test_directory_from_file(self):
    file = Gio.file_new_for_path(os.path.abspath('some_directory'))

    directory = directory_.Directory(file)

    self.assertEqual(directory.value, file.get_path())
    self.assertEqual(directory.type_, directory_.DirectoryTypes.DIRECTORY)

  def test_special_value(self):
    directory = directory_.Directory('some_value', type_=directory_.DirectoryTypes.SPECIAL)

    self.assertEqual(directory.value, 'some_value')
    self.assertEqual(directory.type_, directory_.DirectoryTypes.SPECIAL)

  def test_special_value_with_none_raises_error(self):
    with self.assertRaises(ValueError):
      directory_.Directory(None, type_=directory_.DirectoryTypes.SPECIAL)

  @mock.patch('src.directory.get_special_values', return_value=_TEST_SPECIAL_VALUES)
  def test_resolve_recognized_special_value(self, _mock_get_special_values):
    directory = directory_.Directory('some_value', type_=directory_.DirectoryTypes.SPECIAL)

    self.assertEqual(directory.resolve(None), 'resolved_value')

  def test_resolve_directory_returns_directory_unchanged(self):
    directory = directory_.Directory('some_directory')

    self.assertEqual(directory.resolve(None), 'some_directory')

  def test_resolve_unrecognized_special_value_returns_special_value_unchanged(self):
    directory = directory_.Directory('some_value', type_=directory_.DirectoryTypes.SPECIAL)

    self.assertEqual(directory.resolve(None), 'some_value')
