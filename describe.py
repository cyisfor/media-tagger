#!/bin/python

from description import describe
import db

import sys,os,tempfile
from mmap import mmap
from delete import findId

if len(sys.argv) > 1:
	which = findId(sys.argv[1])
	import subprocess as s
	@describe(which,manual=True)
	def _(oldblurb,changed):
		temp = tempfile.NamedTemporaryFile(suffix=".html")
		if oldblurb:
			print("old",oldblurb)
			temp.write(oldblurb.encode("utf-8"))
			temp.flush()
		editor = os.environ.get("EDITOR","emacs")
		s.call([editor,temp.name])

		buf = mmap(temp.fileno(),0)
		temp.close()
		with buf:
			changed(buf[:])
	raise SystemExit

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Gio

def edit(which):
	@describe(which,manual=True)
	def _(oldblurb,changed):
		temp = tempfile.NamedTemporaryFile(suffix=".html")
		if oldblurb:
			print("old",oldblurb)
			temp.write(oldblurb.encode("utf-8"))
			temp.flush()
		editor = os.environ.get("EDITOR","emacs")
		s = Gio.Subprocess.new([editor,temp.name],
													 Gio.SubprocessFlags.NONE)
		@partial(s.wait_async,None)
		def _(s, res):
			buf = mmap(temp.fileno(),0)
			temp.close()
			with buf:
				changed(buf[:])


from functools import partial

input = lambda p: None

win = Gtk.Window()
loop = GLib.MainLoop()
win.connect("delete-event", lambda *a: loop.quit())

grid = Gtk.Grid()
win.add(grid)

entry = Gtk.Entry()
grid.add(entry)

b = Gtk.Button(label="Paste")
grid.add(b)
clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
def gotclip(c,text):
	try: entry.set_text('%x'%findId(text))
	except ValueError: pass

@partial(b.connect,"clicked")
def _(b):
	clipboard.request_text(gotclip)
# initial guess
clipboard.request_text(gotclip)

b = Gtk.Button(label="Edit")
grid.add(b)

@partial(b.connect,"clicked")
def _(b):
	edit(int(entry.get_text(),0x10))

win.show_all()
loop.run()
