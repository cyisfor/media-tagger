import create
import db

import hashlib

import filedb
import sys
ident = int(sys.argv[1],16)

with open(filedb.mediaPath(ident),"rb") as inp:
	digest = create.mediaHash(inp)
	inp.seek(0,0)
	md5 = hashlib.MD5()
	shutil.copyfileobj(inp,create.writer(md5.update))
	md5 = md5.hexdigest()

db.execute("UPDATE media SET md5 = $3, hash = $2 WHERE id = $1",
					 (ident,digest,md5))
