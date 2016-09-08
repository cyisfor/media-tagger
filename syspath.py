import sys,os
D = os.path.dirname
# sigh...
here = D(os.path.abspath(__file__))

print('a',__name__)
__name__ = "foo.syspath";
print('b',__name__)
try: from .. import syspath
except SystemError as e:
	parent,subname = os.path.split(here)
	name = os.path.basename(parent)
	sys.path.append(D(parent))
	__import__(name)
	__name__ = name + '.' + subname + '.' + syspath
	print('new name',__name__)
	from .. import syspath
	
