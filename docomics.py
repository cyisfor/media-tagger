#!/usr/bin/python3
import note
from bgworker import makeWorker

from redirect import Redirect
from mygi import GLib

foreground = GLib.idle_add

def initBG():
	import comic,db
	from favorites.parse import parse, ParseError, normalize
	import favorites.parsers # side effects galore!

dually,background = makeWorker(initBG,foreground)

from mygi import Gtk,Gdk,GObject
import sys
window = Gtk.Window()
window.connect('destroy',Gtk.main_quit)
window.set_keep_above(True)
box = Gtk.VBox()
window.add(box)
centry = Gtk.Entry()
box.pack_start(centry,True,True,0)
wentry = Gtk.Entry()
box.pack_start(wentry,True,True,0)

window.connect('destroy',Gtk.main_quit)
window.show_all()

def handling(f,*a,**kw):
	def wrapper(handler):
		f(*(a+(handler,)),**kw)
	return wrapper

def justdo(f,*a,**kw):
	def callback(*b,**bkw):
		return f(*a,**kw)
	return callback

from functools import partial

def getinfo(next):
	window = Gtk.Window()
	box = Gtk.VBox()
	window.add(box)
	def e(n):
		h = Gtk.HBox()
		box.pack_start(h,True,True,0)
		h.pack_start(Gtk.Label(n),False,False,2)
		derp = Gtk.Entry()
		h.pack_start(derp,True,True,0)
		return derp
	title = e("title")
	description = e("description")
	source = e("source")
	tags = e("tags")
	title.connect('activate',justdo(description.grab_focus))
	title.grab_focus()
	description.connect('activate',justdo(source.grab_focus))
	source.connect('activate',justdo(tags.grab_focus))
	tags.connect('activate',justdo(window.destroy))
	def herp(title, description, source, tags, *a):
		title = title.get_text() or None
		description = description.get_text() or None
		source = source.get_text() or None
		tags = tags.get_text() or None
		assert title
		background(lambda: next(title,description,source,tags))
	window.connect('destroy',partial(herp,title,description,source,tags))
	window.show_all()
			
@dually
def gotURL(url):
	url = url.strip()
	yield background
	print("Trying {}".format(url))
	sys.stdout.flush()
	from favorites.parse import parse,normalize,ParseError
	try:
		m = parse(normalize(url),noCreate=True)
		if not m:
			print('uhhh',url)
	except ParseError:
		try: m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
		except ValueError:
			print('nope')
			return
	print('ok m is',m)
	w = None
	yield foreground
	c = centry.get_text()
	if c:
		c = int(c,0x10)
		print('yay',hex(c))
	else:
		yield background
		import db
		print('m is still',m)
		c = db.execute('SELECT comic,which FROM comicpage WHERE medium = $1 ORDER BY which DESC',(m,))
		if len(c)>0:
			note.yellow('boop!',c)
			c = c[0]
			c,w = c
			yield foreground
			centry.set_text('{:x}'.format(c))
			wentry.set_text('{:x}'.format(w+1))
			return
		# still in bg
		c = db.execute('SELECT MAX(id)+1 FROM comics')[0][0]
		yield foreground # -> gui
		centry.set_text('{:x}'.format(c))
	if w is None:
		yield foreground
		w = wentry.get_text()
		if w:
			w = int(w,0x10)
		else:
			yield background
			import db
			w = db.execute('SELECT MAX(which)+1 FROM comicpage WHERE comic = $1',(c,))
			if w[0][0]:
				w = w[0][0]
			else:
				w = 0
			yield foreground
			try:
				wentry.set_text('{:x}'.format(w))
			except TypeError:
				print(repr(w))
				raise
	def gotcomic(title,description,source,tags):
		import comic
		note.yellow('find mediaum',c,w,m)

		try:
			comic.findMedium(c,w,m)
		except Redirect: pass
					
		foreground(lambda: wentry.set_text("{:x}".format(w+1)))
	yield background
	import comic
	comic.findInfo(c,
				   lambda next: foreground(lambda: getinfo(next)),
				   gotcomic)

import gtkclipboardy as clipboardy
clipboardy(gotURL,lambda piece: b'http' == piece[:4]).run()

import expire_queries
expire_queries()
