"""Custom exception classes related to batch processing or export."""

from typing import Optional


class BatcherError(Exception):
  pass


class BatcherCancelError(BatcherError):
  pass


class ActionError(BatcherError):
  
  def __init__(self, message, action, item, traceback):
    super().__init__(message)
    
    self.message = message
    self.action = action
    self.item = item
    self.traceback = traceback


class SkipAction(BatcherError):
  pass


class InvalidPdbProcedureError(BatcherError):
  pass


class ExportError(BatcherError):
  
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
      str_ += '\n{} {}'.format(_('Layer:'), self.item_name)
    if self.file_extension:
      str_ += '\n{} {}'.format(_('File extension:'), self.file_extension)
    
    return str_


class InvalidOutputDirectoryError(ExportError):
  pass
