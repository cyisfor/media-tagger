from mycookiejar import setup
import sys

if time.time() - setup.lastChecked < 600:
	import note
	note("only check for cookies every 10min")
	sys.modules[__name__] = False
else:
	import retrievederp
	sys.modules[__name__] = retrievederp-
