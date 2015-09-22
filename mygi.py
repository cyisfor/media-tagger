try:
    import pgi
    pgi.install_as_gi()
except ImportError: pass
import importlib
import gi.repository

class mygi(type(gi.repository)):
    def __init__(self):
        self.__file__ = gi.repository.__file__
        self.__path__ = gi.repository.__path__
    def __getattr__(self,name):
        mod = importlib.import_module('gi.repository.'+name,package='gi.repository')
        setattr(self,name,mod)
        return mod

import sys
sys.modules[__name__] = mygi()
