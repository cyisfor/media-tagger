from db import cursor, c as conn, plainCursor
import sys
from itertools import count
import time

counter = count(0)

plus = "+"
minus = "-"

wanted = """%(name)s(id,path,depth) AS (
SELECT tags.id,ARRAY[tags.id],1 FROM tags
WHERE tags.id = ANY(%(tags)s::INTEGER[])
UNION ALL
SELECT tags.id,path||tags.id,depth + 1 FROM tags
INNER JOIN %(name)s ON %(name)s.id != tags.id
INNER JOIN things ON things.id = tags.id WHERE
    depth < 2 AND
    NOT ARRAY[things.id] @> %(name)s.path AND
    things.neighbors @> ARRAY[%(name)s.id])"""

thingies = "media.id,media.name,media.type,(select array_agg(tags.name) from tags where tags.id = ANY(things.neighbors))"

finalStatement = "SELECT "+thingies+""" FROM media INNER JOIN things ON media.id = things.id %(maybewhere)sORDER BY added DESC NULLS LAST OFFSET %%(offset)s LIMIT %%(limit)s"""

def searchForTags(tags,negatags=None,offset=0,limit=50):
    tags = [getTag(tag) for tag in tags]
    negatags = [getTag(tag) for tag in negatags]
    if not ( tags or negatags ):
        stmt = finalStatement % {'maybewhere': ''}
    else:
        stmt = "WITH RECURSIVE "
        if tags:
            stmt += wanted%{'name':'wantedtags','tags':'%(tags)s'}
        if tags and negatags:
            stmt += ",\n"
        if negatags:
            stmt += wanted%{'name':'unwantedtags','tags':'%(negatags)s'}
        stmt += ",\n"
        stmt += "targetmedia(id) AS (\n"
        if tags:
            # XXX: this is wrong! should be neighbors && tags connected to wantedtag1 and neighbors && tagsl connected to wantedtag2 and etc...
            stmt += """SELECT media.id FROM media INNER JOIN things ON things.id = media.id WHERE things.neighbors && array(SELECT id FROM wantedtags) AND
   (things.neighbors @> %(tags)s::INTEGER[])"""
            if negatags:
                stmt += """AND NOT
    (things.neighbors && %(negatags)s::INTEGER[])"""
        else:
            stmt += """SELECT media.id FROM media INNER JOIN things ON things.id = media.id WHERE NOT things.neighbors && array(SELECT id FROM unwantedtags)
"""
        stmt += finalStatement % {'maybewhere': "WHERE media.id = ANY(array(select id from targetmedia))"}
        stmt = "EXPLAIN ANALYZE "+stmt
        args = {'tags': tags,'negatags': negatags,
                'offset': offset,
                'limit': limit}
    with cursor() as c:
        print(stmt)
        sys.stdout.flush()
        print(c.mogrify(stmt,args).decode('utf-8'))
        c.execute(stmt,args)
        for row in c:
            print(row[0])
        raise SystemExit

def getTag(name):
    with plainCursor() as c:
        for attempt in range(3):
            c.execute("SELECT id FROM tags WHERE name = %s",(name,))
            if c.rowcount > 0: break
            c.execute("INSERT INTO tags (name) VALUES %s RETURNING id",(name,))
        return c.fetchone()[0]

def test():
    with cursor() as c:
        searchForTags([getTag('penis'),getTag('female'),getTag('dog')],[getTag('knot')])
