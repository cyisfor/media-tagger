from mytornado import sleep
from tornado import gen

import tempfile
from contextlib import contextmanager

import os,time
oj = os.path.join

base = os.path.expanduser("/extra/user/filedb")
top = base

@gen.coroutine
def _check(id,category,create=True,contents=None,delay=0.1):
    id = '{:x}'.format(id)
    medium = oj(base,category,id)
    if os.path.exists(medium): raise gen.Return((id,True))
    if not create:
        raise gen.Return(id, False)
    target = oj(base,'temp',id)
    with open(target,'wb') as out:
        if contents:
            out.write(contents.encode('utf-8'))
    os.rename(target,oj(base,'incoming',id))
    exists = False
    for i in range(10):
        if os.path.exists(medium): 
            exists = True
            break
        yield sleep(delay)        
    raise gen.Return((id,exists))

def check(id,**kw):
    kw.setdefault('category','thumb')
    kw.setdefault('delay',0.01)
    if kw.get('create') and kw.get('category') == 'thumb':
        try:
            del kw['contents']
        except KeyError: pass
    return _check(id,**kw)

def checkResized(id,**kw):
    kw.setdefault('delay',0.1)
    return _check(id,'resized',contents="{:x}".format(800),**kw)

def checkOEmbed(id,maxWidth,**kw):
    return _check(id,'oembed',contents='{:x}'.format(maxWidth),**kw)

def mediaPath(id=None):
    loc = os.path.join(base,'media')
    if id:
        return os.path.join(loc,'{:x}'.format(id))
    return loc
def uploadPath(name):
    return os.path.join(base,'uploads',name)

def MediaBecomer(dir=None):
    if isinstance(dir,type('')):
        self = tempfile.NamedTemporaryFile(dir=dir)
    elif dir is None:
        self = tempfile.NamedTemporaryFile(dir=os.path.join(base,'temp'))
    else:
        print(type(dir))
        self = dir
    def become(id):
        medium = mediaPath(id)
        if os.path.exists(medium): return
        print('creating',medium)
        os.chmod(self.name,0o644)
        os.rename(self.name,medium)
        try: self.close()
        except OSError: pass
    setattr(self,'become',become)
    return self

@contextmanager
def mediaBecomer():
    th = None
    try:
        th = MediaBecomer()
        yield th
    finally:
        if th: th.close()
