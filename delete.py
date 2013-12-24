import db,sys,os
import filedb
import clipboardy

def delete(thing,reason=None):
    print("deleting",thing,reason)
    with db.transaction():
        db.c.execute("INSERT INTO blacklist (hash,reason) SELECT hash,$1 from media where media.id = $2",(reason,thing))
        db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(thing,))
        db.c.execute("DELETE FROM sources USING media WHERE media.id = $1 AND sources.id = ANY(media.sources)",(thing,))
        db.c.execute("DELETE FROM things WHERE id = $1",(thing,))
        for category in ('image','thumb','resized'):
            doomed=os.path.join(filedb.top,category,'{:x}'.format(thing))
            if os.path.exists(doomed):
                os.unlink(doomed)

print(sys.argv)
if len(sys.argv)==3:
    delete(int(sys.argv[1],0x10),sys.argv[2])
elif os.environ.get('stdin'):
    reason = sys.stdin.readline()
    for line in sys.stdin:
        delete(int(line.rsplit('/',1)[-1],0x10),reason)
else:
    def gotPiece(piece):
        if ' ' in piece:
            piece,reason = piece.split(' ',1)
        else:
            reason = None
        try:
            delete(int(piece.rsplit('/',1)[-1],0x10),reason)
        except ValueError: pass
    clipboardy.run(gotPiece)
