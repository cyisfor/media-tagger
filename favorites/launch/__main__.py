#!/usr/bin/env python3
import sys
import os

import syspath
import fixprint
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
	catchup = catchup()
	for line in sys.stdin:
		enqueue(line.strip())
		catchup.poke()
	catchup.finish()
else:
	if not 'ferrets' in os.environ:
		os.environ['ferrets'] = '1'
		os.environ['name'] = 'parse';
		os.execvp("daemonize",("daemonize",)+sys.argv
	import application
	application('media.watcher','favorites.launch.ui')
