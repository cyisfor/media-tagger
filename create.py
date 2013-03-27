import db
import withtags
import filedb

from Crypto.Hash import SHA,MD5
from PIL import Image

import base64
import shutil
import re
import os

def imageHash(data):
    digest = SHA.new()
    setattr(digest,'write',digest.update)
    shutil.copyfileobj(data,digest)
    digest = digest.digest()
    digest = base64.b64encode(digest)
    digest = digest[:-3].decode()
    return digest

def sourceId(source):
    id = db.c.execute("SELECT id FROM urisources WHERE uri = $1",(source,))
    if id:
        return id[0][0]
    else:
        with db.saved():
            id = db.c.execute("INSERT INTO sources DEFAULT VALUES RETURNING id")
            id = id[0][0]
            db.c.execute("INSERT INTO urisources (id,uri) VALUES ($1,$2)",(id,source))
        return id

findMD5 = re.compile("[0-9a-fA-F]{32}")

def getanId(sources,uniqueSource,download,name):
    result = db.c.execute("SELECT id FROM media where media.sources @> ARRAY[$1::integer]",(uniqueSource,))
    if result:
        return result[0][0],False
    md5 = None
    for source in sources:
        m = findMD5.search(source)
        if m:
            md5 = m.group(0)
            result = db.c.execute("SELECT id FROM media WHERE md5 = $1",
                        (md5,))
            if result:
                return result[0][0],False

    with filedb.imageBecomer() as data:
        created = download(data)
        print("downloaded",created)
        digest = imageHash(data)
        result = db.c.execute("SELECT id FROM media WHERE hash = $1",(digest,))
        if result:
            print("Oops, we already had this one, from another source!")
            return result[0][0],False
        if md5 is None:
            data.seek(0,0)
            md5 = MD5.new()
            setattr(md5,'write',md5.update)
            shutil.copyfileobj(data,md5)
            md5 = md5.hexdigest()
        with db.saved():
            id = db.c.execute("INSERT INTO things DEFAULT VALUES RETURNING id")
            id = id[0][0]
            print("New image with id {:x}".format(id))
            data.seek(0,0)
            try: image = Image.open(data)
            except IOError as e:
                import time
                print(uniqueSource,data.name)
                time.sleep(9001)
                raise
            type = Image.MIME[image.format]
            sources = set([sourceId(source) for source in sources])
            db.c.execute("INSERT INTO media (id,name,hash,created,size,type,md5,sources) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",(
                id,name,digest,created,
                os.fstat(data.fileno()).st_size,type,md5,sources))
            width,height = image.size
            try:
                image.seek(1)
                animated = True
            except EOFError:
                animated = False
            image = None
            db.c.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(id,animated,width,height))
            data.become(id)
            filedb.check(id)
            return id,True
    raise RuntimeError("huh?")

def internet(download,media,tags,primarySource,otherSources):
    name = media.rsplit('/',1)
    if len(name) == 2:
        name = name[1]
    else:
        name = name[0]
    if name.endswith('.swf'): return None
    sources = set([primarySource,media] + [source for source in otherSources])
    sources = [source for source in sources if source]
    with db.transaction():
        mediaId = sourceId(media)
        id,wasCreated = getanId(sources,mediaId,download,name)
        if not wasCreated:
             print("Old image with id {:x}".format(id))
             sources = set([sourceId(source) for source in otherSources])
             db.c.execute("UPDATE media SET sources = array(SELECT unnest(sources) from media where id = $2 UNION SELECT unnest($1::bigint[])) WHERE id = $2",(sources,id))
    donetags = []
    tags = set(tags)
    print('upd8',len(tags))
    for tag in tags:
        category = withtags.makeTag(tag.category)
        name = withtags.makeTag(tag.name)
        tag = withtags.makeTag(tag.category+':'+tag.name)
        withtags.connect(name,tag)
        withtags.connect(category,tag)
        donetags.append(tag)
    for tag in donetags:
        withtags.connect(tag,id)
