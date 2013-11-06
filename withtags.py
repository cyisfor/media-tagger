from db import c
from itertools import count

import os

explain = False

stmts = {}

place = os.path.dirname(__file__)

with open(os.path.join(place,"sql/withtags.sql")) as inp:
    mode = 0
    for line in inp:
        line = line.rstrip()
        if mode is 0:
            name = line
            mode = 1
            value = []
        else:
            if line[-1]==';':
                mode = 0
                line = line[:-1]
            value.append(line)
            if mode is 0:
                stmts[name] = "\n".join(value)
                value = None
                name = None


class scalartuple(tuple):
    def __add__(self,other):
        if not isinstance(other,tuple):
            other = (other,)
        return scalartuple(super(scalartuple,self).__add__(other))


def searchForTags(tags=None,negatags=None,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    stmt = scalartuple()
    args = {}
    if tags or negatags:
        stmt += "WITH "
        if tags:
            stmt += stmts['wanted']
        if negatags:
            if tags:
                stmt += ','
                notWanted = stmts['notWanted']
            else:
                notWanted = ''
            stmt += stmts['unwanted'] % {'notWanted': notWanted}
        if tags:
            tags = [getTag(tag) if isinstance(tag,str) else tag for tag in tags]
        if negatags:
            negatags = [getTag(tag) if isinstance(tag,str) else tag for tag in negatags]
    pc = stmts['positiveClause']
    if tags:
        pc += ' ' + stmts['positiveWhere']
    if negatags:
        if tags:
            negativeClause = 'AND '+stmts['negativeClause']
            anyWanted = stmts['anyWanted']
        else:
            negativeClause = 'WHERE '+stmts['negativeClause']
            anyWanted = ''
        negativeClause = negativeClause % {'anyWanted': anyWanted}
    else:
        negativeClause = ''

    if wantRelated:
        template = stmts['related']
        targs = {'relatedNoTags': ((stmts['relatedNoTags'] % {'tags': tags}) if tags else '')}
    else:
        template = stmts['main']
        targs = {}

    targs.update({
            'positiveClause': pc,
            'negativeClause': negativeClause,
            'ordering': stmts['ordering']})
    stmt += template % targs

    stmt = " ".join(stmt)
    args = {'offset': offset,'limit': limit}
    if wantRelated:
        args['taglimit'] = taglimit
    if tags or negatags:
        if tags:
            args['tags'] = tags
        if negatags:
            args['negatags'] = negatags
    if explain:
        stmt = "EXPLAIN ANALYZE "+stmt
    for row in c.execute(stmt,args):
        if explain:
            print(row[0])
        else:
            if wantRelated:
                yield row[0]
            else:
                yield row
    if explain:
        raise SystemExit

def makeTag(name):
    for attempt in range(3):
        result = c.execute("SELECT id FROM tags WHERE name = $1",(name,))
        if result: break
        result = c.execute("WITH thing AS (INSERT INTO things DEFAULT VALUES RETURNING id) INSERT INTO tags (id,name) SELECT thing.id,$1 FROM thing RETURNING id",(name,))
    return result[0][0]

def getTag(name):
    result = c.execute("SELECT id FROM tags WHERE name = $1",(name,))
    if result: return result[0][0]
    return None

def names(tags):
    tags = list(tags)
    if not tags or type(tags[0])==str:
        return set(tags)
    names = set()
    for row in c.execute('SELECT name FROM tags WHERE id = ANY($1)',(tags,)):
        names.add(row[0])
    return names

def connect(a,b):
    c.execute(stmts['connect'],(a,b))

def test():
    for tag in searchForTags():
        print(tag)
#test()

def parse(s):
    tags = set()
    negatags = set()
    for thing in s.split(','):
        thing = thing.strip()
        if thing[0] == '-':
            tags.discard(thing[1:])
            negatags.add(thing[1:])
        else:
            tags.add(thing)
    tags = set(makeTag(tag) for tag in tags)
    negatags = set(makeTag(tag) for tag in negatags)
    tags = tags.difference(negatags)
    negatags = negatags.difference(tags)
    print('wtparse',s,tags,negatags)
    return tags,negatags
