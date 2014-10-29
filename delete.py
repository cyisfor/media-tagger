import db,sys,os
import filedb
import clipboardy

def start(s):
    sys.stdout.write(s+'...')
    sys.stdout.flush()

def done(s=None):
    if s is None: s = 'done.'
    print(s)

def delete(thing,reason=None):
    print("deleting {:x}".format(thing),reason)
    with db.transaction():
        # the old LEFT OUTER JOIN trick to skip dupes
        db.c.execute("INSERT INTO blacklist (hash,reason) SELECT media.hash,$1 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(reason,thing))
        start("tediously clearing neighbors")
        db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(thing,))
        done()
        db.c.execute("DELETE FROM sources USING media WHERE media.id = $1 AND sources.id = ANY(media.sources)",(thing,))
        db.c.execute("DELETE FROM things WHERE id = $1",(thing,))
        for category in ('image','thumb','resized'):
            doomed=os.path.join(filedb.top,category,'{:x}'.format(thing))
            if os.path.exists(doomed):
                os.unlink(doomed)

def findId(uri):
    uri = uri.rstrip("\n/")
    uri = uri.rsplit('/')[-1].rstrip()
    return int(uri,0x10)

if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv)==3:
        delete(findId(sys.argv[1]),sys.argv[2])
    elif os.environ.get('stdin'):
        reason = sys.stdin.readline()
        for line in sys.stdin:
            print('got',line)
            delete(findId(line),reason)
    else:
        reason = os.environ['reason']
        def gotPiece(piece):
            try:
                delete(findId(piece),reason)
            except ValueError: pass
        clipboardy.run(gotPiece)
