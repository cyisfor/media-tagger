import sys,os
D = os.path.dirname
# sigh...
here = D(os.path.abspath(__file__))

def import_parent():
	print('a',__name__)
	__name__ = "foo.bar.syspath";
	print('b',__name__)
	parent,subname = os.path.split(here)
	name = os.path.basename(parent)

	__import__(name)
	parentpkg = sys.modules[name]
	print('parent package',name,parentpkg)
	del sys.modules[name]
	if not hasattr(parentpkg,'__file__'):
		return
	sys.modules['foo'] = parentpkg

	subname = name + '.' + subname
	sys.path.append(D(parent))
	print('uhh',sys.path)
	__import__(subname)
	thispkg = sys.modules[subname]
	print('this package',subname,thispkg)
	del sys.modules[subname]
	sys.modules['foo.bar'] = thispkg
	print('ummm',__import__('foo.__init__'))
	print('ok',sorted(sys.modules.keys()))
	print(__name__)
	from .. import syspath
	sys.path.pop()
	
try: from .. import syspath
except (SystemError,ValueError) as e:
	oldname = __name__
	import_parent()
	__name__ = oldname
	
del sys.modules['foo.bar']
del sys.modules['foo']


