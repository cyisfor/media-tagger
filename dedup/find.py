try: 
    import pgi
    pgi.install_as_gi()
except ImportError: pass

import filedb
import db

import queue, threading
import merge

#merge.merge(0x26cf5,0x26bbe,True) # corrupt image
#import delete
#delete.commit()
merger = threading.Condition()

with open('../sql/find-dupes.sql') as inp:
    findStmt = inp.read()

import gi
from gi.repository import Gtk

def tracking(f):
    import traceback
    try: raise RuntimeError
    except RuntimeError:
        here = ''.join(traceback.format_stack())
    def wrapper(*a,**kw):
        try:
            return f(*a,**kw)
        except:
            print('called from:')
            print(here)
            print('-'*20)
            raise
    return wrapper


def once(f):
    def wrapper(*a,**kw):
        try:
            return f(*a,**kw)
        except:
            import traceback
            traceback.print_exc()
            return GLib.SOURCE_REMOVE
    return wrapper

def idle_add(f,*a,**kw):
    GLib.idle_add(once(tracking(f)),*a,**kw)


class Finder:
    def reload(self):
        self.dupes = iter(db.c.execute(findStmt));
    a = b = -1
    starting = True
    def __init__(self):
        self.reload()
        print('starting finder')
        self.next(None)
        self.starting = False
    def next(self,then):
        try: self.source, self.dest, self.hash = next(self.dupes)
        except StopIteration:
            print('all done!')
            Gtk.main_quit()
            return
        if not (
                db.c.execute('SELECT id FROM media WHERE id = $1',(self.dest,))
                and
                db.c.execute('SELECT id FROM media WHERE id = $1',(self.source,))):
            print('oops')
            idle_add(self.next,then)
            return
        print('next',self.hash)
        if self.source < self.dest:
            self.swap()
        else:
            print('now checking2',hex(self.dest),hex(self.source),then)
        if self.starting:
            if then:
                then()
        else:
            assert(then)
            then()
    def nodupe(self,then=None):
        print('nadupe',self.dest,self.source)
        db.c.execute('UPDATE media SET phash = $1 WHERE id = $2 OR id = $3',(
            '0'*15+'3'+'0'*(16-len(self.hash))+self.hash,
            self.dest, self.source))
        self.next(then)
    def dupe(self,inferior,then=None):
        print('dupe',self.dest,self.source)
        merge.merge(self.dest,self.source,inferior)
        with merger:
            merger.notify_all()
        self.next(then)
    def swap(self,then=None):
        temp = self.dest
        self.dest = self.source
        self.source = temp
        print('now checking',self.dest,self.source,then)
        if then: then()

finder = Finder()

import gi
from gi.repository import Gtk,Gdk,GdkPixbuf,GLib

win = Gtk.Window(
        title="Dupe resolver")

vbox = Gtk.VBox()
win.add(vbox)

labelbox = Gtk.HBox()
vbox.pack_start(labelbox,False, True, 0)

imagebox = Gtk.HBox()

images = {}
class Image:
    def __init__(self,name):
        self.name = name
        self.id = getattr(finder,name)
        self.pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(filedb.mediaPath(self.id))
        self.image = Gtk.Image.new_from_animation(self.pixbuf)
        self.label = Gtk.Label(label='{:x}'.format(self.id))
        labelbox.pack_start(self.label,True,True,0)
        imagebox.pack_start(self.image,True,True,0)
    def update(self):
        self.pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(filedb.mediaPath(getattr(finder,self.name)))
        self.refresh()
    def refresh(self):
        self.image.set_from_animation(self.pixbuf)
        self.label.set_text('{:x}'.format(getattr(finder,self.name)))

def swaparoo():
    temp = images['source'].pixbuf
    images['source'].pixbuf = images['dest'].pixbuf
    images['dest'].pixbuf = temp
    images['dest'].refresh()
    images['source'].refresh()

def oneImage(name):
    images[name] = Image(name)

oneImage('dest')

busylabel = Gtk.Label(label='...')
labelbox.pack_start(busylabel,True,True,0)

oneImage('source')

viewport = Gtk.ScrolledWindow(None,None)
viewport.add(imagebox)

viewport.set_size_request(640,480)

scroller = viewport.get_vadjustment()
hscroll = viewport.get_hadjustment()

vbox.pack_start(viewport,True,True,0)

busy = False

updaters = 0
def updateboo(name):
    global updaters
    updaters += 1
    print('updetau',updaters)
    def doit(*a):
        print(a)
        global updaters, busy
        images[name].update()
        updaters -= 1
        print('now updaters',updaters)
        if updaters == 0:
            busylabel.set_text('')
            busy = False
    idle_add(doit)

def refillimages():
    updateboo('dest')
    updateboo('source')

vbox.pack_start(Gtk.Label("Dupe? (note, right one will be deleted)"),False,False,0)

buttonbox = Gtk.HBox()
vbox.pack_start(buttonbox,False,False,0)

buttonkeys = {}

pressed = set()

def onpress(win,e):
    global busy
    if busy: return True
    if e.keyval in pressed: return True
    btn = buttonkeys.get(e.keyval)
    if btn:
        pressed.add(e.keyval)
        btn.clicked()
        return True

    if e.keyval == Gdk.KEY_Up:
        pressed.add(e.keyval)
        incr = scroller.get_page_increment()
        scroller.set_value(scroller.get_value()-incr)
        return True
    elif e.keyval == Gdk.KEY_Down:
        pressed.add(e.keyval)
        incr = scroller.get_page_increment()
        scroller.set_value(scroller.get_value()+incr)
        return True
    elif e.keyval == Gdk.KEY_Left:
        pressed.add(e.keyval)
        hscroll.set_value(hscroll.get_value()-hscroll.get_page_increment())
        return True
    elif e.keyval == Gdk.KEY_Right:
        pressed.add(e.keyval)
        hscroll.set_value(hscroll.get_value()+hscroll.get_page_increment())
        return True
    return False

def unpress(win,e):
    pressed.discard(e.keyval)

win.connect('key-press-event',onpress)
win.connect('key-release-event',unpress)

def addButton(label,shortcut,ambusy=True):
    def decorator(f):
        btn = Gtk.Button(label=label)
        buttonbox.pack_start(btn,True,True,3)
        if ambusy:
            def getbusy(e):
                global busy
                busy = True
                busylabel.set_text('busy')
                idle_add(f,e)
        else:
            getbusy = f
        btn.connect('clicked',getbusy)
        buttonkeys[shortcut] = btn
    return decorator

@addButton("Superior",Gdk.KEY_a)
def answer(e):
    # therefore the right one is inferior (finder.source)
    finder.dupe(True,then=refillimages)

@addButton("Yes",Gdk.KEY_o)
def answer(e):
    finder.dupe(False,then=refillimages)

@addButton("Swap",Gdk.KEY_e,ambusy=False)
def answer(e):
    finder.swap(then=swaparoo)

@addButton("No",Gdk.KEY_u)
def answer(e):
    finder.nodupe(then=refillimages)

win.connect('destroy',Gtk.main_quit)


def regularlyCommit():
    import merge,delete
    db.reopen() # wait... this destroys all prepareds?
    while True:
        delete.commit()
        with merger:
            merger.wait()

t = threading.Thread(target=regularlyCommit)
t.setDaemon(True)
t.start()
win.show_all()
try: 
    Gtk.main()
finally:
    mergequeue.join()
