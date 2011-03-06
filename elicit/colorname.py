import gtk
#import gtk.gdk as gdk
import gobject
from os.path import exists

class ColorName(gtk.ComboBox):
  colors = []
  name_palette_path = None
  def __init__(self, name_palette_path):
    self.name_palette_path = name_palette_path
    gtk.ComboBox.__init__(self)
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
    name_palette = self.__load_name_palette(name_palette_path)

    for c in name_palette:
      r, g, b, name = c

      # if the color is light (RGB Luminance formula)
      if (r * 0.3 + g * 0.59 + b * 0.11) < 127.5:
          fg = '#FFFFFF'
      else:
          fg = '#000000'
      bg = "#%02X%02X%02X" % (r, g, b)

      liststore.append((bg, fg, name))
    self.set_model(liststore)

    # show a scrollbar
    self.set_name('colorname')
    gtk.rc_parse_string('''
                style "my-style" { GtkComboBox::appears-as-list = 1 }
                widget "*.colorname" style "my-style"
        ''')

    label = gtk.CellRendererText()
    self.pack_start(label, True)
    self.set_attributes(label, background=0, foreground=1, text=2)

    if len(name_palette) > 0:
      self.set_active(0)

  def select_closest(self, r, g, b):
    # TODO return if it's a perfect match or not
    shortest = 0x1000000
    #closest = ""
    j = 0
    for i in range(len(self.colors)):
      vr, vg, vb, name = self.colors[i]
      d = (r - vr) ** 2 + (g - vg) ** 2 + (b - vb) ** 2
      if d < shortest:
        #closest = name
        shortest = d
        j = i
    self.set_active(j)

  def __load_name_palette(self, name_palette_path):
    if exists(name_palette_path):
      try:
        f = open(name_palette_path,'r')
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
        print "error: failed to open {0}: {1}".format(name_palette_path, strerror)
        return []
    else:
      return []

