from orm import Select,InnerJoin,AND,OR,With,EQ,NOT,Intersects,array,IN,Limit,Order,AS,Type,ANY,Func,Union,EVERY,GroupBy,argbuilder,Group
#ehhh
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

tagsWhat = [
            'media.id',
            'media.name',
            'media.type',
            array(Select('tags.name',
                         InnerJoin('tags',AS(Select('unnest(neighbors)'),'neigh'),
                                   EQ('neigh.unnest','tags.id'))))
            ]


def tagStatement(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    From = InnerJoin('media','things',EQ('things.id','media.id'))
    negaWanted = Select('id','unwanted')
    negaClause = NOT(Intersects('neighbors',array(negaWanted)))
    if not (tags.posi or tags.nega):
        where = None
    elif tags.posi:
        where = Group(Select(EVERY(Intersects('neighbors','wanted.tags')),'wanted'))
        if tags.nega:
            negaWanted.where = NOT(IN('id',Select('unnest(tags)','wanted')))
            where = AND(where,negaClause)
    elif tags.nega:
        # only negative tags
        negaWanted.where = None
        where = negaClause

    arg = argbuilder()

    mainCriteria = Select('things.id',From,where)
    mainOrdered = Limit(Order(mainCriteria,
                          'media.added DESC'),
                    (arg(offset) if offset else False),arg(limit))

    if tags.posi:
        posi = Type(arg([getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]),'bigint[]')


    if wantRelated:
        mainOrdered = EQ('things.id',ANY(mainOrdered))
        if tags.posi:
            mainOrdered = AND(
                            NOT(EQ('tags.id',ANY(posi))),
                mainOrdered)

        tagStuff = Select(
            ['tags.id','first(tags.name) as name'],
            InnerJoin('tags','things',
                      EQ('tags.id','ANY(things.neighbors)')),
            mainOrdered)
        stmt = Select(['derp.id','derp.name'],
                      AS(
                          Limit(GroupBy(tagStuff,'tags.id'),
                                limit=arg(taglimit)),
                          'derp'))

        stmt = Order(stmt,'derp.name')
    else:
        mainCriteria.what = tagsWhat
        stmt = mainOrdered

    # we MIGHT need a with statement...
    clauses = {}

    if tags.nega:
        nega = Type(arg([getTag(tag) if isinstance(tag,str) else tag for tag in tags.nega]),'bigint[]')
        notWanted = Intersects('things.neighbors',nega)
        if tags.posi:
            notWanted = AND(notWanted,
                            NOT(EQ('things.id',ANY(posi))))
        herp = AS(Func('unnest',nega),'id')

        clauses['unwanted'] = (
            'id',
            Union(Select('tags.id',
                         InnerJoin('tags','things',
                                   EQ('tags.id','things.id')),
                                     notWanted),
                  Select('id',herp)))
    else:
        notWanted = None

    if tags.posi:
        # make sure positive tags don't override negative ones
        noOverride = NOT(EQ('things.id',ANY(posi)))
        notWanted = AND(notWanted,noOverride) if notWanted else noOverride

        clauses['wanted'] = ('tags',Select(array(Select('implications(unnest)')),
                                           Func('unnest',posi)))
                                                 


    if clauses:
        stmt = With(stmt,**clauses)

    return stmt,arg

def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    stmt,args = tagStatement(tags,offset,limit,taglimit,wantRelated)
    stmt = stmt.sql()
    args = args.args
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
    try:
        import tags
        from pprint import pprint
        bags = tags.parse("apple, smile, -evil")
        stmt,args = tagStatement(bags)
        print(stmt.sql())
        print(args)
        for tag in searchForTags(bags):
            print(tag)
    except db.ProgrammingError as e:
        print(e.info['message'].decode('utf-8'))

if __name__ == '__main__':
    test()
