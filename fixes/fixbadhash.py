import db,create,filedb,os


for guy, in db.c.execute("SELECT id FROM media WHERE char_length(hash) = 25"):    
    with open(filedb.mediaPath(guy),'rb') as inp:
        hash = create.mediaHash(inp)
    print("fixing short hash for ",guy)
    conflict = db.c.execute("SELECT id FROM media WHERE hash = $1",(hash,))
    if conflict:
        conflict = conflict[0][0]
    with db.transaction():
        if conflict:
            if guy > conflict: # not bloody likely
                temp = conflict
                conflict = guy
                guy = temp
            db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(neighbors) from things where id = $2) where id = $1",(guy,conflict))
            db.c.execute("UPDATE media SET sources = array(SELECT unnest(sources) UNION SELECT unnest(sources) from media WHERE id = $2) WHERE id = $1",(guy,conflict))
            db.c.execute("UPDATE media SET created = LEAST(media.created,media2.created) FROM media AS media2 where media.id = $1 and media2.id = $2",(guy,conflict))
            # shouldn't be anything else to merge...?
            db.c.execute("DELETE FROM media WHERE id = $1",(conflict,))
        db.c.execute("UPDATE media SET hash = $1 WHERE id = $2",
                (hash,guy))
    if conflict:
        try: 
            os.unlink(filedb.mediaPath(conflict))
        except OSError: pass
        try: 
            os.unlink(os.path.join(filedb.base,'thumb','{:x}'.format(conflict)))
        except OSError: pass
        try: 
            os.unlink(os.path.join(filedb.base,'resized','{:x}'.format(conflict)))
        except OSError: pass
