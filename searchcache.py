import db
import tags

tags = tags.parse("apple bloom, -scootaloo");

db.source('sql/searchcache.sql',False)

table = db.execute("SELECT searchcache.query($1,$2)",
                   (tags.posi,tags.nega))[0][0]
print(table)
print(db.execute("SELECT COUNT(id) FROM searchcache."+table)[0][0])
