import db
import tags
import filedb
import movie
import note

from futurestuff import drain

import imageInfo

from Crypto.Hash import SHA,MD5
from tornado.concurrent import is_future, Future
from tornado import gen

import gzip
import derpmagic as magic
import base64
import shutil
import datetime
import re
import os
import subprocess

def mediaHash(data):
    digest = SHA.new()
    setattr(digest,'write',digest.update)
    shutil.copyfileobj(data,digest)
    digest = digest.digest()
    digest = base64.b64encode(digest)
    digest = digest.decode().rstrip('=')
    return digest

def isGood(type):
    category = type.split('/',1)[0]
    return category in {'image','video','audio'} or type in {'application/x-shockwave-flash'}

def sourceId(source):
    assert source is not None
    assert not isinstance(source,int)
    if source == '': return None
    if source[0] == '/': return None # todo: file sources?
    id = db.execute("SELECT id FROM urisources WHERE uri = $1",(source,))
    if id:
        return id[0][0]
    else:
        with db.saved():
            id = db.execute("INSERT INTO sources DEFAULT VALUES RETURNING id")
            id = id[0][0]
            db.execute("INSERT INTO urisources (id,uri) VALUES ($1,$2)",(id,source))
        return id

findMD5 = re.compile("[0-9a-fA-F]{32}")

class NoGood(Exception): pass

def openImage(data):
    if isinstance(data,str):
        return imageInfo.get(data)
    try: return imageInfo.get(data.name)
    except imageInfo.Error:
        import sys
        et,e,tb = sys.exc_info()
        if e['reason'].startswith('no decode delegate for this image format'):
            return None,None
        raise
    except:
        data.seek(0,0)
        print('Unknown file type')
        print(repr(data.read(20)))
        raise

def createImageDBEntry(id,image):
    db.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(id,)+image)

def retryCreateImage(id):
    source = filedb.mediaPath(id)
    image,type = openImage(source)
    if image:
        createImageDBEntry(id,image)
    return image,type

class Source:
    uri = None
    id = None
    def __repr__(self):
        return "<Source {} {}>".format(self.id,self.uri)
    def __hash__(self):
        if self.id:
            return hash((self.id,self.uri))
        return hash(self.uri)
    def __eq__(self,other):
        if self.id:
            return self.id == other.id
        return self.uri == other.uri
    def __init__(self,uri):
        if isinstance(uri,int):
            self.id = uri
        else: 
            self.uri = uri
    def lookup(self):
        if self.id is None:
            self.id = sourceId(self.uri)
        return self.id

def getanId(sources,uniqueSources,download,name):
    for uniqueSource in uniqueSources:
        result = db.execute("SELECT id FROM media where media.sources @> ARRAY[$1::integer]",(uniqueSource.lookup(),))
        if result:
            yield result[0][0], False
            return
    md5 = None
    for i,source in enumerate(sources):
        if source.uri:
            m = findMD5.search(source.uri)
            if m:
                md5 = m.group(0)
                result = db.execute("SELECT id FROM media WHERE md5 = $1",
                            (md5,))
                if result:
                    yield result[0][0],False
                return
    note("downloading to get an id")
    with filedb.mediaBecomer() as data:
        created = yield download(data)
        note('cerated',created)
        digest = mediaHash(data)
        result = db.execute("SELECT id FROM media WHERE hash = $1",(digest,))
        if result:
            print("Oops, we already had this one, from another source!")
            yield result[0][0],False
            return
        result = db.execute("SELECT medium FROM dupes WHERE hash = $1",(digest,))
        if result:
            id = result[0][0]
            print("Dupe of {:x}".format(id))
            yield id, False
            return
        result = db.execute("SELECT id FROM blacklist WHERE hash = $1",(digest,))
        if result:
            # this hash is blacklisted
            raise NoGood("blacklisted",digest)
        if md5 is None:
            data.seek(0,0)
            md5 = MD5.new()
            setattr(md5,'write',md5.update)
            shutil.copyfileobj(data,md5)
            md5 = md5.hexdigest()
        with db.saved():
            id = db.execute("INSERT INTO things DEFAULT VALUES RETURNING id")
            id = id[0][0]
            image = None
            data.seek(0,0)
            savedData = data
