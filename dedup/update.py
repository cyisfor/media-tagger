import filedb
import db
import versions

from itertools import count
import subprocess as s
import sys,time,os

version = versions.Versioner('media')

@version(1337)
def addColumn():
    db.execute('ALTER TABLE media ADD COLUMN pHash uuid')
@version(1338)
def addColumn():
    db.setup(
        'ALTER TABLE media RENAME COLUMN pHash TO derpHash',
        'ALTER TABLE media ADD COLUMN pHashFail BOOLEAN DEFAULT FALSE',
        'ALTER TABLE media ADD COLUMN pHash int8',
        ''''UPDATE media SET 
    phash = ('x' || substring(uuid_send(derpHash) from 10))::bit(64)::int8, 
    pHashFail = (('x' || substring(uuid_send(derpHash) from 10))::bit(64)::int8 = 2)''',
        '''CREATE TABLE nadupes (
    sis bigint primary key references media(id),
    bro bigint primary key references media(id),
    UNIQUE(sis,bro)
);''',
        '''INSERT INTO nadupes SELECT a.id,b.id FROM media as a, media as b
             WHERE a.id > b.id AND a.phash = b.phash AND (('x' || substring(uuid_send(derpHash) from 1 for 8))::bit(64)::int8 = 3)''')
#        'ALTER TABLE media DROP COLUMN derpHash'

version.setup()

gen = None


def timeify(seconds):
    seconds = int(seconds)
    s = None
    if seconds > 3600:
        hours = seconds // 3600
        s = '{:d}h'.format(hours)
        seconds = seconds % 3600
    if seconds > 60:
        minutes = seconds // 60
        if s:
            s = s + ' {:d}m'.format(minutes)
        else:
            s = '{:d}m'.format(minutes)
        seconds = seconds % 60
    if seconds:
        if s:
            s = s + ' {:d}s'.format(seconds)
        else:
            s = '{:d}s'.format(seconds)
    if not s:
        return 'NOW'
    return s

def create(hid):
    global gen
    if gen is None:
        gen = s.Popen(['./create'],stdin=s.PIPE,stdout=s.PIPE)
        assert(gen)
        gen.stdin.write((filedb.mediaPath()+'\n').encode());
    gen.stdin.write((hid+'\n').encode())
    gen.stdin.flush()
    return gen.stdout.readline().decode().rstrip()

lastlen = 0
def status(s):
    global lastlen
    if lastlen:
        diff = lastlen - len(s)
        if diff > 0:
            sys.stdout.write('\b'*diff+' '*diff)
    lastlen = len(s)
    sys.stdout.write('\r'+s)
    sys.stdout.flush()

if __name__ == '__main__':
    start = time.time()
    total = db.execute('SELECT count(id) FROM media WHERE pHash IS NULL')[0][0]
    achieved = None
    timespent = 0
    if os.path.exists('last'):
        with open('last') as inp:
            achieved = int(inp.readline())
            timespent = float(inp.readline())
    elif os.path.exists('last.temp'):
        with open('last.temp') as inp:
            achieved = count(int(inp.readline()))
            timespent = float(inp.readline())
    counter = count(0)
    achieved = achieved or 1
    elapsed = 0
    current = 0
    for id, in db.execute('SELECT id FROM media WHERE pHash IS NULL ORDER BY id'):
        hid = '{:x}'.format(id)
        status(hid+' '+timeify((total - current) * (timespent + elapsed) / achieved)+' left')
        pHash = create(hid)
        elapsed = time.time() - start
        current = next(counter)
        with open('last.temp','w') as out:
            out.write('{}\n'.format(achieved + current))
            out.write('{}\n'.format(timespent + elapsed))
        os.unlink('last')
        os.rename('last.temp','last')
        if (pHash == 'ERROR'):
            db.execute('UPDATE media SET pHashFail = TRUE WHERE id = $1',(id,))
        else:
            db.execute('UPDATE media SET pHash = $1::bit(64)::int8 WHERE id = $2',(pHash,id))
