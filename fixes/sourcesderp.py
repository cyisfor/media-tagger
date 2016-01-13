# ugh... so many dead links, thanks a lot postgresql arrays
import db

def setup():
    # some sources have no media... good sources have it
    db.execute('''CREATE TABLE IF NOT EXISTS goodsources AS SELECT distinct unnest(sources) FROM media INTERSECT SELECT DISTINCT id FROM sources''')
    # some media have nonexistent sources...
    db.execute('''CREATE TABLE IF NOT EXISTS badsources AS SELECT distinct unnest(sources) FROM media EXCEPT SELECT DISTINCT id FROM goodsources''')
setup()
print('got em yay')

from orm import Select,With,AS,Limit,OuterJoin

derp = Select('*','filesources,urisources',
                    '''filesources.id in (select id from thingy) 
                    or urisources.id in (select id from thingy)''')

derp = Limit(derp,limit=10)


stmt = With(
    derp,
    thingy=((),
            Select('sources.id',OuterJoin('sources','goodsources','sources.id = goodsources.id'),'goodsources.id IS NULL')))

stmt = stmt.sql()
print(stmt)

for row in db.execute(stmt):
    print(row)
