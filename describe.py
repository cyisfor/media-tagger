import db

import sys,os,tempfile
from mmap import mmap
import subprocess as s

def edit(which):
	oldblurb = db.execute("SELECT blurb FROM descriptions WHERE id = $1",
												(which,))

	temp = tempfile.NamedTemporaryFile(suffix=".html")
	if oldblurb:
		print("old",oldblurb)
		temp.write(oldblurb[0][0].encode("utf-8"))
		temp.flush()
	editor = os.environ.get("EDITOR","emacs")
	s.call([editor,temp.name])
	input("Enter to commit...")

	buf = mmap(temp.fileno(),0)
	temp.close()
	print("uhh",buf[:])
	with db.transaction():
		if oldblurb:
			db.execute("UPDATE descriptions SET blurb = $2 WHERE id = $1", (which,buf[:]))
		else:
			db.execute("INSERT INTO descriptions (id,blurb) VALUES($1,$2)", (which,buf[:]))

if len(sys.argv) > 1:
	edit(int(sys.argv[1],0x10))
	raise SystemExit

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from delete import findId

win = Gtk.Window()
win.connect("delete-event", Gtk.main_quit)

grid = Gtk.Grid()
win.add(grid)

entry = Gtk.Entry()
grid.add(entry)

b = Gtk.Button(label="Paste")
grid.add(b)
clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
def gotclip(text):
	entry.set_text(findId(text))

@partial(b.connect,"clicked")
def _(b,e,n):
	clipboard.request_text(gotclip)
# initial guess
clipboard.request_text(gotclip)

b = Gtk.Button(label="Edit")
grid.add(b)

@partial(b.connect,"clicked")
def _(b,e,n):
	edit(int(entry.get_text(),0x10))

win.show_all()
Gtk.main()
