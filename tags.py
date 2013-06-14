#!/usr/bin/python3

import db,sys,os
import filedb

def tag(thing,tags):
    with db.transaction():
        for tag in tags:
            wholetag = db.c.execute("SELECT findTag($1)",(tag,))[0][0]
            if ':' in tag:
                category,tag = tag.split(':')
                category = db.c.execute("SELECT findTag($1)",(category,))[0][0]
            else:
                category = None

            tag = db.c.execute("SELECT findTag($1)",(tag,))[0][0]
            if category:
                db.c.execute("SELECT connect($1,$2)",(wholetag,category))
            db.c.execute("SELECT connect($1,$2)",(tag,wholetag))
            db.c.execute("SELECT connect($1,$2)",(wholetag,tag))
            db.c.execute("SELECT connect($1,$2)",(thing,wholetag))
            db.c.execute("SELECT connect($1,$2)",(wholetag,thing))

if len(sys.argv)==3:
    tag(int(sys.argv[1],0x10),sys.argv[2:])
else:
    import clipboardy
    from gi.repository import Gtk,Gdk,GObject,GLib
    window = Gtk.Window()
    window.connect('destroy',Gtk.main_quit)
    box = Gtk.VBox()
    window.add(box)
    tagentry = Gtk.Entry()
    gobutton = Gtk.ToggleButton(label='Go!')
    box.pack_start(tagentry,True,True,0)
    box.pack_start(gobutton,True,False,0)
    def gotPiece(piece):
        print("Got piece",piece)
        if not gobutton.get_active(): return
        try: num = int(piece.rsplit('/',1)[-1],0x10)
        except ValueError: return
        tags = [tag.strip(" \t") for tag in tagentry.get_text().split(',')]
        tag(num,tags)
    clipboardy.monitor(gotPiece)
    window.show_all()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()
