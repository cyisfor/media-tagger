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
	def __call__(self,*a,**kw):
		if not a and not kw: return self.commit()
		self.contents += a
		self.kw.update(kw)
		return self
	def __enter__(self):
		self.parent = ContextDirty.current_element
		ContextDirty.current_element = self
		return self
	def __exit__(self,*a):
		if self.parent:
			self.parent(self.commit())
		ContextDirty.current_element = self.parent
	committed = None
	def commit(self):
		if self.committed is None:
			contents = tuple(maybecommit(e) for e in self.contents)
			self.committed = getattr(sub,self.name)(*contents,**self.kw)
		return self.committed

class ContextDirty:
	current_element = None
#	RawString = sub.RawString
	def __getattr__(self,name):
		return Element(name)
	class NoAppending:
		def __init__(self
import sys
sys.modules[__name__] = ContextDirty()