#            if data.name[-1] == 'z':
#                try:
#                    data = gzip.open(data)
#                except IOError as e:
#                    raise
            image,type = openImage(data)
            if not image:
                note('we hafe to guess')
                type, encoding = magic.guess_type(data.name)[:2]
                if type is None or type == 'binary':
                    note("What is {}?".format(data.name))
                    os.chdir(filedb.top+'/temp')
                    subprocess.call(['bash'])
                    type = input("Type:")
                    if not type or not '/' in type:
                        raise NoGood("Couldn't determine type of",id)
            if not isGood(type): raise NoGood(uniqueSource if uniqueSource else name,type)
            if not '.' in name:
                name += '.' + magic.guess_extension(type)
            note("New {} with id {:x} ({})".format(type,id,name))
            sources = set([source.lookup() for source in sources])
            db.execute("INSERT INTO media (id,name,hash,created,size,type,md5,sources) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",(
                id,name,digest,created,
                os.fstat(data.fileno()).st_size,type,md5,sources))
            if image: createImageDBEntry(id,image)
            else:
                if type.startswith('video'):
                    movie.isMovie(id,data)
                else:
                    print(RuntimeError('WARNING NOT AN IMAGE OR MOVIE %x'.format(id)))
            data.flush()
            savedData.become(id)
            filedb.check(id) # don't bother waiting for this if it stalls
            yield id,True
            return

tagsModule = tags

def update(id,sources,tags,name):
    donetags = []
    with db.transaction():
        db.execute("UPDATE media SET name = coalesce($3,name), sources = array(SELECT unnest(sources) from media where id = $2 UNION SELECT unnest($1::bigint[])), modified = clock_timestamp() WHERE id = $2",([source.lookup() for source in sources],id,name))
        
    tagsModule.tag(id,tags)

def internet_yield(download,media,tags,primarySource,otherSources,name=None):
    "yields a Future if it needs a download until it's done, then yields the result"
    if not name:
        name = media.rsplit('/',1)
        if len(name) == 2:
            name = name[1]
        else:
            name = name[0]
    uniqueSources = set()
    if media and '://' in media:
        media = Source(media)
        uniqueSources.add(media)
    if primarySource and isinstance(primarySource,int) or '://' in primarySource:
        primarySource = Source(primarySource)
        uniqueSources.add(primarySource)
    if not uniqueSources:
        raise RuntimeError("No unique sources in this attempt to create?")
    note('name is',name)
    otherSources = set(Source(source) for source in otherSources)
    sources = uniqueSources.union(otherSources)
    with db.transaction():
        g = getanId(sources,uniqueSources,download,name)
        result = None
        while True:
            try:
                result = g.send(result)
            except StopIteration: break
            except gen.Return as ret:
                result = ret.value
                break
        id,wasCreated = result
        note('got id',id,wasCreated)
        if not wasCreated:
             note("Old medium with id {:x}".format(id))
    note("update")
    update(id,sources,tags,name)
    yield id,wasCreated

def internet_future(ioloop,*a,**kw):
    "the async version of internet_yield"
    return drain(ioloop,internet_yield(*a,**kw))

def internet(*a,**kw):
    "the sync version of internet_yield"
    g = internet_yield(*a,**kw)
    result = None
    while True:
        try:
            result = g.send(result)
        except StopIteration: 
            break
        except gen.Return as ret:
            result = ret.value
            break
        if is_future(result):
            if result.running():
                raise RuntimeError("Download can't complete right away, but this is the sync version!")
            result = result.result()
            note('future produced',result)
    return result

def copyMe(source):
    def download(dest):
        shutil.copy2(source,dest.name)
        return datetime.datetime.fromtimestamp(os.fstat(dest.fileno()).st_mtime)
    return download

