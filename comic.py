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
        medium INTEGER REFERENCES media(id) ON DELETE CASCADE ON UPDATE CASCADE)""",
        "CREATE UNIQUE INDEX unique_pages ON comicPage(comic,which)",
        """CREATE OR REPLACE FUNCTION setcomicpage(_medium integer, _comic integer, _which integer) RETURNS void AS
$$

BEGIN                                                  
     LOOP                                               
         -- first try to update the key 
         UPDATE comicPage set medium = _medium where comic = _comic and which = _which;
         IF found THEN                                  
             RETURN;                                    
         END IF;                                        
         -- not there, so try to insert the key         
         -- if someone else inserts the same key concurrently
         -- we could get a unique-key failure           
         BEGIN                                          
             INSERT INTO comicPage(medium,comic,which) VALUES (_medium,_comic,_which);
             RETURN;                                    
         EXCEPTION WHEN unique_violation THEN           
             -- Do nothing, and loop to try the UPDATE again.
         END;                                           
     END LOOP;                                          
END;
$$ language 'plpgsql'""")

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

def findMediumDerp(comic,which,medium=None):
    rows = c.execute("SELECT medium FROM comicPage WHERE comic = $1 AND which = $2",(comic,which))
    if len(rows)==0:
        if medium:
            c.execute("INSERT INTO comicPage (comic,which,medium) VALUES ($1,$2,$3)",(comic,which,medium))
            c.execute("UPDATE comics SET added = now() WHERE id = $1",(comic,))
        return medium
    return rows[0][0]

def findMedium(comic,which,medium=None):
    if medium:
        return findMediumDerp(comic,which,medium)
    for tries in range(2):
        medium = findMediumDerp(comic,which)
        if medium:
            return medium
        else:
            print('No medium for ',comic,which)
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

