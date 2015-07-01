#!/usr/bin/python3

import create
import withtags
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

def discover(path):
    discovered = set()

    if path[0] == b'/'[0]:
        for start in (os.path.expanduser("~/art/"),'/home/extra/youtube'):
            relpath = os.path.relpath(path,start.encode('utf-8'))
            if not b'..' in relpath: break
        else: raise ImportError("Can't import path "+path)
        name = os.path.basename(relpath)
        relpath = relpath.decode('utf-8')
        name = name.decode('utf-8')
    else:
        print('nob')
        relpath = name = path.decode('utf-8')

    officialTags = False
    if ' - ' in name:
        tags,rest = name.split(' - ',1)
        if not '-' in tags:
            print('found official tags header',tags)
            print(rest)
            officialTags = True
            discovered = set(tag.strip() for tag in tags.split(','))
            name = rest
            
    discovered = discovered.union(mysplit(relpath[:relpath.rfind('.')].lower(),'/ .-_*"\'?()[]{},'))
    discovered = set([comp for comp in discovered if len(comp)>2 and comp not in boring])

    return discovered,name

def main():

    cod = codecs.lookup('utf-8')

    try:
        db.execute("CREATE TABLE badfiles (path TEXT PRIMARY KEY)")
    except: pass
    
    skipping = False
    recheck = os.environ.get('recheck')
    for path in sys.stdin:
        path = os.path.abspath(path.strip())
        if skipping: 
            if path == 'path at which to restart changes':
                skipping = False
            continue    
        #bpath,length = cod.encode(path,'surrogateescape')
        #if length!=len(path):
        #    raise Exception("Bad path? ",path[:length],'|',repr(path[length:]))
        #print(implied.union(discovered))
        path = path.encode('utf-8')
        bad = db.execute("SELECT COUNT(path) FROM badfiles WHERE path = $1",(path,))
        if bad[0][0] != 0: continue
        idnum = None
        source = db.execute("SELECT id FROM filesources WHERE path = $1",(path,))
        try:
            with db.transaction():
                if source:
                    if not recheck: #(officialTags or recheck):
                        #print("Not rechecking existing file")
                        continue
                    source = source[0][0]
                    idnum = db.execute("SELECT id,hash FROM media WHERE sources @> ARRAY[$1::int]",(source,))
                    if idnum:
                        idnum,hash = idnum[0]
                else:
                    source = db.execute("INSERT INTO sources DEFAULT VALUES RETURNING id")[0][0]
                    db.execute("INSERT INTO filesources (id,path) VALUES ($1,$2)",(source,path))
                if not idnum:
                    with open(path,'rb') as inp:
                        hash = create.mediaHash(inp)
                    idnum = db.execute("SELECT id FROM media WHERE hash = $1",(hash,))
                    if idnum: idnum = idnum[0][0]
                    print("Hasho",idnum)
                try: discovered,name = discover(path)
                except ImportError: continue
                if idnum:
                    print("Adding saource",idnum,source)
                    create.update(idnum,(create.Source(source),),implied.union(discovered),name)
                else:
                    print("importing",path,discovered)
                    create.internet(create.copyMe(path),path.decode('utf-8'),implied.union(discovered),source,(),name=name)
        except create.NoGood: 
            db.execute("INSERT INTO badfiles (path) VALUES ($1)",(path,))
    
if __name__ == '__main__': main()
