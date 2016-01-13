# ugh... so many dead links, thanks a lot postgresql arrays
import db,os
from favorites.parseBase import parse,ParseError
from favorites import parsers # meh, this is a bad code
from impmort import impmort
import urllib.error

def setup():
    # some sources have no media... good sources have it
    db.execute('''CREATE TEMPORARY TABLE goodsources AS SELECT distinct unnest(sources) as id FROM media INTERSECT SELECT DISTINCT id FROM sources''')
    # some media have nonexistent sources...
    db.execute('''CREATE TEMPORARY TABLE badsources AS SELECT distinct unnest(sources) as id FROM media EXCEPT SELECT DISTINCT id FROM goodsources''')
    db.execute('''CREATE TABLE sourceProblems (id INTEGER PRIMARY KEY REFERENCES sources(id), problem TEXT)''')

def main():
    setup()
    print('got em yay')

    from orm import Select,With,AS,Limit,OuterJoin

    stmt = Select('id,(select path from filesources where id = thingy.id),(select uri from urisources where id=thingy.id) from thingy')
    #stmt = Limit(stmt,limit=10)

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
        print('---------------')
        print(id,path,uri)
        if path and os.path.exists(path):
            print('found path',path)
            impmort(path,{'laptop'})
        elif uri:
            print('uri',uri)
            try:
                parse(uri)
            except ParseError as e:
                problem(str(e))
            except urllib.error.HTTPError as e:
                problem(str(e))
        else:
            problem('bad source {} {}'.format(path,uri))
if __name__ == '__main__':
    main()
