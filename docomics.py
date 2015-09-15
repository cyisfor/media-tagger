#!/usr/bin/python3
import comic,db

from favorites.parseBase import parse, ParseError, normalize
import favorites.parsers
import gtkclipboardy as clipboardy
from mygi import Gtk,Gdk,GObject,GLib
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
    tags = e("tags")
    title.connect('activate',lambda *a: description.grab_focus())
    title.grab_focus()
    description.connect('activate',lambda *a: source.grab_focus())
    source.connect('activate',lambda *a: tags.grab_focus())
    tags.connect('activate',lambda *a: window.destroy())
    def herp(*a):
        nonlocal title, description, source, tags
        title = title.get_text() or None
        description = description.get_text() or None
        source = source.get_text() or None
        tags = tags.get_text() or None
        assert title
        next(title,description,source,tags)
    window.connect('destroy',herp)
    window.show_all()
    

def gotURL(url):
    url = url.strip()
    print("Trying {}".format(url))
    sys.stdout.flush()
    try: m = parse(normalize(url))
    except ParseError:
        try: m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
        except ValueError:
            print('nope')
            return
    w = None
    c = centry.get_text()
    if c:
        c = int(c,0x10)
    else:
        c = db.execute('SELECT comic,which FROM comicpage WHERE medium = $1',(m,))
        if len(c)==1:
            c = c[0]
            c,w = c
            centry.set_text('{:x}'.format(c))
            wentry.set_text('{:x}'.format(w+1))
            return
        else:
            c = db.execute('SELECT MAX(id)+1 FROM comics')[0][0]
        centry.set_text('{:x}'.format(c))

    if w is None:
        w = wentry.get_text()
        if w:
            w = int(w,0x10)
        else:
            w = db.execute('SELECT MAX(which)+1 FROM comicpage WHERE comic = $1',(c,))
            if w[0][0]:
                w = w[0][0]
            else:
                w = 0
            try:
                wentry.set_text('{:x}'.format(w))
            except TypeError:
                print(repr(w))
                raise
    @handling(comic.findInfo,c,getinfo)
    def gotcomic(title,description,source,tags):
        comic.findMedium(c,w,m)
        wentry.set_text("{:x}".format(w+1))

clipboardy.run(gotURL,lambda piece: b'http' == piece[:4])
