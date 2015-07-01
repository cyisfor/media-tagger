#!/usr/bin/python3
import comic
from favorites.parseBase import parse, ParseError
import gtkclipboardy as clipboardy
from gi.repository import Gtk,Gdk,GObject,GLib
import sys
window = Gtk.Window()
window.connect('destroy',Gtk.main_quit)
box = Gtk.VBox()
window.add(box)
centry = Gtk.Entry()
box.pack_start(centry,True,True,0)
wentry = Gtk.Entry()
box.pack_start(wentry,True,True,0)

window.show_all()

def getinfo():
    window = Gtk.Window()
    box = Gtk.VBox()
    window.add(box)
    def e(n):
        h = Gtk.HBox()
        box.pack_start(h,True,True,0)
        h.pack_start(Gtk.Label(n),False,False,2)
        derp = Gtk.Entry()
        h.pack_start(derp,True,True,0)
        return derp
    title = e("title")
    description = e("description")
    source = e("source")
    title.connect('activate',lambda *a: description.grab_focus())
    description.connect('activate',lambda *a: source.grab_focus())
    title.grab_focus()
    source.connect('activate',lambda *a: window.destroy())
    window.connect('destroy',Gtk.main_quit)
    window.show_all()
    Gtk.main()
    return title.get_text() or None, description.get_text() or None, source.get_text() or None
    

def gotURL(url):
    url = url.strip()
    print("Trying {}".format(url))
    sys.stdout.flush()
    c = int(centry.get_text(),0x10)
    if not c: return
    w = int(wentry.get_text(),0x10)
    try: m = parse(url)
    except ParseError:
        m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
    comic.findInfo(c,getinfo)
    comic.findMedium(c,w,m)
    wentry.set_text(str(w+1))

clipboardy.run(gotURL,lambda piece: b'http' == piece[:4])
