import sys,os
D = os.path.dirname
# sigh...
here = D(os.path.abspath(__file__))

def import_parent():
	global __name__
	print('a',__name__)
	__name__ = "foo.bar.syspath";
	print('b',__name__)
	parent,subname = os.path.split(here)
	name = os.path.basename(parent)
	subname = name + '.' + subname
	sys.path.append(D(parent))

	__import__(name)
	parentpkg = sys.modules[name]
	print('parent package',name,parentpkg)

	sys.path[-1] = here
	sys.modules['foo'] = parentpkg
	__import__(subname)
	if not hasattr(parentpkg,'__file__'):
		return
	thispkg = sys.modules[subname]
	print('this package',subname,thispkg)
	del sys.modules[subname]
	sys.modules['foo.bar'] = thispkg
	print('ok',sorted(sys.modules.keys()))
	print(__name__)
	from .. import syspath
	
try: from .. import syspath
except (SystemError,ValueError) as e:
	oldname = __name__
	import_parent()
	try:
		del sys.modules['foo']
		del sys.modules['foo.bar']
	except KeyError: pass
	__name__ = oldname


print('whee',sys.path)
