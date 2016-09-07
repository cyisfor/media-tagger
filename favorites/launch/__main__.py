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
		import application
		application('media.watcher','launch.ui')
