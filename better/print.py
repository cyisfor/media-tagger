import sys,io
class Flushfile(object):
    def __init__(self, fd):
        self.fd = fd

    def write(self, x):
        try: ret=self.fd.write(x)
        except UnicodeEncodeError:
            raise RuntimeError(repr(x))
        self.fd.flush()
        return ret

    def writelines(self, lines):
        ret=self.writelines(line)
        self.fd.flush()
        return ret

    def __getattr__(self,name):
        value = getattr(self.fd,name)
        setattr(self,name,value)
        return value

try:
    sys.stdout = Flushfile(io.TextIOWrapper(sys.stdout.buffer,encoding = 'utf-8'))
except AttributeError: pass

print(type(__builtins__))
import os
if 'debug' in os.environ:
	import note
	oldprint = print
	def newprint(*a,**kw):
		if kw:
			return oldprint(*a,**kw)
		return note(*a)
	__builtins__['print'] = newprintx
