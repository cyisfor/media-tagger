import sys

# mysterious error:
# Fatal Python error: PyImport_GetModuleDict: no module dictionary!

def application(name,ui,activate=None):
	sys.modules[__name__] = name
	__import__(ui)
	activate()

sys.modules[__name__] = application
