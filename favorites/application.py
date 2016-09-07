import sys

def application(name,ui,activate=None):
	from mygi import Gtk,Gio
	app = Gtk.Application(name,Gio.ApplicationFlags.FLAGS_NONE)
	def startup(app):
		# change the meaning of import application for the ui module
		sys.modules[__name__] = app
		__import__(ui)
	app.connect('startup',startup)
	if activate:
		app.connect('activate',activate)
	app.run(sys.argv)

sys.modules[__NAME__] = application
