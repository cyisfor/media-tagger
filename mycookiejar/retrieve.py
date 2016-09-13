from mycookiejar import setup
import sys,time

if time.time() - setup.lastChecked < 6:
	import note
	note("only check for cookies every 10min")
	sys.modules[__name__] = False
else:
	from . import retrievederp
	sys.modules[__name__] = retrievederp
	setup.checked()
