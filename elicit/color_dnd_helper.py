import gtk
import glib
from color import Color
import struct

class ColorDndHelper:
  TARGET_TYPE_COLOR = 1
  TARGET_TYPE_TEXT  = 2

  drag_targets = [
      ("application/x-color", 0, TARGET_TYPE_COLOR),
      ("text/plain", 0, TARGET_TYPE_TEXT),
  ]

  def __init__(self, widget, cb_set_color=None, cb_get_color=None, drag_button_mask = gtk.gdk.BUTTON1_MASK):
    self.widget = widget
    self.cb_set_color = cb_set_color
    self.cb_get_color = cb_get_color

    self.drag_color = None
    self.swatch_size = 32
    self.hot_x = self.hot_y = 0

    if self.cb_set_color:
      self.widget.drag_dest_set(0, self.drag_targets, gtk.gdk.ACTION_COPY)
      self.widget.connect('drag-motion', self.cb_drag_motion)
      self.widget.connect('drag-leave', self.cb_drag_leave)
      self.widget.connect('drag-drop', self.cb_drag_drop)
      self.widget.connect('drag-data-received', self.cb_drag_data_received)

    if self.cb_get_color:
      self.widget.drag_source_set(drag_button_mask, self.drag_targets, gtk.gdk.ACTION_COPY)
      self.widget.connect('drag-begin', self.cb_drag_begin)
      self.widget.connect('drag-end', self.cb_drag_end)
      self.widget.connect('drag-data-get', self.cb_drag_data_get)
      #self.widget.connect('drag-failed', self.cb_drag_failed)

  def set_swatch_size(self, size):
    self.swatch_size = size

  def set_hot_spot(self, hot_x, hot_y):
    self.hot_x = hot_x
    self.hot_y = hot_y

  def cb_drag_motion(self, wid, context, x, y, time):
    for target in self.drag_targets:
      if target[0] in context.targets:
        action = gtk.gdk.ACTION_COPY

        if context.get_source_widget() == self.widget:
          action = gtk.gdk.ACTION_MOVE

        context.drag_status(action, time)
        self.widget.drag_highlight()
        return True

    return False

  def cb_drag_drop(self, wid, context, x, y, time):
    for target in self.drag_targets:
      if target[0] in context.targets:
        self.widget.drag_get_data(context, target[0], time)
        break

  def cb_drag_leave(self, wid, context, time):
    self.widget.drag_unhighlight()

  def cb_drag_data_received(self, widget, context, x, y, selection, target_type, time):
    success = False
    valid = False
    color = Color()

    if selection.data != None:
      try:
        if target_type == self.TARGET_TYPE_COLOR:
          col = struct.unpack("HHHH", selection.data)
          color.set_rgb16(*col[0:3])
          valid = True
        elif target_type == self.TARGET_TYPE_TEXT:
          color.set_hex(selection.data)
          valid = True
      except ValueError, struct.error:
        print("Invalid data dropped")

    if valid:
      success = self.cb_set_color(color, x, y)

    if (success and context.action == gtk.gdk.ACTION_MOVE):
      context.finish(success, True, time)
    else:
      context.finish(success, False, time)

    return success

  def build_icon_pixbuf(self, color):
    w = h = self.swatch_size
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, w, h)
    pixels = pb.get_pixels_array()

    for x in range(0,w):
      for y in range(0,h):
        #border
        if x == 0 or y == 0 or x == w-1 or y == h -1:
          pixels[y,x] = (64,64,64)
        else:
          pixels[y,x] = color.rgb()

    return pb

  def cb_drag_begin(self, widget, context):
    self.drag_color = self.cb_get_color()

    if not self.drag_color: return False

    icon_pixbuf = self.build_icon_pixbuf(self.drag_color)
    context.set_icon_pixbuf(icon_pixbuf, self.hot_x, self.hot_y)

    return True

  def cb_drag_end(self, widget, context):
    pass

  def cb_drag_data_get(self, widget, context, selection, target_type, time):
    if target_type == self.TARGET_TYPE_COLOR:
      data = struct.pack("HHHH", *(self.drag_color.rgb16()+(65535,)))
      selection.set("application/x-color", 16, data)
    elif target_type == self.TARGET_TYPE_TEXT:
      data = self.drag_color.hex()
      selection.set_text(data, 7)

