import os,io
from ansi import color,reset,fg,bg,escape,bold

import colored_traceback
colored_traceback.add_hook(always=True)

import sys



white = color('white',styles=(bold,))

def decode(o):
	if hasattr(o,'value'):
		return repr(o.value)
	return str(o)

if 'debug' in os.environ:
	import sys,time
	out = sys.stderr.buffer
	modules = set()
	here = os.path.dirname(__file__)
	always = not 'notalways' in os.environ
	def setroot(where):
		global here
		here = os.path.dirname(where) 
	if hasattr(sys,'_getframe'):
		def getframe():
			return sys._getframe(3)
	else:
		def getframe():
			tb = sys.exc_info()[2]
			if not tb:
				try: raise Exception
				except Exception as e:
					tb = e.__traceback__
				while tb.tb_next:
					tb = tb.tb_next
			# here -> output -> note/alarm/warn/etc -> module
			return tb.tb_frame.f_back.f_back.f_back
	def output(color,s):
		f = getframe()
		# function above us
		module = f.f_globals['__name__'] 
		
		if not always and module not in modules: 
			return

		o = io.TextIOWrapper(io.BytesIO(),encoding='utf-8')
		def writec(c):
			o.flush()
			o.buffer.write(c)


		s = (decode(s) for s in s)
		s = ' '.join(s)
		hasret = '\n' in s

		if not 'simple' in os.environ:
			o.write('== '+str(time.time())+' ')
			writec(white)
			o.write(os.path.relpath(f.f_code.co_filename,here))
			writec(reset)
			o.write(':'+str(f.f_lineno))
			if hasret:
				o.write('\n'+'-'*60+'\n')
			else:
				o.write('\n')
	
		writec(color)
		o.write(s)
		writec(reset)

		if hasret:
			o.write('\n'+'-'*60+'\n')
		else:
			o.write('\n')
		o.flush()
		out.write(o.buffer.getbuffer())
		out.flush()
	class NoteModule:
		def note(self,*s):
			output(color('green',styles=(bold,)),s)
		def alarm(self,*s):
			output(fg(216,0,0)+bg(180,180,0)+escape(bold),s)
		def purple(self,*s):
			output(fg(126,10,216)+escape(bold),s)
		def blue(self,*s):
			output(fg(20,20,216)+escape(bold),s)
		def shout(self,*s):
			output(fg(216,0,216)+escape(bold),s)
		def __call__(self,*s):
			output(color('green'),s)
		def __getattr__(self,n):
			def doit(*s,**kw):
				return output(color(n,**kw)+escape(bold),s)
			return doit
		def monitor(self,module=None):
			if module:
				if hasattr(module,'__name__'):
					module = module.__name__
			else:
				module = '__main__'
			modules.add(module)
	if __name__ == '__main__':
		note = NoteModule()
		note.purple("whoops")		
else:
	class NoteModule:
		def __call__(self,*a,**kw): pass
		def __getattr__(self,n):
			return lambda *a, **kw: None
sys.modules[__name__] = NoteModule()
