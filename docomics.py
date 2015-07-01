#!/usr/bin/python3
import comic
import gtkclipboardy as clipboardy
from gi.repository import Gtk,Gdk,GObject,GLib
window = Gtk.Window()
window.connect('destroy',Gtk.main_quit)
box = Gtk.VBox()
window.add(box)
centry = Gtk.Entry()
box.pack_start(centry,True,True,0)
wentry = Gtk.entry()
box.pack_start(wentry,True,True,0)

window.show_all()

def gotURL(url):
    print("Trying {}".format(piece.strip()))
    sys.stdout.flush()
    c = int(centry.get_text())
    w = int(wentry.get_text())
    m = parse(url)
    comic.findMedium(c,w,m)
    wentry.set_text(str(w+1))

clipboardy.run(gotURL,lambda piece: b'http' == piece[:4])
