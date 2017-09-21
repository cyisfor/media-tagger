import note

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

def later(what,*a,**kw):
	def doit():
		what(*a,**kw)
	GLib.idle_add(doit)


img = ui.get_object("image")
def gotPiece(piece):
	import sys
	from favorites.dbqueue import enqueue
	print("Trying {}".format(piece.strip().replace('\n',' ')[:90]))
	sys.stdout.flush()
	enqueue(piece.strip())
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

seen = set()
def derp(piece):
	if not 'http' == piece[:4]: return False
	h = hash(piece)
	if h in seen: return False
	seen.add(h)
	print("yay",piece)
	return True
c = clipboardy(gotPiece,derp)

def seriouslyQuit():
	print("gettin' outta here")
	c.quit()
	raise SystemExit

def button_release(win,e):
	if e.state & Gdk.ModifierType.CONTROL_MASK:
		return seriouslyQuit()
	# when begin on release, no need to hold the button to drag
	win.begin_move_drag(e.button, e.x_root, e.y_root, e.time)
	
win.connect("button-release-event",button_release)
win.connect('destroy',c.quit)

print("okay?")
c.run()
