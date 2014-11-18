#!/usr/bin/python3
from db import c
import db

def setup():
    db.setup("""CREATE TABLE desktops (
id bigint PRIMARY KEY REFERENCES images(id),
selected timestamptz DEFAULT clock_timestamp() NOT NULL)""",
    "CREATE UNIQUE INDEX orderDesktops ON desktops (added DESC)");

def history(n=0x10):
    return [row[0] for row in c.execute("SELECT id FROM desktops ORDER BY selected DESC LIMIT $1",(n,))]

def next(clean=True,tries=0):
    r = c.execute("""INSERT INTO desktops (id)
    SELECT images.id FROM images INNER JOIN things ON images.id = things.id
    WHERE images.id NOT IN (SELECT id FROM desktops)
        AND ( (NOT $1) OR (
                neighbors && array(SELECT id FROM tags WHERE name IN
                    ('special:safe','rating:safe','clean'))) )
        AND NOT neighbors && array(SELECT id FROM tags
            WHERE name = 'special:rl')
        AND height > 600
        AND width > 800
        AND ratio < 1.8
        AND ratio > 0.8
        ORDER BY random() LIMIT 1 RETURNING desktops.id""",(clean,))
    if not r:
        if tries >= 2:
            raise RuntimeError("Couldn't find any desktops!!")
        c.execute("DELETE FROM desktops")
        return next(clean,tries+1)
    return r[0][0]

if __name__ == '__main__':
    import shutil,os,filedb
    setup()
    id = next()
    desktop = os.path.expanduser("/usr/share/nginx/html/desktop/desktop")
    try: os.unlink(desktop)
    except OSError: pass
    # Can't use filedb.mediaPath why...?
    shutil.copy2(os.path.join(filedb.top,"media",'{:x}'.format(id)),desktop)
    os.execlp("xfdesktop","xfdesktop","--reload")
