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
            import traceback
            traceback.print_exc()
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

import os

findStmt = 'SELECT sis,bro FROM possibleDupes WHERE NOT sis IN (select id from glibsucks) AND NOT bro IN (select id from glibsucks) AND dist < $1 EXCEPT SELECT sis,bro FROM nadupes ORDER BY sis DESC LIMIT 1000'

maxDistance = os.environ.get('distance')
if maxDistance is None:
    maxDistance = 200
else:
    maxDistance = int(maxDistance)

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

idlers = set()

def idle_add(f,*a,**kw):
    # have to slow this down b/c pgi has a bug that infinite loops w/out calling callback
    idlers.add(f)
    GLib.timeout_add(100,once(tracking(f)),*a,**kw)

maxoff = int(db.execute("SELECT max(id) FROM media")[0][0] / 10000)

print('pages',maxoff)
print(findStmt)
class Finder:
    a = b = -1
    done = False
    def __init__(self):
        self.next()
    def next(self):
        try: self.source, self.dest = next(self.dupes)
        except StopIteration:
            self.dupes = iter(db.execute(findStmt,(maxDistance,)))
            try:
                self.source, self.dest = next(self.dupes)
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
        if self.source < self.dest:
            self.source, self.dest = self.dest, self.source
    def nodupe(self,then=None):
        print('nadupe',self.dest,self.source)
        if self.dest > self.source:
            a = self.source
            b = self.dest
        else:
            a = self.dest
            b = self.source
        print('boing',a,b)
        try: db.execute('INSERT INTO nadupes (bro,sis) VALUES ($1,$2)',(a,b))
        except db.ProgrammingError as e:
            print(e)
        self.next()
    def dupe(self,inferior):
        print('dupe',self.dest,self.source)
        mergequeue.put((self.dest,self.source,inferior))
        self.next()

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
imagebox = Gtk.HBox(){:x}
#'.format(self.id))
label = Gtk.Label(label='...')
labelbox.pack_start(self.label,True,True,0)

class Image:
    def __init__(self,id):
        self.id = id
    _pixbuf = None
    @property
    def pixbuf(self):
        if self._pixbuf: return self._pixbuf
        self._pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(filedb.mediaPath(self.id))

class ImageScrobber:
    def __init__(self):
        self.image = Gtk.Image()
    def setup(self,images):
        images = [Image(image) for image in images]
        self.images = images
        self.which = 0
        self.image.set_from_pixbuf(images[0].pixbuf)
    swapping = None
    def next(self):
        self.which += 1
        if self.swapping:
            GLib.source_remove(self.swapping)
        self.alpha = 0x20
        source = self.images[self.which%len(self.images)].pixbuf
        dest = self.image.get_pixbuf()
        if dest.width != source.width:
            dest = dest.scale_simple(source.width,
                                     source.height,
                                     GdkPixbuf.NEAREST)
            self.image.set_from_pixbuf(dest)
        self.swapping = GLib.timeout_add(self.scrob,100,source,dest)
    def scrob(self,source,dest):
        source.composite(dest,
                         0,0,source,width,source.height,0,0,
                         1.0,1.0,GdkPixbuf.NEAREST,self.alpha)
        self.alpha += 0x20
        if self.alpha >= 0x100:
            self.image.set_from_file(filedb.mediaPath(self.images[which]))
            del self.swapping
            return False
        return True

scrobber = ImageScrobber()
imagebox.pack_start(scrobber.image,True,True,0)

viewport = Gtk.ScrolledWindow(None,None)
viewport.add(imagebox)

viewport.set_size_request(640,480)

scroller = viewport.get_vadjustment()
hscroll = viewport.get_hadjustment()

vbox.pack_start(viewport,True,True,0)

busy = False

def scrollReset():
    scroller.set_value(0)
    hscroll.set_value(0)

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
                label.set_text('busy')
                idle_add(f,e)
        else:
            getbusy = f
        btn.connect('clicked',getbusy)
        buttonkeys[shortcut] = btn
    return decorator

@addButton("Superior",Gdk.KEY_a)
def answer(e):
    # therefore the right one is inferior (finder.source)
    finder.dupe(True)
    scrollReset()
    scrobber.setup([finder.source,finder.dest])

@addButton("Yes",Gdk.KEY_o)
def answer(e):
    finder.dupe(False)
    scrollReset()
    scrobber.setup([finder.source,finder.dest])

@addButton("Swap",Gdk.KEY_e,ambusy=False)
def answer(e):
    scrobber.next()

@addButton("No",Gdk.KEY_u)
def answer(e):
    finder.nodupe()
    scrollReset()
    scrobber.setup([finder.source,finder.dest])

def cleanup(e):
    win.hide()
    idle_add(lambda e: loop.quit())

win.connect('destroy',cleanup)
win.show_all()
loop.run()
print('Waiting for merges to finish')
mergequeue.put('done')
mergequeue.join()
