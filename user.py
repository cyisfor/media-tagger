from contextlib import contextmanager
from functools import reduce

import versions,db
import context

v = versions.Versioner('user')

class VersionHolder:
    @v(version=1)
    def initially():
        db.setup("CREATE TABLE uzer (id SERIAL PRIMARY KEY, ident TEXT UNIQUE, rescaleImages boolean DEFAULT TRUE, noDefaultTags boolean DEFAULT FALSE)")
    @v(version=2)
    def impliedList():
        db.setup("CREATE TABLE uzerTags (id bigint REFERENCES tags(id),uzer INTEGER REFERENCES uzer(id), nega BOOLEAN DEFAULT FALSE)");

v.setup()

def currentUser():
    return User

class User(context.Context):
    ident = None
    def tags(self,nega=False):
        for row in db.c.execute("SELECT id FROM uzertags WHERE uzer = $1 AND nega = $2",(self.id,nega)):
            yield row[0]
    def __str__(self):
        return self.ident
    def __repr__(self):
        return '<user '+self.ident+'>'

@contextmanager
def being(ident):
    for go in range(2):
        result = db.c.execute("SELECT id,rescaleImages,noDefaultTags FROM uzer WHERE ident = $1",(ident,))
        if result:
            with User.new():
                User.ident = ident
                User.rescaleImages = result[1] == 't'
                User.noDefaultTags = result[2] == 't'
                yield User
                return
        db.c.execute("INSERT INTO uzer (ident) VALUES ($1)",(ident,))
    raise RuntimeError("Something's inserting the same user weirdly so the database is failing to get it at any time!")

def set(news):
    news = tuple(news)
    names = tuple(new[0] for new in news)
    values = tuple(new[1] for new in news)
    names = tuple("{} = ${}".format(name,i+1) for i,name in enumerate(names))
    stmt = "UPDATE uzer SET "+", ".join(names) + " WHERE id = ${}".format(len(names)+1)
    db.c.execute(stmt,values+(User.get('id'),))
