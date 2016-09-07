import sys

def application(name):
	from mygi import Gtk,Gio
	app = Gtk.Application(name,Gio.ApplicationFlags.FLAGS_NONE)
	def deco(activate):
		app.connect('activate',activate)

		app.run(sys.argv)
	return deco

sys.modules[__NAME__] = application
