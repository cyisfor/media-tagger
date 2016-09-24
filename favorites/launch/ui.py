from favorites import catchup

catchup = catchup(provide_progress=True)

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

# whyyyyy
def watch_catchup():
	while True:
		type = catchup.get()
		if type == catchup.DONE:
			print("Catchup died, will restart.")
		else:
			type,mess = type
			if type == catchup.PROGRESS:
				GLib.idle_add(lambda mess=mess: gui_progress(*mess))
			elif type == catchup.IDLE:
				GLib.idle_add(lambda idle=mess: set_busy(not idle))
			elif type == catchup.COMPLETE:
				GLib.idle_add(lambda remaining=mess: set_remaining(remaining))		
			else:
				print(type,mess)
				raise SystemExit("wat")
import threading
t = threading.Thread(target=watch_catchup)
t.setDaemon(True)
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
def seriouslyQuit(win,e):
	print("Gettin' outta here!",e.button,dir(e.button))
	Gtk.main_quit()
	catchup.terminate()
	raise SystemExit
win.connect("button-release-event",seriouslyQuit)
win.connect('destroy',Gtk.main_quit)
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
except ImportError: pass
else:
	application.add_window(win)

import gtkclipboardy as clipboardy
clipboardy(gotPiece,lambda piece: b'http' == piece[:4]).start()
print('Ready!')
