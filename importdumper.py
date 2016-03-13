import filedb
import impmort

from tracker_coroutine import coroutine

import subprocess as s

from functools import wraps
import os

importPath = os.path.join(filedb.base,"dump")
if not os.path.exists(importPath):
    os.mkdir(importPath)

ino = None
def getino():
    global ino
    if ino is not None: return ino
    ino = s.Popen(['inotifywait',"-q","-m","-c",importPath],stdout=s.PIPE);

    return ino

def forked(f):
    "very basic, returns nothing just does stuff, for resource isolation temporary GUIs etc"
    @wraps(f)
    def wrapper(*a,**kw):
        print('call',f,a,kw)
        pid = os.fork()
        if pid == 0:
            f(*a,**kw)
            os._exit(0)
        opid, status = os.waitpid(pid,0)
        assert opid == pid
        assert status == 0
    return wrapper

@forked
def take(name):
    from mygi import Gtk,Gdk,GObject,GLib

    discovered, name = impmort.discover(name)    

    window = Gtk.Window()
    window.connect('destroy',lambda *a: print("uhhhh") or Gtk.main_quit())
    box = Gtk.VBox()
    window.add(box)
    tagentry = Gtk.Entry()
    sourceentry = Gtk.Entry()
    gobutton = Gtk.ToggleButton(label='Go!')
    box.pack_start(tagentry,True,True,0)
    box.pack_start(sourceentry,True,True,0)

    tagentry.set_text(', '.join(discovered.union(impmort.implied)))
    
    def maybeSubmit(*a):
        print('event',a)
    window.connect('key_release_event',maybeSubmit)

    window.show_all()
    Gtk.main()    

def catchup():
    for name in os.listdir(importPath):
        take(name)

@coroutine
def watch():
    attribs = set()
        
    while True:
        line = yield getino().stdout.read_until(b'\n')
        line = line[:-1] # \n
        line = line.split(b'"')
        derp = []
        inquote = False
        for bit in line:
            if inquote:
                derp.append(bit)
                inquote = False
            else:
                bit = bit.strip(b',')
                for thing in bit.split(b','):
                    derp.append(thing)
                inquote = True
        if len(derp) != 3: continue
        top,event,name = derp
        name = name.decode('utf-8')
        event = set(event.decode().split(','))
        if 'ATTRIB' in event:
            attribs.add(name)
        elif 'CLOSE_WRITE' in event:
            if name in attribs:
                print('OK we can take this one',name)
                attribs.discard(name)
                take(name)
        elif 'MOVED_TO' in event:
            print('OK moved to is ok too',name)
            take(name)
        print('name',event,name)
        #take(name)
        
        

def main():
    #catchup()
    watch()

if __name__ == '__main__':
    main()
