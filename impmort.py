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

cod = codecs.lookup('utf-8')

try:
    db.c.execute("CREATE TABLE badfiles (path TEXT PRIMARY KEY)")
except: pass

skipping = False
recheck = os.environ.get('recheck')
for path in sys.stdin:
    path = os.path.abspath(path.strip())
    if skipping: 
        if path == '/home/user/art/laptop/frozen elsa disney movie poster black.jpg':
            skipping = False
        continue    
    #bpath,length = cod.encode(path,'surrogateescape')
    #if length!=len(path):
    #    raise Exception("Bad path? ",path[:length],'|',repr(path[length:]))
    for start in (os.path.expanduser("~/art/"),'/home/extra/youtube'):
        relpath = os.path.relpath(path,start)
        if not '..' in relpath: break
    else: continue
    name = os.path.basename(relpath)
    discovered = set()
    officialTags = False
    if ' - ' in name:
        tags,rest = name.split(' - ',1)
        if not '-' in tags:
            print('found official tags header',tags)
            officialTags = True
            discovered = set(tag.strip() for tag in tags.split(','))
    discovered = discovered.union(mysplit(relpath[:relpath.rfind('.')].lower(),'/ .-_*"\'?()[]{},'))
    discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])
    #print(implied.union(discovered))
    path = path.encode('utf-8')
    bad = db.c.execute("SELECT COUNT(path) FROM badfiles WHERE path = $1",(path,))
    if bad[0][0] != 0: continue
    idnum = None
    source = db.c.execute("SELECT id FROM filesources WHERE path = $1",(path,))
    try:
        with db.transaction():
            if source:
                if not recheck: #(officialTags or recheck):
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
                    hash = create.mediaHash(inp)
                idnum = db.c.execute("SELECT id FROM media WHERE hash = $1",(hash,))
                if idnum: idnum = idnum[0][0]
                print("Hasho",idnum)
            if idnum:
                print("Adding saource",idnum,source)
                db.c.execute("UPDATE media SET sources=array(SELECT unnest(sources) UNION SELECT $2) WHERE id = $1",(idnum,source))
            print("importing",path,discovered)
            create.internet(create.copyMe(path),path.decode('utf-8'),implied.union(discovered),source,())
    except create.NoGood: 
        db.c.execute("INSERT INTO badfiles (path) VALUES ($1)",(path,))
