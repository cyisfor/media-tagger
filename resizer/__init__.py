import ctypes
import sys,os

here = os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))

lib = os.path.join(here,"python.so");

from ctypes import cdll,c_int,c_uint

os.chdir("/home/.local/filedb")

def init():
	global queue
	l = cdll.LoadLibrary(lib)
	l.init()
	queue = lambda id,width=0: l.queue(id,width)
	l.queue.argtypes = [c_uint, c_uint]

import subprocess as s
s.check_call(["make","-C",here,"python.so"])
	
try:
	init()
except (AttributeError,OSError):
	init()

queue(0x7f837)
