import gtk
#import gtk.gdk as gdk
import gobject
#from os.path import exists

class NamePalette(gtk.Widget):

  __gsignals__ = {
      'colorname-changed' : (gobject.SIGNAL_RUN_FIRST,
                             gobject.TYPE_NONE,
                             (gobject.TYPE_PYOBJECT,)
                            )
      }

  def __init__(self, palette_path, color):
    # TODO WTF
    super(NamePalette, self).__init__()
    self.palette_path = palette_path
    self.palette = self.__load_name_palette()
    self.color = color

  def __load_name_palette(self):
    try:
      f = open(self.palette_path, 'r')
      self.colors = []
      palette = set()
      for l in f:
        foo = l.rstrip().split(None,3)
        try:
          rgb = [int(x) for x in foo[:3]]
          name, = foo[3:]
        except:
          continue
        k = ':'.join(foo[:3])
        if k not in palette:
          palette.add(k)
          self.colors.append(rgb + [name])
      f.close()
      return self.colors
    except IOError as (errno, strerror):
      print "error: failed to open {0}: {1}".format(self.palette_path, strerror)

  def closest(self, r, g, b):
    shortest = 0x1000000
    closest = ""
    #j = 0
    is_exact_match = False
    for i in range(len(self.palette)):
      vr, vg, vb, name = self.palette[i]
      d = (r - vr) ** 2 + (g - vg) ** 2 + (b - vb) ** 2
      if d == 0:
        closest = name
        sr, sg, sb = vr, vg, vb
        is_exact_match=True
        break
      if d < shortest:
        closest = name
        sr, sg, sb = vr, vg, vb
        shortest = d
    ret = {}
    ret['name'] = closest
    ret['is_exact_match'] = is_exact_match
    ret['r'] = sr
    ret['g'] = sg
    ret['b'] = sb
    self.emit('colorname-changed', ret)

class ColorLabel(gtk.Label):
  def __init__(self):
    super(ColorLabel, self).__init__()

  def colorname_changed(self, widget, color_dict):
    if color_dict['is_exact_match']:
      suffix = ''
    else:
      suffix = ' (approx.)'
    text = color_dict['name'] + suffix
    self.set_text(text)

class ColorName(gtk.TreeView):

  def __init__(self, name_palette):
    self.name_palette = name_palette
    super(ColorName, self).__init__()
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
    for c in name_palette.palette:
      r, g, b, name = c

      # if the color is light (RGB Luminance formula)
      if (r * 0.299 + g * 0.587 + b * 0.114) < 127.5:
          fg = '#FFFFFF'
      else:
          fg = '#000000'
      bg = "#%02X%02X%02X" % (r, g, b)

      liststore.append((bg, fg, name))
    self.set_model(liststore)
    self.column = gtk.TreeViewColumn('Color')
    self.append_column(self.column)
    label = gtk.CellRendererText()
    self.column.pack_start(label, True)
    self.column.set_attributes(label, background=0, foreground=1, text=2)
    self.connect('row-activated', self.cb_row_activated)

  def hex_to_rgb(self, value):
      value = value.lstrip('#')
      lv = len(value)
      return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

  def cb_row_activated(self, widget, row, col):
    model = widget.get_model()
    hex = model[row][0]
    self.name_palette.color.set_hex(hex)
    #rgb = self.hex_to_rgb(hex)
    #ret = rgb
    #ret.append(model[row][2])
    #self.emit('colorname-changed', rgb)

