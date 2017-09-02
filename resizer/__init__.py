import ctypes
import sys,os

here = os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))
lib = os.path.join(here,"python.so");

import subprocess as s
s.check_call(["make","-s","-C",here,"python.so"])

from ctypes import cdll,c_int,c_uint,c_char_p

os.chdir("/home/.local/filedb")

def init(base):
	global queue
	l = cdll.LoadLibrary(lib)
	l.init.argtypes = [c_char_p]
	l.init.restype = None
	base = base.encode("utf-8")
	l.init(base,len(base))
	def queue(id,width=0):
		res = l.queue(id,width or 0)
		assert(res == 0, res)
	l.queue.argtypes = [c_uint, c_uint]
	l.queue.restype = c_int
