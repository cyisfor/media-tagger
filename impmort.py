#!/usr/bin/python3

import create,withtags
import filedb
import db
import fixstdin
import fixprint

from PIL import Image
from Crypto.Hash import MD5

import codecs
import shutil
import datetime
import sys,os

implied = set()
for tag in os.environ['tags'].split(','):
    tag = tag.strip()
    implied.add(tag)

def mysplit(s,cs):
    pending = ''
    for c in s:
        if c in cs:
            if pending:
                try: int(pending)
                except ValueError as e:
                    # only yield if NOT an integer
                    yield pending
            pending = ''
        else:
            pending += c
    if pending:
        try: int(pending)
        except ValueError as e:
            yield pending

boring = set(["the","for","this","and","not","how","are","files","xcf","not","my","in"])

def copyMe(source):
    def download(dest):
        shutil.copy2(source,dest.name)
        return datetime.datetime.fromtimestamp(os.fstat(dest.fileno()).st_mtime)
    return download

cod = codecs.lookup('utf-8')

for path in sys.stdin:
    path = os.path.abspath(path.strip())
    #bpath,length = cod.encode(path,'surrogateescape')
    #if length!=len(path):
    #    raise Exception("Bad path? ",path[:length],'|',repr(path[length:]))
    for start in (os.path.expanduser("~/art/"),'/home/extra/youtube'):
        relpath = os.path.relpath(path,start)
        if '..' in relpath: break
    else: continue
    discovered = tuple(mysplit(relpath[:relpath.rfind('.')].lower(),'/ .-_*"\'?()[]{},'))
    discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])
    path = path.encode('utf-8')
    idnum = None
    source = db.c.execute("SELECT id FROM filesources WHERE path = $1",(path,))
    if source:
        if not 'recheck' in os.environ:
            #print("Not rechecking existing file")
            continue
        source = source[0][0]
        idnum = db.c.execute("SELECT id,hash FROM media WHERE sources @> ARRAY[$1::int]",(source,))
        if idnum:
            idnum,hash = idnum[0]
    else:
        source = db.c.execute("INSERT INTO sources DEFAULT VALUES RETURNING id")[0][0]
        db.c.execute("INSERT INTO filesources (id,path) VALUES ($1,$2)",(source,path))
    if not idnum:
        with open(path,'rb') as inp:
            hash = create.imageHash(inp)
        idnum = db.c.execute("SELECT id FROM media WHERE hash = $1",(hash,))
        if idnum: idnum = idnum[0][0]
        print("Hasho",idnum)
    if idnum:
        db.c.execute("UPDATE media SET sources=array(SELECT unnest(sources) UNION SELECT $2) WHERE id = $1",(idnum,source))
    print("importing",path)
    create.internet(copyMe(path),path.decode('utf-8'),implied.union(discovered),source,())
