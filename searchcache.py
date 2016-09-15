import db
import tags

tags = tags.parse("apple bloom, evil, -scootaloo, -character:scootaloo");

db.source('sql/searchcache.sql',False)

table = db.execute("SELECT searchcache.query($1,$2)",
                   (tags.posi,tags.nega))[0][0]
print(db.execute("SELECT count FROM searchcache.queries WHERE name = $1",
                 (table,)))

