"""Widget holding an array of GUI widgets.

The widget is used as the default GUI for `setting.ArraySetting` instances.
"""

from __future__ import annotations

import collections
import contextlib
from typing import Optional

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .. import utils as pgutils

from . import drag_and_drop_context as drag_and_drop_context_

__all__ = [
  'ItemBox',
  'ArrayBox',
  'ItemBoxItem',
]


class ItemBox(Gtk.ScrolledWindow):
  """Base class for a scrollable box holding a vertical list of items.

  Each item is an instance of the `ItemBoxItem` class or one of its subclasses.
  """
  
  ITEM_SPACING = 3
  VBOX_SPACING = 4
  
  def __init__(self, item_spacing: int = ITEM_SPACING, **kwargs):
    super().__init__(**kwargs)
    
    self._item_spacing = item_spacing
    
    self._drag_and_drop_context = drag_and_drop_context_.DragAndDropContext()
    self._items = []
    
    self._vbox_items = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      homogeneous=False,
      spacing=self._item_spacing,
    )
    
    self._vbox = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
      homogeneous=False,
      spacing=self.VBOX_SPACING,
    )
    self._vbox.pack_start(self._vbox_items, False, False, 0)

    self.add(self._vbox)
    self.get_child().set_shadow_type(Gtk.ShadowType.NONE)
  
  @property
  def items(self):
    return self._items
  
  def add_item(self, item: ItemBoxItem) -> ItemBoxItem:
    self._vbox_items.pack_start(item.widget, False, False, 0)
    
    item.button_remove.connect('clicked', self._on_item_button_remove_clicked, item)
    item.widget.connect('key-press-event', self._on_item_widget_key_press_event, item)
    
    self._setup_drag(item)
    
    self._items.append(item)
    
    return item
  
  def reorder_item(self, item: ItemBoxItem, position: int) -> int:
    new_position = min(max(position, 0), len(self._items) - 1)
    
    self._items.pop(self._get_item_position(item))
    self._items.insert(new_position, item)
    
    self._vbox_items.reorder_child(item.widget, new_position)
    
    return new_position
  
  def remove_item(self, item: ItemBoxItem):
    item_position = self._get_item_position(item)
    if item_position < len(self._items) - 1:
      next_item_position = item_position + 1
      self._items[next_item_position].item_widget.grab_focus()
    
    self._vbox_items.remove(item.widget)
    
    self._items.remove(item)
  
  def clear(self):
    for _unused in range(len(self._items)):
      self.remove_item(self._items[0])
  
  def _setup_drag(self, item):
    self._drag_and_drop_context.setup_drag(
      item.widget,
      self._get_drag_data,
      self._on_drag_data_received,
      [item],
      [item],
    )
  
  def _get_drag_data(self, dragged_item):
    return bytes([self._items.index(dragged_item)])
  
  def _on_drag_data_received(self, dragged_item_index_as_bytes, destination_item):
    dragged_item = self._items[list(dragged_item_index_as_bytes)[0]]
    self.reorder_item(dragged_item, self._get_item_position(destination_item))

  def _on_item_widget_key_press_event(self, widget, event, item):
    if event.state & Gdk.ModifierType.MOD1_MASK:     # Alt key
      key_name = Gdk.keyval_name(event.keyval)
      if key_name in ['Up', 'KP_Up']:
        self.reorder_item(item, self._get_item_position(item) - 1)
      elif key_name in ['Down', 'KP_Down']:
        self.reorder_item(item, self._get_item_position(item) + 1)
  
  def _on_item_button_remove_clicked(self, button, item):
    self.remove_item(item)
  
  def _get_item_position(self, item):
    return self._items.index(item)


