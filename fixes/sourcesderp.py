# ugh... so many dead links, thanks a lot postgresql arrays
import note
import db,os,time
from favorites.parseBase import parse,ParseError,normalize
from favorites import parsers # meh, this is a bad code
from impmort import impmort
import urllib.error
import http.client

def setup():
    # some sources have no media... good sources have it
    if not db.tableExists('goodsources'):
        db.execute('''CREATE TABLE goodsources AS SELECT distinct unnest(sources) as id FROM media INTERSECT SELECT DISTINCT id FROM sources''')
    # some media have nonexistent sources...
    if not db.tableExists('badsources'):
        db.execute('''CREATE TABLE badsources AS SELECT distinct unnest(sources) as id FROM media EXCEPT SELECT DISTINCT id FROM goodsources''')
    db.execute('''CREATE TABLE IF NOT EXISTS sourceProblems (id INTEGER PRIMARY KEY REFERENCES sources(id), problem TEXT)''')

def recalculate():
    note.red('calibrating')
    db.execute('DROP TABLE goodsources')
    setup()
    
    
def main():
    recalculate()
    setup()
    note.magenta('got em yay')

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
    note.blue(stmt)

    def problem(ident,s):
        note.alarm('+++',ident,s)
        if ident is None: return
        db.execute('INSERT INTO sourceProblems (id,problem) VALUES ($1,$2)',
                   (ident,s))
    
    for id,path,uri in db.execute(stmt):
        print('---------------')
        note.blue(id)
        note.blue(path,uri)
        time.sleep(1)#input()
        if path and os.path.exists(path):
            note.green('found path',path)
            impmort(path,{'laptop','special:recovery'})
        elif uri:
            if uri.startswith('file://'):
                path = uri[len('file://'):]
                note.green('uri path',path)
                if os.path.exists(path):
                    impmort(path,{'laptop','special:recovery'})
                else:
                    id = problem(id,'bad file: uri')
            else:
                note.green('uri',uri)
                try:
                    norm = normalize(uri)
                    if uri != norm:
                        id = problem(id,'denormalized uri: {}'.format(norm))
                        newid = db.execute('SELECT id FROM urisources where uri = $1',(norm,))
                        if newid:
                            id = newid[0][0]
                        else:
                            id = None							
                    parse(norm)
                except ParseError as e:
                    id = problem(id,str(e))
                except urllib.error.HTTPError as e:
                    id = problem(id,str(e))
                except http.client.RemoteDisconnected as e:
                    id = problem(id,str(e))
        elif path:
            id = problem(id,'bad path')
        else:
            id = problem(id,'no path, and a bad uri')
if __name__ == '__main__':
    main()
