import syspath
from favorites import dbqueue
import db
import sys

def gen():
	for num in sys.stdin:
		num = int(num)
		source = "https://derpibooru.org/"+str(num)
		yield source
gen = gen()

def readtobuf(buf):
	try:
		source = next(gen)
	except StopIteration: return None
	assert(len(buf) > len(source))
	b = source.encode('utf-8')
	buf[:] = b
	return len(b)

with db:
	db.execute("CREATE TEMPORARY TABLE absentderpi (host TEXT,uri TEXT)")
	dbqueue.enqueue(source)
		
