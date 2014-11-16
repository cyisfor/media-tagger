from override import override

import tornado.concurrent
import note

note.monitor(__name__)

from functools import wraps
import sys

last = None

def getframe():
    for top in range(3,20):
        f = sys._getframe(top)
        name = f.f_globals.get('__name__')
        file = f.f_globals.get('__file__')
        if name.startswith('tornado'): continue
        if name == '__main__': break
        if name.startswith('_'): continue
        if file and file.startswith('/opt/pypy3/l'): continue
        break
    class Frame:
        def __init__(self,f):
            self.filename = f.f_code.co_filename
            self.name = f.f_code.co_name
            self.lineno = f.f_lineno
    return Frame(f)

def message(self,f,s):
    global last
    if last is None:
        last = self
    where = f.name + ' ' + f.filename + ':' + str(f.lineno)
    sys.stderr.write(str(id(self)-id(last))+' '+s+' '+where+'\n')
    sys.stderr.flush()

@override(tornado.concurrent.Future,'__init__')
def __init__(self,superduper):
    superduper(self)
    self.initframe = getframe()
    message(self,self.initframe,'created from')

@override(tornado.concurrent.Future,'_set_done')
def _set_done(self, superduper):
    message(self,self.initframe,'done from')
    try: return superduper(self)
    except TypeError:
        print('ugh bad future')
