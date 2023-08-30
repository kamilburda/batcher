import io
import sys
import unittest

import mock
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
  @mock.patch(pgutils.get_pygimplib_module_path() + '.logging.os.makedirs')
  @mock.patch('builtins.open')
  def test_create_log_file(
        self,
        test_case_name_suffix,
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
