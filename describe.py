import db

import sys,os,tempfile
from mmap import mmap

which = int(sys.argv[1],0x10)

temp = tempfile.NamedTemporaryFile()

s.call([editor,temp.name))
input("Enter to commit...")

buf = mmap(temp.fileno(),0)
temp.close()

with db.transaction():
	db.execute("UPDATE descriptions SET blurb = $2 WHERE id = $1", (which,buf))
