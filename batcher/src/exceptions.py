"""Custom exception classes related to batch processing or export."""

from typing import Optional


class BatcherError(Exception):
  pass


class BatcherCancelError(BatcherError):
  pass


class BatcherFileLoadError(BatcherError):

  def __init__(self, message, filepath):
    super().__init__(message)

    self.message = message
    self.filepath = filepath

  def __str__(self):
    return self.message


class BatcherFileNotFoundError(BatcherFileLoadError):
  pass


class CommandError(BatcherError):
  
  def __init__(self, message, command, item, traceback=None):
    super().__init__(message)
    
    self.message = message
    self.command = command
    self.item = item
    self.traceback = traceback


class SkipCommand(BatcherError):
  pass


class ImageExportError(BatcherError):
  
  def __init__(
        self,
        message: str = '',
        item_name: Optional[str] = None,
        file_extension: Optional[str] = None,
  ):
    super().__init__()
    
    self._message = message
    self.item_name = item_name
    self.file_extension = file_extension
  
  def __str__(self):
    str_ = self._message
    
    if self.item_name:
      str_ += '\n{} {}'.format(_('Item:'), self.item_name)
    if self.file_extension:
      str_ += '\n{} {}'.format(_('File extension:'), self.file_extension)
    
    return str_


class InvalidOutputDirectoryError(ImageExportError):
  pass
