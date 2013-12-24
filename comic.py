from db import c,setup,saved
import db
from redirect import Redirect

from urllib.error import HTTPError as Error
from functools import wraps

setup("""CREATE TABLE comics
    (id INTEGER PRIMARY KEY, 
     title TEXT UNIQUE, 
     description TEXT,
     added TIMESTAMPTZ DEFAULT NOW())""",
    """CREATE TABLE comicPage (id SERIAL PRIMARY KEY, 
        comic INTEGER REFERENCES comics(id) ON DELETE CASCADE ON UPDATE CASCADE,
        which INTEGER,
        image INTEGER REFERENCES images(id) ON DELETE CASCADE ON UPDATE CASCADE)""",
        "CREATE UNIQUE INDEX unique_pages ON comicPage(comic,which)")

def withC(f):
    @wraps(f)
    def wrapper(*a,**kw):
        with saved():
            f(*a,**kw)
    return wrapper

def findComicByTitle(title,getinfo):
    rows = c.execute("SELECT id FROM comics WHERE title = $1",(title,));
    if len(rows) == 0:
        description = getinfo();
        return c.execute("INSERT INTO comics (title,description) VALUES ($1,$2) RETURNING id",
                (title,
                description))[0][0]
    return rows[0][0]

def findInfo(id,getinfo):
    rows = c.execute("SELECT title,description,(SELECT uri FROM urisources WHERE id = comics.source) FROM comics WHERE id = $1",(id,))
    if len(rows) == 0:
        title,description,source = getinfo() # some GUI thing
        c.execute("INSERT INTO comics (id,title,description VALUES ($1,$2,$3) RETURNING id",(id,title,description))
        return title, description,source
    return rows[0]

def findImageDerp(comic,which,image=None):
    rows = c.execute("SELECT image FROM comicPage WHERE comic = $1 AND which = $2",(comic,which))
    if len(rows)==0:
        if image:
            c.execute("INSERT INTO comicPage (comic,which,image) VALUES ($1,$2,$3)",(comic,which,image))
            c.execute("UPDATE comics SET added = now() WHERE id = $1",(comic,))
        return image
    return rows[0][0]

def findImage(comic,which,image=None):
    if image:
        return findImageDerp(comic,which,image)
    for tries in range(2):
        image = findImageDerp(comic,which)
        if image:
            return image
        else:
            print('No image for ',comic,which)
            np = pages(comic)
            if which == 0 and np == 0:
                return 0x5c911
            if which >= np:
                print('wnpt',which,np)
                # XXX: this should be in pages.py
                if which == 0:
                    raise Redirect("../")
                raise Redirect("../0/")
            print("Time to reorder!")
            with db.transaction():
                c.execute("CREATE TEMPORARY TABLE orderincomix AS SELECT id,(row_number() OVER (partition by comic order by which))-1 AS which FROM comicpage")
                c.execute("UPDATE comicpage SET which = orderincomix.which FROM orderincomix WHERE orderincomix.id = comicpage.id")
                c.execute("DROP TABLE orderincomix")
    raise Error("I give up. The comic {:x} is messed up on page {:x}!".format(com,which))

def numComics():
    rows = c.execute("SELECT COUNT(id) FROM comics")
    return rows[0][0]

def pages(comic):
    rows = c.execute("SELECT COUNT(id) FROM comicPage WHERE comic = $1",(comic,))
    return rows[0][0]

def list(page):
    return c.execute("SELECT id,title FROM comics ORDER BY added DESC, id OFFSET $1 LIMIT $2",(page*0x20,0x20))

