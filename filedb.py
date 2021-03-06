from gevent import sleep
import tempfile
from contextlib import contextmanager

import resizer

import os,time
oj = os.path.join

base = os.path.expanduser("/home/.local/filedb")
top = base
resizer.init(base)

temp = oj(base,'temp')

def _incoming(id,contents=None):
	target = oj(temp,id)
	if os.path.exists(target): return
	with open(target,'wb') as out:
		if contents:
			out.write(contents.encode('utf-8'))
	os.rename(target,oj(base,'incoming',id))

def incoming(id,contents=None):
	return _incoming('{:x}'.format(id),contents)
	
def _check(id,category,create=True,width=0):
	xid = '{:x}'.format(id)
	medium = oj(base,category,xid)
	if os.path.exists(medium): return xid,True
	if not create:
		return xid, False
	resizer.queue(id,width)
	return xid, os.path.exists(medium)

def check(id,**kw):
	kw.setdefault('category','thumb')
	if kw.get('create') and kw.get('category') == 'thumb':
		try:
				del kw['width']
		except KeyError: pass
	return _check(id,**kw)

def checkResized(id,**kw):
	kw.setdefault('width',800)
	return _check(id,category='resized',**kw)

def checkOEmbed(id,maxWidth,**kw):
	return _check(id,category='oembed',width=maxWidth,**kw)

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
