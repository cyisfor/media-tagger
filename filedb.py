import tempfile
from contextlib import contextmanager

import os,time
oj = os.path.join

base = os.path.expanduser("~/art/filedb")
top = base

def _check(id,category,contents=None,delay=0.1):
    id = '{:x}'.format(id)
    medium = oj(base,category,id)
    if os.path.exists(medium): return id,True
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
        time.sleep(delay)
    return id,exists

def check(id):
    return _check(id,'thumb',delay=0.01)

def checkResized(id):
    return _check(id,'resized',"{:x}".format(800),delay=0.1)

def checkOEmbed(id,maxWidth):
    return _check(id,'oembed','{:x}'.format(maxWidth))

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
        if os.path.exists(media): return
        os.chmod(self.name,0o644)
        os.rename(self.name,media)
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
