#!/usr/bin/python3
import comic
from favorites.parseBase import parse, ParseError, normalize
import favorites.parsers
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

window.connect('destroy',Gtk.main_quit)
window.show_all()

def handling(f,*a,**kw):
    def wrapper(handler):
        f(*(a+(handler,)),**kw)
    return wrapper

def getinfo(next):
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
    def herp(*a):
        nonlocal title, description, source
        title = title.get_text() or None
        description = description.get_text() or None
        source = source.get_text() or None
        assert title
        next(title,description,source)
    window.connect('destroy',herp)
    window.show_all()
    

def gotURL(url):
    url = url.strip()
    print("Trying {}".format(url))
    sys.stdout.flush()
    c = centry.get_text()
    if not c: return
    c = int(c,0x10)
    w = wentry.get_text()
    if w:
        w = int(w,0x10)
    else:
        w = 0
    try: m = parse(normalize(url))
    except ParseError:
        m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
    @handling(comic.findInfo,c,getinfo)
    def gotcomic(title,description,source):
        comic.findMedium(c,w,m)
        wentry.set_text("%x".format(w+1))

clipboardy.run(gotURL,lambda piece: b'http' == piece[:4])
