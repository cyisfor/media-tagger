import filedb
import db
import versions

from itertools import count
import subprocess as s
import sys,time,os

oj = os.path.join

here = os.path.dirname(sys.argv[0]) or os.curdir

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
        '''UPDATE media SET 
    phash = ('x' || encode(substring(uuid_send(derpHash) from 10),'hex'))::bit(64)::int8, 
        pHashFail = (('x' || encode(substring(uuid_send(derpHash) from 1 for 8),'hex'))::bit(64)::int8 = 2)''',
        '''CREATE TABLE nadupes (
        id serial primary key,
    sis bigint references media(id),
    bro bigint references media(id),
    UNIQUE(sis,bro)
);''',
        '''INSERT INTO nadupes (sis,bro) SELECT a.id,b.id FROM media as a, media as b 
             WHERE a.id > b.id AND a.phash = b.phash AND (('x' || encode(substring(uuid_send(a.derpHash) from 1 for 8),'hex'))::bit(64)::int8 = 3) AND (('x' || encode(substring(uuid_send(b.derpHash) from 1 for 8),'hex'))::bit(64)::int8 = 3)''')
#        'ALTER TABLE media DROP COLUMN derpHash'

@version(1339)
def _():
    db.setup('ALTER TABLE media ADD COLUMN mh_hash bit varying')
    
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
        gen = s.Popen([oj(here,'create')],stdin=s.PIPE,stdout=s.PIPE)
        assert(gen)
        gen.stdin.write((filedb.mediaPath()+'\n').encode());
    gen.stdin.write((hid+'\n').encode())
    gen.stdin.flush()
    return gen.stdout.readline().decode().rstrip()

mh_gen = None
def createMH(hid):
    global mh_gen
    if mh_gen is None:
        mh_gen = s.Popen([oj(here,'mh_create')],stdin=s.PIPE,stdout=s.PIPE)
        assert(mh_gen)
        mh_gen.stdin.write((filedb.mediaPath()+'\n').encode());
    mh_gen.stdin.write((hid+'\n').encode())
    mh_gen.stdin.flush()
    return mh_gen.stdout.readline().decode().rstrip()

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
        total = db.execute('SELECT count(id) FROM media WHERE NOT pHashFail AND pHash IS NULL')[0][0]
        achieved = 0
        timespent = 0
        if os.path.exists('last'):
                with open('last') as inp:
                        achieved = int(inp.readline())
                        timespent = float(inp.readline())
        elif os.path.exists(oj(here,'last.temp')):
                with open(oj(here,'last.temp')) as inp:
                        achieved = int(inp.readline())
                        timespent = float(inp.readline())
        counter = count(0)
        elapsed = 0
        current = 0
        where = '''FROM media WHERE 
NOT pHashFail AND 
pHash IS NULL AND
type = ANY($1)'''
        types = ['image/png','image/jpeg']
        which = count(1)
        with db.transaction():
            totalderp = db.execute('SELECT COUNT(1) '+where,(types,))[0][0]
            for id, in db.execute('SELECT id ' + where + 'ORDER BY id',(types,)):
                hid = '{:x}'.format(id)
                status(str(next(which))+'/'+str(totalderp)+' '+ hid+' '+timeify((total - current) * (timespent + elapsed) / (achieved if achieved else 1))+' left')
                if not os.path.exists(filedb.mediaPath(id)):
                        print('uhhh',hid)
                        raise SystemExit
                current = next(counter)
                if (current+1)%10==0:
                        db.retransaction()
                        with open('last.temp','w') as out:
                                out.write('{}\n'.format(achieved))
                                out.write('{}\n'.format(timespent + elapsed))
                        try: os.unlink('last')
                        except OSError: pass
                        os.rename('last.temp','last')
                        print('retransaction')
                pHash = create(hid)
                elapsed = time.time() - start
                if (pHash == 'ERROR'):
                        print('err')
                        db.execute('UPDATE media SET pHashFail = TRUE WHERE id = $1',(id,))
                else:
                        db.execute('UPDATE media SET pHash = $1::bit(64)::int8 WHERE id = $2',('x'+pHash,id))
                achieved = achieved + 1

        where = '''FROM media WHERE
    NOT phashFail AND
    mh_hash IS NULL AND
    pHash = 0 AND
    type = ANY($1)'''
        totalderp = db.execute('SELECT COUNT(1) '+where,(types,))[0][0]
        which = count(1)
        for id, in db.execute('SELECT id '+where+' ORDER BY id',(types,)):
            hid = '{:x}'.format(id)
            print("need mh hash for",hid,"{}/{}".format(next(which),totalderp))
            mh_hash = createMH(hid)
            assert(mh_hash != 'ERROR')
            db.execute("UPDATE media SET mh_hash = $1::bit(576) WHERE id = $2",('x'+mh_hash,id))
            db.retransaction()

