# it's prettier to say with d.table: etc

import dirty.html as sub

current_element = None

class Element:
	def __init__(self,name,*a,**kw):
		self.name = name
		self.contents = contents
		self.kw = kw
		self.parent = current_element
	def __enter__(self):
		global current_element
		current_element = self
	def __exit__(self):
		if self.parent
			self.parent.append(self.commit())
		current_element = self.parent
	def commit(self):
		return getattr(sub,self.name)(*self.contents,**self.kw)

class ContextDirty:
	def __getattr__(self,name):
		return lambda *a,**kw: Element(name,*a,**kw)
		
import sys
sys.modules[__name__] = ContextDirty()
