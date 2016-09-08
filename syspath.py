import sys,os
D = os.path.dirname
# sigh...
here = D(os.path.abspath(__file__))

class Module:
	pkg = None
	name = None
	def __init__(self, pkg, name, *children):
		self.pkg = pkg
		self.name = name
		self.children = set(children)

top = Module(sys.modules[__name__],__name__)
del sys.modules[__name__]

sys.path.append(here)

def import_parent():
	global __name__
	print('a',__name__)
	__name__ = "foo.bar.syspath";
	print('b',__name__)
	parent = here
	while True:
		parent,subname = os.path.split(parent)
		sys.path[-1] = parent
		pkg = __import__(name)
		print('parent package',name,pkg)
		if not hasattr(pkg,'__file__'):
			return
		top = Module(pkg,name,top)

def commit_packages(top,prefix=None):
	if prefix is None:
		name = top.name
	else:
		name = prefix + '.' + top.name
	sys.modules[top.name] = top.pkg
	for child in top.children:
		commit_packages(child,name)

try: from .. import syspath
except (SystemError,ValueError) as e:
	import_parent()
	commit_packages(top)
	
print('whee',sys.path)
print('ummm',sorted(sys.modules.keys()))
