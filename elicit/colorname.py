import gtk
#import gtk.gdk as gdk
import gobject
from os.path import exists
from find_closest import find_closest_init, find_closest

class ColorName(gtk.ComboBox):
  colors = []
  colors_s = ''
  name_palette_path = None
  def __init__(self, name_palette_path):
    self.name_palette_path = name_palette_path
    gtk.ComboBox.__init__(self)
    liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
                              gobject.TYPE_STRING)
    name_palette = self.__load_name_palette(name_palette_path)

    for x in self.colors:
      self.colors_s += '%d, %d, %d\n' % (x[0], x[1], x[2])
    find_closest_init(self.colors_s)

    for c in name_palette:
      r, g, b, name = c
      # if the color is light
      if ((r + g + b) / 3.) < 128.:
          fg = '#FFFFFF'
      else:
          fg = '#000000'
      bg = "#%02X%02X%02X" % (r, g, b)

      liststore.append((bg, fg, name))
    self.set_model(liststore)

    self.set_name('colorname')
    # show a scrollbar
    gtk.rc_parse_string('''
                style "my-style" { GtkComboBox::appears-as-list = 1 }
                widget "*.colorname" style "my-style"
        ''')

    label = gtk.CellRendererText()
    self.pack_start(label, True)
    self.set_attributes(label, background=0, foreground=1, text=2)

    if len(name_palette) > 0:
      self.set_active(0)

  def select_closest__(self, r, g, b):
    pass
    #import time
    #from random import randint
    #x = time.time()
    #self.set_active(randint(0, 10))
    #time.sleep(0.003)
    #print 'it tooks: %.4f' % (time.time() -x )


  # This takes about 3ms on my machine
  def select_closest(self, r, g, b):
    #DEBUG
    #import time
    #x = time.time()
    #print 'IN'
    # TODO return if it's a perfect match or not
    # TODO use kdtree or octree
    shortest = 0x1000000
    closest = ""
    j = 0
    #loop = time.time()
    for i in range(len(self.colors)):
      vr, vg, vb, name = self.colors[i]
      d = (r - vr) ** 2 + (g - vg) ** 2 + (b - vb) ** 2
      if d < shortest:
        closest = name
        shortest = d
        j = i
    #print 'loop: %.4f' % (time.time() -loop )
    # return closest,j
    #z = time.time()
    self.set_active(j)
    #print 'set_active: %.4f' % (time.time() -z )
    #print 'it tooks: %.4f' % (time.time() -x )

  def select_closest_(self, r, g, b):
    #print self.colors_s
    #import time
    #x = time.time()
    res = find_closest(r, g, b)
    if res[-1] == '~':
      self.set_active(int(res[:-1]))
    else:
      self.set_active(int(res))
    #print 'it tooks: %.4f' % (time.time() -x )

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

