import tempfile
from contextlib import contextmanager

import os,time
oj = os.path.join

base = os.path.expanduser("~/art/filedb")
top = base

def _check(id,category,contents=None,delay=0.1):
    id = '{:x}'.format(id)
    image = oj(base,category,id)
    if os.path.exists(image): return id,True
    target = oj(base,'temp',id)
    with open(target,'wb') as out:
        if contents:
            out.write(contents.encode('utf-8'))
    os.rename(target,oj(base,'incoming',id))
    exists = False
    for i in range(10):
        if os.path.exists(image): 
            exists = True
            break
        time.sleep(delay)
    return id,exists

def check(id):
    return _check(id,'thumb',delay=0.01)

def checkResized(id):
    return _check(id,'resized',"{:x}".format(800),delay=0.1)

def imagePath(id):
    return os.path.join(base,'image','{:x}'.format(id))
def uploadPath(name):
    return os.path.join(base,'uploads',name)

def ImageBecomer(dir):
    if type(dir)==type(''):
        self = tempfile.NamedTemporaryFile(dir=dir)
    else:
        print(type(dir))
        self = dir
    def become(id):
        image = imagePath(id)
        if os.path.exists(image): return
        os.chmod(self.name,0o644)
        os.rename(self.name,image)
        try: self.close()
        except OSError: pass
    setattr(self,'become',become)
    return self

@contextmanager
def imageBecomer():
    th = None
    try:
        th = ImageBecomer(dir=os.path.join(base,'temp'))
        yield th
    finally:
        if th: th.close()
