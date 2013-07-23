from contextlib import contextmanager
from functools import reduce

import versions,db
from obj import obj

v = versions.Versioner('user')

class VersionHolder:
    @v(version=1)
    def initially():
        db.setup("CREATE TABLE uzer (id SERIAL PRIMARY KEY, ident TEXT UNIQUE, rescaleImages boolean DEFAULT TRUE)")

v.setup()

userstack = []

def currentUser():
    return userstack[-1]

class User(obj): pass

@contextmanager
def being(ident):
    for go in range(2):
        result = db.c.execute("SELECT id,rescaleImages FROM uzer WHERE ident = $1",(ident,))
        if result:
            user = dict(zip(result.fields,result[0]))
            user['ident'] = ident
            user['rescaleImages'] = user['rescaleimages'] == 't'
            print('userstack',userstack)
            userstack.append(user)
            yield user
            userstack.pop()
            return
        db.c.execute("INSERT INTO uzer (ident) VALUES ($1)",(ident,))
    raise RuntimeError("Something's inserting the same user weirdly so the database is failing to get it at any time!")

def set(news):
    user = currentUser()
    news = tuple(news)
    names = tuple(new[0] for new in news)
    values = tuple(new[1] for new in news)
    names = tuple("SET {} = ${}".format(name,i+1) for i,name in enumerate(names))
    stmt = "UPDATE uzer "+" ".join(names) + " WHERE id = ${}".format(len(names)+1)
    print(stmt,values)
    db.c.execute(stmt,values+(user.get('id'),))
