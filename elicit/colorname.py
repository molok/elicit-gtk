import gtk
import gtk.gdk as gdk
import gobject
from os.path import exists
from find_closest import find_closest

class ColorName(gtk.ComboBox):
  colors = []
  name_palette_path = None
  def __init__(self, name_palette_path, wrap_width=1):
    self.name_palette_path = name_palette_path
    gtk.ComboBox.__init__(self)
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
    name_palette = self.__load_name_palette(name_palette_path)
    for c in name_palette:
      r, g, b, name = c
      # if the color is light
      if ((r + g + b) / 3.) < 128.:
          fg = '#DDDDDD'
      else:
          fg = '#222222'
      bg = "#%02X%02X%02X" % (r, g, b)

      liststore.append((bg, fg, name))
    self.set_model(liststore)

    style = gtk.rc_parse_string('''
                style "my-style" { GtkComboBox::appears-as-list = 1 }
                widget "*" style "my-style"
        ''')
    self.set_name('mycombo')
    self.set_style(style)
    print self



    label = gtk.CellRendererText()
    self.pack_start(label, True)
    self.set_attributes(label, background=0, foreground=1, text=2)
    self.set_wrap_width(wrap_width)
    

    if len(name_palette) > 0:
      self.set_active(0)
    self.show_all()

  # TODO FIXME unused right now
  def select_closest_no(self, r, g, b):
    # TODO return if it's a perfect match or not
    # TODO use kdtree or octree
    shortest = 0x1000000
    closest = ""
    j = 0
    for i in range(len(self.colors)):
      vr, vg, vb, name = self.colors[i]
      d = (r - vr) ** 2 + (g - vg) ** 2 + (b - vb) ** 2
      if d < shortest:
        closest = name
        shortest = d
        j = i
    # return closest,j
    self.set_active(j)

  def select_closest(self, r, g, b):
    res = find_closest(self.name_palette_path, r, g, b)
    if res[-1] == '~':
      self.set_active(int(res[:-1]))
    else:
      self.set_active(int(res))

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

