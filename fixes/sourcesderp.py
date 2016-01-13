# ugh... so many dead links, thanks a lot postgresql arrays
import db,os
from favorites.parseBase import parse
from impmort import impmort

def setup():
    # some sources have no media... good sources have it
    db.execute('''CREATE TABLE goodsources AS SELECT distinct unnest(sources) as id FROM media INTERSECT SELECT DISTINCT id FROM sources''')
    # some media have nonexistent sources...
    db.execute('''CREATE TABLE badsources AS SELECT distinct unnest(sources) as id FROM media EXCEPT SELECT DISTINCT id FROM goodsources''')
with db.transaction():
    setup()
    print('got em yay')

    from orm import Select,With,AS,Limit,OuterJoin

    stmt = Select('filesources.id,filesources.path,urisources.uri',
                  # wow, a genuine full join
                  'filesources,urisources',
                  '''filesources.id in (select id from thingy) 
                  or urisources.id in (select id from thingy)''')
    stmt = Limit(stmt,limit=10)

    stmt = With(
        stmt,
        thingy=((),
                Select('sources.id',
                       OuterJoin('sources',
                                 'goodsources',
                                 'sources.id = goodsources.id'),
                       'goodsources.id IS NULL')))

    stmt = stmt.sql()
    print(stmt)

    for id,path,uri in db.execute(stmt):
        if path and os.path.exists(path):
            print('found path',path)
            impmort(path)
        elif uri:
            print('uri',uri)
            parse(uri)
        else:
            print('bad source',id,path,uri)
            raise RuntimeError()
