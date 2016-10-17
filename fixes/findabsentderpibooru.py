import syspath
from favorites import dbqueue
import db
import sys

def gen():
	for num in sys.stdin:
		num = int(num)
		source = "https://derpibooru.org/"+str(num)
		print(num)
		yield source
gen = gen()

host = dbqueue.host("derpibooru.org")
print(host)

def readtobuf(buf):
	try:
		source = next(gen)
	except StopIteration: return None
	assert len(buf) > len(source),len(buf)
	b = (source + "\n").encode('utf-8')
	buf[:len(b)] = b
	return len(b)

with db.transaction():
	db.execute("CREATE TEMPORARY TABLE absentderpi (uri TEXT)")
	db.copy("COPY absentderpi (uri) FROM STDIN WITH encoding 'utf8'",readtobuf)
	db.execute("INSERT INTO parseQueue (host,uri) SELECT $1,uri FROM absentderpi WHERE NOT EXISTS(select 1 from parseQueue where parseQueue.uri = absentderpi.uri)", (host,))
	print("go")
