from ...setting import sources as sources_


class StubSource(sources_.Source):

  def __init__(self, source_name, source_type):
    super().__init__(source_name, source_type)

    self.data = []

  def clear(self):
    pass

  def has_data(self):
    return False

  def read_data_from_source(self):
    return self.data

  def write_data_to_source(self, data):
    pass
