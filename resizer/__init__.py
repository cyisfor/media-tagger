import ctypes
import sys,os

here = os.path.dirname(sys.modules[__name__].__file__)
if not here: here = os.curdir
lib = os.path.join(here,"python.so");

from ctypes import cdll

def init():
	global dest, queue
	l = cdll.LoadLibrary(lib)
	dest = l.init()
	queue = l.queue
	queue.argtypes = [c_int, c_uint, c_uint]


try:
	init()
except AttributeError:
	import subprocess as s
	s.call(["make","-C",here,"python.so"])
	init()

print(dest)

