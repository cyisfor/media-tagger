# whyyyyy
import db
import filedb
import os
import shutil
from itertools import count

for offset in count(0):
    for id, in db.c.execute("SELECT id FROM media ORDER BY id DESC OFFSET $1 LIMIT 50",(offset*50,)):
        if not os.path.exists(filedb.imagePath(id)):
            source,path = db.c.execute("SELECT id,path FROM filesources WHERE id in (SELECT unnest(sources) FROM media WHERE id = $1)",(id,))[0]
            print(path,'->',id)
            shutil.copy2(path,filedb.imagePath(id))
        else:
            print("ok",id)
