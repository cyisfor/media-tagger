from mygi import GLib, Gtk, Gdk

def derp(f):
	def wrapper(*a,**kw):
		#print('derp',f)
		return f(*a,**kw)
	return wrapper

import threading

def make(handler,check=None):
	seen = set()
	clipboard = None
	def gotClip(clipboard, text, nun=None):
		if text:
			if check:
				res = check(text)
				if isinstance(res,(str,bytes,bytearray,memoryview)):
					text = res
				elif not res:
					return True
				
			if not text in seen:
				seen.add(text)
				if type(text)==bytes:
					text = text.decode('utf-8')
				handler(text)
	def gotDerp(clipboard, text, nun=None):
		try:
			gotClip(clipboard, text, nun)
		finally:
			GLib.timeout_add(200,derp(checkClip))
	
	def checkClip(nun=None):
		assert(clipboard)
		clipboard.request_text(gotDerp,None)
		return False
	
	def start(nun=None):
		nonlocal clipboard
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clipboard.set_text('',0)
		GLib.timeout_add(200,derp(checkClip))

	oldint = None
	def run():
		GLib.timeout_add(200,derp(start))
		import signal
		nonlocal oldint
		oldint = signal.signal(signal.SIGINT, signal.SIG_DFL)
		Gtk.main()
	def quit():
		import signal
		signal.signal(signal.SIGINT, oldint)
		Gtk.main_quit()
		
	class BothOrStart(tuple):
		def start(self):
			return start()
		def quit(self,*a):
			return quit()
		def run(self,derphandler=None):
			nonlocal handler
			if derphandler:
				handler = derphandler
			run()
	return BothOrStart((start,run))

import sys
sys.modules[__name__] = make
