
import versions,db
import filedb

import signal
import io
from contextlib import contextmanager
from functools import reduce
import re
import time

v = versions.Versioner('movies')

# defaultTags means when there is no tags for a user, use the default ones as implied tags.
# defaultTags=False means when there are no tags, have no implied tags.

class VersionHolder:
    @v(version=1)
    def initially():
        db.setup('''CREATE TABLE videos (
        id bigint PRIMARY KEY REFERENCES things(id),
        width integer,
        height integer,
        fps float,
        vcodec text,
        acodec text,
        container text)''')

v.setup()

@contextmanager
def process(*a):
    import subprocess as s
    pid = None
    try:
        pid = s.Popen(a,stderr=s.PIPE)
        yield pid
    except:
        import traceback
        traceback.print_exc()
    finally:
        if pid:
            pid.terminate()
            oldsig = None
            try:
                oldsig = signal.signal(signal.SIGALRM,signal.SIG_IGN)
                if pid.wait(): return
            except ValueError:
                time.sleep(1)
            finally:
                if oldsig:
                    signal.signal(signal.SIGALRM,oldsig)
            pid.kill()
            pid.wait()

ffmpegcrap = {
        'videoline': re.compile('Stream #.*Video: ([^ ]+)'),
        'audio': re.compile('Stream #.*Audio: ([^ ]+)'),
        'dimensions': re.compile('([1-9][0-9]+)x([0-9]+)'),
        'fps': re.compile('([.0-9]+) fps'),
        'container': re.compile('Input #[0-9]+, ([^ ]+)'),
        'convert': {}
}


def conversion(ff,info):
    for derp in ff.split(','):
        if derp:
            ffmpegcrap['convert'][derp] = info

def lookup(ff):
    for derp in ff.split(','):
        if derp:
            derp = ffmpegcrap['convert'].get(derp)
            if derp: return derp


conversion("mov,mp4,m4a,3gp,3g2,mj2,",("video/mp4","mp4"))
conversion("matroska,webm",("video/webm","webm"))

def ffmpegInfo(thing):
    info = {}
    with process("ffmpeg","-i",filedb.imagePath(thing)) as pid:
        inp = io.TextIOWrapper(pid.stderr)
        while True:
            line = inp.readline()
            if not line: 
                break
            m = ffmpegcrap['videoline'].search(line)
            if m:
                info['vcodec'] = m.group(1)
                m = ffmpegcrap['dimensions'].search(line)
                info['width'] = int(m.group(1))
                info['height'] = int(m.group(2))
                m = ffmpegcrap['fps'].search(line)
                info['fps'] = float(m.group(1))
            else:
                m = ffmpegcrap['audio'].search(line)
                if m:
                    info['acodec'] = m.group(1)
                else:
                    m = ffmpegcrap['container'].search(line)
                    if m:
                        info['container'] = lookup(m.group(1))

    return info

        


def isMovie(thing,getInfo=ffmpegInfo):
    id = db.c.execute("SELECT id FROM videos WHERE id = $1",(thing,))
    if id: return id[0][0]

    info = getInfo(thing)
    info['id'] = thing

    keys,values = zip(*info.items())

    id = db.c.execute("INSERT INTO videos ("+",".join(keys)+") VALUES ("+",".join("$"+str(i+1) for i in range(len(keys)))+") RETURNING id",values)
    return id[0][0]

