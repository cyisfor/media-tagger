import db

db.source('sql/searchcache.sql',False)

table = db.execute("SELECT searchcache.query($1,$2)",
                   (tags.posi,tags.nega))

for id in db.execute("SELECT id FROM searchcache."+table):
	print(id)
