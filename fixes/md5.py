from hashlib import md5 as MD5
from create import writer
import db,filedb
import shutil

with db.transaction():
    while True:
        row = db.execute('SELECT id FROM media where md5 IS NULL LIMIT 1')
        if not row: break
        id = row[0][0]
        md5 = MD5()
        with open(filedb.mediaPath(id),'rb') as data:
            shutil.copyfileobj(data,writer(md5.update))
        md5 = md5.hexdigest()
        print('fixing',id,md5)
        db.execute('UPDATE media SET md5 = $1 WHERE id = $2',(md5,id))
    
