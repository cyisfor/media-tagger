import gi.repository as girepo
from gi.repository import Gtk, GLib, Gdk
import threading
import sys
main = threading.current_thread()


def check():
    if threading.current_thread() != main:
        raise RuntimeError('not main thread')

class derpwatcher: pass
    
def maybewatcher(o):
    if isinstance(o,derpwatcher):
        print('is a watcher',o)
        return o
    return watcher(o)


def watcher(what):
    class accessor(derpwatcher):
        def __getattribute__(self,n):
            check()
            try: val = getattr(what,n)
            except AttributeError as e:
                print(what,n)
                import importlib
                val = importlib.import_module(n,what.__package__)
            return maybewatcher(val)
        def __call__(self,*a,**kw):
            check()
            try:
                return maybewatcher(what(*a,**kw))
            except:
                print(self,what,a,kw)
                raise
        def __get__(self):
            return what
    return accessor()

girepo.Gtk = maybewatcher(Gtk)
girepo.Gdk = maybewatcher(Gdk)
girepo.GLib = maybewatcher(GLib)

# import sys
# out = open('trace.log','wt')
# def hi(frame,type,eh):
#     out.write(frame.f_code.co_name+'\n')
#     #raise SystemExit

# sys.settrace(hi)
