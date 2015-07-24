try: 
    import pgi
    pgi.install_as_gi()
except ImportError: pass

from gi.repository import GLib, Gtk, Gdk

def derp(f):
    def wrapper(*a,**kw):
        #print('derp',f)
        return f(*a,**kw)
    return wrapper

import threading

def make(handler,check):
    seen = set()
    clipboard = None
    def gotClip(clipboard, text, nun=None):

        if text:
            if check:
                res = check(text)
                if isinstance(res,(str,bytes,bytearray,memoryview)):
                    text = res
            if not text in seen:
                seen.add(text)
                if type(text)==bytes:
                    text = text.decode('utf-8')
                handler(text)
        GLib.timeout_add(200,derp(checkClip))
    
    def checkClip(nun):
        assert(clipboard)
        clipboard.request_text(gotClip,None)
        return False
    
    def start(nun):
        nonlocal clipboard
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text('',0)
        GLib.timeout_add(200,derp(checkClip))
    
    def run():
        GLib.timeout_add(200,derp(start))
        #import signal
        #signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()
    return start,run

def run(handler,check):
    start,run = make(handler,check)
    run()
    return start,run
