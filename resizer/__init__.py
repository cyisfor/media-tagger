import ctypes
import sys,os

here = os.path.dirname(sys.modules[__name__].__file__)
if not here: here = os.curdir
lib = os.path.join(here,"python.so");

from ctypes import cdll

lib = cdll.LoadLibrary(lib)
print(lib)

