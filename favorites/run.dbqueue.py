import syspath
from favorites import dbqueue

if __name__ == '__main__':
	import sys,os
	import io
	inp = io.TextIOWrapper(sys.stdin.buffer,encoding='utf-8')
	for line in inp:
		dbqueue.enqueue(line.strip())
	if not 'nolaunch' in os.environ:
		from favorites.launch import __main__
