import gi.repository as girepo
import threading
import sys
main = threading.current_thread()

print(getattr(girepo,'__spec__'))
raise SystemExit

class watcher:
    def __init__(self,what):
        self.what = what
    def __getattr__(self,n):
        print('uhh',n)
        if threading.current_thread() != main:
            raise RuntimeError('not main thread',self.what,n)
        return watcher(getattr(self.what,n))

import inspect
import __builtin__
savimp = __builtin__.__import__

def newimp(name, *x):
  return watcher(savimp(name, *x))

__builtin__.__import__ = newimp
    
sys.modules['gi.repository'] = watcher(girepo)

# import sys
# out = open('trace.log','wt')
# def hi(frame,type,eh):
#     out.write(frame.f_code.co_name+'\n')
#     #raise SystemExit

# sys.settrace(hi)
