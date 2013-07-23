import db
import withtags
import filedb

from Crypto.Hash import SHA,MD5
from PIL import Image

from pprint import pprint

import gzip
import magic
import base64
import shutil
import re
import os
import subprocess

def imageHash(data):
    digest = SHA.new()
    setattr(digest,'write',digest.update)
    shutil.copyfileobj(data,digest)
    digest = digest.digest()
    digest = base64.b64encode(digest)
    print(digest)
    digest = digest.decode().rstrip('=')
    return digest

def isGood(type):
    category = type.split('/',1)[0]
    return category in {'image','video','audio'} or type in {'application/x-shockwave-flash'}

def sourceId(source):
    if source is None: return None
    if isinstance(source,int): return source
    if source[0] == '/': return None
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

class NoGood(Exception): pass

def getanId(sources,uniqueSource,download,name):
    result = db.c.execute("SELECT id FROM media where media.sources @> ARRAY[$1::integer]",(uniqueSource,)) if uniqueSource else False
    if result:
        return result[0][0],False
    md5 = None
    for source in sources:
        if isinstance(source,int): continue
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
        result = db.c.execute("SELECT id FROM blacklist WHERE hash = $1",(digest,))
        if result:
            # this hash is blacklisted
            raise NoGood("blacklisted")
        if md5 is None:
            data.seek(0,0)
            md5 = MD5.new()
            setattr(md5,'write',md5.update)
            shutil.copyfileobj(data,md5)
            md5 = md5.hexdigest()
        with db.saved():
            id = db.c.execute("INSERT INTO things DEFAULT VALUES RETURNING id")
            id = id[0][0]
            image = None
            data.seek(0,0)
            savedData = data
            if data.name[-1] == 'z':
                try:
                    data = gzip.open(data)
                except IOError as e:
                    raise
            try:
                image = Image.open(data)
            except IOError as e:
                pass
            if image:
                type = Image.MIME[image.format]
            else:
                type, encoding = magic.guess_type(data.name)
                if type is None:
                    print("What is {}?".format(data.name))
                    os.chdir(filedb.top+'/temp')
                    subprocess.call(['bash'])
                    type = input("Type:")
                    if not type or not '/' in type:
                        raise SystemExit("Bailing out")
            print('XXXXXXX',type)
            if not isGood(type): raise NoGood()
            if not '.' in name:
                name += '.' + magic.guess_extension(type)
            print("New {} with id {:x} ({})".format(type,id,name))
            sources = set([sourceId(source) for source in sources])
            db.c.execute("INSERT INTO media (id,name,hash,created,size,type,md5,sources) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",(
                id,name,digest,created,
                os.fstat(data.fileno()).st_size,type,md5,sources))
            if image:
                width,height = image.size
                try:
                    image.seek(1)
                    animated = True
                except EOFError:
                    animated = False
                image = None
                db.c.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(id,animated,width,height))
            data.flush()
            savedData.become(id)
            filedb.check(id)
            return id,True
    raise RuntimeError("huh?")

def internet(download,media,tags,primarySource,otherSources):
    name = media.rsplit('/',1)
    if len(name) == 2:
        name = name[1]
    else:
        name = name[0]
    name = name.rsplit('?',1)[-1]
    if '://' in media and '://' in primarySource:
        sources = set([primarySource,media] + [source for source in otherSources])
    else:
        sources = otherSources
    sources = [source for source in sources if source]
    with db.transaction():
        mediaId = sourceId(media)
        try:
            id,wasCreated = getanId(sources,mediaId,download,name)
        except NoGood:
            return
        if not wasCreated:
             print("Old image with id {:x}".format(id))
             sources = set([sourceId(source) for source in otherSources])
             db.c.execute("UPDATE media SET sources = array(SELECT unnest(sources) from media where id = $2 UNION SELECT unnest($1::bigint[])) WHERE id = $2",(sources,id))
    donetags = []
    tags = set(tags)
    for tag in tags:
        if hasattr(tag,'category'):
            name = withtags.makeTag(tag.name)
            if tag.category and tag.category != 'general':
                category = withtags.makeTag(tag.category)
                tag = withtags.makeTag(tag.category+':'+tag.name)
                withtags.connect(tag,name)
                withtags.connect(name,tag)
                withtags.connect(category,tag)
                # NOT this:
                # withtags.connect(tag,category)
            else:
                tag = name
        else:
            tag = withtags.makeTag(tag)
        donetags.append(tag)
    for tag in donetags:
        withtags.connect(id,tag)
        withtags.connect(tag,id)
