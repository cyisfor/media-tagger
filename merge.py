#!/usr/bin/env python

import db
from delete import delete, findId

import sys,os

# note using LEAST leaves the old one in order
# using MOST moves the old one to where the new one was.

db.setup("""CREATE OR REPLACE FUNCTION mergeAdded(_a bigint, _b bigint) RETURNS VOID AS
$$
DECLARE
_aadd timestamptz;
_badd timestamptz;
BEGIN
    _aadd := added FROM media WHERE id = _a;
    _badd := added FROM media WHERE id = _b;
    UPDATE media SET added = NULL WHERE id = _b;
    UPDATE media SET added = GREATEST(_aadd,_badd) WHERE id = _a;
END
$$ language 'plpgsql'""")


def merge(dest,source):
    with db.transaction():
        db.c.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(things2.neighbors) FROM things as things2 where things2.id = $2) WHERE id = $1",
                (dest,source))
        db.c.execute("SELECT mergeAdded($1,$2)",(dest,source))
        db.c.execute("""UPDATE media as m1 SET sources = array(SELECT unnest(m1.sources) UNION SELECT unnest(m2.sources)), created = LEAST(m1.created,m2.created), modified = LEAST(m1.modified,m2.modified) FROM media AS m2 WHERE  m2.id = $2 AND m1.id = $1""",
                (dest,source))
        db.c.execute("UPDATE comicpage SET image = $1 WHERE image = $2",
                (dest,source))
        db.c.execute("UPDATE desktops SET id = $1 WHERE id = $2 AND NOT EXISTS(SELECT id FROM desktops WHERE id = $1)",    
                (dest,source))
        db.c.execute("""WITH updoot AS (UPDATE visited as v1 SET visits = v1.visits + v2.visits FROM visited as v2 WHERE v1.medium = $1 AND v2.medium = $2 AND v1.uzer = v2.uzer RETURNING v2.id)
        DELETE FROM visited WHERE id IN (SELECT id FROM updoot)""",
                (dest,source))
        # the following statement won't hit unique violations, because we updated/deleted them 
        # in the staement above.
        db.c.execute("UPDATE visited SET medium = $2 WHERE medium = $1",                
                (dest,source))
        db.c.execute("UPDATE uploads as u1 SET media = $1 WHERE media = $2 AND NOT EXISTS(SELECT * FROM uploads as u2 WHERE media = $1 AND uzer = u1.uzer)",
                (dest,source))
        # the leftover uploads will be deleted by cascade
        delete(source,os.environ.get('reason','dupe of {:x}'.format(dest)))

def main():
    a = findId(sys.argv[1])
    b = findId(sys.argv[2])
    merge(min(a,b),max(a,b))

if __name__ == '__main__': main()
