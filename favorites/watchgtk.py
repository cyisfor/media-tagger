import gi.repository as girepo
import threading
import sys
main = threading.current_thread()

def check():
    if threading.current_thread() != main:
        raise RuntimeError('not main thread')

class derpwatcher: pass
    
def maybewatcher(o):
    if isinstance(o,derpwatcher):
        return o
    return watcher(o)


def watcher(what):
    class accessor(derpwatcher):
        def __getattribute__(self,n):
            check()
            try: return maybewatcher(getattr(what,n))
            except AttributeError as e:
                print(e)
                print(what,n)
        def __call__(self,*a,**kw):
            check()
            return maybewatcher(what(*a,**kw))
        def __get__(self):
            return self
    return accessor()

import inspect
import builtins
savimp = builtins.__import__

def newimp(name, *x, **kw):
    try: mod = savimp(name, *x, **kw)
    except TypeError as e:
        raise e
    if name[:3] == 'gi.' or name[:4] == 'pgi.':
        print('imp',name)
        return watcher(mod)
    else:
        return mod

builtins.__import__ = newimp
    
# import sys
# out = open('trace.log','wt')
# def hi(frame,type,eh):
#     out.write(frame.f_code.co_name+'\n')
#     #raise SystemExit

# sys.settrace(hi)
