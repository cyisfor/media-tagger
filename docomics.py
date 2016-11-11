#!/usr/bin/python3
import note
from bgworker import makeWorkers

from mygi import GLib

def databaseInit():
	import comic,db
	from favorites.parse import parse, ParseError, normalize
	import favorites.parsers # side effects galore!
	
foreground = GLib.idle_add
in_foreground,background = makeWorkers(foreground, databaseInit)

from redirect import Redirect
import expire_queries
something_changed = expire_queries()

from mygi import Gtk,Gdk,GObject
import sys
window = Gtk.Window()

window.set_keep_above(True)
ui = {
	'box': Gtk.VBox(),
	'c': Gtk.Entry(),
	'w': Gtk.Entry(),
	'status': Gtk.Label()
}

window.add(ui['box'])
ui['box'].pack_start(ui['c'],True,True,0)
ui['box'].pack_start(ui['w'],True,True,0)

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
	note("getwinfo");
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

import queue
urlqueue = queue.Queue()
numqueued = 0

def gotURL(url):
	url = url.strip()
	note("Queueing {}".format(url))
	sys.stdout.flush()
	numqueued += 1
	ui['status'].set_text(str(numqueued));
	urlqueue.put(url)

def in_background(f):
	def wrapper(*a,**kw):
		background(lambda: f(*a,**kw))
	return wrapper

@in_background
def parseOne():
	note("getting....");
	url = urlqueue.get()
	yield foreground
	numqueued -= 1
	ui['status'].set_text(str(numqueued))
	yield background
	note("trying",url)
	from favorites.parse import parse,normalize,ParseError
	try:
		m = parse(normalize(url),noCreate=True)
		if not m:
			note.red('uhhh',url)
	except ParseError:
		try: m = int(url.rstrip('/').rsplit('/',1)[-1],0x10)
		except ValueError:
			note.red('nope')
			return
	note('ok m is',m)
	w = None
	yield foreground
	c = ui['c'].get_text()
	if c:
		c = int(c,0x10)
		note('yay',hex(c))
	else:
		yield background
		import db
		note('m is still',m)
		c = db.execute('SELECT comic,which FROM comicpage WHERE medium = $1 ORDER BY which DESC',(m,))
		if len(c)>0:
			note.yellow('boop!',c)
			c = c[0]
			c,w = c
			yield foreground
			ui['c'].set_text('{:x}'.format(c))
			ui['w'].set_text('{:x}'.format(w+1))
			parseOne()
			return
		# still in bg
		c = db.execute('SELECT MAX(id)+1 FROM comics')[0][0]
		yield foreground # -> gui
		ui['c'].set_text('{:x}'.format(c))
	if w is None:
		yield foreground
		w = ui['w'].get_text()
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
				ui['w'].set_text('{:x}'.format(w))
			except TypeError:
				note.red(repr(w))
				raise
	def gotcomic(title,description,source,tags):
		try: note.yellow('find mediaum',c,w,m)
		finally:
			note.alarm("foo")
		import comic

		try:
			_,created = comic.findMediumDerp(c,w,m)
			if created:
				note.yellow("something changed",m)
				something_changed()
			else:
				note("nothing changed",m)
		except Redirect: pass
		yield foreground
		ui['w'].set_text("{:x}".format(w+1))		
		parseOne()
		
	yield background
	import comic
	note("getting comic")
	gen = comic.findInfo(c,
											 lambda next: foreground(lambda: getinfo(next)),
											 gotcomic)
	if gen:
		yield from gen

parseOne()

import gtkclipboardy as clipboardy

c = clipboardy(gotURL,lambda piece: b'http' == piece[:4])
window.connect('destroy',c.quit)
c.run()
