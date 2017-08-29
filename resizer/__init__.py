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
	q = l.init(base.encode("utf-8"))
	queue = lambda id,width=0: l.queue(q, id,width or 0)
	l.queue.argtypes = [c_uint, c_uint]
