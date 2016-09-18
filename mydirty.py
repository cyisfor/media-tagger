# it's prettier to say with d.table: etc

import dirty.html as sub

def makeE(name):
	tag = sub.Tag(name)
	def makeE(*a,**kw):
		return sub.Element(tag,*a,**kw)
	setattr(sub,name,makeE)

makeE('audio')
makeE('video')
makeE('source')
makeE('embed')

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
		self.parent = ContextDirty.current_element
		if self.parent:
			self.parent(self)
	def __repr__(self):
		return "<"+self.name+repr(self.kw)+'>'
	def __call__(self,*a,**kw):
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
	committed = None
	def commit(self):
		if self.committed is None:
			contents = tuple(maybecommit(e) for e in self.contents)
			self.committed = getattr(sub,self.name)(*contents,**self.kw)
		return self.committed

class NoParent:
	parent = None
	def __enter__(self):
		self.parent = ContextDirty.current_element
		ContextDirty.current_element = None
	def __exit__(self,*a):
		ContextDirty.current_element = self.parent
	
class ContextDirty:
	current_element = None
#	RawString = sub.RawString
	def __getattr__(self,name):
		return Element(name)
	NoParent = NoParent()
import sys
sys.modules[__name__] = ContextDirty()
