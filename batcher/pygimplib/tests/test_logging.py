import sys
import io

import unittest
import unittest.mock as mock

import parameterized

from .. import logging as pglogging
from .. import utils as pgutils


class TestCreateLogFile(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ('valid_file_and_first_dirpath',
     ['file'], [None, None], 'file', 1),
    
    ('valid_file_and_second_dirpath',
     ['file'], [OSError(), None], 'file', 2),
    
    ('valid_file_invalid_dirpath',
     ['file'], [OSError(), OSError()], None, 2),
    
    ('valid_second_file',
     [IOError(), 'file'], [None, None], 'file', 2),
    
    ('invalid_file',
     IOError(), [None, None], None, 2),
  ])
  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.logging.os.makedirs')
  @mock.patch(f'{pgutils.get_pygimplib_module_path()}.logging.open')
  def test_create_log_file(
        self,
        _test_case_suffix,
        io_open_side_effect,
        makedirs_side_effect,
        expected_result,
        expected_num_calls_makedirs,
        mock_io_open,
        mock_makedirs):
    log_dirpaths = ['dirpath_1', 'dirpath_2']
    log_filename = 'output.log'
    
    mock_io_open.side_effect = io_open_side_effect
    mock_makedirs.side_effect = makedirs_side_effect

    log_file = pglogging.create_log_file(log_dirpaths, log_filename)
    
    self.assertEqual(log_file, expected_result)
    self.assertEqual(mock_makedirs.call_count, expected_num_calls_makedirs)


@mock.patch('sys.stdout', new=io.StringIO())
class TestTee(unittest.TestCase):

  def setUp(self):
    self.string_files = [io.StringIO()]

  def test_write(self):
    tee = pglogging.Tee(sys.stdout, log_header_title='Test Header')
    tee.start(self.string_files)

    print('Hello')
    self.assertTrue(self.string_files[0].getvalue().endswith('Hello\n'))
    self.assertTrue('Test Header' in self.string_files[0].getvalue())

    print('Hi There Again')
    self.assertTrue(self.string_files[0].getvalue().endswith('Hello\nHi There Again\n'))

  def test_stop(self):
    tee_stdout = pglogging.Tee(
      sys.stdout,
      log_header_title='Test Header')

    print('Hi There')
    self.assertFalse(self.string_files[0].getvalue().endswith('Hi There\n'))

    tee_stdout.start(self.string_files)

    print('Hello')
    self.assertTrue(self.string_files[0].getvalue().endswith('Hello\n'))

    string_value = self.string_files[0].getvalue()
    tee_stdout.stop()

    print('Hi There Again')
    self.assertFalse(string_value.endswith('Hi There Again\n'))

  def test_invalid_stream(self):
    with self.assertRaises(ValueError):
      # noinspection PyTypeChecker
      pglogging.Tee('invalid_stream', log_header_title='Test Header')
