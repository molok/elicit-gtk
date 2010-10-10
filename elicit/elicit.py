import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import gconf
import os
import math
import appinfo

import xdg.BaseDirectory as base

from magnifier import Magnifier
from colorpicker import ColorPicker

from palette import Palette
from color import Color
from palette_view import PaletteView
from palette_tools import PaletteList, PaletteCombo

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

try:
  import numpy
except ImportError:
  print "Numeric Python (numpy) is required."
  raise SystemExit

# TODO:
# CMYK actual code (pychrom)
# Color Wheel automatic resize
# Color Wheel tab icon
# NameThatColor
# Terminal name
# Refresh after zoom in/out

class Elicit:

  def save(self):
    old_filename = self.palette.filename
    self.palette.save()
    if old_filename == None:
      self.gconf.set_string('/apps/elicit/palette', os.path.basename(self.palette.filename))

  def quit(self, widget=None, data=None):
    self.save()
    gtk.main_quit()

  def main(self):
    gtk.main()

  def show(self):
    self.win.show_all()

  def hide(self):
    self.win.hide()

  def grab(self, x, y, w ,h):
    self.mag.grab(x,y,w,h)

  def mag_grid_toggled(self, mag):
    self.grid_check.set_active(mag.show_grid)

  def mag_zoom_changed(self, mag):
    self.gconf.set_int('/apps/elicit/zoom_level', mag.zoom)

  def mag_measure_changed(self, mag):
    if mag.measure_rect:
      text = "[%dx%d] (%.1f diag) " % (mag.measure_rect.width,
          mag.measure_rect.height,
          math.sqrt(mag.measure_rect.width**2 + mag.measure_rect.height**2)
          )
    else:
      text = ""

    self.measure_label.set_text(text)

  def mag_location_changed(self, mag):
    if mag.screen_rect:
      text = "  (%d,%d) %dx%d" % (mag.screen_rect.x, mag.screen_rect.y,
          mag.screen_rect.width, mag.screen_rect.height)
    else:
      text = ""

    self.mag_label.set_text(text)

  def grid_check_toggled(self, check):
    self.gconf.set_bool('/apps/elicit/show_grid', check.get_active())

  def zoom_spin_value_changed(self, spin):
    self.gconf.set_int('/apps/elicit/zoom_level', int(spin.get_value()))

  def picker_save_color(self, picker):
    c = Color()
    c.set_rgb(*picker.color.rgb())
    self.palette.append(c)
    self.palette_view.select(c)

  def palette_view_select_color(self, palette_view, color):
    if color == None:
      self.color_name_entry.set_text("")
      self.color_name_entry.set_sensitive(False)
    else:
      self.gconf.set_string('/apps/elicit/color', color.hex())
      self.color_name_entry.set_text(color.name)
      self.color_name_entry.set_sensitive(True)

  def palette_view_delete_color(self, palette_view, color):
    self.palette.remove(color)

  def wheel_changed(self, wheel):
    h, s, v = wheel.get_color()
    h = h * 360.
    h_o, s_o, v_o = self.color.hsv()
    if h_o != h or s_o != s or v_o != v:
      self.color.set_hsv(h, s, v)

  def color_name_entry_changed(self, color_name_entry):
    if self.palette and self.palette_view.selected:
      self.palette_view.selected.name = color_name_entry.get_text()

  def color_changed(self, color):
    for type in 'r', 'g', 'b', 'h', 's', 'v':
      self.colorspin[type].handler_block(self.h_ids[type])

    self.hex_entry.handler_block(self.h_ids['hex'])
    self.wheel.handler_block(self.h_ids['wheel'])

    self.colorspin['r'].set_value(self.color.r)
    self.colorspin['g'].set_value(self.color.g)
    self.colorspin['b'].set_value(self.color.b)

    self.colorspin['h'].set_value(self.color.h)
    self.colorspin['s'].set_value(self.color.s)
    self.colorspin['v'].set_value(self.color.v)

    self.hex_entry.set_text(self.color.hex())

    h, s, v = color.hsv()
    self.wheel.set_color(h / 360., s, v)

    if self.palette_view.selected and color.hex() != self.palette_view.selected.hex():
      self.palette_view.select(None)

    for type in 'r', 'g', 'b', 'h', 's', 'v':
      self.colorspin[type].handler_unblock(self.h_ids[type])
    self.hex_entry.handler_unblock(self.h_ids['hex'])
    self.wheel.handler_unblock(self.h_ids['wheel'])

  def color_spin_rgb_changed(self, spin):
    r,g,b = self.color.rgb()
    if spin == self.colorspin['r']:
      r = spin.get_value()
    elif spin == self.colorspin['g']:
      g = spin.get_value()
    elif spin == self.colorspin['b']:
      b = spin.get_value()
    self.color.set_rgb(r,g,b)

  def color_spin_cmyk_changed(self, spin):
    # TODO
    pass

  def color_spin_hsv_changed(self, spin):
    h,s,v = self.color.hsv()
    if spin == self.colorspin['h']:
      h = spin.get_value()
    elif spin == self.colorspin['s']:
      s = spin.get_value()
    elif spin == self.colorspin['v']:
      v = spin.get_value()
    self.color.set_hsv(h,s,v)

  def hex_entry_changed(self, entry):
    text = entry.get_text()
    if text != '':
      if ((text[0] == '#' and len(text) == 7) or
          (text[0] != '#' and len(text) == 6)):
        self.color.set_hex(text)

  def palette_combo_selected(self, combo, palette):
    if (self.palette != palette):
      if (palette.filename):
        self.gconf.set_string('/apps/elicit/palette', os.path.basename(palette.filename))
      if self.palette:
        old_filename = self.palette.filename
        self.palette.save()

        #update palette list with new filename
        if old_filename != self.palette.filename:
          index = self.palette_list.index_of_palette(self.palette)
          if index != None:
            self.palette_list[index][1] = self.palette.filename

      self.palette = palette
      self.palette_view.set_palette(self.palette)
      self.color_name_entry.set_sensitive(False)

  def add_palette(self, button):
    p = Palette()
    p.name = "Untitled Palette"
    self.palette_list.append(p)
    self.palette_combo.select(self.palette_list.index_of_palette(p))

  def delete_palette(self, button):
    if not self.palette: return

    d = gtk.MessageDialog(self.win,
        gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
        gtk.BUTTONS_OK_CANCEL, None)

    d.set_markup("Are you sure you want to delete the palette <b>%s</b>? This cannot be undone." % self.palette.name)
    response = d.run()
    d.destroy()
    if response == gtk.RESPONSE_OK:
      p = self.palette
      self.palette_combo.remove(self.palette_list.index_of_palette(p))
      p.delete()

  def select_color_clicked(self, button):
    sel_action = self.actiongroup.get_action("Select Color")
    sel_action.activate()

  def magnify_clicked(self, button):
    mag_action = self.actiongroup.get_action("Magnify")
    mag_action.activate()

  def build_menu(self):
    uimanager = gtk.UIManager()
    accelgroup = uimanager.get_accel_group()
    self.accelgroup = accelgroup
    self.win.add_accel_group(accelgroup)

    actiongroup = gtk.ActionGroup('ElicitActions')
    self.actiongroup = actiongroup

    actiongroup.add_actions([
      ('Quit', gtk.STOCK_QUIT, '_Quit', '<Ctrl>q', 'Quit Elicit', self.action_quit),
      ('Save', gtk.STOCK_QUIT, '_Save Palette', '<Ctrl>s', 'Save Palette', self.action_save),
      ('About', gtk.STOCK_ABOUT, '_About', None, 'About Elicit', self.action_about),
      ('Magnify', gtk.STOCK_ABOUT, '_Magnify', '<Ctrl>z', 'Start Magnifying', self.action_magnify),
      ('Select Color', gtk.STOCK_ABOUT, 'Select _Color', '<Ctrl>d', 'Start Selecting Color', self.action_pick_color),
      ('File', None, '_File'),
      ('Action', None, '_Action'),
      ('Help', None, '_Help')
      ])

    uimanager.insert_action_group(actiongroup)
    uimanager.add_ui_from_string("""
    <ui>
      <menubar name="ElicitMain">
        <menu action="File">
          <menuitem action="Save"/>
          <menuitem action="Quit"/>
        </menu>
        <menu action="Action">
          <menuitem action="Magnify"/>
          <menuitem action="Select Color"/>
        </menu>
        <menu action="Help">
          <menuitem action="About"/>
        </menu>
      </menubar>
    </ui>
    """)
    menubar = uimanager.get_widget("/ElicitMain")
    return menubar

  def build_gui(self):
    self.win = gtk.Window()
    self.win.set_title("Elicit")
    self.win.set_icon_name('rephorm-elicit')
    self.win.connect('destroy', self.quit, None)

    main_vbox = gtk.VBox(False, 2)
    self.win.add(main_vbox)

    menubar = self.build_menu()
    main_vbox.pack_start(menubar, False)

    frame_mag = gtk.Frame()
    # frame_mag.set_shadow_type(gtk.SHADOW_IN)

    frame_mag_inner = gtk.Frame()
    frame_mag_inner.set_shadow_type(gtk.SHADOW_IN)
    self.mag = Magnifier()
    frame_mag_inner.add(self.mag)
    mag_vbox = gtk.VBox()
    mag_vbox.pack_start(frame_mag_inner)
    frame_mag.add(mag_vbox)
    self.mag.connect('zoom-changed', self.mag_zoom_changed)
    self.mag.connect('grid-toggled', self.mag_grid_toggled)
    self.mag.connect('measure-changed', self.mag_measure_changed)
    self.mag.connect('location-changed', self.mag_location_changed)

    hbox = gtk.HBox(False, 0)

    self.mag_label = gtk.Label()
    hbox.pack_start(self.mag_label, False)

    icon_path = os.path.join(os.path.dirname(__file__), 'data', 'icons')

    frame_wheel = gtk.Frame()
    self.notebook = gtk.Notebook()
    frame_mag_label = gtk.Image()
    frame_mag_label.set_from_file(os.path.join(icon_path, "magnify-button.png"));
    # TODO: Color Wheel image (from Gimp picker?)
    frame_wheel_label = gtk.Label('Color Wheel')
    self.notebook.append_page(frame_mag, frame_mag_label)
    self.notebook.append_page(frame_wheel, frame_wheel_label)
    self.wheel = gtk.HSV()
    # TODO: automatic resize
    self.wheel.set_metrics(200, 20)
    frame_wheel.add(self.wheel)
    self.h_ids['wheel'] = self.wheel.connect('changed', self.wheel_changed)

    main_vbox.pack_start(self.notebook, True, True)
    mag_vbox.pack_start(hbox, False)


    pick_view_hbox = gtk.HBox()
    button = gtk.Button()
    button.set_relief(gtk.RELIEF_NONE)
    img = gtk.Image()
    img.set_from_file(os.path.join(icon_path, "dropper-button.png"));
    button.set_image(img)
    button.set_tooltip_text("Start Selecting Color\n(Left Click to stop)")
    button.connect('clicked', self.select_color_clicked);
    pick_view_hbox.pack_start(button, False)
    main_vbox.pack_start(pick_view_hbox)

    button = gtk.Button()
    button.set_relief(gtk.RELIEF_NONE)
    img = gtk.Image()
    img.set_from_file(os.path.join(icon_path, "magnify-button.png"));
    button.set_image(img)
    button.set_tooltip_text("Start Magnifying\n(Left Click to stop)")
    button.connect('clicked', self.magnify_clicked);
    hbox.pack_end(button, False)

    self.measure_label = gtk.Label()
    hbox.pack_end(self.measure_label, False)


    hbox = gtk.HBox(False, 5)
    mag_vbox.pack_start(hbox, False)

    check = gtk.CheckButton("Show Grid")
    check.set_active(self.mag.show_grid)
    check.connect('toggled', self.grid_check_toggled)
    hbox.pack_start(check)
    self.grid_check = check

    spin = gtk.SpinButton()
    spin.set_range(1,50)
    spin.set_increments(1,10)
    spin.set_value(self.mag.zoom)
    spin.connect('value-changed', self.zoom_spin_value_changed)
    hbox.pack_end(spin, False)
    self.zoom_spin = spin

    zoom_label = gtk.Label("Zoom:")
    hbox.pack_end(zoom_label, False)


    hbox = gtk.HBox(False, 5)
    main_vbox.pack_start(hbox, False)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    pick_view_hbox.pack_end(frame, True, True)

    self.colorpicker = ColorPicker()
    frame.add(self.colorpicker)
    self.colorpicker.connect('save-color', self.picker_save_color)
    self.colorpicker.set_magnifier(self.mag)

    self.colorspin = {}
    # add RGB spinboxes
    table = gtk.Table(6,4)
    hbox.pack_start(table, False)

    row = 0
    for type in ("r","g","b"):
      label = gtk.Label(type.upper())
      table.attach(label, 0,1,row,row+1,0,0,2,2)
      spin = gtk.SpinButton()
      spin.set_range(0,255)
      spin.set_increments(1,10)
      self.h_ids[type] = spin.connect('value-changed', self.color_spin_rgb_changed)
      table.attach(spin, 1,2,row,row+1,gtk.FILL,gtk.EXPAND,2,2)
      self.colorspin[type] = spin
      row += 1

    row = 0
    for type in ("h","s","v"):
      label = gtk.Label(type.upper())
      table.attach(label, 2,3,row,row+1,0,0,2,2)
      spin = gtk.SpinButton()
      if type == 'h':
        spin.set_range(0,360)
        spin.set_increments(1,10)
      else:
        spin.set_digits(2)
        spin.set_range(0,1.0)
        spin.set_increments(.01,.1)
      self.h_ids[type] = spin.connect('value-changed', self.color_spin_hsv_changed)
      table.attach(spin, 3,4,row,row+1,gtk.FILL,gtk.EXPAND,2,2)
      self.colorspin[type] = spin
      row += 1

    row = 0
    for type in ("c","m","y", "k"):
      label = gtk.Label(type.upper())
      table.attach(label, 4,5,row,row+1,0,0,2,2)
      spin = gtk.SpinButton()
      spin.set_range(0,100)
      spin.set_increments(1, 10)
      self.h_ids[type] = spin.connect('value-changed', self.color_spin_cmyk_changed)
      table.attach(spin, 5,6,row,row+1,gtk.FILL,gtk.EXPAND,2,2)
      self.colorspin[type] = spin
      row += 1

    self.hex_label = gtk.Label("Hex")
    table.attach(self.hex_label,0,1,3,4,gtk.FILL,gtk.EXPAND,2,2)

    self.hex_entry = gtk.Entry()
    self.hex_entry.set_max_length(7)
    # self.hex_entry.set_width_chars(7)
    table.attach(self.hex_entry,1,4,3,4,gtk.FILL,gtk.EXPAND,2,2)
    self.h_ids['hex'] = self.hex_entry.connect('changed', self.hex_entry_changed)


    sep = gtk.HSeparator()
    main_vbox.pack_start(sep, False)

    # palette tools
    hbox = gtk.HBox(False, 5)
    main_vbox.pack_start(hbox, False)

    # Palette tools
    hbox.pack_start(gtk.Label("Palette:"), False)

    self.palette_combo = PaletteCombo()
    hbox.pack_start(self.palette_combo)
    self.palette_combo.connect('selected', self.palette_combo_selected)

    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON))
    button.set_tooltip_text("Add Palette")
    button.set_relief(gtk.RELIEF_NONE)
    button.connect('clicked', self.add_palette)
    hbox.pack_start(button, False)

    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE,gtk.ICON_SIZE_BUTTON))
    button.set_tooltip_text("Delete Palette")
    button.set_relief(gtk.RELIEF_NONE)
    button.connect('clicked', self.delete_palette)
    hbox.pack_start(button, False)


    # palette view
    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    main_vbox.pack_start(frame, False)

    self.palette_view = PaletteView()
    self.palette_view.connect('select-color', self.palette_view_select_color)
    self.palette_view.connect('delete-color', self.palette_view_delete_color)
    frame.add(self.palette_view)

    # color name entry / palette tools
    hbox = gtk.HBox(False, 5)
    main_vbox.pack_start(hbox, False)

    hbox.pack_start(gtk.Label("Color Name:"), False)

    self.color_name_entry = gtk.Entry()
    self.color_name_entry.set_sensitive(False)
    self.color_name_entry.connect('changed', self.color_name_entry_changed)
    hbox.pack_start(self.color_name_entry, True, True)

  def init_config(self):
    self.gconf = gconf.client_get_default()
    self.gconf.add_dir('/apps/elicit', preload=True)
    self.gconf_id = self.gconf.notify_add("/apps/elicit", self.config_changed)

  def load_config(self):
    color = self.gconf.get_string('/apps/elicit/color')
    if color: self.color.set_hex(color)

    zoom_level = self.gconf.get_int('/apps/elicit/zoom_level')
    self.mag.set_zoom(zoom_level)
    self.zoom_spin.set_value(self.mag.zoom)

    grab_rate = self.gconf.get_int('/apps/elicit/grab_rate')
    if grab_rate > 0: self.mag.grab_rate = grab_rate

    show_grid = self.gconf.get_bool('/apps/elicit/show_grid')
    self.mag.set_show_grid(show_grid)
    self.grid_check.set_active(self.mag.show_grid)

    palette = self.gconf.get_string('/apps/elicit/palette')
    if not palette: palette = 'default.gpl'
    index = self.palette_list.index_of_file(palette)
    if index == None:
      index = 0
    self.palette_combo.select(index)

  def config_changed(self, client, gconf_id, entry, user_data):
    key = entry.key[13:]

    if key == 'color':
      hex = entry.value.get_string()
      self.color.set_hex(hex)
    elif key == 'zoom_level':
      self.mag.set_zoom(entry.value.get_int())
      self.zoom_spin.set_value(self.mag.zoom)
    elif key == 'show_grid':
      self.mag.set_show_grid(entry.value.get_bool())
      self.grid_check.set_active(self.mag.show_grid)
    elif key == 'palette':
      palette = entry.value.get_string()
      if not palette: palette = 'default.gpl'
      self.palette_combo.select(self.palette_list.index_of_file(palette))
    elif key == 'grab_rate':
      self.mag.set_grab_rate(entry.value.get_int())

  def action_quit(self, action):
    self.quit()

  def action_save(self, action):
    self.save()

  def action_about(self, action):
    a = gtk.AboutDialog()
    a.set_name(appinfo.name)
    a.set_version(appinfo.version)
    a.set_website(appinfo.website)
    a.set_authors([appinfo.author])
    a.set_logo_icon_name('rephorm-elicit')

    a.connect('response', lambda dialog,respons: dialog.destroy())
    a.show()

  def action_magnify(self, action):
    if self.mag.grabbing:
      self.mag.grab_stop()

    if self.colorpicker.picking:
      self.colorpicker.pick_stop()

    self.mag.grab_start()

  def action_pick_color(self, action):
    if self.colorpicker.picking:
      self.colorpicker.pick_stop()

    if self.mag.grabbing:
      self.mag.grab_stop()

    self.colorpicker.pick_start()

  def __init__(self):
    self.palette = None
    self.color = Color()
    self.h_ids = {}
    self.color.connect('changed', self.color_changed)

    self.init_config()
    self.build_gui()

    self.palette_dir = os.path.join(base.save_config_path(appinfo.pkgname), 'palettes')
    Palette.PaletteDir = self.palette_dir

    self.palette_list = PaletteList()
    self.palette_list.load(self.palette_dir)
    self.palette_combo.set_model(self.palette_list)

    # no palettes, so create default
    if len(self.palette_list) == 0:
      palette = Palette()
      palette.name = "Default Palette"
      palette.filename = os.path.join(self.palette_dir, 'default.gpl')
      self.palette_list.append(palette)

      self.palette_combo.select(0)

    self.colorpicker.set_color(self.color)

    self.load_config()

if __name__ == "__main__":
  el = Elicit()
  el.show()
  el.main()
