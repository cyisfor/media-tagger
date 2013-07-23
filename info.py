import db

def getID(path):
    if len(path)>1:
        return int(path[1],0x10)
    return None

def page(path,params):
    return db.c.execute("""SELECT
    media.id,
    (SELECT MAX(id) FROM media AS prev WHERE prev.id < media.id),
    (SELECT MIN(id) FROM media AS next WHERE next.id > media.id),
    name,
    type,
    images.width,
    array(select name from tags where id = ANY(things.neighbors) ORDER BY name)
        FROM media
        INNER JOIN things ON media.id = things.id
        LEFT OUTER JOIN images ON images.id = media.id
    WHERE media.id = $1
""",(getID(path),))[0]

def source(sourceID):
    try: return db.c.execute("SELECT uri FROM urisources WHERE id = $1",(sourceID,))[0][0]
    except IndexError: return None

def info(path,params):
    result = db.c.execute("SELECT media.id,name,type,sources,images.width,images.height,size,hash,created,added,md5 FROM media LEFT OUTER JOIN images ON images.id = media.id WHERE media.id = $1",(getID(path),))
    return dict(zip(result.fields,result[0]))

def user(path,params): pass

def like(*a):
    return None

