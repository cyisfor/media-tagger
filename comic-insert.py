import db
import sys

comic, which, medium = sys.argv[1:]
comic = int(comic,0x10)
which = int(which,0x10)
medium = int(medium,0x10)

with db.transaction():
    db.execute("DELETE FROM comicpage WHERE comic = $1 AND medium = $2",
               (comic, medium))
    db.execute("DROP INDEX unique_pages");
    db.execute("""UPDATE comicpage
    SET which = which + 1
    WHERE comic = $1 AND
    which >= $2
    """, (comic, which))
    for row in db.execute("SELECT which FROM comicpage WHERE comic = $1 ORDER BY which",(comic,)):
        print(row[0])
    db.execute("INSERT INTO comicpage (comic,which,medium) VALUES ($1,$2,$3)",
               (comic, which, medium))
    db.execute("CREATE UNIQUE INDEX unique_pages ON comicpage(comic,which)")
