#!/usr/bin/env python3

import db
import delete

import sys,os

# note using LEAST leaves the old one in order
# using MOST moves the old one to where the new one was.

def merge(dest,source,inferior=True):
    "source is destroyed, its info sent to dest"
    with db.transaction():
        db.execute("UPDATE things SET neighbors = array(SELECT unnest(neighbors) UNION SELECT unnest(things2.neighbors) FROM things as things2 where things2.id = $2) WHERE id = $1",
                (dest,source))
        
        # this will make it appear as if the newer medium is kept, but possibly with the older id
        db.execute("SELECT mergeAdded($1,$2)",(dest,source))
        db.execute("""UPDATE media as m1 SET sources = array(SELECT unnest(m1.sources) UNION SELECT unnest(m2.sources)), created = LEAST(m1.created,m2.created), modified = LEAST(m1.modified,m2.modified) FROM media AS m2 WHERE  m2.id = $2 AND m1.id = $1""",
                (dest,source))
        # created/modified not unique, so can just smash them through

        print('updatan')
        db.execute("UPDATE media SET sources = NULL WHERE id = $1",(source,)) 
        # don't delete the sources, they pass to the dest!

        db.execute("UPDATE comicpage SET medium = $1 WHERE medium = $2",
                (dest,source))
        db.execute("UPDATE desktops SET id = $1 WHERE id = $2 AND NOT EXISTS(SELECT id FROM desktops WHERE id = $1)",    
                (dest,source))
        db.execute("""WITH updoot AS (UPDATE visited as v1 SET visits = v1.visits + v2.visits FROM visited as v2 WHERE v1.medium = $1 AND v2.medium = $2 AND v1.uzer = v2.uzer RETURNING v2.id)
        DELETE FROM visited WHERE id IN (SELECT id FROM updoot)""",
                (dest,source))
        # the following statement won't hit unique violations, because we updated/deleted them 
        # in the staement above.
        db.execute("UPDATE visited SET medium = $2 WHERE medium = $1",                
                (dest,source))
        db.execute("UPDATE uploads as u1 SET media = $1 WHERE media = $2 AND NOT EXISTS(SELECT * FROM uploads as u2 WHERE media = $1 AND uzer = u1.uzer)",
                (dest,source))
        print('deletan')
        # the leftover uploads will be deleted by cascade
        delete.dupe(dest, source, inferior)

def main():
    #note b will be DESTROYED and a should be the good one.
    a = delete.findId(sys.argv[1])
    b = delete.findId(sys.argv[2])
    merge(a,b,'identical' in os.environ)

if __name__ == '__main__': main()
