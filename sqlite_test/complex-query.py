onequery = ('SELECT medium FROM media_tags WHERE tag = (SELECT id FROM tags WHERE name = ?)\n',)

def list(db,posi,nega,limit,offset):
    query = ' INTERSECT '.join(onequery * len(posi))
    if nega:
        query = query + ' EXCEPT '+ ' EXCEPT '.join(onequery * len(nega))
    args = tuple(posi)+tuple(nega)
    query = 'SELECT * FROM media WHERE id IN (' + query + ') ORDER BY added DESC'
    if limit is not None:
        query = query + ' LIMIT ?'
        args += (limit,)
    if offset is not None:
        query = query + ' OFFSET ?'
        args += (offset,)
    try:
        return db.execute(query,args)
    except sqlite3.OperationalError as e:
        print(query)
        print('\n'.join(str(s) for s in args))
        print('-'*100)
        print(e.args)
        #print('\n'.join(dir(e)))
        raise



import sqlite3,time
from contextlib import closing

conn = sqlite3.connect("pics.sqlite")


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory
start =time.time()

with closing(conn.cursor()) as db:
    for row in list(db,{"general:derpibooru","general:sweetie belle"},{"general:apple bloom","general:rarity"},10,20):
        print('\n'.join(repr(i) for i in row.items()))

print('took',time.time()-start,'seconds')
