import filedb

from tornado import ioloop, gen
from tornado.process import Subprocess as s

from functools import wraps
import os

importPath = os.path.join(filedb.base,"dump")
if not os.path.exists(importPath):
    os.mkdir(importPath)

ino = None
def getino():
    global ino
    if ino is not None: return ino
    ino = s(['inotifywait',"-q","-m","-c","-e","moved_to",importPath],stdout=s.STREAM);

    return ino

def forked(f):
    "very basic, returns nothing just does stuff, for resource isolation temporary GUIs etc"
    @wraps(f)
    def wrapper(*a,**kw):
        print('call',f,a,kw)
        pid = os.fork()
        if pid == 0:
            try: f(*a,**kw)
            except Exception as e:
                print(e)
            print("all done")
            os._exit(0)
        opid, status = os.waitpid(pid,0)
        assert opid == pid
        assert status == 0
    return wrapper

@forked
def take(name):
    try:
        import pgi
        pgi.install_as_gi()
    except ImportError: pass

    from gi.repository import Gtk,Gdk,GObject,GLib

    window = Gtk.Window()
    window.connect('destroy',lambda *a: print("uhhhh") or Gtk.main_quit())
    box = Gtk.VBox()
    window.add(box)
    tagentry = Gtk.Entry()
    sourceentry = Gtk.Entry()
    gobutton = Gtk.ToggleButton(label='Go!')
    box.pack_start(tagentry,True,True,0)
    box.pack_start(sourceentry,True,True,0)

    def maybeSubmit(*a):
        print('event',a)
    window.connect('key_release_event',maybeSubmit)

    window.show_all()
    Gtk.main()    

def catchup():
    for name in os.listdir(importPath):
        take(name)

@gen.coroutine
def watch():
    files = {}
        
    while True:
        line = yield getino().stdout
        line = line[:-1] # \n
        line = line.split('"')
        derp = []
        inquote = False
        for bit in line:
            if inquote:
                derp.append(bit)
                inquote = False
            else:
                for thing in bit.split(','):
                    derp.append(thing)
                inquote = True
        print(derp)
        if len(derp) != 3: continue
        top,event,name = derp
        print('name',event,name)
        #take(name)
        
        

def main():
    catchup()
    watch()
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
