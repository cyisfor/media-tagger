import sys,sqlite3
import db # postgresql
from contextlib import contextmanager
from itertools import count
derp = sqlite3.connect("pics.sqlite")
derp.execute('PRAGMA foreign_keys = ON')

@contextmanager
def cursor():
    try:
        c = derp.cursor()
        yield c
    except:
        derp.rollback()
        raise
    finally:
        if c:
            c.close()	
    derp.commit()

media = ('id','name',
         'hash', 'created', 'added', 'size', 'type', 'md5',
         'thumbnailed', 'modified', 'phashfail', 'phash')

def setup():
    with open('schema.sql',encoding='utf-8') as inp:
        with cursor() as c:
            try: c.executescript(inp.read())
            except sqlite3.OperationalError: pass
setup()

tagQ = '(SELECT neighbors from things WHERE things.id = media.id)'

def explain(s):
    print(db.execute('EXPLAIN '+s))
    raise SystemExit

def domedia(c,off):
    i = 0
    for row in db.execute('SELECT '+','.join(media)+',sources,'+tagQ+' FROM media ORDER BY id DESC LIMIT $1 OFFSET $2',(5000,off*5000)):
        if (i+1)%1000==0:
            print('commit')
            derp.commit()
        medium = row[0]
        tags = row.pop(-1)
        sources = row.pop(-1)
        #print('medium',hex(medium),len(tags) if tags else None)
        c.execute('SELECT id FROM media WHERE id = ?',(medium,))
        if c.fetchone(): continue
        i = i + 1
        c.execute('INSERT INTO media ('+','.join(media)+') VALUES ('+','.join('?' for v in media)+')',row)
        if sources:
            for source in sources:
                c.execute('SELECT id FROM sources WHERE id = ?',(source,))
                if not c.fetchone():
                    uri = db.execute('SELECT uri FROM urisources WHERE id = $1',(source,))
                    if uri:
                        uri = uri[0][0]
                        c.execute('INSERT INTO sources (medium,schema,uri) VALUES (?,?,?)',
                                  (medium,1 if uri.startswith('https:') else 0, uri))
        if not tags: continue
        for tag in tags:
            c.execute('SELECT id FROM tags WHERE id = ?',(tag,))
            if not c.fetchone():
                name = db.execute('SELECT name FROM tags WHERE id = $1',(tag,))
                if not name: continue
                name = name[0][0]
                c.execute('INSERT INTO tags (id,name) VALUES (?,?)',(tag,name))
            c.execute('SELECT id FROM media_tags WHERE medium = ? AND tag = ?',
                      (medium,tag))
            if not c.fetchone():
                c.execute('INSERT INTO media_tags (medium,tag) VALUES (?,?)',
                          (medium,tag))
    if i == 0:
        derp.commit()
        raise SystemExit
    
with derp, cursor() as c:
    for off in count(0):
        print('page',off)
        domedia(c,off)
        
