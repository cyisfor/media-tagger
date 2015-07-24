#!/usr/bin/python3

# when passing a function as an argument, make a reply identifier
# and save the function to a replying dict

class Importer:
    def run(self):
        import favorites.parsers
    def gotClipboard(self,uri,c,w):
        from favorites.parseBase import parse, ParseError, normalize
        import comic
        url = url.strip()
        print("Trying {}".format(url))
        sys.stdout.flush()
        try: m = parse(normalize(url))
        except ParseError:
            m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
        comic.findInfo(m,self.gui.getInfo,lambda *a: self.comicReady(c,w,m))
    def openComic(self):
        import db
        return db.c.execute("SELECT (SELECT MAX(id)+1 FROM comic)")
    def maxWhich(self,c):
        import db
        return db.c.execute("SELECT (SELECT MAX(which) FROM comicPage WHERE comic = $1",(c,))
    def comicReady(self,c,w,m):
        import comic
        c,w = self.gui.getStuff()
        comic.findMedium(c,w,m)        
        self.gui.setWhich(w+1)
    def __init__(self,gui):
        self.gui = gui
        
class GUI:
    def run(self):
        import gtkclipboardy as clipboardy
        from gi.repository import Gtk
        import sys

        window = Gtk.Window()
        window.connect('destroy',Gtk.main_quit)
        box = Gtk.VBox()
        window.add(box)
        self.centry = Gtk.Entry()
        box.pack_start(self.centry,True,True,0)
        self.wentry = Gtk.Entry()
        box.pack_start(self.wentry,True,True,0)

        window.connect('destroy',Gtk.main_quit)
        window.show_all()
        clipboardy.run(self.gotClipboard,
                       lambda piece: b'http' == piece[:4])
    def setWhich(self,which):
        self.wentry.set_text('{:x}'.format(which))
    def gotClipboard(self,uri):
        c = self.centry.get_text()
        if not c:
            c = self.db.openComic()
            self.centry.set_text('{:x}'.format(c))
        w = self.wentry.get_text()
        if w:
            w = int(w,0x10)
        else:
            w = self.db.maxWhich()+1
            self.wentry.set_text('{:x}'.format(w))
        self.db.gotClipboard(uri,c,w)
    def getInfo(self,next):
        from gi.repository import Gtk
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

def runGUI(socket):
    g = GUI()
    g.db = Proxy(Importer,socket)
    g.run()

def runImporter(socket):
    i = Importer()
    i.gui = Proxy(GUI,socket)
    i.run()

import os,socket,signal

gui,importer = socket.socketpair()

pid = os.fork()
if pid:
    runGUI(gui)
    os.exit(0)

try: runImporter(importer)
finally:
    os.kill(pid,signal.SIGTERM)
