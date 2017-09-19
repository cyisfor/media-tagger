import db
import filedb
import os

print("cd",filedb.mediaPath())

def gewdint(s):
	try: return int(s)
	except ValueError:
		print("rm",s)
		return None

paths = (gewdint(s,16) for s in os.listdir(filedb.mediaPath()))
paths = (path for path in paths if path is not None)
paths = set(paths)
media = set(db.execute("SELECT id FROM media WHERE id = ANY($1::int[])",(paths,)))

for path in paths - media:
	print("rm {:x}".format(path))
