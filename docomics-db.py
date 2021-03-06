#!/usr/bin/python3

# when passing a function as an argument, make a reply identifier
# and save the function to a replying dict

from itertools import count
import json,struct

import socket

def R(a):
    if isinstance(a,socket.socket): return a.fileno()
    return a

def note(*a):
    import sys
    l = []
    for e in a:
        l.append(str(R(e)))
    sys.stdout.write(' '.join(l)+'\n')
    sys.stdout.flush()

replying = {}
replyid = count(0)

def saveCallables(arg):
    if callable(arg):
        id = next(replyid)
        replying[id] = arg
        return ('call',id)
    return arg # uhh

class MessageDecoder:
    size = None
    def __init__(self):
        self.buffer = b''
    def pull(self,socket):
        while True:
            try: buf = socket.recv(0x1000)
            except BlockingIOError: break
            if not buf: break # closed?
            self.buffer += buf
            while True:
                if self.size is None:
                    if len(self.buffer) < 2: break
                    self.size = struct.unpack('H', self.advance(socket,2))[0]
                    note("got size",self.size)
                if len(self.buffer) < self.size:
                    break
                derp = self.size
                del self.size
                yield self.advance(socket,derp)
    def advance(self,socket,amt):
        ret = self.buffer[:amt]
        self.buffer = self.buffer[amt:]
        note(R(socket),'advance',amt,ret,self.buffer)
        return ret

def encode(*a):
    b = json.dumps(a).encode('utf-8')
    return struct.pack('H',len(b))+b
    
def proxifyCallables(socket,arg):
    # UHH...
    if isinstance(arg,list) and arg and arg[0] == 'call' and isinstance(arg[1],int):
        return lambda *a,**kw: socket.send(encode(arg[1],a,kw))
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
        note(self.proxy,'calling',self.name)
        self.proxy.send(encode(self.name,returnid,a,kw))
        return self.proxy.waitFor(returnid)

class Proxy:
    def __repr__(self):
        return 'proxy for '+self.name
    def __init__(self,name,outward,inward,socket,guihack):
        self.name = name
        self.outward = outward
        self.inward = inward
        self.socket = socket
        self.guihack = guihack
        if guihack:
            self.socket.setblocking(False)
        self.md = MessageDecoder()
        self.pos = 0
    def send(self,b):
        note('send',R(self.socket),b)
        return self.socket.send(b)
    def __getattr__(self,name):
        assert name != 'waitFor'
        method = getattr(self.outward,name)
        return ProxyMethod(self,
                           name,
                           method.__func__.__annotations__.get('return'),
                           method)
    def waitFor(self,returnid=None):
        if returnid is not None:
            note(self,'wait for',returnid,R(self.socket))
        while True:
            for message in self.md.pull(self.socket):
                print('jsony',message)
                message = json.loads(message.decode('utf-8'))
                id,*message = message
                note('message',id,message)
                if isinstance(id,str):
                    realmethod = getattr(self.inward,id)
                    returns,a,kw = message
                    for i,v in enumerate(a):
                        a[i] = proxifyCallables(self.socket,v)
                    for n,v in kw.items():
                        kw[n] = proxifyCallables(self.socket,v)
                    note("calling",realmethod,a,kw)
                    ret = realmethod(*a,**kw)
                    if returns is not None:
                        self.send(encode(returns,ret))
                elif returnid is not None and id == returnid:
                    ret = message[0]
                    note(self,'returning',ret)
                    try: 
                        for i,v in enumerate(ret):
                            ret[i] = proxifyCallables(self.socket,v)
                    except TypeError:
                        ret = proxifyCallables(self.socket,ret)
                    return ret
                else:
                    a,kw = message
                    for i,v in enumerate(a):
                        a[i] = proxifyCallables(self.socket,v)
                    for n,v in kw.items():
                        kw[n] = proxifyCallables(self.socket,v)
                    reply = replying[id]
                    note('found reply',id,reply)
                    del replying[id]
                    reply(*a,**kw)
            if self.guihack:
                if returnid is None:
                    from mygi import GLib
                    GLib.timeout_add(200,lambda *a: self.waitFor())
                    return                
                else:
                    # augh
                    from mygi import GLib,Gtk
                    GLib.timeout_add(200,Gtk.main_quit)
                    Gtk.main()
            else:
                while True:
                    r,w,l = select.select([self.socket.fileno()],[],[])
                    if r: break
            

class Importer:
    def run(self):
        import favorites.parsers
        return self.gui.waitFor(None)
    def gotClipboard(self,url,c,w):
        from favorites.parseBase import parse, ParseError, normalize
        import comic
        url = url.strip()
        note("Trying {}".format(url))
        sys.stdout.flush()
        try: m = parse(normalize(url))
        except ParseError:
            m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
        comic.findInfo(c,self.gui.getInfo
                       ,lambda *a: self.comicReady(c,w,m))
    def openComic(self) -> int:
        import db
        return db.execute("SELECT MAX(id)+1 FROM comics")[0][0]
    def maxWhich(self,c) -> int:
        import db
        return db.execute("SELECT MAX(which) FROM comicPage WHERE comic = $1",(c,))[0][0]
    def comicReady(self,c,w,m):
        import comic
        print('ready {:x} {:x} {:x}'.format(c,w,m))
        comic.findMedium(c,w,m)
        self.gui.setWhich(w+1)

def once(f):
    def wrapper(*a,**kw):
        try:
            f(*a,**kw)
        except Exception as e:
            import traceback
            traceback.print_exc()
            from mygi import Gtk
            Gtk.main_quit()
        else:
            return False
    return wrapper

def kbquit(f):
    def wrapper(*a,**kw):
        try:
            return f(*a,**kw)
        except KeyboardInterrupt:
            note("quitting")
            from mygi import Gtk
            Gtk.main_quit()
    return wrapper

class GUI:
    def run(self):
        from mygi import Gtk,GLib
        import sys

        GLib.idle_add(once(self.setup))
        Gtk.init(())
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()
    @kbquit
    def setup(self,um=None):
        from mygi import Gtk
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
        clipboardy(self.gotClipboard,
                   lambda piece: b'http' == piece[:4]).start()
    def setWhich(self,which):
        self.wentry.set_text('{:x}'.format(which))
    @kbquit
    def gotClipboard(self,uri):
        c = self.centry.get_text()
        if c:
            c = int(c,0x10)
        else:
            c = self.db.openComic()
            self.centry.set_text('{:x}'.format(c))
        w = self.wentry.get_text()
        if w:
            w = int(w,0x10)
        else:
            w = self.db.maxWhich(c)
            if w is None:
                w = 0
            else:
                w = w + 1
            self.wentry.set_text('{:x}'.format(w))
        self.db.gotClipboard(uri,c,w)
    def getInfo(self,next):
        from mygi import Gtk
        print("Getting the infos?",next)
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
        title.set_text("Spike Wins a Gameshow")
        description.set_text("Big head Spike loses a gameshow about how to pick which pony is Rarity... by orally pleasuring the Apple Family (sans Applejack)")
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
g.db = Proxy('Importer',i,g,importer,True)
i.gui = Proxy('GUI',g,i,gui,False)

note('gi',R(gui),R(importer))


pid = os.fork()
if pid == 0:
    import sys
    i.run()
    raise SystemExit

try:
    g.run()
    os.waitpid(pid,0)
    pid = None
finally:
    importer.close()
    if pid is not None:
        os.waitpid(pid,0)
        os.kill(pid,signal.SIGTERM)
