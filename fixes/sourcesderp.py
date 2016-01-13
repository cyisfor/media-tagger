# ugh... so many dead links, thanks a lot postgresql arrays
import db,os
from favorites.parseBase import parse,ParseError
from favorites import parsers # meh, this is a bad code
from impmort import impmort
import urllib.error

def setup():
    # some sources have no media... good sources have it
    if not db.tableExists('goodsources'):
        db.execute('''CREATE TABLE goodsources AS SELECT distinct unnest(sources) as id FROM media INTERSECT SELECT DISTINCT id FROM sources''')
    # some media have nonexistent sources...
    if not db.tableExists('badsources'):
        db.execute('''CREATE TABLE badsources AS SELECT distinct unnest(sources) as id FROM media EXCEPT SELECT DISTINCT id FROM goodsources''')
    db.execute('''CREATE TABLE IF NOT EXISTS sourceProblems (id INTEGER PRIMARY KEY REFERENCES sources(id), problem TEXT)''')

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
                       OuterJoin(
                           OuterJoin('sources',
                                     'goodsources',
                                     'sources.id = goodsources.id'),
                           'sourceProblems',
                           'sources.id = sourceProblems.id'),
                       'goodsources.id IS NULL AND sourceProblems.id IS NULL')))

    stmt = stmt.sql()
    print(stmt)

    def problem(ident,s):
        db.execute('INSERT INTO sourceProblems (id,problem) VALUES ($1,$2)',
                   (ident,s))
    
    for id,path,uri in db.execute(stmt):
        print('---------------')
        print(hex(id))
        print(path,uri)
        input()
        if path and os.path.exists(path):
            print('found path',path)
            impmort(path,{'laptop','special:recovery'})
        elif uri:
            if uri.startswith('file://'):
                path = uri[len('file://'):]
                print('uri path',path)
                if os.path.exists(path):
                    impmort(path,{'laptop','special:recovery'})
                else:
                    problem(id,'bad file: uri')
            else:
                print('uri',uri)
                try:
                    parse(uri)
                except ParseError as e:
                    problem(id,str(e))
                except urllib.error.HTTPError as e:
                    problem(id,str(e))
        elif path:
            problem(id,'bad path')
        else:
            problem(id,'no path, and a bad uri')
if __name__ == '__main__':
    main()
