import sys,sqlite3
import db # postgresql
from contextlib import contextmanager

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
         'thumbnailed', 'sources', 'modified', 'phashfail', 'phash')

def setup():
    with open('schema.sql',encoding='utf-8') as inp:
        with cursor() as c:
            try: c.executescript(inp.read())
            except sqlite3.OperationalError: pass

with derp, cursor() as c:
    for row in db.execute('SELECT '+','.join(media)+' FROM media ORDER BY id DESC LIMIT $1',(50,)):
        medium = row[0]
        print('medium',medium)
        c.execute('INSERT INTO media ('+','.join(media)+') VALUES ('+','.join('?' for v in media)')',row)
        neighb = db.execute('SELECT id,name FROM tags WHERE id IN(SELECT unnest(neighbors) FROM things WHERE id = $1)',(medium,))
        for tag,name in neighb:
            print('  tag',name)
            if not hash(name) in tags:
                c.execute('INSERT INTO tags (id,name) VALUES (?,?)',(tag,name))
                tags.add(hash(name))
            c.execute('INSERT INTO media_tags (medium,tag) VALUES (?,?)',
                      (medium,tag))
