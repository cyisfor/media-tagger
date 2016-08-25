import db

import sys,os,tempfile
from mmap import mmap
import subprocess as s

which = int(sys.argv[1],0x10)

oldblurb = db.execute("SELECT blurb FROM descriptions WHERE id = $1",
                      which)

temp = tempfile.NamedTemporaryFile()
if oldblurb:
	temp.write(oldblurb[0][0])
editor = os.environ.get("EDITOR","emacs")
s.call([editor,temp.name])
input("Enter to commit...")

buf = mmap(temp.fileno(),0)
temp.close()

with db.transaction():
	if oldblurb:
		db.execute("UPDATE descriptions SET blurb = $2 WHERE id = $1", (which,buf[:]))
	else:
		db.execute("INSERT INTO descriptions (id,blurb) VALUES($1,$2)", (which,buf[:]))
