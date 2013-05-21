import db

def page(id):
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
""",(id,))[0]

def info(id):
    result = db.c.execute("SELECT media.id,name,type,array(SELECT uri FROM urisources WHERE id = ANY(sources)) AS sources,images.width,images.height,size,hash,created,added,md5 FROM media LEFT OUTER JOIN images ON images.id = media.id WHERE media.id = $1",(id,))
    return dict(zip(result.fields,result[0]))

def like(id):
    return None

