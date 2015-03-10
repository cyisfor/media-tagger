import filedb

from tornado.process import Subprocess as s
import os

importPath = os.path.join(filedb.base,"dumphere")
if not os.path.exists(importPath):
    os.mkdir(importPath)

ino = None
def getino():
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
            os.exit(0)
        opid, status = os.waitpid(pid)
        assert opid == pid
        assert status == 0

@forked
def take(name):
    try:
        import pgi
        pgi.install_as_gi()
    except ImportError: pass

    from gi.repository import Gtk,Gdk,GObject,GLib

    window = Gtk.Window()
    window.connect('destroy',Gtk.main_quit)
    box = Gtk.VBox()
    window.add(box)
    tagentry = Gtk.Entry()
    sourceentry = Gtk.Entry()
    gobutton = Gtk.ToggleButton(label='Go!')
    box.pack_start(tagentry,True,True,0)
    box.pack_start(sourceentry,True,True,0)

    def maybeSubmit(e):
        print('event',e)
    window.connect('keyup',maybeSubmit)

    window.show_all()
    Gtk.main()    

def catchup():
    for name in os.walk(importPath):
        take(name)

@gen.coroutine
def watch():
    while True:
        line = yield getino().stdout
        line = line[:-1] # \n
        path = line.split(',',2)
        if len(line) != 3: continue
        name = line[2]
        take(name)
        
        
    
    def main():
    catchup()
    
