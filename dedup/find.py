try: 
    import pgi
    pgi.install_as_gi()
except ImportError: pass

import threading, queue

#merge.merge(0x26cf5,0x26bbe,True) # corrupt image
mergequeue = queue.Queue()

def regularlyCommit():
    import merge
    while True:
        message = None
        try:
            message = mergequeue.get()
            if message == 'done': 
                print('done')
                break
            dest,source,inferior = message
            merge.merge(dest,source,inferior)
            print('left',mergequeue.qsize())
        except Exception as e:
            import sys
            sys.print_exc()
        finally:
            if message:
                mergequeue.task_done()

t = threading.Thread(target=regularlyCommit)
t.setDaemon(True)
t.start()

import gi
from gi.repository import Gtk,GLib

import filedb
import db

import merge

with open('../sql/find-dupes.sql') as inp:
    findStmt = inp.read()

loop = GLib.MainLoop()

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
        print('uh')
        try:
            return f(*a,**kw)
        except:
            import traceback
            traceback.print_exc()
            return GLib.SOURCE_REMOVE
    return wrapper

def idle_add(f,*a,**kw):
    # have to slow this down b/c pgi has a bug that infinite loops w/out calling callback
    GLib.timeout_add(100,once(tracking(f)),*a,**kw)

maxoff = int(db.execute("SELECT max(id) FROM media")[0][0] / 10000)

print('pages',maxoff)
print(findStmt)
class Finder:
    def reload(self):
        print('go')
        self.dupes = iter(db.execute(findStmt))
        print('go2')
    a = b = -1
    starting = True
    done = False
    def __init__(self):
        self.reload()
        print('starting finder')
        self.next(None)
        self.starting = False
    def next(self,then):
        try: self.source, self.dest, self.hash = next(self.dupes)
        except StopIteration:
            self.done = True
            print('all done!')
            loop.quit()
            return
        if not (
                db.execute('SELECT id FROM media WHERE id = $1',(self.dest,))
                and
                db.execute('SELECT id FROM media WHERE id = $1',(self.source,))):
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
        db.execute('UPDATE media SET phash = $1 WHERE id = $2 OR id = $3',(
            '0'*15+'3'+'0'*(16-len(self.hash))+self.hash,
            self.dest, self.source))
        self.next(then)
    def dupe(self,inferior,then=None):
        print('dupe',self.dest,self.source)
        mergequeue.put((self.dest,self.source,inferior))
        self.next(then)
    def swap(self,then=None):
        temp = self.dest
        self.dest = self.source
        self.source = temp
        print('now checking',self.dest,self.source,then)
        if then: then()

finder = Finder()
if finder.done:
    raise SystemExit

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

win.connect('destroy',lambda e: loop.quit())
win.show_all()
loop.run()
print('Waiting for merges to finish')
mergequeue.put('done')
mergequeue.join()
