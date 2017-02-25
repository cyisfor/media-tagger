from eventlet.greenthread import sleep
import tempfile
from contextlib import contextmanager

import os
oj = os.path.join

base = os.path.expanduser("/home/.local/filedb")
top = base

temp = oj(base,'temp')

def _incoming(id,contents=None):
	target = oj(temp,id)
	with open(target,'wb') as out:
		if contents:
			out.write(contents.encode('utf-8'))
	os.rename(target,oj(base,'incoming',id))

def incoming(id,contents=None):
	return _incoming('{:x}'.format(id),contents)
	
def _check(id,category,create=True,contents=None):
    id = '{:x}'.format(id)
    medium = oj(base,category,id)
		def on_done(handler):
			if not create:
				return handler(id, False)
			if os.path.exists(medium): return handler(id, True)
			_incoming(id,contents)
			def tryagain():
        if os.path.exists(medium): handler(id,True)
				return handler(id, tryagain)
			return tryagain()

def just_wait(checker,*a,**kw):
	"mostly just an example of how to undo the CPS of _check et al"
	import time
	tryagain = None
	@checker(*a,**kw):
	def result(id, exists):
		nonlocal tryagain
		if exists is True:
			return id, True
		elif exists is False:
			return id, False
		else:
			tryagain = exists
			return None
	delay = kw.get('delay',0.1)
	for attempt in range(3):
		if result is not None:
			return result
		time.sleep(delay)
		result = tryagain()
	return id, False

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
def thumbPath(id=None):
    loc = os.path.join(base,'thumb')
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
