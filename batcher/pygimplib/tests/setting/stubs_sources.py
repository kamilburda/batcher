"""Stubs primarily to be used in the `test_sources` module."""

from ...setting import sources as sources_


class StubSource(sources_.Source):

  def __init__(self, source_name):
    super().__init__(source_name)

    self.data = []

  def clear(self):
    self.data = []

  def has_data(self):
    return bool(self.data)

  def read_data_from_source(self):
    return self.data

  def write_data_to_source(self, data):
    self.data = data
