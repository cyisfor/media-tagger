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

tagQ = 'SELECT tags.id FROM tags INNER JOIN things ON things.neighbors @> ARRAY[tags.id] WHERE things.id = media.id'

def explain(s):
    print(db.execute('EXPLAIN '+s))
    raise SystemExit

def domedia(c,off):
    i = 0
    for row in db.execute(explain('SELECT '+','.join(media)+',array('+tagQ+') FROM media ORDER BY id DESC LIMIT $1 OFFSET $2'),(5000,off*5000)):
        if (i+1)%1000==0:
            derp.commit()
        medium = row[0]
        tags = row.pop(-1)
        print('medium',medium,len(tags))
        c.execute('SELECT id FROM media WHERE id = ?',(medium,))
        if c.fetchone(): continue
        i = i + 1
        c.execute('INSERT INTO media ('+','.join(media)+') VALUES ('+','.join('?' for v in media)+')',row)
        for tag in tags:
            c.execute('SELECT id FROM tags WHERE id = ?',(tag,))
            if not c.fetchone():
                name = db.execute('SELECT name FROM tags WHERE id = $1',(tag,))[0][0]
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
        domedia(c,off)
        
