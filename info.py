import db
import comic
from user import User,UserError
from session import Session

db.setup("CREATE TABLE visited (id SERIAL PRIMARY KEY, uzer INTEGER REFERENCES uzers(id), medium bigint REFERENCES media(id), visits INTEGER DEFAULT 0)",
        "create unique index visitorunique on visited(uzer,medium)")

def getID(path):
    if len(path)>1:
        return int(path[1],0x10)
    raise RuntimeError("No ID found in path")

def simple(path,params):
    if Session.head: return
    id = getID(path)
    return id,db.execute("SELECT type FROM media WHERE id = $1",(id,))[0][0]

def oembed(path,params):
    if Session.head: return
    id = getID(path)
    return id,[row[0] for row in db.execute("SELECT tags.name FROM tags, things where tags.id = ANY(things.neighbors) AND things.id = $1 ORDER BY name",(id,))]

def tagsFor(medium):
    return db.execute("""SELECT tags.name FROM tags 
INNER JOIN things ON tags.id = ANY(things.neighbors)
WHERE things.id = $1""",(medium,))

def pageInfo(id):
    info = db.execute("""SELECT
    media.id,
    (SELECT MAX(id) FROM media AS prev WHERE prev.id < media.id),
    (SELECT MIN(id) FROM media AS next WHERE next.id > media.id),
    name,
    type,
    COALESCE(images.width,videos.width),
    COALESCE(images.height,videos.height),
    media.size,
    EXTRACT (epoch FROM media.modified),
    array(SELECT tags.name FROM tags 
        where id = ANY(thing1.neighbors) ORDER BY name),
    comics.id, comics.title,
    CASE WHEN which > 0 THEN (select medium from comicpage AS sub where sub.comic = comics.id and sub.which = comicpage.which - 1) END,
    (select medium from comicpage AS sub where sub.comic = comics.id and sub.which = comicpage.which + 1)

    FROM things as thing1
    INNER JOIN media ON media.id = thing1.id
    LEFT OUTER JOIN comicpage ON medium = media.id
    LEFT OUTER JOIN comics ON comicpage.comic = comics.id 
    LEFT OUTER JOIN images ON images.id = media.id
    LEFT OUTER JOIN videos ON videos.id = media.id

    WHERE media.id = $1
""",(id,))
    db.execute("""WITH upda AS (
        UPDATE visited SET visits = visits + 1 WHERE uzer = $1 AND medium = $2 RETURNING id),
    goodmedium AS ( SELECT id FROM media WHERE id = $2 )
    INSERT INTO visited (uzer,medium,visits) SELECT $1,$2,1 WHERE NOT EXISTS(SELECT id FROM upda) AND EXISTS(SELECT id FROM goodmedium) RETURNING id
    """,(User.id,id))
    if not info:
        raise UserError("Medium {:x} not found.".format(id))
    row = info[0]
    return tuple(row[:-4])+(row[-4:] if row[-4] else None,)

def page(path,params):
    if Session.head:
        return db.execute("SELECT id,EXTRACT(EPOCH FROM modified),size FROM media WHERE id = $1",(getID(path),))[0]
    return pageInfo(getID(path))


def source(sourceID):
    if sourceID is None: return None
    try: return db.execute("SELECT uri FROM urisources WHERE id = $1",(sourceID,))[0][0]
    except IndexError: return None

def random(path,params):
    if Session.head: return
    return db.execute(stmts['main'] % {'positiveClause': stmts['positiveClause'],
        'negativeClause': '',
        'ordering': 'ORDER BY random() LIMIT 48'
        })
    

def info(path,params):
    if Session.head:
        return {'sessmodified': 
                db.execute("SELECT EXTRACT(epoch FROM modified) FROM media WHERE id = $1",(getID(path),))[0][0]}
    result = db.execute("""SELECT 
    media.id,
    name,
    type,
    sources,
    COALESCE(images.width,videos.width) AS width,
    COALESCE(images.height,videos.height) AS height,
    size,
    hash,
    to_hex(phash) AS "perceptual hash",
    created,
    added,
    EXTRACT (epoch FROM modified) AS sessmodified,
    md5,
    array(SELECT tags.name FROM tags 
        where id = ANY(thing1.neighbors) ORDER BY name) AS tags
    FROM things as thing1
    INNER JOIN media ON media.id = thing1.id
    LEFT OUTER JOIN videos ON videos.id = media.id
    LEFT OUTER JOIN images ON images.id = media.id 
    WHERE media.id = $1""",
        (getID(path),))
    return dict(zip(result.fields,result[0]))

def user(path,params): pass
 
def like(*a):
    return None

