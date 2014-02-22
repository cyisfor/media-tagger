import db
import comic
from user import User,UserError

db.setup("CREATE TABLE visited (id SERIAL PRIMARY KEY, uzer INTEGER REFERENCES uzers(id), medium bigint REFERENCES media(id), visits INTEGER DEFAULT 0)",
        "create unique index visitorunique on visited(uzer,medium)")

def getID(path):
    if len(path)>1:
        return int(path[1],0x10)
    return None

def simple(path,params):
    id = getID(path)
    return id,db.c.execute("SELECT type FROM media WHERE id = $1",(id,))[0][0]

def oembed(path,params):
    id = getID(path)
    return id,[row[0] for row in db.c.execute("SELECT tags.name FROM tags, things where id = ANY(things.neighbors) AND things.id = $1 ORDER BY name",(id,))]

def pageInfo(id):
    info = db.c.execute("""SELECT
    media.id,
    (SELECT MAX(id) FROM media AS prev WHERE prev.id < media.id),
    (SELECT MIN(id) FROM media AS next WHERE next.id > media.id),
    name,
    type,
    images.width,
    media.size,
    EXTRACT (epoch FROM media.modified),
    array(SELECT tags.name FROM tags 
        where id = ANY(thing1.neighbors) ORDER BY name)

    FROM things as thing1
    INNER JOIN media ON media.id = thing1.id
    LEFT OUTER JOIN images ON images.id = media.id

    WHERE media.id = $1
""",(id,))
    db.c.execute("""WITH upda AS (
        UPDATE visited SET visits = visits + 1 WHERE uzer = $1 AND medium = $2 RETURNING id),
    goodmedium AS ( SELECT id FROM media WHERE id = $2 )
    INSERT INTO visited (uzer,medium,visits) SELECT $1,$2,1 WHERE NOT EXISTS(SELECT id FROM upda) AND EXISTS(SELECT id FROM goodmedium) RETURNING id
    """,(User.id,id))
    if not info:
        raise UserError("Image {:x} not found.".format(id))
    return info[0]

def page(path,params):
    return pageInfo(getID(path))


def source(sourceID):
    if sourceID is None: return None
    try: return db.c.execute("SELECT uri FROM urisources WHERE id = $1",(sourceID,))[0][0]
    except IndexError: return None

def info(path,params):
    result = db.c.execute("""SELECT 
    media.id,
    name,
    type,
    sources,
    images.
    width,
    images.height,
    size,
    hash,
    created,
    added,
    EXTRACT (epoch FROM modified) AS sessmodified,
    md5 FROM media 
    LEFT OUTER JOIN images ON images.id = media.id WHERE media.id = $1""",
        (getID(path),))
    return dict(zip(result.fields,result[0]))

def user(path,params): pass

def comicInfoer(path,params):
    if len(path) == 1:
        def pages(offset):
            return comic.list(offset)
        return pages
    elif len(path) == 2:
        def pages(offset):
            return comic.pages(int(path[1]),offset)
        return pages
    elif len(path) > 2:
        return comic.findImage(int(path[1]),int(path[2]))

def like(*a):
    return None

