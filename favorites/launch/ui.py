import note
from favorites import catchup

import fcntl,os,time
from itertools import count
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

# whyyyyy
def watch_catchup():
	import struct
	@catchup.run
	def _(message):
		global catchup
		from favorites import build_catchup_states as C # wheeeeee
		type = message[0]
		note("type",C.lookup_client[type])
		if type == C.DONE:
			print("Catchup died, will restart?")
			catchup = C(provide_progress=True)
		elif type == C.PROGRESS:
			cur,total = struct.unpack("II",message[1:])
			GLib.idle_add(lambda cur=cur,total=total: gui_progress(cur,total))
		elif type == C.IDLE:
			idle = message[1] == 1
			GLib.idle_add(lambda idle=idle: set_busy(not idle))
		elif type == C.COMPLETE:
			remaining = struct.unpack("H",message[1:])[0]
			GLib.idle_add(lambda remaining=remaining: set_remaining(remaining))		
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

c.run()
