import sys,os
D = os.path.dirname
# sigh...
here = D(os.path.abspath(__file__))

print('a',__name__)
__name__ = "foo.bar.syspath";
print('b',__name__)
try: from .. import syspath
except SystemError as e:
	print(here)
	parent,subname = os.path.split(here)
	print(parent,subname)
	name = os.path.basename(parent)
	subname = name + '.' + subname
	sys.path.append(D(parent))
	print('this package',subname)
	__import__(subname)
	thispkg = sys.modules[subname]
	del sys.modules[subname]
	sys.modules['foo.bar'] = thispkg
	__import__(name)
	print('parent package',name)
	parentpkg = sys.modules[name]
	del sys.modules[name]
	sys.modules['foo'] = parentpkg
	print('ok',sorted(sys.modules.keys()))
	print(__name__)
	from .. import syspath
	sys.path.pop()
	
del sys.modules['foo.bar']
del sys.modules['foo']