class ItemBoxItem:
  
  _HBOX_BUTTONS_SPACING = 3
  _HBOX_SPACING = 3
  
  def __init__(self, item_widget: Gtk.Widget, button_display_mode='on_hover'):
    self._item_widget = item_widget
    self._button_display_mode = button_display_mode

    self._hbox_indicator_buttons = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=self._HBOX_BUTTONS_SPACING,
    )
    
    self._event_box_indicator_buttons = Gtk.EventBox()
    self._event_box_indicator_buttons.add(self._hbox_indicator_buttons)
    
    self._hbox_buttons = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      homogeneous=False,
      spacing=self._HBOX_BUTTONS_SPACING,
    )
    
    self._event_box_buttons = Gtk.EventBox()
    self._event_box_buttons.add(self._hbox_buttons)

    self._hbox = Gtk.Box(
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._HBOX_SPACING,
    )
    self._hbox.pack_start(self._event_box_indicator_buttons, False, False, 0)
    self._hbox.pack_start(self._item_widget, True, True, 0)
    self._hbox.pack_start(self._event_box_buttons, False, False, 0)

    self._vbox = Gtk.Box(
      orientation=Gtk.Orientation.VERTICAL,
    )
    self._vbox.pack_start(self._hbox, False, False, 0)

    self._event_box = Gtk.EventBox()
    self._event_box.add(self._vbox)
    
    self._has_hbox_buttons_focus = False

    self._button_remove = self._setup_item_button(icon=GimpUi.ICON_WINDOW_CLOSE)

    self._is_event_box_allocated_size = False
    self._buttons_allocation = None

    if self._button_display_mode == 'on_hover':
      self._event_box.connect('enter-notify-event', self._on_event_box_enter_notify_event)
      self._event_box.connect('leave-notify-event', self._on_event_box_leave_notify_event)
      self._event_box.connect('size-allocate', self._on_event_box_size_allocate)
      self._event_box_buttons.connect('size-allocate', self._on_event_box_buttons_size_allocate)
    
    self._event_box.show_all()

    if self._button_display_mode == 'on_hover':
      self._hbox_buttons.set_no_show_all(True)
      self._hbox_indicator_buttons.set_no_show_all(True)
  
  @property
  def widget(self) -> Gtk.Widget:
    return self._event_box

  @property
  def vbox(self) -> Gtk.Box:
    return self._vbox

  @property
  def item_widget(self) -> Gtk.Widget:
    return self._item_widget

  @property
  def button_remove(self) -> Gtk.Button:
    return self._button_remove

  def _setup_item_button(self, icon=None, text=None, position=None, button_class=Gtk.Button):
    return self._setup_button(self._hbox_buttons, icon, text, position, button_class)
  
  def _setup_item_indicator_button(self, icon=None, text=None, position=None):
    button = self._setup_button(self._hbox_indicator_buttons, icon, text, position)
    button.connect('notify::visible', self._on_indicator_button_visible_changed)
    return button

  @staticmethod
  def _setup_button(
        hbox, icon_name_or_image=None, text=None, position=None, button_class=Gtk.Button):
    if not issubclass(button_class, Gtk.Button):
      raise TypeError('button_class must be the Gtk.Button class or one of its subclasses')

    button = button_class()

    if icon_name_or_image is not None:
      if isinstance(icon_name_or_image, Gtk.Image):
        button.set_image(icon_name_or_image)
      else:
        button.set_image(Gtk.Image.new_from_icon_name(icon_name_or_image, Gtk.IconSize.BUTTON))

    if text is not None:
      button.set_label(text)

    button.set_relief(Gtk.ReliefStyle.NONE)

    hbox.pack_start(button, False, False, 0)
    if position is not None:
      hbox.reorder_child(button, position)

    button.show_all()

    return button
  
  def _on_event_box_enter_notify_event(self, _event_box, event):
    if event.detail != Gdk.NotifyType.INFERIOR:
      self._hbox_buttons.show()
  
  def _on_event_box_leave_notify_event(self, _event_box, event):
    if event.detail != Gdk.NotifyType.INFERIOR:
      self._hbox_buttons.hide()
  
  def _on_event_box_size_allocate(self, _event_box, allocation):
    if not self._is_event_box_allocated_size and self._buttons_allocation is not None:
      self._is_event_box_allocated_size = True
      
      # Assign enough height to the box to make sure it does not resize when showing buttons.
      if self._buttons_allocation.height >= allocation.height:
        self._hbox.set_property('height-request', allocation.height)
  
  def _on_event_box_buttons_size_allocate(self, _event_box, allocation):
    # Checking for 1-pixel width and height prevents wrong size from being allocated
    # when parent widgets are resized.
    if self._buttons_allocation is None and allocation.width > 1 and allocation.height > 1:
      self._buttons_allocation = allocation
      
      # Make sure the width allocated to the buttons remains the same even if
      # buttons are hidden. This avoids a problem with unreachable buttons when
      # the horizontal scrollbar is displayed.
      self._event_box_buttons.set_property('width-request', self._buttons_allocation.width)
      
      self._hbox_buttons.hide()

  def _on_indicator_button_visible_changed(self, _button, _property_spec):
    any_indicator_button_is_visible = any(
      child.get_visible() for child in self._hbox_indicator_buttons.get_children())

    if any_indicator_button_is_visible:
      self._event_box_indicator_buttons.show()
    else:
      self._event_box_indicator_buttons.hide()


