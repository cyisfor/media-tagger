import create,withtags
import filedb
import db

from PIL import Image
from Crypto.Hash import MD5

import shutil
import datetime
import sys,os

implied = set()
for tag in os.environ['tags'].split(','):
    tag = tag.strip()
    tag = withtags.makeTag(tag)
    implied.add(tag)

def isGood(name):
    name = name.lower()
    return name[-4:]=='.gif' or name[-4:]=='.png' or name[-5:]=='.jpeg' or name[-4:]=='.jpg'


vtop = os.getcwd()

def mysplit(s,cs):
    pending = ''
    for c in s:
        if c in cs:
            try: int(pending)
            except ValueError as e:
                yield pending
            pending = ''
        else:
            pending += c
    try: int(pending)
    except ValueError as e:
        yield pending

boring = set(["the","for","this","and","not","how","are","files","xcf"])

for top,dirs,names in os.walk(vtop):
    for name in names:
        if not isGood(name): continue
        path = os.path.join(top,name)
        print(path)
        discovered = tuple(mysplit(path[len(vtop)+1:path.rfind('.')].lower(),'/ .-_*"\'?()[]{}'))
        discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])
        discovered = [withtags.makeTag(tag) for tag in discovered]
        idnum = None
        source = db.c.execute("SELECT id FROM filesources WHERE path = $1",(path,))
        if source:
            source = source[0][0]
            idnum = db.c.execute("SELECT id,hash FROM media WHERE sources @> ARRAY[$1::int]",(source,))
            if idnum:
                idnum,hash = idnum[0]
        print("derp",idnum)
        if not idnum:
            if not source:
                source = db.c.execute("INSERT INTO sources DEFAULT VALUES RETURNING id")[0][0]
                db.c.execute("INSERT INTO filesources (id,path) VALUES ($1,$2)",(source,path))
            with open(path,'rb') as inp:
                hash = create.imageHash(inp)
            idnum = db.c.execute("SELECT id FROM media WHERE hash = $1",(hash,))
            if idnum: idnum = idnum[0][0]
            print("Hasho",idnum)
        if not idnum:
            print("importing",path)
            with db.transaction(),filedb.imageBecomer() as data:
                try: image = Image.open(path)
                except:
                    print(path)
                    continue
                size = os.stat(path).st_size
                type = Image.MIME[image.format]
                md5 = MD5.new()
                created = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
                setattr(md5,'write',md5.update)
                with open(path,'rb') as inp:
                    shutil.copyfileobj(inp,md5)
                    inp.seek(0,0)
                    shutil.copyfileobj(inp,data)
                md5 = md5.hexdigest()

                idnum = db.c.execute("INSERT INTO things DEFAULT VALUES RETURNING id")[0][0]
                db.c.execute("INSERT INTO media (id,name,hash,created,size,type,md5,sources) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
                    (idnum,name,hash,created,size,type,md5,[source]))
                width,height = image.size
                try:
                    image.seek(1)
                    animated = True
                except EOFError:
                    animated = False
                image = None
                db.c.execute("INSERT INTO images (id,animated,width,height) VALUES ($1,$2,$3,$4)",(idnum,animated,width,height))
                data.become(idnum)
            print("tagging",idnum)
            for tag in implied.union(discovered):
                withtags.connect(idnum,tag)
            db.c.execute("UPDATE media SET sources = array(SELECT unnest(sources) FROM media WHERE id = $1 UNION SELECT $2) WHERE id = $1",(idnum,source))
