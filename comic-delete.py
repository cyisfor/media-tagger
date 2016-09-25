import db
import sys

comic, which = sys.argv[1:]
comic = int(comic,0x10)
which = int(which,0x10)

with db.transaction():
	db.execute("DELETE FROM comicpage WHERE comic = $1 AND which = $2",
	           (comic, which))
	db.execute("DROP INDEX unique_pages");
	db.execute("""UPDATE comicpage
	SET which = which - 1
	WHERE comic = $1 AND
	which > $2
	""", (comic, which))
	db.execute("CREATE UNIQUE INDEX unique_pages ON comicpage(comic,which)")
