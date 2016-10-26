import sys

def application(name,ui,activate=None):
	from mygi import Gtk,Gio
	app = Gtk.Application(application_id=name+'derp',
	                      flags=Gio.ApplicationFlags.FLAGS_NONE)
	def startup(app):
		# HAX: change the meaning of import application for the ui module
		sys.modules[__name__] = app
		__import__(ui)
	app.connect('startup',startup)
	if activate:
		app.connect('activate',activate)
	else:
		def gtksucks(app): pass
		app.connect('activate',gtksucks)
	app.run(sys.argv)

sys.modules[__name__] = application
