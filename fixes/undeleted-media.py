import db
import filedb
import os

paths = set(int(s,16) for s in os.listdir(filedb.mediaPath()))
media = set(db.execute("SELECT id FROM media WHERE id = ANY($1::int[])",(paths,)))

print("cd",filedb.mediaPath())

for path in paths - media:
	print("rm {:x}".format(path))
