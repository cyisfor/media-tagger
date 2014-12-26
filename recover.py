import create,withtags
import filedb
import db

from PIL import Image
from Crypto.Hash import MD5

import shutil
import datetime
import sys,os

recovered = withtags.makeTag('special:recovered')

for path in os.listdir(os.path.join(filedb.base,'media')):
    base = path
    path = os.path.join(filedb.base,'media',base)
    try:
        id = int(base,0x10)
        if db.execute("SELECT id FROM things WHERE id = $1",(id,)):
            continue
    except ValueError: continue
    with open(path,'rb') as inp:
        hash = create.mediaHash(inp)
    oldid = db.execute("SELECT id FROM media WHERE hash = $1",(hash,))
    if oldid:
        oldid = oldid[0][0]
        # we got this, OK to delete.
        mtime = min(os.stat(filedb.mediaPath(oldid)).st_mtime, os.stat(path).st_mtime)
        os.utime(filedb.mediaPath(oldid),(mtime,mtime))
        print('rm',path)
        continue
    # now we're sure path is a lost medium!
    with db.transaction():
        db.execute("INSERT INTO things (id) VALUES ($1)",(id,))
        # TODO: recover lost media not just lost images
        try: image = Image.open(path)
        except:
            print(path)
            raise
        size = os.stat(path).st_size
        type = Image.MIME[image.format]
        md5 = MD5.new()
        created = datetime.datetime.fromtimestamp(mtime)
        setattr(md5,'write',md5.update)
        with open(path,'rb') as inp:
            shutil.copyfileobj(inp,md5)
        md5 = md5.hexdigest()
        db.execute("INSERT INTO media (id,name,hash,created,size,type,md5) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                (id,"unknown."+image.format.lower(),hash,created,size,type,md5))
        width,height = image.size
        try:
            image.seek(1)
            animated = True
        except EOFError:
            animated = False
        image = None
        db.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(id,animated,width,height))
        withtags.connect(id,recovered)
    print("We saved a file!",file=sys.stderr)
