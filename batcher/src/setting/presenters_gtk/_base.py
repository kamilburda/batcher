from .. import presenter as presenter_


__all__ = [
  'GtkPresenter',
]


class GtkPresenter(presenter_.Presenter):
  """Abstract `setting.Presenter` subclass for GTK GUI widgets."""

  _ABSTRACT = True

  def __init__(self, *args, **kwargs):
    self._event_handler_id = None

    super().__init__(*args, **kwargs)

  def get_sensitive(self):
    return self._widget.get_sensitive()

  def set_sensitive(self, sensitive):
    self._widget.set_sensitive(sensitive)

    super().set_sensitive(sensitive)

  def get_visible(self):
    return self._widget.get_visible()

  def set_visible(self, visible):
    self._widget.set_visible(visible)

    super().set_visible(visible)

  def _connect_value_changed_event(self):
    self._event_handler_id = self._widget.connect(
      self._VALUE_CHANGED_SIGNAL, self._on_value_changed)

  def _disconnect_value_changed_event(self):
    self._widget.disconnect(self._event_handler_id)
    self._event_handler_id = None
