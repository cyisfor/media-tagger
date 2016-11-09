import note
from favorites import catchup

import fcntl,os,time
from itertools import count
from functools import partial
from mygi import Gtk, GLib, GdkPixbuf, Gdk, GObject
import os

here = os.path.dirname(__file__)

print('loading UI')
ui = Gtk.Builder.new_from_file(os.path.join(here,"ui.xml"))			
progress = ui.get_object("progress")
progress.set_name("progress")

def gui_progress(cur,total):
	progress.set_fraction(cur/total)
	progress.show()

processed = 0
def set_remaining(remaining):
	global processed
	win.set_tooltip_text("%d→%d"%(remaining,processed))
	processed += 1

busy = GdkPixbuf.PixbufAnimation.new_from_file(
	os.path.join(here,"sweetie_thinking.gif"))
busystatic = busy.get_static_image()
ready = GdkPixbuf.Pixbuf.new_from_file(
	os.path.join(here, "squeetie.png"))
win = ui.get_object("top")
	
def set_busy(is_busy=True):
	print('set busy',is_busy)
	if not is_busy:
		progress.hide()
		img.set_from_pixbuf(ready)
		win.set_keep_above(False)
		win.set_icon(ready)
		return
	win.set_keep_above(True)
	win.set_icon(busystatic)
	img.set_from_animation(busy)
	progress.set_fraction(0)

catchup = catchup(provide_progress=True)

def later(what,*a,**kw):
	def doit():
		what(*a,**kw)
	GLib.idle_add(doit)

@partial(GLib.timeout_add,10000)
def _():
	try: catchup.status()
	except Exception:
		import traceback
		traceback.print_exc()
	return GLib.SOURCE_CONTINUE
	
# whyyyyy
def watch_catchup():
	import struct
	@catchup.run
	def _(message):
		global catchup
		from favorites import build_catchup_states as C # wheeeeee
		type = message[0]
		if type == C.DONE:
			print("Catchup died, will restart?")
			catchup = C(provide_progress=True)
		elif type == C.STATUS:
			cur,total,remaining,idle = struct.unpack("IIHB",message[1:])
			note("got status",cur,total,remaining,idle)
			not_idle = (idle == 0)
			later(set_remaining,remaining)
			later(gui_progress,cur,total)
			later(set_busy,not_idle)
		elif type == C.PROGRESS:
			cur,total = struct.unpack("II",message[1:])
			later(gui_progress,cur,total)
		elif type == C.IDLE:
			note("got idle",message[1])
			later(set_busy,message[1] == 0)
		elif type == C.COMPLETE:
			remaining = struct.unpack("H",message[1:])[0]
			later(set_remaining,remaining)
		else:
			print(type,message)
			raise SystemExit("wat")
import threading
t = threading.Thread(target=watch_catchup,daemon=True)
t.start()


img = ui.get_object("image")
def gotPiece(piece):
	import sys
	from favorites.dbqueue import enqueue
	print("Trying {}".format(piece.strip().replace('\n',' ')[:90]))
	sys.stdout.flush()
	enqueue(piece.strip())
	catchup.poke()
	print("poked")

	print('Ready to parse')
win.set_title('parse')
win.show_all()

css = Gtk.CssProvider()
css.load_from_path(os.path.join(here,"ui.css"))

# get the default screen for the default display
screen = Gdk.Screen.get_default()

# new object which will store styling information affecting widget
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

try:
	import application
	application.add_window(win)
except ImportError: pass
except AttributeError: pass

import gtkclipboardy as clipboardy

c = clipboardy(gotPiece,lambda piece: b'http' == piece[:4])

def seriouslyQuit():
	print("gettin' outta here")
	catchup.stop()
	c.quit()
	raise SystemExit

def button_release(win,e):
	if e.state & Gdk.ModifierType.CONTROL_MASK:
		return seriouslyQuit()
	# when begin on release, no need to hold the button to drag
	win.begin_move_drag(e.button, e.x_root, e.y_root, e.time)
	
win.connect("button-release-event",button_release)
win.connect('destroy',c.quit)

catchup.poke()
c.run()
