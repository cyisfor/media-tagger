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

current_element = None

def maybecommit(e):
	if hasattr(e,'commit'):
		return e.commit()
	return e

class Element:
	def __init__(self,name):
		self.name = name
		self.contents = ()
		self.kw = {}
		self.parent = current_element
	def __call__(self,*a,**kw):
		if not a and not kw: return self.commit()
		a = tuple(maybecommit(e) for e in a)
		self.contents += a
		self.kw.update(kw)
	def __enter__(self):
		global current_element
		self.parent = current_element
		current_element = self
	def __exit__(self):
		if self.parent
			self.parent.append(self.commit())
		current_element = self.parent
	committed = None
	def commit(self):
		if self.committed is None:
			self.committed = getattr(sub,self.name)(*self.contents,**self.kw)
		return self.committed

class ContextDirty:
	def __getattr__(self,name):
		return Element(name)
		
import sys
sys.modules[__name__] = ContextDirty()
