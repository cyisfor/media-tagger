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

mod = sys.modules[__name__]
#del sys.modules[__name__]
__name__ = 'syspath'
top = Module(mod,__name__)

sys.path.append(here)

def import_parent(here):
	global top
	upper = here
	while True:
		parent,name = os.path.split(here)
		sys.path[-1] = parent
		pkg = __import__(name)
		print('parent package',name,pkg)
		if not hasattr(pkg,'__file__'):
			return upper
		top = Module(pkg,name,top)
		upper = here
		here = parent

def commit_packages(top,prefix=None):
	print(('commit',prefix,top.name))
	if prefix is None:
		name = top.name
	else:
		name = prefix + '.' + top.name
	sys.modules[name] = top.pkg
	for child in top.children:
		commit_packages(child,name)

sys.path[-1] = import_parent(here)
for child in top.children:
	commit_packages(child)
	
print('whee',sys.path)
print('ummm',sorted(sys.modules.keys()))
