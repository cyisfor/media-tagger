import psycopg2
import sys
from itertools import count
from contextlib import contextmanager
from progressbar import ProgressBar

counter = count(0)

@contextmanager
def derp(makeCursor):
    cursor = None
    try:
        cursor = makeCursor()
        yield cursor
    finally:
        if cursor is not None:
            cursor.close()


with open("passwd") as inp:
    password = inp.read()

semantics = psycopg2.connect("dbname=derp user=ion port=5433 password="+password)

plus = "INTERSECT"
minus = "EXCEPT"

def makeCriteria(tags):
    tags.sort(key=lambda tag: tag[0] is plus)
    if tags[0][0] is plus:
        hasPositive = True
    else:
        hasPositive = False
    if hasPositive:
        first = True
    else:
        yield "SELECT blue FROM connections"
    for tag in tags:
        if hasPositive and first:
            first = False
        else:
            yield tag[0]
        yield "SELECT blue FROM connections where red = %s"

with open("withtags.sql") as inp:
    withTags = inp.read()

def searchForTags(tags):
    stmt = withTags % {
            'criteria': "\n".join(makeCriteria(tags))
            }
    print(stmt)
    with derp(semantics.cursor) as c:
        for tag in tags:
            c.execute("SELECT id FROM tags WHERE name = %s",(tag[1],))
            tag.append(c.fetchone()[0])
        print(tags)
        c.execute(stmt,tuple(tag[2] for tag in tags))
        for row in c:
            print(row)

plus = "INTERSECT"
minus = "EXCEPT"

#searchForTags(((plus,"ferret"),))
searchForTags(([plus,"female"],[plus,"ferret"]))
#searchForTags(((plus,"ferret"),(plus,"photos"),(minus,"tongue")))

"""XXX:
 with recursive search(blue,path,depth) AS (select blue,ARRAY[red],1 from connections where red = 6 UNION ALL select connections.blue,path || ARRAY[connections.red], depth + 1 from search inner join connections on connections.red = search.blue inner join tags on tags.id = connections.red where depth < 3 and not connections.blue = any(path)), searchimg(id) AS (select blue from search inner join images on search.blue = images.id limit 10) select tags.id,tags.name FROM tags inner join search ON tags.id = search.blue;
"""
