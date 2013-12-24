#!/usr/bin/python3

import db,sys,os
import filedb

import clipboardy
from gi.repository import Gtk,Gdk,GObject,GLib
window = Gtk.Window()
window.connect('destroy',Gtk.main_quit)
box = Gtk.VBox()
window.add(box)

def label(name,entry):
    box = Gtk.HBox()
    box.pack_start(Gtk.Label(name))
    box.pack_start(entry)
    return box

comic = Gtk.Entry()
box.pack_start(label("Comic",comic),True,True,0)
page = Gtk.Entry()
box.pack_start(label("Page",page),True,True,0)

gobutton = Gtk.ToggleButton(label='Go!')
box.pack_start(gobutton,True,False,0)
def gotImage(image):
    if not gobutton.get_active(): return
    try: num = int(image.rsplit('/',1)[-1],0x10)
    except ValueError: return
    com = comic.get_text()
    if not com: 
        alert("Please select a comic to add to!")
        com.set_text(
        return
        tag(num,tags)
    clipboardy.monitor(gotPiece)
    window.show_all()
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()
