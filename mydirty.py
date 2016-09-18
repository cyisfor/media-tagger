# it's prettier to say with d.table: etc

import dirty.html as sub

def makeE(tag):
	tag = sub.Tag(tag)
	def makeE(*a,**kw):
		return sub.Element(tag,*a,**kw)
	setattr(sub,tag,makeE)

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
		self.parent(self)
	def __call__(self,*a,**kw):
		if not a and not kw: return self.commit()
		self.contents += a
		self.kw.update(kw)
	def __enter__(self):
		self.parent = ContextDirty.current_element
		ContextDirty.current_element = self
		return self
	def __exit__(self):
		if self.parent
			self.parent.append(self.commit())
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
		
import sys
sys.modules[__name__] = ContextDirty()
