#!/usr/bin/python3

# when passing a function as an argument, make a reply identifier
# and save the function to a replying dict

from itertools import count
import json

replying = {}
replyid = count(0)

def saveCallables(arg):
    if callable(arg):
        id = next(replyid)
        replying[id] = arg
        return ('call',id)
    return arg # uhh

def proxifyCallables(socket,arg):
    # UHH...
    if isinstance(arg,tuple) and arg and arg[0] == 'call' and isinstance(arg[1],'int'):
        return lambda *a,**kw: socket.send(json.dumps([arg[1],a,kw]).encode('utf-8'))
    return arg    
    
class ProxyMethod:
    def __init__(self,proxy,name,returns,method):
        self.name = name
        self.proxy = proxy
        self.method = method
        self.returns = returns
    def __call__(self,*a,**kw):
        a = list(a)
        for i,e in enumerate(a):
            a[i] = saveCallables(e)
        for n,v in kw.items():
            kw[n] = saveCallables(v)
        # if annotation nowait, don't add a return function
        returnid = None
        if self.returns:
            returnid = next(replyid)
        
        self.proxy.send(json.dumps(
            [self.name,returnid,a,kw]).encode('utf-8'))
        self.proxy.waitFor(returnid)

class Proxy:
    def __init__(self,backend,socket):
        self.backend = backend # only run on one not the other
        self.socket = socket
        self.buffer = bytearray(0x1000)
        self.pos = 0
    def send(self,b):
        return self.socket.send(b)
    def __getattr__(self,name):
        assert name != 'waitFor'
        method = getattr(self.backend,name)
        print(dir(method.__func__))
        return ProxyMethod(
                           name,
                           self.socket,
                           method.__func__.__annotations__.get('return'),
                           method)
    def waitFor(self,returnid=None):
        while True:
            amt = self.socket.recv_into(memoryview(self.buffer)[self.pos:])
            self.pos += amt
            try:
                message = json.loads(memoryview(self.buffer)[self.pos:].decode('utf-8'))
            except Exception as e:
                print(type(e))
                raise
            else:
                end = len(self.buffer) - self.pos
                self.buffer[:] = self.buffer[self.pos:]
                self.pos = end
                id,*message = message
                if isinstance(id,str):
                    realmethod = getattr(self.backend,id)
                    returns,a,kw = message
                    for i,v in enumerate(a):
                        a[i] = proxifyCallables(self.socket,v)
                    for n,v in kw.items():
                        kw[n] = proxifyCallables(self.socket,v)
                    ret = realmethod(*a,**kw)
                    if returns is not None:
                        self.socket.send(json.dumps([returns,ret]).encode('utf-8'))
                if returnid is not None and id == returnid:
                    ret = message[0]
                    for i,v in enumerate(ret):
                        ret[i] = proxifyCallables(self.socket,v)
                    return ret
                else:
                    a,kw = message
                    for i,v in enumerate(a):
                        a[i] = proxifyCallables(self.socket,v)
                    for n,v in kw.items():
                        kw[n] = proxifyCallables(self.socket,v)
                    reply = replying[id]
                    del replying[id]
                    reply(*a,**kw)

class Importer:
    def run(self):
        import favorites.parsers
        self.gui.waitFor(None)
    def gotClipboard(self,uri,c,w):
        from favorites.parseBase import parse, ParseError, normalize
        import comic
        url = url.strip()
        print("Trying {}".format(url))
        sys.stdout.flush()
        try: m = parse(normalize(url))
        except ParseError:
            m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
        comic.findInfo(m,self.gui.getInfo
                       ,lambda *a: self.comicReady(c,w,m))
    def openComic(self) -> int:
        import db
        return db.c.execute("SELECT (SELECT MAX(id)+1 FROM comic)")
    def maxWhich(self,c) -> int:
        import db
        return db.c.execute("SELECT (SELECT MAX(which) FROM comicPage WHERE comic = $1",(c,))
    def comicReady(self,c,w,m):
        import comic
        c,w = self.gui.getStuff()
        comic.findMedium(c,w,m)        
        self.gui.setWhich(w+1)

def once(f):
    def wrapper(*a,**kw):
        try:
            f(*a,**kw)
        except Exception as e:
            import traceback
            traceback.print_exc()
        else:
            return False
    return wrapper
        
class GUI:
    def run(self):
        try: 
            import pgi
            pgi.install_as_gi()
        except ImportError: pass
        from gi.repository import Gtk,GLib
        import sys

        GLib.idle_add(once(self.setup))
        Gtk.main()
    def setup(self,um=None):
        print('um?',um)
        from gi.repository import Gtk
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
        import gtkclipboardy as clipboardy
        start,run = clipboardy.make(self.gotClipboard,
                       lambda piece: b'http' == piece[:4])
        start()
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
        title.grab_focus()
        title.connect('activate',lambda *a: description.grab_focus())
        description.connect('activate',lambda *a: source.grab_focus())
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

g = GUI()
i = Importer()

import os,socket,signal

gui,importer = socket.socketpair()
g.db = Proxy(i,importer)
i.gui = Proxy(g,gui)

pid = os.fork()
if pid == 0:
    import sys
    sys.stderr.close()
    i.run()
    raise SystemExit

try:
    g.run()
    os.waitpid(pid)
    pid = None
finally:
    if pid is not None:
        os.kill(pid,signal.SIGTERM)
