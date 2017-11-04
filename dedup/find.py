try:
	import pgi
	pgi.install_as_gi()
except ImportError: pass

from threading import Thread
import queue

#merge.merge(0x26cf5,0x26bbe,True) # corrupt image
mergequeue = queue.Queue(0x100)

import filedb
import db


def regularlyCommit():
	import merge
	while True:
		message = None
		try:
			message = mergequeue.get()
			if message == 'done':
				print('done')
				break
			dest,source,inferior = message
			print(hex(dest),'inferior to',hex(source))
			merge.merge(source,dest,inferior)
			print('left',mergequeue.qsize())
		except Exception as e:
			import traceback
			traceback.print_exc()
		finally:
			if message:
				mergequeue.task_done()

t = Thread(target=regularlyCommit)
t.start()

import gi
from gi.repository import Gtk,GLib
from functools import partial


import merge

import os

findStmt = '''WITH
nasis AS (SELECT sis AS id,count(bro) FROM nadupes GROUP BY sis),
nabro AS (SELECT bro AS id,count(sis) FROM nadupes GROUP BY bro),
toomanynas AS (
SELECT id FROM nasis WHERE count > 10
UNION
SELECT id FROM nabro WHERE count > 10)
SELECT sis,bro FROM possibleDupes WHERE 
NOT sis IN (select id from glibsucks) AND 
NOT bro IN (select id from glibsucks) AND
NOT sis IN (SELECT id FROM toomanynas) AND
NOT bro IN (SELECT id FROM toomanynas) AND
NOT (
  sis IN (select sis FROM nadupes WHERE nadupes.bro = possibleDupes.bro) OR
  sis IN (select bro FROM nadupes WHERE nadupes.sis = possibleDupes.bro) 
) AND
sis IN (select id from media where type = ANY($2)) AND 
bro IN (select id from media where type = ANY($2)) AND 
dist < $1 ORDER BY sis DESC LIMIT 1000'''

maxDistance = os.environ.get('distance')
if maxDistance is None:
	maxDistance = 200
else:
	maxDistance = int(maxDistance)

loop = GLib.MainLoop()

def tracking(f):
	import traceback
	try: raise RuntimeError
	except RuntimeError:
		here = ''.join(traceback.format_stack())
	def wrapper(*a,**kw):
		try:
			return f(*a,**kw)
		except:
			print('called from:')
			print(here)
			print('-'*20)
			raise
	return wrapper


def once(f):
	def wrapper(*a,**kw):
		print('uh')
		try:
			return f(*a,**kw)
		except:
			import traceback
			traceback.print_exc()
			return GLib.SOURCE_REMOVE
	return wrapper

idlers = set()

def idle_add(f,*a,**kw):
	# have to slow this down b/c pgi has a bug that infinite loops w/out calling callback
	idlers.add(f)
	GLib.timeout_add(100,once(tracking(f)),*a,**kw)

maxoff = int(db.execute("SELECT max(id) FROM media")[0][0] / 10000)

print('pages',maxoff)
print(findStmt)
class Finder:
	a = b = -1
	done = False
	def __init__(self):
		self.dupes = iter(())
		self.next()
	def next(self):
		try: self.source, self.dest = next(self.dupes)
		except StopIteration:
			print('reloading dupes!')
			self.dupes = iter(db.execute(findStmt,(
				maxDistance,
				['image/png',
				 'image/jpeg'])))
			try:
				self.source, self.dest = next(self.dupes)
			except StopIteration:
				self.done = True
				print('all done!')
				loop.quit()
				return
		if not (
				db.execute('SELECT id FROM media WHERE id = $1',(self.dest,))
				and
				db.execute('SELECT id FROM media WHERE id = $1',(self.source,))):
			print('oops')
			idle_add(self.next)
			return
		if self.source > self.dest:
			self.source, self.dest = self.dest, self.source
	def nodupe(self,then=None):
		print('nadupe',hex(self.dest),hex(self.source))
		if self.dest > self.source:
			a = self.source
			b = self.dest
		else:
			a = self.dest
			b = self.source
		print('boing',a,b)
		try: db.execute('INSERT INTO nadupes (bro,sis) VALUES ($1,$2)',(a,b))
		except db.ProgrammingError as e:
			print(e)
		self.next()
	def dupe(self,inferior):
		print('dupe',hex(self.dest),hex(self.source))
		mergequeue.put((self.dest,self.source,inferior))
		self.next()

finder = Finder()
if finder.done:
	raise SystemExit

import gi
from gi.repository import Gtk,Gdk,GdkPixbuf,GLib

