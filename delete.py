import db
import filedb

from itertools import count
import sys,os

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
        good bigint REFERENCES media(id) ON DELETE CASCADE,
        bad bigint NOT NULL REFERENCES media(id) ON DELETE CASCADE,
        reason text,
        inferior boolean)''')

def start(s):
    sys.stdout.write(s+'...')
    sys.stdout.flush()

def done(s=None):
    if s is None: s = 'done.'
    print(s)


def dbdelete(good,bad,reason,inferior):
    print("deleting {:x}".format(bad),'dupe' if good else reason)
    # the old LEFT OUTER JOIN trick to skip duplicate rows
    if good:
        # XXX: this is bad and I feel bad...
        db.execute("INSERT INTO dupes (medium,hash,inferior) SELECT $1,media.hash,$3 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(good, bad, inferior))
    else:
        db.execute("INSERT INTO blacklist (hash,reason) SELECT media.hash,$1 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(reason,bad))
    start("tediously clearing neighbors")
    # it's way less lag if we break this hella up
    for id, in db.execute('SELECT id FROM things WHERE neighbors @> ARRAY[$1::bigint]',(bad,)):
        db.execute('UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) WHERE id = $1',(id,))
        sys.stdout.write('.')
        sys.stdout.flush()
    #db.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT $1) where neighbors @> ARRAY[$1]",(bad,))
    done()
    db.execute("DELETE FROM sources USING media WHERE media.id = $1 AND sources.id = ANY(media.sources)",(bad,))
    db.execute('DELETE FROM tobedeleted WHERE bad = $1',(bad,))
    db.execute("DELETE FROM things WHERE id = $1",(bad,))



def dupe(good, bad, inferior=True):
    db.execute('INSERT INTO tobedeleted (good,bad,inferior) VALUES ($1,$2,$3)',(good, bad, inferior))

def delete(thing, reason=None):
    db.execute('INSERT INTO tobedeleted (bad,reason) VALUES ($1,$2)',(thing,reason))



def commit():
    counter = count(1)
    done = False
    while not done:
        with db.transaction():
            bads = []
            done = True
            for good, bad, reason, inferior in db.execute('SELECT good,bad,reason,inferior FROM tobedeleted'):
                bads.append(bad)
                dbdelete(good,bad,reason,inferior)
                if next(counter) % 4 == 0:
                    # commit every 4 images or so
                    done = False
                    break

            for category in ('image','thumb','resized'):
                place=os.path.join(filedb.top,category)
                for bad in bads:
                    doomed = os.path.join(place,'{:x}'.format(bad))
                    # if we crash here, transaction will abort and the images will be un-deleted
                    # but will get deleted next time so that the files are cleaned up
                    if os.path.exists(doomed):
                        os.unlink(doomed)

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
        import clipboardy
        reason = os.environ['reason']
        def gotPiece(piece):
            try:
                delete(findId(piece),reason)
            except ValueError: pass
        try: clipboardy.run(gotPiece)
        except KeyboardInterrupt: pass
    commit()
