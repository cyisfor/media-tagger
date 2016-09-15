import db
import tags

tags = tags.parse("apple bloom, -scootaloo, -character:scootaloo");

db.source('sql/searchcache.sql',False)

table = db.execute("SELECT searchcache.query($1,$2)",
                   (tags.posi,tags.nega))[0][0]
print(db.execute("SELECT count FROM searchcache.queries WHERE name = $1",
                 (table,)))
for id, in db.execute("SELECT id FROM searchcache."+table):
	print('<a href="http://cy.h/art/~page/{:x}"><img src="http://cy.h/thumb/{:x}" /></a>'.format(id,id))
