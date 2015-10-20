from orm import Select,InnerJoin,AND,OR,With,EQ,NOT,Intersects,array,IN,Limit,Order,AS
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

class argbuilder:
    n = 0
    def __init__(self):
        self.args = []
        self.names = {}
    def __call__(self,arg,name=None):
        if name is not None:
            if name in self.names:
                return self.names[name]
        num = '$'+str(self.n)
        self.n += 1			
        self.args.append(arg)
        if name is not None:
            self.names[name] = num
        return num

def tagStatement(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    From = InnerJoin('media','things',EQ('things.id','media.id'))
    negaWanted = Select('id','unwanted')
    negaClause = NOT(Intersects('neighbors',array(negaWanted)))
    if tags.posi or not tags.nega:
        # if any positive tags, or no positive but also no negative, this good
        if tags.posi:
            where = Select('EVERY(neighbors && wanted.tags)','wanted')
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
                    arg(offset),arg(limit))
    if wantRelated:
        mainOrdered = EQ('things.id',ANY(mainOrdered))
        if tags.posi:
            mainOrdered = And(
                NOT(EQ('tags.id',ANY(
                        Type(next(arg),'bigint[]')))),
                mainOrdered)
            
        tagStuff = Select(
            ['tags.id','first(tags.name) as name'],
            InnerJoin('tags','things',
                      EQ('tags.id','ANY(things.neighbors)')()),
            mainOrdered)
        stmt = Select(['derp.id','derp.name'],
                      AS(
                          Limit(Group(tagStuff,'tags.id'),
                                Type(arg(taglimit),'int')),
                          'derp'))
        stmt = Order(stmt,'derp.name')
    else:
        mainCriteria.what = [
            'media.id',
            'media.name',
            'media.type',
            array(Select('tags.name',
                         InnerJoin('tags',AS(Select('unnest(neighbors)'),'neigh'),
                                   EQ('neigh.unnest','tags.id'))))
            ]
        stmt = mainOrdered

    if tags.posi or tags.nega:
        if tags.posi:
            tags.posi = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.posi]
        if tags.nega:
            tags.nega = [getTag(tag) if isinstance(tag,str) else tag for tag in tags.nega]

        # we're gonna need a with statement...
        notWanted = Intersect('things.neighbors',Type(arg(tags.nega,'nega'),'bigint[]'))
        if tags.posi:
            # make sure positive tags don't override negative ones
            notWanted = AND(notWanted,
                            NOT(EQ('things.id',ANY(arg(tags.posi,'posi')))))
        stmt = With(stmt,
                    wanted=('tags',Select(array(
                        Select('implications(unnest)',
                               Func('unnest',arg(tags.posi,'posi')))))),
                    unwanted=(
                        'id',
                        Union(Select('tags.id',
                                     InnerJoin('tags','things',
                                               EQ('tags.id','things.id')),
                                     notWanted),
                              Select('id',AS(
                                  Func('unnest',arg(tags.nega,'nega'),'id'))))))
                                                    
    return stmt,arg.args

def searchForTags(tags,offset=0,limit=0x30,taglimit=0x10,wantRelated=False):
    stmt,args = tagStatement(tags,offset,limit,taglimit,wantRelated)
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
    bags = tags.parse("apple, smile, -evil")
    print(tagStatement(bags))
    for tag in searchForTags(bags):
        print(tag)
        
if __name__ == '__main__':
    test()
