import note

from favorites.launch.protocol import to_catchup, Handler

import fcntl,os,time
from itertools import count
from functools import partial
from mygi import Gtk, GLib, GdkPixbuf, Gdk, GObject
import os

here = os.path.dirname(__file__)

print('loading UI')
ui = Gtk.Builder.new_from_file(os.path.join(here,"ui.xml"))			

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
	progress.show()
	win.set_keep_above(True)
	win.set_icon(busystatic)
	# keep above, not present, avoids stealing focus
	#win.present()
	win.set_focus(None) # this doesn't really do anything
	img.set_from_animation(busy)
	progress.set_fraction(0)

def on_progress(frac):
	if frac is None:
		set_busy(False)
		return
	
progress = ui.get_object("progress")
progress.set_name("progress")

@to_catchup
class Progress(Handler):
	def starting(ident):
		from favorites.dbqueue import urifor
		win.set_tooltip_text(urifor(ident))
		set_busy(True)
	def progressed(frac):
		progress.set_fraction(frac)
	def done():
		set_busy(False)

#Progress.poke()

img = ui.get_object("image")
def gotPiece(piece):
	import sys
	from favorites.dbqueue import enqueue
	print("Trying {}".format(piece.strip().replace('\n',' ')[:90]))
	sys.stdout.flush()
	enqueue(piece.strip())
	Progress.poke()
	print('Tried')
	
win.set_title('parse')
win.show_all()
#GLib.idle_add(win.iconify)

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
