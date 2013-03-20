import db

def page(id):
    return db.c.execute("SELECT images.id,name,type,images.width,array(select name from tags where id = ANY(things.neighbors) ORDER BY name) FROM images INNER JOIN media ON images.id = media.id INNER JOIN things ON images.id = things.id WHERE images.id = $1",(id,))[0]

def info(id):
    result = db.c.execute("SELECT media.id,name,type,array(SELECT uri FROM urisources WHERE id = ANY(sources)) AS sources,images.width,images.height,size,hash,created,added FROM media INNER JOIN images ON images.id = media.id WHERE media.id = $1",(id,))
    return dict(zip(result.fields,result[0]))

def like(id):
    return None
