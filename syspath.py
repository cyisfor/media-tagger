import sys,os

# sys.path[0] is by default the path of the script
# so adjust that to the actual top

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

def import_parent(here):
	global top
	upper = here
	while True:
		parent,name = os.path.split(here)
		sys.path[0] = parent
		pkg = __import__(name)
		if not hasattr(pkg,'__file__'):
			return upper
		top = Module(pkg,name,top)
		upper = here
		here = parent

def commit_packages(top,prefix=None):
	if prefix is None:
		name = top.name
	else:
		name = prefix + '.' + top.name
	sys.modules[name] = top.pkg
	for child in top.children:
		commit_packages(child,name)


sys.path[0] = import_parent(here)
for child in top.children:
	commit_packages(child)
