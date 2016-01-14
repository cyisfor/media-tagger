import db
from version import Versioner
import filedb

from itertools import count
import sys,os

version = Versioner('delete')

@version(1)
def _():
    db.setup('''CREATE TABLE blacklist(
        id SERIAL PRIMARY KEY,
        hash character varying(28) UNIQUE,
        reason TEXT)''',
             '''CREATE TABLE dupes(
        id SERIAL PRIMARY KEY,
        medium bigint REFERENCES media(id),
        hash character varying(28) UNIQUE,
        inferior BOOLEAN DEFAULT FALSE,
        UNIQUE(medium,hash))''')

@version(2)
def _():
    # batch clearing of neighbors for deleting
    db.setup(
            '''CREATE TABLE IF NOT EXISTS doomed (
            id bigint PRIMARY KEY REFERENCES things(id) ON DELETE CASCADE)
            ''',
            '''ALTER TABLE blacklist ADD COLUMN oldmedium bigint UNIQUE''',
            '''ALTER TABLE dupes ADD COLUMN oldmedium bigint UNIQUE''')

def start(s):
    sys.stdout.write(s+'...')
    sys.stdout.flush()

def done(s=None):
    if s is None: s = 'done.'
    print(s)


def commitDoomed():
    start("tediously clearing neighbors")
    # it's way less lag if we break this hella up
    with db.transaction():
        db.execute('UPDATE things SET neighbors = array(SELECT unnest(neighbors) EXCEPT SELECT id FROM doomed) WHERE neighbors && array(SELECT id FROM doomed)')
        db.execute("DELETE FROM sources USING media WHERE media.id in (select id from doomed) AND sources.id = ANY(media.sources)")
        db.execute("DELETE FROM things WHERE id in (select id from doomed)")
    done()

commitDoomed()

def dbdelete(good,bad,reason,inferior):
    print("deleting {:x}".format(bad),'dupe' if good else reason)
    # the old LEFT OUTER JOIN trick to skip duplicate rows
    if good:
        # XXX: this is bad and I feel bad...
        db.execute("INSERT INTO dupes (oldmedium,medium,hash,inferior) SELECT $2, $1,media.hash,$3 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(good, bad, inferior))
    else:
        db.execute("INSERT INTO blacklist (oldmedium,hash,reason) SELECT $2,media.hash,$1 from media LEFT OUTER JOIN blacklist ON media.hash = blacklist.hash where blacklist.id IS NULL AND media.id = $2",(reason,bad))
    db.execute('INSERT INTO doomed (id) VALUES ($1)',(bad,))


def filedelete(bad):
    for category in ('image','thumb','resized'):
        place=os.path.join(filedb.top,category)
        doomed = os.path.join(place,'{:x}'.format(bad))
        # if we crash here, transaction will abort and the images will be un-deleted
        # but will get deleted next time so that the files are cleaned up
        if os.path.exists(doomed):
            os.unlink(doomed)

def dupe(good, bad, inferior=True):
    with db.transaction():
        dbdelete(good,bad,None,inferior)
        filedelete(bad)

def delete(thing, reason=None):
    print('deleting',thing,reason)
    with db.transaction():
        dbdelete(None, thing, reason, False)
        filedelete(thing)

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
            print('derp',piece)
            try:
                delete(findId(piece),reason)
            except ValueError: pass
        try: clipboardy.run(gotPiece)
        except KeyboardInterrupt: pass
