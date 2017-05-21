# it's prettier to say with d.table: etc

import dirty.html as sub

sub.xhtml.DTD = "<!DOCTYPE html>"
sub.xhtml.XMLNS = None

def makeE(name):
	tag = sub.Tag(name)
	def makeE(*a,**kw):
		return sub.Element(tag,*a,**kw)
	setattr(sub,name,makeE)

makeE('audio')
makeE('video')
makeE('source')
makeE('embed')

def nocycles(o,e):
	for sub in e:
		if id(sub) == id(o): raise RuntimeError("cycle adding",o)
		try:
			if not sub: continue
			if type(sub[0]) == type(sub): continue
			nocycles(o,sub)
		except TypeError: pass

def maybecommit(e):
	if hasattr(e,'committed') and e.committed is not None:
		return e.committed
	if hasattr(e,'commit'):
		return e.commit()
	return e

class Element:
	def __init__(self,name):
		self.name = name
		self.contents = ()
		self.kw = {}
		self.pending = ()
		self.parent = ContextDirty.current_element
		if ContextDirty.derping and self.parent:
			nocycles(self,self.parent.contents)
			self.parent(self)
	def __repr__(self):
		return "<"+self.name+repr(self.kw)+'>'
	def __call__(self,*a,**kw):
		nocycles(self,a)
		self.contents += a
		self.kw.update(kw)
		return self
	def __enter__(self):
		self.parent = ContextDirty.current_element
		#print('going down',self,self.parent)
		ContextDirty.current_element = self
		return self
	def __exit__(self,*a):
		#print('going up',self,self.parent)
		ContextDirty.current_element = self.parent
	def committing(self,f):
		self.pending += (f,)
	committed = None
	def commit(self):
		if self.committed is None:
			with self:
				for commit in self.pending:
					commit()
			contents = tuple(maybecommit(e) for e in self.contents)
			print(contents)
			self.committed = getattr(sub,self.name)(*contents,**self.kw)
		return self.committed

class NoParent:
	parent = None
	derping = False
	def __enter__(self):
		self.parent = ContextDirty.current_element
		ContextDirty.current_element = None
	def __exit__(self,*a):
		print('none done',self.parent)
		ContextDirty.current_element = self.parent
class ContextDirty:
	current_element = None
	derping = True
#	RawString = sub.RawString
	def __getattr__(self,name):
		return Element(name)
	NoParent = NoParent()
import sys
ContextDirty = ContextDirty()
sys.modules[__name__] = ContextDirty
