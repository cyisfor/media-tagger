#!/usr/bin/env python3
import sys
import os

import syspath
import fixprint
from dbqueue import enqueue


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

if __name__ == '__main__':
	if mode == 0:
		enqueue(sys.argv[1])
	elif mode == 1:
		import settitle
		settitle.set('parse')
		from catchup import Catchup
		catchup = Catchup()
		for line in sys.stdin:
			enqueue(line.strip())
			catchup.poke()
		catchup.finish()
	else:
		import application
		application('media.watcher','parse.ui')
