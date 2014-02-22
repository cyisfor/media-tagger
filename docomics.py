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
    box.pack_start(Gtk.Label(name),True,True,0)
    box.pack_start(entry,True,True,0)
    return box

comic = Gtk.Entry()
box.pack_start(label("Comic",comic),True,True,0)
page = Gtk.Entry()
box.pack_start(label("Page",page),True,True,0)

gobutton = Gtk.ToggleButton(label='Go!')
box.pack_start(gobutton,True,False,0)

builder = Gtk.Builder()

def createComic(com):
    message = "Please Give Comic {:x}'s Info".format(com)
    win = Gtk.Dialog()
    win.set_title(message)

    title = Gtk.Entry()
    desc = Gtk.Entry()
    source = Gtk.Entry()

    action_area = win.get_internal_child(builder,"action_area")
    action_area.pack_start(Gtk.Label(message),True,True,0)
    action_area.pack_start(label('Title',title),True,True,0)
    action_area.pack_start(label('Description',desc),True,True,0)
    action_area.pack_start(label('Source',source),True,True,0)

    title.connect('activate',lambda e: win.destroy())
    desc.connect('activate',lambda e: win.destroy())
    source.connect('activate',lambda e: win.destroy())

    win.show_all()
    response = Gtk.ResponseType(win.run())
    print(response)
    if response == Gtk.ResponseType.DELETE_EVENT: 
        win.destroy()
        raise RuntimeError('Aborted creation')

    source = source.get_text()
    if source:
        s = db.c.execute('SELECT id FROM urisources WHERE uri = $1',(source,))
        if s:
            source = s[0][0]
        else:
            s = db.c.execute('WITH (INSERT INTO sources DEFAULT VALUES RETURNING id) as derp INSERT INTO urisources (id,uri,code) SELECT id,$1,200 FROM derp RETURNING urisources.id',(source,))
            source = s[0][0]
        assert(source)
    else:
        source = None

    tit = title.get_text()
    de = desc.get_text()
    assert(tit and de)

    if source is not None:
       db.c.execute('INSERT INTO comics (title,description,source) VALUES ($1,$2,$3)',(
           tit,
           de,
           source))
    else:
       db.c.execute('INSERT INTO comics (title,description) VALUES ($1,$2)',(
           tit,
           de))




def gotImage(image):
    if not gobutton.get_active(): return
    try: image = int(image.rstrip('/').rsplit('/',1)[-1],0x10)
    except ValueError: return
    print('yay',image)
    try:
        com = int(comic.get_text(),0x10)
        pag = int(page.get_text(),0x10)
    except ValueError:
        checkInitialized()
        return
    with db.transaction():
        if db.c.execute('SELECT count(id) FROM comics WHERE id = $1',(com,))[0][0] == 0:
            createComic(com)
        db.c.execute('SELECT setComicPage($1,$2,$3)',(image,com,pag))
    page.set_text('{:x}'.format(pag+1))

def checkInitialized(e=None):
    com = comic.get_text()
    if com: 
        com = int(com,0x10)
    else:
        com = db.c.execute('SELECT MAX(id) + 1 FROM comics')[0][0]
        comic.set_text('{:x}'.format(com))
    pag = page.get_text()
    if pag == '':
        pag = db.c.execute('SELECT MAX(which) + 1 FROM comicPage WHERE comic = $1',(com,))
        if pag:
            pag = pag[0][0]
            if not pag:
                pag = 0
        else:
            pag = 0
        page.set_text('{:x}'.format(pag))
gobutton.connect('toggled',checkInitialized)
clipboardy.monitor(gotImage)
window.show_all()
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
