import db,sys,os
import filedb

def delete(thing):
    with db.transaction():
        db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(thing,))
        db.c.execute("DELETE FROM sources USING media WHERE media.id = $1 AND sources.id = ANY(media.sources)",(thing,))
        db.c.execute("DELETE FROM things WHERE id = $1",(thing,))
        for category in ('image','thumb','resized'):
            doomed=os.path.join(filedb.top,'category','{:x}'.format(thing))
            if os.path.exists(doomed):
                os.unlink(doomed)

if len(sys.argv)==2:
    delete(int(sys.argv[1],0x10))
else:
    for line in sys.stdin:
        delete(int(line.rsplit('/',1)[-1],0x10))
