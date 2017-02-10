#!/usr/bin/env python3
import sys
import os

import syspath
from better import print as _
from favorites.dbqueue import enqueue


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

if len(sys.argv)>1:
	enqueue(sys.argv[1])
elif 'stdin' in os.environ:
	import settitle
	settitle.set('parse')
	from favorites import catchup
	@catchup
	def _(poke,stop):
		for line in sys.stdin:
			enqueue(line.strip())
			poke()
		#stop()
else:
	if not 'ferrets' in os.environ:
		os.environ['ferrets'] = '1'
		os.environ['name'] = 'parse';
		import sys,os
		script = os.path.abspath(sys.modules[__name__].__file__)
		os.execvp("daemonize",["daemonize",sys.executable,script])
	import application
	application('media.watcher','favorites.launch.ui')
