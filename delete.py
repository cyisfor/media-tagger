import db,sys,os
import filedb
import clipboardy

db.setup('''CREATE TABLE blacklist(
        id SERIAL PRIMARY KEY,
        hash character varying(28) UNIQUE,
        reason TEXT)''',
        '''CREATE TABLE dupes(
        id SERIAL PRIMARY KEY,
        medium bigint REFERENCES media(id),
        hash character varying(28) UNIQUE,
        inferior BOOLEAN DEFAULT FALSE,
        UNIQUE(medium,hash))''',
        '''CREATE TABLE tobedeleted (
        good bigint REFERENCES media(id),
        bad bigint REFERENCES media(id) NOT NULL,
        reason text,
        inferior boolean)''')

def start(s):
    sys.stdout.write(s+'...')
    sys.stdout.flush()

def done(s=None):
    if s is None: s = 'done.'
    print(s)


def realdelete(good,bad,reason,inferior):
    with db.transaction():
        # the old LEFT OUTER JOIN trick to skip duplicate rows
        if good:
            # XXX: this is bad and I feel bad...
            db.c.execute("INSERT INTO dupes (medium,hash,inferior) SELECT $1,media.hash,$3 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(good, bad, inferior))
        else:
            db.c.execute("INSERT INTO blacklist (hash,reason) SELECT media.hash,$1 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(reason,bad))
        start("tediously clearing neighbors")
        db.c.execute("UPDATE bads SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(bad,))
        done()
        db.c.execute("DELETE FROM sources USING media WHERE media.id = $1 AND sources.id = ANY(media.sources)",(bad,))
        db.c.execute('DELETE FROM tobedeleted WHERE bad = $1',(bad,))
        db.c.execute("DELETE FROM bads WHERE id = $1",(bad,))
        for category in ('image','thumb','resized'):
            doomed=os.path.join(filedb.top,category,'{:x}'.format(bad))
            # if we crash here, transaction will abort and the image will be un-deleted
            # but will get deleted next time so that the files are cleaned up
            if os.path.exists(doomed):
                os.unlink(doomed)

def dupe(good, bad, inferior=True):
    db.c.execute('INSERT INTO tobedeleted (good,bad,inferior) VALUES ($1,$2,$3)',(good, bad, inferior))

def delete(thing, reason=None):
    print("deleting {:x}".format(thing),reason)
    db.c.execute('INSERT INTO tobedeleted (bad,reason) VALUES ($1,$2)',(thing,reason))

def commit():
    for good, bad, reason, inferior in db.c.execute('SELECT good,bad,reason,inferior FROM tobedeleted'):
        realdelete(good,bad,reason,inferior)

def findId(uri):
    uri = uri.rstrip("\n/")
    uri = uri.rsplit('/')[-1].rstrip()
    return int(uri,0x10)

if __name__ == '__main__':
    if len(sys.argv)==3:
        delete(findId(sys.argv[1]),sys.argv[2])
    elif os.environ.get('stdin'):
        reason = sys.stdin.readline()
        for line in sys.stdin:
            delete(findId(line),reason)
    else:
        reason = os.environ['reason']
        def gotPiece(piece):
            try:
                delete(findId(piece),reason)
            except ValueError: pass
        try: clipboardy.run(gotPiece)
        except KeyboardInterrupt: pass
    commit()