class ArrayBox(ItemBox):
  """Class suitable for interactively editing arrays of values.

  This class can be used to edit, for example, `setting.ArraySetting`
  instances interactively.
  
  Signals:
    array-box-changed:
      An item was added, reordered or removed by the user.
    array-box-item-changed:
      The contents of an item were modified by the user. Currently,
      this signal is not invoked in this widget and can only be invoked
      explicitly by calling ``ArrayBox.emit('array-box-item-changed')``.
  """
  
  __gsignals__ = {
    'array-box-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    'array-box-item-changed': (GObject.SignalFlags.RUN_FIRST, None, ())}
  
  def __init__(
        self,
        new_item_default_value,
        min_size: int = 0,
        max_size: Optional[int] = None,
        item_spacing: int = ItemBox.ITEM_SPACING,
        **kwargs):
    """Initializes an `ArrayBox` instance.

    Args:
      new_item_default_value:
        Default value for new items
      min_size:
        Minimum number of items.
      max_size:
        Maximum number of items. If ``None``, the number of items is unlimited.
      item_spacing:
        Vertical spacing in pixels between items.
      **kwargs:
        Additional keyword arguments that can be passed to the
        `Gtk.ScrolledWindow()` constructor.
    """
    super().__init__(item_spacing=item_spacing, **kwargs)
    
    self._new_item_default_value = new_item_default_value
    self._min_size = min_size if min_size >= 0 else 0
    
    if max_size is None:
      self._max_size = GLib.MAXINT
    else:
      self._max_size = max_size if max_size >= min_size else min_size
    
    self.on_add_item = pgutils.empty_func
    """Callback that creates a `Gtk.Widget` when calling `add_item`.
    
    The callback must accept two arguments - value for the new widget and
    index (position starting from 0) at which the new widget will be inserted.
    
    The callback must return a single argument - the new `Gtk.Widget` instance.
    """

    self.on_reorder_item = pgutils.empty_func
    """Callback triggered when calling `reorder_item`.
    
    The callback must accept two arguments - original and new index (position
    starting from 0).
    """

    self.on_remove_item = pgutils.empty_func
    """Callback triggered when calling `remove_item`.
    
    The callback must accept one argument - the index (position starting from 0)
    of the removed item.
    """
    
    self._items_total_width = None
    self._items_total_height = None
    self._items_allocations = {}
    self._locker = _ActionLocker()
    
    self._init_gui()
  
  def _init_gui(self):
    self._size_spin_button = Gtk.SpinButton(
      adjustment=Gtk.Adjustment(
        value=0,
        lower=self._min_size,
        upper=self._max_size,
        step_increment=1,
        page_increment=10,
      ),
      digits=0,
      numeric=True,
    )

    self._vbox.pack_start(self._size_spin_button, False, False, 0)
    self._vbox.reorder_child(self._size_spin_button, 0)

    separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
    self._vbox.pack_start(separator, False, False, 0)
    self._vbox.reorder_child(separator, 1)

    self._size_spin_button.connect('value-changed', self._on_size_spin_button_value_changed)

  def add_item(self, item_value=None, index: Optional[int] = None):
    if item_value is None:
      item_value = self._new_item_default_value

    item = ItemBoxItem(self.on_add_item(item_value, index))
    
    super().add_item(item)

    if index is not None:
      with self._locker.lock_temp('emit_array_box_changed_on_reorder'):
        self.reorder_item(item, index)
    
    if self._locker.is_unlocked('update_spin_button'):
      with self._locker.lock_temp('emit_size_spin_button_value_changed'):
        self._size_spin_button.spin(Gtk.SpinType.STEP_FORWARD, increment=1)
    
    return item
  
  def reorder_item(self, item: ItemBoxItem, new_position: int):
    orig_position = self._get_item_position(item)
    processed_new_position = super().reorder_item(item, new_position)
    
    self.on_reorder_item(orig_position, processed_new_position)
    
    if self._locker.is_unlocked('emit_array_box_changed_on_reorder'):
      self.emit('array-box-changed')
  
  def remove_item(self, item: ItemBoxItem):
    if (self._locker.is_unlocked('prevent_removal_below_min_size')
        and len(self._items) == self._min_size):
      return
    
    if self._locker.is_unlocked('update_spin_button'):
      with self._locker.lock_temp('emit_size_spin_button_value_changed'):
        self._size_spin_button.spin(Gtk.SpinType.STEP_BACKWARD, increment=1)
    
    item_position = self._get_item_position(item)
    
    super().remove_item(item)
    
    if item in self._items_allocations:
      self._update_height(-(self._items_allocations[item].height + self._item_spacing))
      del self._items_allocations[item]
    
    self.on_remove_item(item_position)
  
  def set_values(self, values):
    self._locker.lock('emit_size_spin_button_value_changed')
    self._locker.lock('prevent_removal_below_min_size')
    
    orig_on_remove_item = self.on_remove_item
    self.on_remove_item = pgutils.empty_func
    
    self.clear()
    
    # This fixes an issue of items being allocated height of 1 when the array
    # size was previously 0.
    self.set_property('height-request', -1)
    
    for index, value in enumerate(values):
      self.add_item(value, index)
    
    self.on_remove_item = orig_on_remove_item
    
    self._size_spin_button.set_value(len(values))
    
    self._locker.unlock('prevent_removal_below_min_size')
    self._locker.unlock('emit_size_spin_button_value_changed')
  
  def _on_size_spin_button_value_changed(self, size_spin_button):
    if self._locker.is_unlocked('emit_size_spin_button_value_changed'):
      self._locker.lock('update_spin_button')
      
      new_size = size_spin_button.get_value_as_int()
      
      if new_size > len(self._items):
        num_items_to_add = new_size - len(self._items)
        for _unused in range(num_items_to_add):
          self.add_item()
      elif new_size < len(self._items):
        num_items_to_remove = len(self._items) - new_size
        for _unused in range(num_items_to_remove):
          self.remove_item(self._items[-1])
      
      self.emit('array-box-changed')
      
      self._locker.unlock('update_spin_button')
  
  def _on_item_button_remove_clicked(self, button, item):
    self._locker.lock('emit_size_spin_button_value_changed')
    
    should_emit_signal = (
      len(self._items) > self._min_size
      or self._locker.is_locked('prevent_removal_below_min_size'))

    # noinspection PyProtectedMember
    super()._on_item_button_remove_clicked(button, item)
    
    if should_emit_signal:
      self.emit('array-box-changed')
    
    self._locker.unlock('emit_size_spin_button_value_changed')


class _ActionLocker:
  
  def __init__(self):
    self._tokens = collections.defaultdict(int)
  
  @contextlib.contextmanager
  def lock_temp(self, key: str) -> contextlib.AbstractContextManager:
    self.lock(key)
    try:
      yield
    finally:
      self.unlock(key)
  
  def lock(self, key: str):
    self._tokens[key] += 1
  
  def unlock(self, key: str):
    if self._tokens[key] > 0:
      self._tokens[key] -= 1
  
  def is_locked(self, key: str) -> bool:
    return self._tokens[key] > 0
  
  def is_unlocked(self, key: str) -> bool:
    return self._tokens[key] == 0


GObject.type_register(ArrayBox)
