import gtk
import gtk.gdk as gdk
from os.path import exists

class ColorName(gtk.ComboBox):
  def __init__(self, name_palette_path, wrap_width=1):
    gtk.ComboBox.__init__(self)
    liststore = gtk.ListStore(gtk.gdk.Color, str)
    name_palette = self.__load_name_palette(name_palette_path)
    for c in name_palette:
      r, g, b, name = c
      r, g, b = [x/255.0 for x in (r,g,b)]
      color = gtk.gdk.Color(r,g,b)
      liststore.append((color,name))
    self.set_model(liststore)

    swatch = gtk.CellRendererText()
    swatch.set_property("width",40)
    self.pack_start(swatch,False)
    self.set_attributes(swatch,background_gdk=0)

    label = gtk.CellRendererText()
    label.set_property("xpad",10)
    # label.set_property('background', '#00b057')
    self.pack_start(label,True)
    self.set_attributes(label,text=1)

    self.set_wrap_width(wrap_width)
    

    if len(name_palette) > 0:
      self.set_active(0)
    self.show_all()

  def __load_name_palette(self, name_palette_path):
    if exists(name_palette_path):
      try:
        f = open(name_palette_path,'r')
        colors = []
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
            colors.append(rgb + [name])
        f.close()
        return colors
      except IOError as (errno, strerror):
        print "error: failed to open {0}: {1}".format(name_palette_path, strerror)
        return []
    else:
      return []

