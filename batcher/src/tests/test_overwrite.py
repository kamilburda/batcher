import unittest
import unittest.mock as mock

from src import overwrite


class InteractiveOverwriteChooserStub(overwrite.InteractiveOverwriteChooser):
  
  def __init__(self, values_and_display_names, default_value, default_response):
    super().__init__(values_and_display_names, default_value, default_response)
    
    self._values = list(self.values_and_display_names)
  
  def _choose(self, filepath):
    if self._overwrite_mode not in self._values:
      self._overwrite_mode = self.default_response
    
    return self._overwrite_mode
  
  def set_overwrite_mode(self, overwrite_mode):
    self._overwrite_mode = overwrite_mode


class TestInteractiveOverwriteChooser(unittest.TestCase):
  
  def setUp(self):
    self.values_and_display_names = {
      overwrite.OverwriteModes.SKIP: 'Skip',
      overwrite.OverwriteModes.REPLACE: 'Replace',
      overwrite.OverwriteModes.RENAME_NEW: 'Rename new',
      overwrite.OverwriteModes.RENAME_EXISTING: 'Rename existing',
    }
    self.default_response = overwrite.OverwriteModes.SKIP
    self.overwrite_chooser = InteractiveOverwriteChooserStub(
      self.values_and_display_names, overwrite.OverwriteModes.REPLACE, self.default_response)
  
  def test_choose_overwrite_default_value(self):
    self.overwrite_chooser.choose()
    self.assertEqual(self.overwrite_chooser.overwrite_mode, overwrite.OverwriteModes.REPLACE)

  def test_choose_overwrite(self):
    for mode in self.values_and_display_names:
      self.overwrite_chooser.set_overwrite_mode(mode)
      self.overwrite_chooser.choose()
      self.assertEqual(self.overwrite_chooser.overwrite_mode, mode)
    
  def test_choose_overwrite_default_response(self):
    self.overwrite_chooser.set_overwrite_mode('unrecognized_value')
    self.overwrite_chooser.choose()
    self.assertEqual(self.overwrite_chooser.overwrite_mode, self.default_response)


class TestHandleOverwrite(unittest.TestCase):
  
  def setUp(self):
    self.filepath = '/test/image.png'
    self.overwrite_chooser = overwrite.NoninteractiveOverwriteChooser(
      overwrite.OverwriteModes.REPLACE)
  
  @mock.patch('batcher.src.overwrite.os.path.exists')
  def test_handle_overwrite_file_exists(self, mock_os_path_exists):
    mock_os_path_exists.return_value = True
    
    self.assertEqual(
      overwrite.handle_overwrite(self.filepath, self.overwrite_chooser),
      (self.overwrite_chooser.overwrite_mode, self.filepath))
  
  @mock.patch('batcher.src.overwrite.os.path.exists')
  def test_handle_overwrite_file_does_not_exist(self, mock_os_path_exists):
    mock_os_path_exists.return_value = False
    
    self.assertEqual(
      overwrite.handle_overwrite(self.filepath, self.overwrite_chooser),
      (overwrite.OverwriteModes.DO_NOTHING, self.filepath))
