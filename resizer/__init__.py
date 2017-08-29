import ctypes
import sys,os

here = os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))

lib = os.path.join(here,"python.so");

from ctypes import cdll,c_int,c_uint

os.chdir("/home/.local/filedb")

def init():
	global queue
	l = cdll.LoadLibrary(lib)
	print(l.init)
	dest = l.init()
	queue = lambda id,width=0: l.queue(dest,id,width)
	l.queue.argtypes = [c_int, c_uint, c_uint]

try:
	init()
except AttributeError:
	import subprocess as s
	s.call(["make","-C",here,"python.so"])
	init()

queue(0x7f851)