win = Gtk.Window(
		title="Dupe resolver")

vbox = Gtk.VBox()
win.add(vbox)

labelbox = Gtk.HBox()
vbox.pack_start(labelbox,False, True, 0)
imagebox = Gtk.HBox()
label = Gtk.Label(label='...')
labelbox.pack_start(label,True,True,0)

class Image:
	def __init__(self,id):
		self.id = id
	_animation = None
	@property
	def animation(self):
		if self._animation: return self._animation
		self._animation = GdkPixbuf.PixbufAnimation.new_from_file(filedb.mediaPath(self.id))
		return self._animation

class ImageFlipper:
	def __init__(self):
		self.image = Gtk.Image()
	def setup(self,images):
		global busy
		print('new images',images)
		images = [Image(image) for image in images]
		self.images = images
		self.which = 0
		self.image.set_from_animation(images[0].animation)
		label.set_text(hex(self.images[self.which].id))
		busy = False
	def next(self):
		self.which = (self.which + 1)%len(self.images)
		label.set_text(hex(self.images[self.which].id))
		self.image.set_from_animation(self.images[self.which].animation)
		if self.images[self.which].id == finder.dest:
			# derp
			finder.dest, finder.source = finder.source, finder.dest

flipper = ImageFlipper()
imagebox.pack_start(flipper.image,True,True,0)

viewport = Gtk.ScrolledWindow(None,None)
viewport.add(imagebox)

viewport.set_size_request(640,480)

scroller = viewport.get_vadjustment()
hscroll = viewport.get_hadjustment()

vbox.pack_start(viewport,True,True,0)

busy = True

def scrollReset():
	scroller.set_value(0)
	hscroll.set_value(0)

vbox.pack_start(Gtk.Label("Dupe? (note, right one will be deleted)"),False,False,0)

buttonbox = Gtk.HBox()
vbox.pack_start(buttonbox,False,False,0)

activator = Gtk.ToggleButton.new_with_label('Activated')
buttonbox.pack_start(activator,False,False,0)

buttonkeys = {}

pressed = set()

def onpress(win,e):
	global busy
	if busy: return True
	if not activator.get_active(): return True
	if e.keyval in pressed: return True
	btn = buttonkeys.get(e.keyval)
	if btn:
		pressed.add(e.keyval)
		btn.clicked()
		return True

	if e.keyval == Gdk.KEY_Up:
		pressed.add(e.keyval)
		incr = scroller.get_page_increment()
		scroller.set_value(scroller.get_value()-incr)
		return True
	elif e.keyval == Gdk.KEY_Down:
		pressed.add(e.keyval)
		incr = scroller.get_page_increment()
		scroller.set_value(scroller.get_value()+incr)
		return True
	elif e.keyval == Gdk.KEY_Left:
		pressed.add(e.keyval)
		hscroll.set_value(hscroll.get_value()-hscroll.get_page_increment())
		return True
	elif e.keyval == Gdk.KEY_Right:
		pressed.add(e.keyval)
		hscroll.set_value(hscroll.get_value()+hscroll.get_page_increment())
		return True
	return False

def unpress(win,e):
	pressed.discard(e.keyval)

win.connect('key-press-event',onpress)
win.connect('key-release-event',unpress)

def addButton(text,shortcut,ambusy=True):
	def decorator(f):
		btn = Gtk.Button(label=text)
		buttonbox.pack_start(btn,True,True,3)
		if ambusy:
			def getbusy(e):
				global busy
				busy = True
				label.set_text('busy')
				idle_add(f,e)
		else:
			getbusy = f
		btn.connect('clicked',getbusy)
		buttonkeys[shortcut] = btn
	return decorator

flipper.setup([finder.source,finder.dest])

@addButton("Superior",Gdk.KEY_7)
def answer(e):
	# therefore the right one is inferior (finder.source)
	finder.dupe(True)
	scrollReset()
	flipper.setup([finder.source,finder.dest])

@addButton("Yes",Gdk.KEY_8)
def answer(e):
	finder.dupe(False)
	scrollReset()
	flipper.setup([finder.source,finder.dest])

@addButton("Swap",Gdk.KEY_9,ambusy=False)
def answer(e):
	flipper.next()

@addButton("No",Gdk.KEY_0)
def answer(e):
	finder.nodupe()
	scrollReset()
	flipper.setup([finder.source,finder.dest])

def cleanup(e):
	win.hide()
	idle_add(lambda: loop.quit())

win.connect('destroy',cleanup)
win.show_all()
try:
	loop.run()
finally:
	print('Waiting for merges to finish')
	mergequeue.put('done')
	mergequeue.join()
