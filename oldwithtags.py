import db												# 
from versions import Versioner
import resultCache
from itertools import count
from tags import Taglist

import os

explain = False

stmts = {}
import sqlparse
sqlparse.debugging = True
stmts = db.source('sql/withtags.sql')
db.setup(*db.source('sql/connect.sql',False))

def derp():
    print('-'*60)
    for stmt in stmts.items():
        print(stmt)
        print('-'*60)
    raise SystemExit
#derp()

v = Versioner('tag')
@v(1)
def setup():
    db.execute(stmts['complextagalter'])
    db.execute(stmts['complextagindex'])
db.execute(stmts['implications'])
class scalartuple(tuple):
    def __add__(self,other):
        if not isinstance(other,tuple):
            other = (other,)
        return scalartuple(super(scalartuple,self).__add__(other))

def nonumbers(f):
    def filter(tags):
        for id,tag in tags:
            if isinstance(tag,'str'):
                yield tag
            else:
                db.execute("DELETE FROM tags WHERE id = $1",(id,))
    def wrapper(*k,**a):
        return filter(f(*k,**a))
    return wrapper

def tagStatement(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    stmt = scalartuple()
    args = {}
    if tags.posi or tags.nega:
        stmt += "WITH "
        if tags.posi:
            stmt += stmts['wanted']
        if tags.nega:
            if tags.posi:
                stmt += ','
                notWanted = stmts['notWanted']
            else:
                notWanted = ''
            stmt += stmts['unwanted'] % {'notWanted': notWanted}
        if tags.posi:
            tags.posi = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]
        if tags.nega:
            tags.nega = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.nega]
    pc = stmts['positiveClause']
    if tags.posi:
        pc += ' ' + stmts['positiveWhere']
    if tags.nega:
        if tags.posi:
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
        targs = {'relatedNoTags': ((stmts['relatedNoTags'] % {'tags': tags.posi}) if tags.posi else '')}
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
    if tags.posi or tags.nega:
        if tags.posi:
            args['tags'] = tags.posi
        if tags.nega:
            args['negatags'] = tags.nega
    return stmt

def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    stmt = tagStatement(tags,offset,limit,taglimit,wantRelated)
    if explain:
        print(stmt)
        print(args)
        stmt = "EXPLAIN ANALYZE "+stmt		
    for row in resultCache.encache(stmt,args,not explain):
        if explain:
            print(row[0])
        else:
            if wantRelated:
                id,tag = row
                if isinstance(tag,str):
                    yield tag
                else:
                    db.execute("DELETE FROM tags WHERE id = $1",(id,))
            else:
                yield row
    if explain:
        raise SystemExit


def test():
    import tags
    herp = tags.parse("apple, smile, -evil")
    print(tagStatement(herp))
    print(tagStatement(herp,wantRelated=True))
    return
    for tag in searchForTags(herp):
        print(tag)
        
if __name__ == '__main__':
    test()
