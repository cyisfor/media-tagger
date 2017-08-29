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
	l.init(base)
	queue = lambda id,width=0: l.queue(id,width or 0)
	l.queue.argtypes = [c_uint, c_uint]
