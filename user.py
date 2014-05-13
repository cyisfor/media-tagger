import tags

from contextlib import contextmanager
from functools import reduce

import versions,db
import context

v = versions.Versioner('user')

# defaultTags means when there is no tags for a user, use the default ones as implied tags.
# defaultTags=False means when there are no tags, have no implied tags.

class VersionHolder:
    @v(version=1)
    def initially():
        db.setup("CREATE TABLE uzers (id SERIAL PRIMARY KEY, ident TEXT UNIQUE, rescaleImages boolean DEFAULT TRUE, defaultTags boolean DEFAULT TRUE)")
    @v(version=2)
    def impliedList():
        db.setup("CREATE TABLE uzerTags (id bigint REFERENCES tags(id),uzer INTEGER REFERENCES uzers(id), nega BOOLEAN DEFAULT FALSE)");
    @v(version=3)
    def sameTags():
        "Two users might want to have the same tag, one nega and one posi!"
        db.setup("CREATE TABLE uzerTags2 (id SERIAL PRIMARY KEY, tag bigint REFERENCES tags(id),uzer INTEGER REFERENCES uzers(id), nega BOOLEAN DEFAULT FALSE)",
            "INSERT INTO uzerTags2 (tag,uzer,nega) SELECT id,uzer,nega FROM uzerTags",
            "DROP TABLE uzerTags",
            "ALTER TABLE uzerTags2 RENAME TO uzerTags",
            "CREATE UNIQUE INDEX nodupeuzertags ON uzerTags(tag,uzer)")


v.setup()

def currentUser():
    return User

defaultTags = '-rating:explicit, -gore'
dtags = tags.parse(defaultTags)

@context.Context
class User:
    ident = None
    def tags(self):
        if self.defaultTags:
            return dtags
        result = tags.Taglist()
        for id,nega in db.c.execute("SELECT tag,nega FROM uzertags WHERE uzer = $1",(self.id,)):
            if nega:
                result.nega.add(id)
            else:
                result.posi.add(id)
        return result
    def __str__(self):
        return self.ident
    def __repr__(self):
        return '<user '+self.ident+'>'

@contextmanager
def being(ident):
    for go in range(2):
        result = db.c.execute("SELECT id,rescaleImages,defaultTags FROM uzers WHERE ident = $1",(ident,))
        if result and len(result[0]) == 3:
            result = result[0]
            with User:
                User.ident = ident
                User.id = result[0]
                User.rescaleImages = result[1]
                User.defaultTags = result[2]
                yield User
                return
        db.c.execute("INSERT INTO uzers (ident) VALUES ($1)",(ident,))
    raise RuntimeError("Something's inserting the same user weirdly so the database is failing to get it at any time!")

def set(news):
    news = tuple(news)
    names = tuple(new[0] for new in news)
    values = tuple(new[1] for new in news)
    names = tuple("{} = ${}".format(name,i+1) for i,name in enumerate(names))
    stmt = "UPDATE uzers SET "+", ".join(names) + " WHERE id = ${}".format(len(names)+1)
    with db.transaction():
        db.c.execute(stmt,values+(User.id,))

class UserError(Exception): 
    def __init__(self,message,*args):
        self.message = message
        super().__init__((message,)+args)

