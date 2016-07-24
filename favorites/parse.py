#!/usr/bin/env python3
import sys
import os

myself = os.path.abspath(sys.modules[__name__].__file__)
here = os.path.dirname(myself)

if len(sys.argv)>1:
	mode = 0
elif 'stdin' in os.environ:
	mode = 1
else:
	mode = 2
	if not 'ferrets' in os.environ:
		os.environ['ferrets'] = 'yep'
		os.environ['name'] = 'parser'
		os.execlp('daemonize',
		          'daemonize',sys.executable,os.path.abspath(myself))

import syspath
import fixprint
from dbqueue import enqueue

def doparsethingy2():
	import fcntl,os,time
	from itertools import count
	import gtkclipboardy as clipboardy
	from mygi import Gtk, GLib, GdkPixbuf, Gdk, GObject
	GObject.threads_init()
	from catchup import Catchup, Empty
	print('loading UI')
	ui = Gtk.Builder.new_from_file(os.path.join(here,"parseui.xml"))			
	progress = ui.get_object("progress")
	progress.set_name("progress")
	css = Gtk.CssProvider()
	css.load_from_path(os.path.join(here,"parseui.css"))

	# get the default screen for the default display
	screen = Gdk.Screen.get_default()

	# new object which will store styling information affecting widget
	styleContext = Gtk.StyleContext()
	styleContext.add_provider_for_screen(screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	def gui_progress(cur,total):
		print('progress',cur,total,cur/total)
		progress.set_fraction(cur/total)
		progress.show()

	busy = GdkPixbuf.PixbufAnimation.new_from_file(
		os.path.join(here,"sweetie_thinking.gif"))
	ready = GdkPixbuf.Pixbuf.new_from_file(
		os.path.join(here, "squeetie.png"))
	win = ui.get_object("top")

	def set_busy(is_busy=True):
		print('set busy',is_busy)
		if not is_busy:
			progress.hide()
			img.set_from_pixbuf(ready)
			win.set_keep_above(False)
			return
		win.set_keep_above(True)
		img.set_from_animation(busy)
		progress.set_fraction(0)

	import catchup
	catchup = Catchup(provide_progress=True)
	# whyyyyy
	def watch_catchup():
		while True:
			type,mess = catchup.get()
			if type == catchup.PROGRESS:
				GLib.idle_add(lambda mess=mess: gui_progress(*mess))
			elif type == catchup.IDLE:
				GLib.idle_add(lambda idle=mess: set_busy(not idle))
	import threading
	t = threading.Thread(target=watch_catchup)
	t.setDaemon(True)
	t.start()
	img = ui.get_object("image")
	def gotPiece(piece):
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
	print('Okay!')
	clipboardy.run(gotPiece,lambda piece: b'http' == piece[:4])
	print('done yay',os.getpid())

def doparsethingy():
	try:
		doparsethingy2()
	except Exception as e:
		import traceback
		traceback.print_exc()
		raise SystemExit(23)
	finally:
		sys.stdout.flush()
		sys.stderr.flush()

if __name__ == '__main__':
	if mode == 0:
		enqueue(sys.argv[1])
	elif mode == 1:
		import settitle
		settitle.set('parse')
		from catchup import Catchup
		catchup = Catchup()
		for line in sys.stdin:
			enqueue(line.strip())
			catchup.poke()
		catchup.finish()
	else:
		doparsethingy()
