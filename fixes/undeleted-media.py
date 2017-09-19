import db
import filedb
import os

os.chdir(filedb.mediaPath())

def gewdint(s):
	try: return int(s,16)
	except ValueError:
		os.unlink(s)
		return None

paths = (gewdint(s) for s in os.listdir(filedb.mediaPath()))
paths = (path for path in paths if path is not None)
paths = set(paths)
media = set(r[0] for r in db.execute("SELECT id FROM media WHERE id = ANY($1::int[])",(paths,)))

for id in paths - media:
	print("culling",id)
	os.unlink('{:x}'.format(id))
